"""Agent boundary regressions; no live credentials or paid calls required."""
import json
from dataclasses import replace

import pytest

from deletion_audit.ai_auditor import AuditInvestigator, compact
from deletion_audit.inputs import InputError
from deletion_audit.investigator import TOOL_SCHEMAS
from deletion_audit.observations import EvidenceStore
from deletion_audit.proposals import (FACT, POLICY_CATEGORIES, apply_grounded_updates,
                                     fact_signature, validate_json)
from deletion_audit.providers import Provider
from test_ai_foundation import api_tools, fact, proposal, chat, ProviderConfig


def test_case17_shaped_thirteen_observations_page_without_silent_loss():
    tools = api_tools()
    source = tools.store.observations[0]
    store = EvidenceStore()
    # Thirteen subject-linked observations, including newer contradictory readbacks.
    store.add(replace(source, observation_id=f"readback_{i:02}",
                      observed_at=source.observed_at.replace(hour=i),
                      fields={**source.fields, "status": "ABSENT" if i == 12 else "PRESENT",
                              "long_original": "x" * 2100}) for i in range(13))
    tools = replace(tools, store=store)
    page = compact(tools.search_evidence("user_id", "user_fixture"))
    assert page["total_count"] == page["total"] == 13
    assert page["shown_count"] == len(page["observations"]) == 12
    assert page["truncated"] and page["next_cursor"]
    assert page["observations"][0]["observation_id"] == "readback_12"
    assert len(page["observations"][0]["fields"]["long_original"]) == 2100
    second = tools.search_evidence("user_id", "user_fixture", cursor=page["next_cursor"])
    assert second["shown_count"] == 1 and not second["truncated"] and second["next_cursor"] is None
    assert len({o["observation_id"] for p in [page, second] for o in p["observations"]}) == 13
    with pytest.raises(InputError, match="CURSOR"):
        tools.search_evidence("user_id", "unknown", cursor=page["next_cursor"])


def test_resource_schema_requires_system_but_identifier_queries_do_not():
    schema = TOOL_SCHEMAS[0]["parameters"]
    for value in [{"kind": "resource", "value": "opaque"},
                  {"kind": "resource", "value": "opaque", "system_id": ""}]:
        with pytest.raises(InputError):
            validate_json(value, schema)
    validate_json({"kind": "resource", "value": "opaque", "system_id": "account_service"}, schema)
    validate_json({"kind": "email", "value": "person@example.test"}, schema)


def test_categories_equal_supplied_vocabulary_and_data_flow():
    assert set(POLICY_CATEGORIES) == set(api_tools().policy.rules) | {"DATA_FLOW"}
    value = fact(api_tools().store.observations[0]); value["category"] = "OBJECT_STORAGE_FILE"
    with pytest.raises(InputError, match="category"):
        validate_json(value, FACT)


def agent_with_responses(tmp_path, monkeypatch, responses, **kwargs):
    monkeypatch.setenv("LLM_ENABLED", "true")
    agent = AuditInvestigator(tmp_path / "dataset", "deepseek", cache=tmp_path / "cache", **kwargs)
    histories = []
    def transport(url, body, headers, timeout):
        histories.append(body)
        return responses.pop(0)
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test"), agent.ledger, transport)
    return agent, histories


BASELINE = {"issues": [{"code": "NO_DIRECT_STATE"}], "resource_keys": [["account_service", "opaque"]]}


def test_invalid_arguments_do_not_consume_tool_budget_and_round_trace_is_linked(tmp_path, monkeypatch):
    calls = [{"id": str(i), "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}
             for i, (name, args) in enumerate([
                 ("search_evidence", {"kind": "resource", "value": "opaque"}), ("trace_identity", {})])]
    agent, _ = agent_with_responses(tmp_path, monkeypatch, [chat(calls=calls), chat(json.dumps(proposal()))], max_tools=1)
    agent.investigate(api_tools(), BASELINE)
    trace = agent.events[-1]["tool_trace"]
    assert not trace[0]["budget_consumed"] and trace[1]["budget_consumed"]
    assert trace[1]["result"]["users"] == ["user_fixture"]
    first = agent.events[-1]["rounds"][0]
    assert len(first["context_hash"]) == 64 and len(first["tool_call_batch"]) == 2
    assert agent.ledger.records[0]["call_id"] == first["call_id"] == trace[0]["model_call_id"]


def test_grounding_error_gets_one_correction_without_relaxing_source_checks(tmp_path, monkeypatch):
    tools = api_tools(); bad = fact(tools.store.observations[0]); bad["state"] = "ABSENT"
    good = fact(tools.store.observations[0])
    agent, histories = agent_with_responses(tmp_path, monkeypatch,
        [chat(json.dumps(proposal([bad]))), chat(json.dumps(proposal([good])))])
    assert agent.investigate(tools, BASELINE) == []  # existing fact remains a duplicate
    assert len(histories) == 2 and "tools" not in histories[-1]
    assert "PROPOSED_STATE_OR_CATEGORY_NOT_IN_SOURCE" in histories[-1]["messages"][-2]["content"]
    event = agent.events[-1]
    assert event["grounding_attempts"][0]["validation"] == "REJECTED"
    assert event["grounding_attempts"][1]["validation"] == "SOURCE_GROUNDED"
    assert event["accepted"][0]["new_fact"] is False


def test_repeated_bad_grounding_cannot_extend_turn_budget(tmp_path, monkeypatch):
    tools = api_tools(); bad = fact(tools.store.observations[0]); bad["state"] = "ABSENT"
    agent, histories = agent_with_responses(tmp_path, monkeypatch,
        [chat(json.dumps(proposal([bad]))), chat(json.dumps(proposal([bad])))])
    assert agent.investigate(tools, BASELINE) == []
    assert len(histories) == 2 and agent.events[-1]["rejected"]


def test_same_identifier_enrichment_replaces_case_copy_and_rejects_source_changes():
    tools = api_tools(); source = tools.store.observations[0]
    source = replace(source, provenance={"sha256": "imagehash", "raw": source.fields})
    store = EvidenceStore(); store.add([source])
    update = replace(source, scope={**source.scope, "vision_corroborated": True,
                     "provider": "gemini", "model": "fixture", "vision_image_sha256": "imagehash"})
    local = apply_grounded_updates(store, [update], tools.request.audit_at)
    assert len(local.observations) == 1 and local.observations[0] == update
    assert local.by_resource[(source.system_id, source.resource_id)][0].scope["vision_corroborated"]
    assert store.observations == [source] and "vision_corroborated" not in source.scope
    assert fact_signature(source) == fact_signature(update)
    assert update.observation_id == source.observation_id and update.provenance == source.provenance
    with pytest.raises(InputError, match="IMMUTABLE"):
        apply_grounded_updates(store, [replace(update, fields={"status": "ABSENT"})], tools.request.audit_at)
    with pytest.raises(InputError, match="CUTOFF"):
        apply_grounded_updates(store, [replace(update, captured_at=source.captured_at.replace(year=2030))], tools.request.audit_at)


def test_solver_actually_receives_existing_observation_metadata(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from deletion_audit import solver
    from deletion_audit.providers import UsageLedger
    from test_solver import ROOT
    tools = api_tools(); source = tools.store.observations[0]
    source = replace(source, provenance={"sha256": "imagehash", "raw": source.fields})
    store = EvidenceStore(); store.add([source])
    update = replace(source, scope={"vision_corroborated": True, "provider": "gemini",
                                    "model": "fixture", "vision_image_sha256": "imagehash"})
    subject = replace(tools.request, case_id="case_999")
    monkeypatch.setattr(solver, "ingest", lambda _: store)
    monkeypatch.setattr(solver, "enrich", lambda _: None)
    monkeypatch.setattr(solver, "load_requests", lambda *args: {subject.case_id: subject})
    monkeypatch.setattr(solver.IdentityGraph, "load", lambda *args: tools.graph)
    received = []
    original_decide = solver.decide_case
    def inspect(request, evidence, graph, policy):
        received.append(evidence.observations[0])
        return original_decide(request, evidence, graph, policy)
    monkeypatch.setattr(solver, "decide_case", inspect)
    agent = SimpleNamespace(investigate=lambda *args: [update], events=[], ledger=UsageLedger())
    report = solver.solve(ROOT / "dataset", "sample", tmp_path / "candidate.csv", ai=agent)
    assert received == [source, update]
    assert report["cases"][0]["accepted_ai_observations"] == [source.observation_id]
    assert store.observations == [source]


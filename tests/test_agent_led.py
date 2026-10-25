"""Blind context, independently grounded certificates and noncircular obligation checks."""
import copy
import json
from dataclasses import replace
from types import SimpleNamespace

import pytest

from deletion_audit.agent_led import blind_context, grounded, verify, SCHEMA
from deletion_audit.ai_auditor import AuditInvestigator
from deletion_audit.inputs import InputError
from deletion_audit.proposals import validate_json
from deletion_audit.providers import Provider
from deletion_audit.ai_config import ProviderConfig
from deletion_audit.solver import solve
from test_ai_foundation import api_tools, fact, chat
from test_audit_recommendations import recommendation


def draft(tools=None):
    result = recommendation(tools)
    result["proof_certificates"] = []
    return result


def certificate(tools):
    source = tools.store.observations[0]
    return {"claim_type": "EXPLICIT_STATE", "fact": fact(source), "subject_user_id": "user_fixture",
        "captured_at": source.captured_at.isoformat(), "limitations": "This exact captured profile only"}


def test_blind_context_has_sources_policy_and_no_baseline_conclusions():
    context = blind_context(api_tools())
    assert {"policy_definitions", "source_index", "proof_goals", "identity"} <= context.keys()
    assert not {"baseline", "submission_status", "resource_states", "issues", "steps"} & context.keys()
    assert context["coverage"]["shown_count"] == len(context["source_index"])
    assert all(s["inspect_source_available"] == bool(s["file_id"]) for s in context["source_index"])


def test_independent_verifier_never_calls_decide_case(monkeypatch):
    value = draft()
    def forbidden(*a, **k): raise AssertionError("baseline authority leaked")
    monkeypatch.setattr("deletion_audit.solver.decide_case", forbidden)
    result = verify(value, api_tools())
    assert result["validation"] == "ACCEPTED"
    assert result["independent_status"] == "INCOMPLETE"
    assert not result["baseline_agreement_is_acceptance_rule"]


def test_supported_steps_survive_missing_plan_obligation():
    value = draft(); value["audit_recommendation"]["proposed_verifications"] = []
    result = verify(value, api_tools())
    assert result["validation"] != "ACCEPTED" and not result["plan_scope_complete"]
    assert len(result["step_validation"]) == 2
    assert all(s["validation"] == "SOURCE_POLICY_GROUNDED" for s in result["step_validation"])
    assert result["missing_obligations"][0]["operation"] == "VERIFY_RECORD_ABSENT"


def test_source_certificate_is_checked_and_duplicate_not_counted_new():
    tools = api_tools(); value = draft(tools); value["proof_certificates"] = [certificate(tools)]
    updates, _, certs = grounded(value, tools)
    assert updates == [] and certs[0]["validation"] == "SOURCE_GROUNDED"
    assert certs[0]["proof_delta"] == "duplicate"


@pytest.mark.parametrize("field,value", [("captured_at", "2027-01-01T00:00:00Z"),
    ("subject_user_id", "other")])
def test_certificate_cannot_invent_capture_or_subject(field, value):
    tools = api_tools(); proposal = draft(tools); cert = certificate(tools); cert[field] = value
    proposal["proof_certificates"] = [cert]
    assert grounded(proposal, tools)[2][0]["validation"] == "REJECTED"
    assert verify(proposal, tools)["validation"] != "ACCEPTED"


def test_certificate_cannot_broaden_positive_readback_to_negative_scope():
    tools = api_tools(); value = draft(tools); cert = certificate(tools); cert["claim_type"] = "NEGATIVE_SCOPE"
    value["proof_certificates"] = [cert]
    assert grounded(value, tools)[2][0]["reason"] == "CERTIFICATE_NEGATIVE_SCOPE_NOT_DECLARED"


def test_unsupported_semantic_interpretation_stays_outside_certificate_schema():
    tools = api_tools(); value = draft(tools); cert = certificate(tools); cert["claim_type"] = "FUZZY_IDENTITY"
    value["proof_certificates"] = [cert]
    with pytest.raises(InputError): validate_json(value, SCHEMA)


def test_future_source_and_fake_citation_are_not_accepted():
    tools = api_tools(); value = draft(tools)
    value["audit_recommendation"]["proposed_findings"][0]["evidence_id"] = "invented"
    assert verify(value, tools)["step_validation"][0]["validation"] == "REJECTED"
    source = tools.store.observations[0]
    from deletion_audit.observations import EvidenceStore
    store = EvidenceStore(); store.add([replace(source, captured_at=source.captured_at.replace(year=2027))])
    assert verify(draft(tools), replace(tools, store=store))["validation"] != "ACCEPTED"


def test_false_complete_is_rejected_by_obligations():
    value = draft(); value["audit_recommendation"]["recommended_deletion_status"] = "COMPLETE"
    assert "VERDICT_NOT_SUPPORTED_BY_OBLIGATIONS" in {r["code"] for r in verify(value, api_tools())["issues"]}


def test_real_loop_first_request_is_blind_and_baseline_comparison_is_later(tmp_path, monkeypatch):
    tools = api_tools(); monkeypatch.setenv("LLM_ENABLED", "true")
    agent = AuditInvestigator(tmp_path / "dataset", "agent-led", cache=tmp_path / "cache",
        case_ids=[tools.request.case_id], max_rounds=3)
    histories = []
    def transport(url, body, headers, timeout):
        histories.append(copy.deepcopy(body)); return chat(json.dumps(draft(tools)))
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test"), agent.ledger, transport)
    baseline = {"issues": [], "resource_keys": [["account_service", "opaque"]],
                "submission_status": "COMPLETE", "steps": ["BASELINE_SENTINEL_DO_NOT_LEAK"]}
    agent.investigate(tools, baseline)
    assert "BASELINE_SENTINEL_DO_NOT_LEAK" not in json.dumps(histories[0])
    first_context = json.loads(histories[0]["messages"][1]["content"])
    assert "baseline" not in first_context
    event = agent.events[-1]
    assert event["recommendation_validation"]["validation"] == "ACCEPTED"
    assert event["baseline_comparison"] == {"diagnostic_only": True, "status_agrees": False}


def test_experimental_mode_cannot_overwrite_root_submission(tmp_path):
    dataset = tmp_path / "dataset"; dataset.mkdir()
    with pytest.raises(InputError, match="cannot publish"):
        solve(dataset, "full", tmp_path / "output.csv", ai=SimpleNamespace(agent_led=True))


def test_nonliteral_certificate_quote_is_rejected():
    tools = api_tools(); value = draft(tools); cert = certificate(tools)
    cert["fact"]["quote"] = "unshown source wording"; value["proof_certificates"] = [cert]
    assert grounded(value, tools)[2][0]["reason"] == "CERTIFICATE_SOURCE_SPAN_NOT_EXACT"


def test_blind_draft_reserves_correction_turn_without_extra_calls(tmp_path, monkeypatch):
    tools = api_tools(); monkeypatch.setenv("LLM_ENABLED", "true")
    agent = AuditInvestigator(tmp_path / "dataset", "agent-led", cache=tmp_path / "cache",
        case_ids=[tools.request.case_id], max_rounds=3)
    bad = draft(tools); bad["audit_recommendation"]["recommended_deletion_status"] = "COMPLETE"
    call = [{"id": "lookup", "type": "function", "function": {"name": "search_evidence",
        "arguments": json.dumps({"kind": "resource", "value": "opaque", "system_id": "account_service"})}}]
    responses = [chat(calls=call), chat(json.dumps(bad)), chat(json.dumps(draft(tools)))]; histories = []
    def transport(url, body, headers, timeout):
        histories.append(copy.deepcopy(body)); return responses.pop(0)
    agent.providers["deepseek"] = Provider(ProviderConfig("deepseek", "deepseek-flash", "unit-test"), agent.ledger, transport)
    agent.investigate(tools, {"issues": [], "resource_keys": [["account_service", "opaque"]]})
    assert len(histories) == 3 and "tools" not in histories[1]
    assert agent.events[-1]["rounds"][1]["draft_requested"]
    assert agent.events[-1]["recommendation_validation"]["validation"] == "ACCEPTED"


def test_failed_agent_trace_is_visible_in_markdown():
    from evaluation.report_agent_audit import render
    run = {"request_count": 1, "model_usage": {}, "ai_investigations": [{"case_id": "custom",
        "status": "INVESTIGATION_FAILED", "error": "INVALID_FINAL_JSON", "tool_trace": [{
            "round_id": 1, "name": "inspect_source", "arguments": {"file_id": "source"},
            "result": {"observation_id": "readback", "truncated": False}}]}]}
    output = render([("failed experiment", run)])
    assert "INVALID_FINAL_JSON" in output and "inspect_source" in output and "no validated final" in output

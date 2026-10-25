"""Independent recommendations must survive the actual source/policy/planner boundary."""
import copy
import json
from dataclasses import replace

import pytest

from deletion_audit.recommendations import AUDIT_PROPOSAL_SCHEMA, assess_recommendation
from deletion_audit.proposals import validate_json
from deletion_audit.solver import decide_case
from test_ai_foundation import api_tools, proposal, chat
from test_agent_corrections import agent_with_responses
from test_solver import obs, AT
from deletion_audit.solver import scope_negatives
from deletion_audit.observations import EvidenceStore


def recommendation(tools=None):
    tools = tools or api_tools()
    decision = decide_case(tools.request, tools.store, tools.graph, tools.policy)
    source = tools.store.observations[0]
    steps = [{k: v for k, v in s.items() if k != "step_no"} for s in decision.steps]
    rec = {"request_intent": {"kind": "DELETE", "target": "ACCOUNT", "quote": tools.request.request_text,
        "explanation": "The user explicitly requests account deletion."},
        "investigation_goals": [{"goal": "Check profile state", "system_id": "account_service",
            "resource_id": "opaque", "status": "SATISFIED"}],
        "investigated_resources": [{"system_id": "account_service", "resource_id": "opaque",
            "policy_rule_id": "rule_01", "interpretation": "Directly present profile requires deletion."}],
        "evidence_references": [{"evidence_id": source.source_id, "observation_id": source.observation_id,
            "observed_at": source.observed_at.isoformat(), "scope": "Exact profile readback"}],
        "unresolved_obligations": [], "recommended_deletion_status": decision.status,
        "verdict_justification": "Existing attributable profile violates DELETE policy.",
        "proposed_findings": [s for s in steps if s["phase"] == "FINDING"],
        "proposed_remediations": [s for s in steps if s["phase"] == "REMEDIATION"],
        "proposed_verifications": [s for s in steps if s["phase"] == "VERIFICATION"],
        "alternative_interpretations": [], "confidence_rationale": "Literal subject link and direct profile presence.",
        "proof_ledger": [{"goal_id": kind, "kind": kind, "system_id": "", "resource_id": "",
            "required_proof": "Independently establish " + kind, "tool_evidence_inspected": [],
            "accepted_source_references": [], "coverage_status": "unresolved",
            "agent_recommendation": "Preserve uncertainty until source checked", "admissible_source_leads": []}
            for kind in ("AUTHORIZATION", "IDENTITY", "OWNERSHIP", "STATE", "TREATMENT", "RECREATION", "RETENTION", "PLAN")]}
    return {**proposal(), "audit_recommendation": rec}


def test_complete_recommendation_is_validated_without_mutating_sources():
    tools = api_tools(); before = copy.deepcopy(tools.store.observations)
    result = assess_recommendation(recommendation(tools), tools)
    assert result["validation"] == "ACCEPTED" and result["independent_status"] == "INCOMPLETE"
    assert len(result["canonical_steps"]) == 3 and tools.store.observations == before


@pytest.mark.parametrize("change,code", [
    (lambda r:r.update(recommended_deletion_status="COMPLETE"), "VERDICT_NOT_INDEPENDENTLY_ESTABLISHED"),
    (lambda r:r["request_intent"].update(kind="NON_DELETION"), "INTENT_NOT_INDEPENDENTLY_ESTABLISHED"),
    (lambda r:r["request_intent"].update(quote="invented request"), "INTENT_QUOTE_NOT_LITERAL"),
    (lambda r:r["evidence_references"][0].update(evidence_id="invented"), "UNKNOWN_OR_MISMATCHED_EVIDENCE"),
    (lambda r:r["evidence_references"][0].update(observed_at="2027-01-01T00:00:00Z"), "OBSERVATION_TIMESTAMP_MISMATCH"),
    (lambda r:r["investigated_resources"][0].update(resource_id="other"), "RESOURCE_OWNERSHIP_UNPROVEN"),
    (lambda r:r["investigated_resources"][0].update(policy_rule_id="rule_15"), "POLICY_RULE_MISMATCH"),
    (lambda r:r.update(proposed_verifications=[]), "PLAN_OBLIGATION_OR_CITATION_MISMATCH"),
])
def test_recommendation_cannot_override_independent_checks(change, code):
    value = recommendation(); change(value["audit_recommendation"])
    result = assess_recommendation(value, api_tools())
    assert result["validation"] == "REJECTED"
    assert code in {i["code"] for i in result["issues"]}


def test_full_schema_requires_all_audit_fields():
    value = recommendation(); del value["audit_recommendation"]["confidence_rationale"]
    with pytest.raises(ValueError):
        validate_json(value, AUDIT_PROPOSAL_SCHEMA)


def test_schema_forbids_future_remediation_citation():
    value = recommendation()
    value["audit_recommendation"]["proposed_remediations"][0]["evidence_id"] = "evidence_1"
    with pytest.raises(ValueError):
        validate_json(value, AUDIT_PROPOSAL_SCHEMA)


def test_audit_mode_allows_result_dependent_second_tool_turn(tmp_path, monkeypatch):
    tools = api_tools(); source = tools.store.observations[0]
    def call(name, args):
        return [{"id": name, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]
    replies = [chat(calls=call("search_evidence", {"kind": "resource", "value": "opaque", "system_id": "account_service"})),
        chat(calls=call("inspect_source", {"file_id": source.file_id, "observation_id": source.observation_id})),
        chat(json.dumps(recommendation(tools)))]
    agent, histories = agent_with_responses(tmp_path, monkeypatch, replies,
        audit_mode=True, case_ids=[tools.request.case_id])
    baseline = decide_case(tools.request, tools.store, tools.graph, tools.policy).diagnostic
    assert agent.investigate(tools, baseline) == []
    event = agent.events[-1]
    assert event["recommendation_validation"]["validation"] == "ACCEPTED"
    assert len(histories) == 3 and "tools" in histories[1]
    assert [t["name"] for t in event["tool_trace"]] == ["search_evidence", "inspect_source"]
    assert not event["rounds"][1]["draft_requested"]


def test_recommendation_gets_precise_bounded_verdict_correction(tmp_path, monkeypatch):
    tools = api_tools(); bad = recommendation(tools)
    bad["audit_recommendation"]["recommended_deletion_status"] = "COMPLETE"
    agent, histories = agent_with_responses(tmp_path, monkeypatch,
        [chat(json.dumps(bad)), chat(json.dumps(recommendation(tools)))],
        audit_mode=True, case_ids=[tools.request.case_id])
    baseline = decide_case(tools.request, tools.store, tools.graph, tools.policy).diagnostic
    assert agent.investigate(tools, baseline) == []
    assert len(histories) == 2
    assert any("VERDICT_NOT_INDEPENDENTLY_ESTABLISHED" in (m.get("content") or "") for m in histories[1]["messages"])
    assert agent.events[-1]["recommendation_validation"]["validation"] == "ACCEPTED"


def test_reference_future_capture_is_rejected():
    tools = api_tools(); value = recommendation(tools)
    future = replace(tools.store.observations[0], captured_at=AT.replace(year=2027))
    store = EvidenceStore(); store.add([future]); tools = replace(tools, store=store)
    checked = assess_recommendation(value, tools)
    assert "EVIDENCE_AFTER_CUTOFF_OR_UNDATED" in {i["code"] for i in checked["issues"]}


def test_reference_to_independently_projected_negative_is_recognized():
    tools = api_tools(); store = EvidenceStore(); store.add(tools.store.observations)
    inventory = obs(fields={"user_id": "unrelated"}, resource="other", when="2026-01-25T00:00:00Z",
                    capture="2026-01-25T00:00:00Z", scope={"table": "customer_profiles"})
    store.add([inventory]); tools = replace(tools, store=store)
    scoped = scope_negatives(store, {("account_service", "opaque")}, AT)
    assert len(scoped) == 1
    value = recommendation(tools); source = scoped[0]
    value["audit_recommendation"]["evidence_references"] = [{"evidence_id": source.source_id,
        "observation_id": source.observation_id, "observed_at": source.observed_at.isoformat(),
        "scope": "Known resource absent from captured complete table"}]
    assert assess_recommendation(value, tools)["validation"] == "ACCEPTED"

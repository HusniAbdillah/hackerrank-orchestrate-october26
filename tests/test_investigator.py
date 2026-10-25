from dataclasses import replace

import pytest

from deletion_audit.inputs import InputError
from deletion_audit.investigator import AuditTools, TOOL_SCHEMAS
from deletion_audit.observations import EvidenceStore
from deletion_audit.policy import Policy
from test_solver import AT, ROOT, graph, obs, request


def tools():
    store = EvidenceStore(); store.add([obs(fields={"user_id": "user_fixture", "email": "person@example.test"}),
                                      obs(when="2026-02-02T00:00:00Z")])
    return AuditTools(request(), store, graph(), Policy.load(ROOT / "dataset"))


def test_exact_search_never_returns_future_observations():
    api = tools()
    result = api.search_evidence("email", "PERSON@EXAMPLE.TEST")
    assert result["total"] == 1 and len(result["observations"]) == 1
    assert api.search_evidence("email", "prefixperson@example.test")["total"] == 0
    assert len(api.inspect_timeline("account_service", "opaque")["observations"]) == 1
    assert api.search_evidence("file_id", "evidence_1")["total"] == 1
    assert api.inspect_timeline("account_service", "opaque")["observations"][0]["direct_state"] == "PRESENT"


def test_all_results_are_detached_copies():
    api = tools()
    result = api.search_evidence("user_id", "user_fixture")
    result["observations"][0]["fields"]["user_id"] = "attacker"
    assert api.store.observations[0].fields["user_id"] == "user_fixture"
    identity = api.trace_identity(); identity["resources"][0]["ownership_basis"].clear()
    assert api.trace_identity()["resources"][0]["ownership_basis"]
    rule = api.explain_policy("USER_PROFILE"); rule["required_action"] = "RETAIN"
    assert api.explain_policy("USER_PROFILE")["required_action"] == "DELETE"


@pytest.mark.parametrize("limit", [0, -1, 101, True, 1.5, "10"])
def test_bounded_tools(limit):
    with pytest.raises(InputError): tools().search_evidence("user_id", "user_fixture", limit=limit)


@pytest.mark.parametrize("name,args", [("delete_record", {}), ("__getattribute__", {}),
                                      ("search_evidence", {"kind": "resource", "value": "opaque"}),
                                      ("trace_identity", {"audit_at": "2030-01-01"}),
                                      ("explain_policy", {"category": "UNKNOWN"})])
def test_dispatcher_cannot_write_or_override_cutoff(name, args):
    with pytest.raises(InputError): tools().invoke(name, args)


def test_tool_schemas_are_read_only_and_closed():
    assert {t["name"] for t in TOOL_SCHEMAS} == {"search_evidence", "trace_identity", "inspect_timeline", "explain_policy", "inspect_source"}
    assert all(t["read_only"] and t["parameters"]["additionalProperties"] is False for t in TOOL_SCHEMAS)
    assert tools().invoke("trace_identity", {})["users"] == ["user_fixture"]

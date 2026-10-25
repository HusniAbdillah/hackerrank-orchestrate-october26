"""Independent business cases; no public expected answers enter these fixtures."""
from dataclasses import replace
from pathlib import Path

import pytest

from deletion_audit.authorization import authorize
from deletion_audit.contract import order_key
from deletion_audit.identity import IdentityGraph
from deletion_audit.inputs import Request, timestamp
from deletion_audit.observations import EvidenceStore
from deletion_audit.parsers import Builder
from deletion_audit.planner import plan
from deletion_audit.policy import Policy
from deletion_audit.solver import audit, enrich, scope_negatives, solve
from deletion_audit.state import ResourceState, reconstruct

ROOT = Path(__file__).resolve().parents[1]
AT = timestamp("2026-02-01T00:00:00Z")


def obs(category="USER_PROFILE", fields=None, resource="opaque", system="account_service",
        when="2026-01-20T00:00:00Z", capture="2026-01-20T00:00:00Z", kind="direct", scope=None):
    b = Builder({"file_id": "evidence_1", "file_path": "evidence/custom.json", "captured_at": capture}, "fixture")
    b.emit(resource + when, fields or {"user_id": "user_fixture"}, system=system, resource=resource,
           category=category, observed=when, kind=kind, scope=scope)
    return b.result.observations[0]


def graph():
    return IdentityGraph([{"user_id": "user_fixture", "name": "Fictional", "email": "person@example.test",
        "phone": "+15555550101", "email_hash": "a" * 64, "updated_at": "2026-01-01T00:00:00Z"}], [])


def request(text="Please delete my account."):
    return Request("case_custom", AT, "person@example.test", text)


@pytest.mark.parametrize("text", [
    "Please delete my account.", "Please erase the account linked to this address.",
    "I deleted this account but please remove any remaining copy of my profile.",
    "My account page is gone. Can you remove that search result too?",
    "I changed the email before deleting it. Please check the old address.",
    "Please investigate and finish the deletion.", "Eliminar mi cuenta.",
    "Je demande la suppression definitive du compte.", "Exclusao permanente da conta.",
    "アカウントを削除してください", "계정을 삭제해 주세요", "删除我的账户", "Hapus akun saya.",
])
def test_authorization_positive(text):
    assert authorize(text).authorized is True


@pytest.mark.parametrize("text", [
    "Please do not delete my account.", "Don't erase my profile.",
    "Please change my email address.", "Please send a copy of my personal data.",
    "Stop promotional messages only; I still need my account.",
    "I am not asking for deletion. Please export my information.",
    "I don't want to delete my account.", "Do not want to erase my profile.",
])
def test_authorization_negative(text):
    assert authorize(text).authorized is False


def test_unknown_intent_is_not_consent():
    assert authorize("Could someone help me?").authorized is None


def test_retained_audit_record_alone_cannot_prove_account_deletion():
    store = EvidenceStore()
    store.add([obs("SECURITY_AUDIT_LOG", {"user_id": "user_fixture"}, "journal", "security_service")])
    status, _, report = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "INCOMPLETE" and report["abstained"]
    assert any(i["code"] == "PRIMARY_PROFILE_VERIFICATION_UNGROUNDED" for i in report["issues"])


def test_custom_replica_drift_flow_and_retained_verification():
    # Independent case 1: clean primary cannot erase the dirty regional copy;
    # disable the connector before deleting the replica and verify retained audit data.
    store = EvidenceStore()
    store.add([
        obs(kind="scoped_negative", fields={"result": "NOT_FOUND", "user_id": "user_fixture"}),
        obs(scope={"replica": "regional_replica"}),
        obs("DATA_FLOW", {"user_id": "user_fixture", "enabled": True}, "connector", "integration_service"),
        obs("SECURITY_AUDIT_LOG", {"user_id": "user_fixture", "retention_until": "2027-01-01T00:00:00Z"},
            "journal", "security_service"),
    ])
    status, steps, report = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "INCOMPLETE" and not report["abstained"]
    rem = [s["operation"] for s in steps if s["phase"] == "REMEDIATION"]
    assert rem == ["DISABLE_DATA_FLOW", "DELETE_RECORD"]
    assert any(s["operation"] == "VERIFY_RECORD_PRESENT" for s in steps)
    assert all(s["evidence_id"] == "" for s in steps if s["phase"] != "FINDING")
    assert steps == sorted(steps, key=order_key)
    assert [s["step_no"] for s in steps] == list(range(1, len(steps) + 1))


def test_custom_tombstone_and_future_capture():
    # Independent case 2: retain stable reference, redact PII, ignore a later capture
    # even when it embeds an earlier business timestamp.
    clean = obs("ACCOUNT_TOMBSTONE", {"user_id": "user_fixture", "email": None, "name": None,
                 "account_status": "DELETED"}, "reference", "identity_service")
    dirty = replace(clean, fields={**clean.fields, "email": "person@example.test"},
                    captured_at=timestamp("2026-02-02T00:00:00Z"))
    store = EvidenceStore(); store.add([clean, dirty])
    status, steps, _ = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "COMPLETE" and steps[0]["operation"] == "VERIFY_RECORD_REDACTED"
    dirty = replace(dirty, captured_at=clean.captured_at, observed_at=timestamp("2026-01-21T00:00:00Z"))
    store = EvidenceStore(); store.add([clean, dirty])
    status, steps, _ = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "INCOMPLETE"
    assert any(s["operation"] == "REDACT_RECORD" for s in steps)
    assert not any(s["operation"] == "DELETE_RECORD" for s in steps)


def test_custom_access_and_unsupported_state_abstain():
    # Independent case 3: access is not deletion; a successful worker claim alone
    # cannot prove absence for an otherwise explicitly authorized request.
    store = EvidenceStore(); store.add([obs(kind="reported_claim", fields={"user_id": "user_fixture", "result": "SUCCESS"})])
    assert audit(request("Please send a copy of my data."), store, graph(), Policy.load(ROOT / "dataset"))[:2] == ("NOT_APPLICABLE", [])
    status, steps, report = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert status == "INCOMPLETE" and steps == [] and report["abstained"]
    assert report["issues"][0]["code"] == "NO_DIRECT_STATE"


def test_simultaneous_contradictions_preserved():
    values, issues = reconstruct([obs(), obs(kind="scoped_negative", fields={"result": "NOT_FOUND"})], AT)
    assert values[0].state == "PRESENT" and values[0].contradictions


def test_later_empty_collection_does_not_clear_explicit_service_readback():
    present = obs()
    negative = replace(present, kind="scoped_negative", fields={"result": "NOT_FOUND"},
                       observed_at=timestamp("2026-01-21T00:00:00Z"),
                       scope={"projected_negative": True}, collection="customer_profiles")
    values, _ = reconstruct([present, negative], AT)
    assert values[0].state == "PRESENT" and len(values[0].copies) == 2


def test_clean_replica_cannot_clear_dirty_primary():
    primary = obs()
    replica = replace(primary, kind="scoped_negative", fields={"result": "NOT_FOUND"},
                      observed_at=timestamp("2026-01-21T00:00:00Z"), scope={"replica": "regional_replica"})
    values, _ = reconstruct([primary, replica], AT)
    assert values[0].state == "PRESENT" and len(values[0].copies) == 2


def test_explicit_copy_identity_does_not_require_replica_word():
    dirty = obs(scope={"replica": "eu_west"})
    clean = obs(kind="scoped_negative", fields={"result": "NOT_FOUND"}, scope={"replica": "ap_south"})
    values, _ = reconstruct([dirty, clean], AT)
    assert values[0].state == "PRESENT" and len(values[0].copies) == 2


def test_future_embedded_observation_is_excluded():
    future = obs(when="2026-02-02T00:00:00Z")
    assert reconstruct([future], AT) == ([], [])


def test_scoped_negatives_never_create_subject_links():
    store = EvidenceStore(); known = obs()
    empty = replace(known, resource_id=None, collection="customer_profiles", kind="scoped_negative",
                    fields={}, scope={"complete_collection": True})
    store.add([known, empty])
    assert scope_negatives(store, set(), AT) == []
    negatives = scope_negatives(store, {("account_service", "opaque")}, AT)
    assert len(negatives) == 1 and negatives[0].resource_id == "opaque"


def test_every_supplied_policy_rule_is_executable():
    policy = Policy.load(ROOT / "dataset")
    assert len(policy.rules) == 15
    for category, rule in policy.rules.items():
        fields = {"user_id": "user_fixture", "account_status": "DELETED", "shared_context": True,
                  "shared_attachment": False, "hold_active": True, "retention_until": "2027-01-01T00:00:00Z"}
        evidence = obs(category, fields)
        state = "ACTIVE" if category == "BACKUP_ARCHIVE" else "IDENTIFIABLE" if rule["required_action"] in {"REDACT", "ANONYMIZE"} else "PRESENT"
        decision = policy.decide(ResourceState("svc", "opaque", category, state, evidence, (evidence,)), AT)
        assert decision.rule_id == rule["rule_id"] and decision.verification and not decision.issue


@pytest.mark.parametrize("category,fields,issue", [
    ("SECURITY_AUDIT_LOG", {"retention_until": "2025-01-01T00:00:00Z"}, "RETENTION_EXPIRED_NO_FALLBACK_RULE"),
    ("LEGAL_HOLD_RECORD", {"hold_active": False}, "LEGAL_HOLD_INACTIVE_NO_FALLBACK_RULE"),
    ("SUPPORT_ATTACHMENT", {"shared_attachment": True}, "ATTACHMENT_OWNERSHIP_CONDITION_UNRESOLVED"),
    ("SUPPORT_MESSAGE", {"shared_context": False}, "SUPPORT_RETENTION_CONDITION_UNRESOLVED"),
    ("ACCOUNT_TOMBSTONE", {"email": None}, "TOMBSTONE_REFERENCE_CONDITION_UNRESOLVED"),
])
def test_policy_conditions_do_not_invent_fallback(category, fields, issue):
    evidence = obs(category, fields)
    decision = Policy.load(ROOT / "dataset").decide(ResourceState("svc", "opaque", category, "PRESENT", evidence, (evidence,)), AT)
    assert decision.issue == issue and decision.remediation is None


def test_policy_action_comes_from_csv():
    evidence = obs(fields={"email": "person@example.test"})
    policy = Policy([{"rule_id": "custom", "data_category": "USER_PROFILE", "required_action": "ANONYMIZE", "condition": "Always"}])
    decision = policy.decide(ResourceState("svc", "opaque", "USER_PROFILE", "PRESENT", evidence, (evidence,)), AT)
    assert decision.remediation == "ANONYMIZE_RECORD"


def test_no_resource_links_are_visible_abstention():
    status, steps, report = audit(request(), EvidenceStore(), graph(), Policy.load(ROOT / "dataset"))
    assert (status, steps) == ("INCOMPLETE", [])
    assert report["gap_classification"] == "unresolved" and report["abstained"]


def test_sample_solver_never_decodes_reference(monkeypatch, tmp_path):
    original = Path.open
    def guarded(path, mode="r", *args, **kwargs):
        if path.name == "sample_output.csv" and "b" not in mode:
            raise AssertionError("Solver attempted to decode reference answers")
        return original(path, mode, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    report = solve(ROOT / "dataset", "sample", tmp_path / "predictions.csv")
    assert report["prediction_count"] == 32 and report["dataset_integrity"] == {"unchanged": True, "file_count": 103}
    assert report["model_usage"]["calls"] == 0
    assert len(report["pending_multimodal"]) == 11
    assert all(case["authorization"] is True for case in report["cases"])

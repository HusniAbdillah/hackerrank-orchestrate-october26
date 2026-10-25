"""Conditional retention must be established for the absent resource itself."""
from deletion_audit.policy import Policy
from deletion_audit.state import ResourceState
from test_solver import ROOT, AT, obs


def decision(category, fields):
    source = obs(category, fields, kind="scoped_negative")
    resource = ResourceState(source.system_id, source.resource_id, category, "ABSENT", source, (source,))
    return Policy.load(ROOT / "dataset").decide(resource, AT)


def test_absent_security_record_requires_its_own_admissible_retention_period():
    unknown = decision("SECURITY_AUDIT_LOG", {"result": "NOT_FOUND", "subject_reference": "user_fixture"})
    assert unknown.issue == "RETENTION_CONDITION_UNPROVEN"
    assert unknown.finding is None and unknown.remediation is None and unknown.verification is None
    required = decision("SECURITY_AUDIT_LOG", {"retention_until": "2027-01-01T00:00:00Z"})
    assert required.issue == "REQUIRED_RETAINED_RECORD_MISSING" and required.remediation is None
    expired = decision("SECURITY_AUDIT_LOG", {"retention_until": "2025-01-01T00:00:00Z"})
    assert expired.issue == "RETENTION_EXPIRED_NO_FALLBACK_RULE"


def test_absent_legal_record_requires_explicit_active_hold():
    assert decision("LEGAL_HOLD_RECORD", {"result": "NOT_FOUND"}).issue == "LEGAL_HOLD_CONDITION_UNPROVEN"
    assert decision("LEGAL_HOLD_RECORD", {"hold_active": True}).issue == "REQUIRED_RETAINED_RECORD_MISSING"
    assert decision("LEGAL_HOLD_RECORD", {"hold_active": False}).issue == "LEGAL_HOLD_INACTIVE_NO_FALLBACK_RULE"

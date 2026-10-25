"""All supplied policy categories, with explicit conditional safeguards."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .inputs import InputError, read_csv, timestamp
from .state import ResourceState, actual_fields


@dataclass(frozen=True)
class Decision:
    rule_id: str
    finding: str | None
    remediation: str | None
    verification: str | None
    issue: str | None = None


class Policy:
    def __init__(self, rules: list[dict]):
        self.rules = {r["data_category"]: r for r in rules}
        if len(self.rules) != len(rules):
            raise InputError("Duplicate deletion policy category")
        if any(r["required_action"] not in {"DELETE", "REDACT", "ANONYMIZE", "RETAIN"} for r in rules):
            raise InputError("Unsupported deletion policy action")

    @classmethod
    def load(cls, dataset: Path):
        return cls(read_csv(dataset / "deletion_rules.csv", ["rule_id", "data_category", "condition", "required_action"]))

    def decide(self, resource: ResourceState, at: datetime) -> Decision:
        category, state = resource.category, resource.state
        if category == "DATA_FLOW":
            return Decision("contract:data_flow", "REPORT_ACTIVE_DATA_FLOW" if state == "ACTIVE" else None,
                            "DISABLE_DATA_FLOW" if state == "ACTIVE" else None, "VERIFY_DATA_FLOW_DISABLED")
        rule = self.rules.get(category)
        if rule is None:
            return Decision("", None, None, None, "UNSUPPORTED_POLICY_CATEGORY")
        rid, action = rule["rule_id"], rule["required_action"]
        fields = actual_fields(resource.evidence)
        if category == "BACKUP_ARCHIVE":
            return Decision(rid, "REPORT_RESTORE_RISK" if state == "ACTIVE" else None,
                            "BLOCK_RESTORE" if state == "ACTIVE" else None, "VERIFY_RESTORE_BLOCKED")
        if action == "DELETE":
            if category == "SUPPORT_ATTACHMENT" and fields.get("shared_attachment") is True:
                return Decision(rid, None, None, None, "ATTACHMENT_OWNERSHIP_CONDITION_UNRESOLVED")
            return Decision(rid, "REPORT_REMAINING_RECORD" if state != "ABSENT" else None,
                            "DELETE_RECORD" if state != "ABSENT" else None, "VERIFY_RECORD_ABSENT")
        if action == "RETAIN":
            deadline = fields.get("retention_until", fields.get("retained_until"))
            if deadline and timestamp(deadline) < at:
                return Decision(rid, None, None, None, "RETENTION_EXPIRED_NO_FALLBACK_RULE")
            if fields.get("hold_active") is False:
                return Decision(rid, None, None, None, "LEGAL_HOLD_INACTIVE_NO_FALLBACK_RULE")
            if state == "ABSENT":
                return Decision(rid, None, None, None, "REQUIRED_RETAINED_RECORD_MISSING")
            # The supplied security readback/register category is the retention context;
            # never invent a deadline when the exported row has none.
            return Decision(rid, None, None, "VERIFY_RECORD_PRESENT")
        if state == "ABSENT":
            return Decision(rid, None, None, None, "REQUIRED_KEPT_RECORD_MISSING")
        if category == "SUPPORT_MESSAGE" and fields.get("shared_context") is False:
            return Decision(rid, None, None, None, "SUPPORT_RETENTION_CONDITION_UNRESOLVED")
        if category == "ACCOUNT_TOMBSTONE":
            reference = fields.get("subject_reference", fields.get("user_id", fields.get("customer_reference")))
            if not reference or fields.get("account_status", "DELETED") != "DELETED":
                return Decision(rid, None, None, None, "TOMBSTONE_REFERENCE_CONDITION_UNRESOLVED")
        expected = "REDACTED" if action == "REDACT" else "ANONYMIZED"
        return Decision(rid, "REPORT_EXPOSED_PII" if state != expected else None,
                        f"{action}_RECORD" if state != expected else None, f"VERIFY_RECORD_{expected}")

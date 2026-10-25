"""Cutoff-aware, copy-specific direct state with preserved competing observations."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from .observations import Observation, identifiers


def actual_fields(obs: Observation) -> dict:
    fields = obs.fields.get("decoded_record", obs.fields)
    if isinstance(fields.get("profile"), dict):
        return fields["profile"]
    if isinstance(fields.get("document"), dict):
        return fields["document"]
    if isinstance(fields.get("hits"), dict) and fields["hits"].get("documents"):
        return fields["hits"]["documents"][0]
    return fields


def boolean(value):
    if value in (True, "true", "1", 1):
        return True
    if value in (False, "false", "0", 0):
        return False
    return None


def exposed(fields: dict, *, anonymize=False) -> bool | None:
    if "direct_identifiers" in fields:
        return str(fields["direct_identifiers"]) != "0"
    keys = {"name", "full_name", "display_name", "email", "phone", "email_hash", "requester_name",
            "requester_email", "requester_phone", "owner_email", "owner_phone", "customer_email"}
    if anonymize:
        keys |= {"user_id", "customer_reference", "subject_reference"}
    present = [value for key, value in fields.items() if key in keys]
    if any(value not in (None, "", "null", "[REDACTED]", "REDACTED") for value in present):
        return True
    if fields.get("message_text") == "[REDACTED]":
        return False
    # Conversation exports can embed literal contact details in the message body
    # while omitting requester_email/phone columns. Missing columns are not proof
    # of redaction. Stable subject references outside this text remain permitted.
    if any(kind in {"email", "phone", "email_hash"}
           for kind, _ in identifiers({"text": fields.get("message_text", "")})):
        return True
    if fields.get("matched_value") not in (None, "", "null"):
        return True
    if present:
        return False
    return None


def observed_state(obs: Observation) -> str | None:
    if obs.kind not in {"direct", "scoped_negative"}:
        return None
    fields = actual_fields(obs)
    result = fields.get("result", obs.fields.get("result"))
    states = {"NOT_FOUND": "ABSENT", "FOUND": "PRESENT", "IDENTIFIABLE": "IDENTIFIABLE",
              "ANONYMIZED": "ANONYMIZED", "REDACTED": "REDACTED", "ACTIVE": "ACTIVE",
              "DISABLED": "DISABLED", "BLOCKED": "BLOCKED"}
    if result in states:
        return states[result]
    if obs.kind == "scoped_negative":
        return "ABSENT"
    category = obs.category
    if category == "DATA_FLOW":
        flag = boolean(fields.get("enabled"))
        return "ACTIVE" if flag is True else "DISABLED" if flag is False else None
    if category == "BACKUP_ARCHIVE":
        flag = boolean(fields.get("restore_allowed", fields.get("eligible")))
        if fields.get("decision") == "deny" or boolean(fields.get("deletion_block")) is True:
            flag = False
        return "ACTIVE" if flag is True else "BLOCKED" if flag is False else None
    if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY", "SUPPORT_MESSAGE", "ACCOUNT_TOMBSTONE", "EMAIL_DELIVERY_LOG"}:
        pii = exposed(fields, anonymize=category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"})
        return "IDENTIFIABLE" if pii is True else (
            "ANONYMIZED" if category in {"ANALYTICS_PROFILE", "PRODUCT_TELEMETRY"} else "REDACTED"
        ) if pii is False else None
    if category:
        return "PRESENT"
    return None


@dataclass(frozen=True)
class ResourceState:
    system_id: str
    resource_id: str
    category: str
    state: str
    evidence: Observation
    copies: tuple[Observation, ...]
    contradictions: tuple[str, ...] = ()


def reconstruct(observations: list[Observation], at: datetime) -> tuple[list[ResourceState], list[dict]]:
    resources = defaultdict(list)
    issues = []
    for obs in observations:
        if obs.admissible(at) and obs.system_id and obs.resource_id:
            resources[(obs.system_id, obs.resource_id)].append(obs)
    result = []
    for (system, resource), history in sorted(resources.items()):
        candidates = [o for o in history if observed_state(o) is not None and o.category]
        if not candidates:
            issues.append({"code": "NO_DIRECT_STATE", "system_id": system, "resource_id": resource})
            continue
        # Distinguish replicas within a single snapshot topology. An unscoped readback
        # never silently deletes a known dirty replica from another explicit copy.
        copies = defaultdict(list)
        for obs in candidates:
            table = obs.scope.get("replica")
            explicit_copy = table and (not obs.scope.get("table") or "replica" in table)
            copy = table if explicit_copy else (
                "collection_scope:" + str(obs.collection)
                if obs.scope.get("projected_negative") and not table else "primary")
            copies[copy].append(obs)
        selected = []
        conflicts = []
        for copy, values in copies.items():
            latest = max(o.observed_at for o in values)
            ties = [o for o in values if o.observed_at == latest]
            states = {observed_state(o) for o in ties}
            if len(states) > 1:
                conflicts.append(f"{copy}: conflicting direct states at {latest.isoformat()}")
            # Stable tie-break: preserve a violation at a simultaneous contradiction.
            risk = {"IDENTIFIABLE": 5, "PRESENT": 4, "ACTIVE": 4, "ABSENT": 0,
                    "REDACTED": 0, "ANONYMIZED": 0, "DISABLED": 0, "BLOCKED": 0}
            selected.append(max(ties, key=lambda o: (risk.get(observed_state(o), 0), o.captured_at, o.source_id, o.observation_id)))
        # A later clean replica cannot clear an independently dirty primary.
        category = max(candidates, key=lambda o: (o.observed_at, o.captured_at, o.source_id)).category
        bad = [o for o in selected if observed_state(o) in {"PRESENT", "IDENTIFIABLE", "ACTIVE"}]
        selected_obs = max(bad or selected, key=lambda o: (o.observed_at, o.captured_at, o.source_id, o.observation_id))
        result.append(ResourceState(system, resource, category, observed_state(selected_obs), selected_obs,
                                    tuple(selected), tuple(conflicts)))
    return result, issues

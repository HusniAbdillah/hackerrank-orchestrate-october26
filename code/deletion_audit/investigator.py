"""Read-only, cutoff-bound tools for a future optional AI investigator.

No model client, arbitrary file access, execution tool, or decision-writing capability.
"""
from copy import deepcopy
import re
from dataclasses import dataclass
from typing import Protocol, Any

from .inputs import InputError, Request
from .observations import EvidenceStore, normalize
from .identity import IdentityGraph
from .policy import Policy
from .state import observed_state


class Investigator(Protocol):
    def investigate(self, tools: "AuditTools", diagnostic: dict) -> dict[str, Any]:
        """Return a proposal, never an automatically accepted deletion verdict."""
        ...


def _schema(properties, required):
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


TOOL_SCHEMAS = [
    {"name": "search_evidence", "read_only": True, "parameters": _schema({
        "kind": {"type": "string", "enum": ["user_id", "email", "email_hash", "phone", "resource", "file_id", "asset_reference"]},
        "value": {"type": "string", "minLength": 1, "maxLength": 512},
        "system_id": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, ["kind", "value"])},
    {"name": "trace_identity", "read_only": True, "parameters": _schema({}, [])},
    {"name": "inspect_timeline", "read_only": True, "parameters": _schema({
        "system_id": {"type": "string"}, "resource_id": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 100}}, ["system_id", "resource_id"])},
    {"name": "explain_policy", "read_only": True, "parameters": _schema({
        "category": {"type": "string"}}, ["category"])},
]


@dataclass(frozen=True)
class AuditTools:
    request: Request
    store: EvidenceStore
    graph: IdentityGraph
    policy: Policy

    def _limit(self, limit):
        if type(limit) is not int or not 1 <= limit <= 100:
            raise InputError("Tool limit must be an integer in 1..100")
        return limit

    def _result(self, observations, limit):
        admissible = [o for o in observations if o.admissible(self.request.audit_at)]
        admissible.sort(key=lambda o: (o.observed_at, o.captured_at, o.observation_id))
        return {"cutoff": self.request.audit_at.isoformat(), "total": len(admissible),
                "truncated": len(admissible) > limit,
                "observations": deepcopy([o.to_dict() for o in admissible[:limit]])}

    def search_evidence(self, kind: str, value: str, system_id: str | None = None, limit: int = 50):
        self._limit(limit)
        if not isinstance(value, str) or not value or len(value) > 512:
            raise InputError("Exact search value required (maximum 512 characters)")
        if kind == "asset_reference":
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_. -]{0,150}\.(?:pdf|png|zip|json|csv|zst)", value):
                raise InputError("Asset reference must be a literal supported filename")
            values = [o for o in self.store.observations if o.collection in {"ocr_text", "pdf_text"}
                      and re.search(r"(?<![\w])" + re.escape(value) + r"(?![\w])", o.fields.get("text", ""))]
        elif kind == "file_id":
            values = [o for o in self.store.observations if o.file_id == value]
        elif kind == "resource":
            if not system_id:
                raise InputError("Resource searches require system_id")
            values = self.store.by_resource.get((system_id, value), [])
        elif kind in {"user_id", "email", "email_hash", "phone"}:
            values = self.store.by_identifier.get((kind, normalize(kind, value)), [])
            if system_id:
                values = [o for o in values if o.system_id == system_id]
        else:
            raise InputError("Unsupported exact identifier kind")
        return self._result(values, limit)

    def trace_identity(self):
        at = self.request.audit_at
        users = self.graph.resolve("email", self.request.email, at)
        ownership = self.graph.ownership(self.store, at)
        versions = [{"user_id": v.user_id, "kind": v.kind, "value": v.value,
                     "valid_from": v.valid_from.isoformat() if v.valid_from else None,
                     "valid_to": v.valid_to.isoformat() if v.valid_to else None,
                     "known_at": v.known_at.isoformat(), "source_id": v.source_id}
                    for uid in sorted(users) for v in self.graph.versions_for_user(uid, at)]
        return deepcopy({"cutoff": at.isoformat(), "users": sorted(users), "versions": versions,
                         "resources": [{"system_id": key[0], "resource_id": key[1], "ownership_basis": reasons}
                                       for key, reasons in sorted(ownership.items()) if users.intersection(reasons)]})

    def inspect_timeline(self, system_id: str, resource_id: str, limit: int = 100):
        result = self.search_evidence("resource", resource_id, system_id, limit)
        for item in result["observations"]:
            original = next(o for o in self.store.by_resource[(system_id, resource_id)] if o.observation_id == item["observation_id"])
            item["direct_state"] = observed_state(original)
        return result

    def explain_policy(self, category: str):
        if category == "DATA_FLOW":
            return {"category": category, "source": "problem_statement.md:Allowed Operations", "required_action": "DISABLE_DATA_FLOW",
                    "condition": "An active process can copy or recreate subject data"}
        rule = self.policy.rules.get(category)
        if rule is None:
            raise InputError("Unknown supplied policy category")
        return deepcopy({"source": "dataset/deletion_rules.csv", **rule})

    def invoke(self, name: str, arguments: dict):
        # Fixed dispatcher: no getattr, arbitrary method or filesystem invocation.
        handlers = {"search_evidence": self.search_evidence, "trace_identity": self.trace_identity,
                    "inspect_timeline": self.inspect_timeline, "explain_policy": self.explain_policy}
        if name not in handlers or not isinstance(arguments, dict):
            raise InputError("Unsupported read-only tool call")
        try:
            return handlers[name](**arguments)
        except TypeError as exc:
            raise InputError("Invalid read-only tool arguments") from exc

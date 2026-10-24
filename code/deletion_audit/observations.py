"""Normalized evidence and exact identifier tokens; no deletion decisions."""

import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Iterable


EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9_.+%-]+@(?:[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}(?![\w@-])")
USER = re.compile(r"(?<![\w])user_[A-Za-z0-9]+(?![\w])")
HASH = re.compile(r"(?<![\w])[a-fA-F0-9]{64}(?![\w])")
RESOURCE = re.compile(r"(?<![\w])(?:account|search|analytics|support|export|data_flow|backup|tombstone|audit_record|legal_hold|marketing|cache)_[A-Za-z0-9]+(?![\w])")


def normalize(kind: str, value: str) -> str:
    if kind in {"email", "email_hash"}:
        return value.strip().casefold()
    if kind == "phone":
        # Formatting normalization only; never compare suffixes or infer country codes.
        return ("+" if value.strip().startswith("+") else "") + re.sub(r"\D", "", value)
    return value.strip()


def identifiers(value: Any) -> tuple[tuple[str, str], ...]:
    found = set()

    def visit(item, key=""):
        if isinstance(item, dict):
            for k, v in item.items():
                # Integrity seals are not customer email hashes.
                if k not in {"integrity_seal", "checksum", "fingerprint"}:
                    visit(v, k)
        elif isinstance(item, list):
            for v in item:
                visit(v, key)
        elif isinstance(item, str):
            found.update(("email", normalize("email", m[0])) for m in EMAIL.finditer(item))
            found.update(("user_id", m[0]) for m in USER.finditer(item))
            found.update(("email_hash", m[0].lower()) for m in HASH.finditer(item))
            for match in re.finditer(r"(?<![\w])\+[0-9][0-9 ()-]{6,}[0-9](?![0-9])", item):
                found.add(("phone", normalize("phone", match[0])))
            if "phone" in key and item.strip() not in {"", "null", "[REDACTED]"}:
                normalized = normalize("phone", item)
                if len(re.sub(r"\D", "", normalized)) >= 7:
                    found.add(("phone", normalized))
    visit(value)
    return tuple(sorted(found))


@dataclass(frozen=True)
class Observation:
    observation_id: str
    source_id: str
    file_id: str | None
    system_id: str | None
    resource_id: str | None
    collection: str | None
    category: str | None
    observed_at: datetime | None
    captured_at: datetime
    kind: str
    fields: dict[str, Any]
    scope: dict[str, Any]
    provenance: dict[str, Any]
    identifiers: tuple[tuple[str, str], ...] = ()
    related_resources: tuple[tuple[str, str], ...] = ()

    def admissible(self, at: datetime) -> bool:
        return self.observed_at is not None and self.observed_at <= at and self.captured_at <= at

    def to_dict(self) -> dict:
        result = asdict(self)
        result["observed_at"] = self.observed_at.isoformat() if self.observed_at else None
        result["captured_at"] = self.captured_at.isoformat()
        return result


@dataclass
class EvidenceStore:
    cache_token: object = field(default_factory=object, repr=False)
    observations: list[Observation] = field(default_factory=list)
    files: list[dict] = field(default_factory=list)
    issues: list[dict] = field(default_factory=list)
    # Each original text is retained once, rather than copied per case.
    source_text: dict[str, str] = field(default_factory=dict)
    by_resource: dict[tuple[str, str], list[Observation]] = field(default_factory=lambda: defaultdict(list))
    by_identifier: dict[tuple[str, str], list[Observation]] = field(default_factory=lambda: defaultdict(list))

    def add(self, observations: Iterable[Observation]) -> None:
        for obs in observations:
            self.observations.append(obs)
            if obs.system_id and obs.resource_id:
                self.by_resource[(obs.system_id, obs.resource_id)].append(obs)
            for token in obs.identifiers:
                self.by_identifier[token].append(obs)

    def for_resource(self, system_id: str, resource_id: str, at: datetime) -> list[Observation]:
        return [obs for obs in self.by_resource.get((system_id, resource_id), []) if obs.admissible(at)]

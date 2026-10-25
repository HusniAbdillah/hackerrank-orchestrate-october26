"""Exact, temporal identity indexes and evidence-grounded resource ownership links."""

from collections import defaultdict
from copy import copy
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path

from .inputs import InputError, Request, read_csv, timestamp
from .observations import EvidenceStore, normalize


IDENTITY_FIELDS = ["user_id", "name", "email", "phone", "email_hash", "updated_at"]
AUDIT_FIELDS = ["audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"]
INDEXED_FIELDS = {"email", "phone", "email_hash"}


@dataclass(frozen=True)
class IdentifierVersion:
    user_id: str
    kind: str
    value: str
    valid_from: datetime | None
    valid_to: datetime | None
    known_at: datetime
    source_id: str


class IdentityGraph:
    def __init__(self, identities: list[dict], changes: list[dict]):
        self.index: dict[tuple[str, str], list[IdentifierVersion]] = defaultdict(list)
        self.by_user: dict[str, list[IdentifierVersion]] = defaultdict(list)
        self.issues: list[dict] = []
        self.snapshot_rows = len(identities)
        self.audit_rows = len(changes)
        self._ownership_cache = {}
        snapshots = {row["user_id"]: row for row in identities}
        if len(snapshots) != len(identities) or any(not uid for uid in snapshots):
            raise InputError("Duplicate or empty identity user_id")
        events = defaultdict(list)
        seen_audits = set()
        user_first_event = {}
        for change in changes:
            uid, kind, aid = change["user_id"], change["field_name"], change["audit_id"]
            if uid not in snapshots or kind not in INDEXED_FIELDS or aid in seen_audits:
                raise InputError("Unknown identity, unsupported identity field, or duplicate audit ID")
            seen_audits.add(aid)
            when = timestamp(change["event_time"])
            user_first_event[uid] = min(user_first_event.get(uid, (when, aid)), (when, aid))
            events[(uid, kind)].append((when, change))
        versions = set()
        for uid, row in snapshots.items():
            updated = timestamp(row["updated_at"])
            first, first_source = min((updated, uid), user_first_event.get(uid, (updated, uid)))
            versions.add(IdentifierVersion(uid, "user_id", uid, first, None, first, first_source))
            for kind in sorted(INDEXED_FIELDS):
                history = sorted(events[(uid, kind)], key=lambda e: (e[0], e[1]["audit_id"]))
                for i, (when, change) in enumerate(history):
                    old, new = (normalize(kind, change[k]) for k in ("old_value", "new_value"))
                    previous = history[i - 1] if i else None
                    follows = previous is not None and normalize(kind, previous[1]["new_value"]) == old
                    if previous and not follows:
                        self.issues.append({"code": "IDENTITY_HISTORY_GAP", "user_id": uid,
                                            "field": kind, "audit_id": change["audit_id"]})
                    # old_value becomes available at this event, unless an earlier event already established it.
                    versions.add(IdentifierVersion(uid, kind, old, previous[0] if follows else None,
                                                   when, previous[0] if follows else when,
                                                   previous[1]["audit_id"] if follows else change["audit_id"]))
                    end = history[i + 1][0] if i + 1 < len(history) else None
                    versions.add(IdentifierVersion(uid, kind, new, when, end, when, change["audit_id"]))
                current = normalize(kind, row[kind])
                last = history[-1] if history else None
                if last and normalize(kind, last[1]["new_value"]) != current:
                    self.issues.append({"code": "SNAPSHOT_HISTORY_CONFLICT", "user_id": uid, "field": kind})
                # Prevent a current snapshot from revealing an audited future value under a stale updated_at.
                matches_last = last and normalize(kind, last[1]["new_value"]) == current
                known = max(updated, last[0]) if matches_last else updated
                start = last[0] if matches_last else updated
                versions.add(IdentifierVersion(uid, kind, current, start, None, known, uid))
        for version in sorted(versions, key=lambda v: (v.user_id, v.kind, v.value, v.known_at, v.source_id)):
            if not version.value:
                raise InputError("Empty identity identifier")
            self.index[(version.kind, version.value)].append(version)
            self.by_user[version.user_id].append(version)

    @classmethod
    def load(cls, dataset: Path) -> "IdentityGraph":
        return cls(read_csv(dataset / "user_identities.csv", IDENTITY_FIELDS),
                   read_csv(dataset / "user_audit_log.csv", AUDIT_FIELDS))

    def fork(self):
        """Share immutable identifier indexes, isolate per-case ownership memoization."""
        graph = copy(self)
        graph._ownership_cache = {}
        return graph

    def matching_versions(self, kind: str, value: str, at: datetime) -> list[IdentifierVersion]:
        return [replace(v, valid_to=None if v.valid_to and v.valid_to > at else v.valid_to)
                for v in self.index.get((kind, normalize(kind, value)), []) if v.known_at <= at]

    def resolve(self, kind: str, value: str, at: datetime) -> frozenset[str]:
        return frozenset(v.user_id for v in self.matching_versions(kind, value, at))

    def versions_for_user(self, user_id: str, at: datetime) -> list[IdentifierVersion]:
        # Future transitions cannot leak even the future valid_to of a known identifier.
        return [replace(v, valid_to=None if v.valid_to and v.valid_to > at else v.valid_to)
                for v in self.by_user.get(user_id, []) if v.known_at <= at]

    def ownership(self, store: EvidenceStore, at: datetime) -> dict:
        cache_key = (store.cache_token, len(store.observations), at)
        if cache_key in self._ownership_cache:
            return self._ownership_cache[cache_key]
        owners = defaultdict(dict)
        edges = []
        for obs in store.observations:
            if not obs.admissible(at) or not obs.system_id or not obs.resource_id:
                continue
            key = (obs.system_id, obs.resource_id)
            for kind, value in obs.identifiers:
                for version in self.matching_versions(kind, value, at):
                    uid = version.user_id
                    basis = {"observation_id": obs.observation_id, "source_id": obs.source_id,
                             "evidence_kind": obs.kind, "identifier_kind": kind,
                             "identity_source": version.source_id,
                             "known_at": max(version.known_at, obs.captured_at, obs.observed_at).isoformat()}
                    owners[key].setdefault(uid, [])
                    if basis not in owners[key][uid]:
                        owners[key][uid].append(basis)
            for related in obs.related_resources:
                edges.append((key, related, obs))
        # Propagate only explicit schema-defined source-resource links, never fuzzy co-occurrence.
        changed = True
        while changed:
            changed = False
            for left, right, source in edges:
                for origin, target in ((left, right), (right, left)):
                    for uid, reasons in list(owners[origin].items()):
                        if uid not in owners[target]:
                            owners[target][uid] = [{**reasons[0], "via_resource": list(origin),
                                                   "resource_link_source": source.observation_id,
                                                   "known_at": max(timestamp(reasons[0]["known_at"]),
                                                                   source.captured_at, source.observed_at).isoformat()}]
                            changed = True
        result = dict(owners)
        self._ownership_cache[cache_key] = result
        return result

    def observations_for_user(self, user_id: str, store: EvidenceStore, at: datetime) -> list:
        keys = {key for key, users in self.ownership(store, at).items() if user_id in users}
        return [obs for key in sorted(keys) for obs in store.for_resource(*key, at)]


def identity_coverage(graph: IdentityGraph, requests: dict[str, Request], store: EvidenceStore) -> dict:
    rows = []
    current = historical = 0
    for cid, request in sorted(requests.items()):
        versions = graph.matching_versions("email", request.email, request.audit_at)
        users = sorted({v.user_id for v in versions})
        unique = len(users) == 1
        if unique:
            active = any(v.valid_to is None and (v.valid_from is None or v.valid_from <= request.audit_at)
                         for v in versions)
            current += active
            historical += not active
        ownership = graph.ownership(store, request.audit_at) if unique else {}
        keys = [key for key, owners in ownership.items() if unique and users[0] in owners]
        rows.append({"case_id": cid, "resolution": "unique" if unique else "unresolved" if not users else "ambiguous",
                     "user_ids": users, "identity_sources": sorted({v.source_id for v in versions}),
                     "resource_count": len(keys),
                     "ambiguous_resource_count": sum(len(ownership[key]) > 1 for key in keys),
                     "admissible_observations": sum(len(store.for_resource(*key, request.audit_at)) for key in keys)})
    resolved = sum(r["resolution"] == "unique" for r in rows)
    return {"request_count": len(rows), "uniquely_resolved": resolved,
            "coverage": resolved / len(rows) if rows else 1.0,
            "current_email": current, "historical_email_only": historical,
            "unresolved": sum(r["resolution"] == "unresolved" for r in rows),
            "ambiguous": sum(r["resolution"] == "ambiguous" for r in rows),
            "with_grounded_resource_links": sum(r["resource_count"] > 0 for r in rows), "cases": rows}

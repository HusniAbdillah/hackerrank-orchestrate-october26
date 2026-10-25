from dataclasses import replace

import pytest

from deletion_audit.identity import IdentityGraph, identity_coverage
from deletion_audit.inputs import Request, timestamp
from deletion_audit.observations import EvidenceStore
from deletion_audit.parsers import Builder


CUTOFF = timestamp("2026-02-01T12:00:00Z")


def snapshot(uid="user_1", email="new@example.test", updated="2026-01-20T00:00:00Z"):
    return {"user_id": uid, "name": "Same Fictional Name", "email": email,
            "phone": "+1 (212) 555-0101" if uid == "user_1" else "+1 (212) 555-0102",
            "email_hash": "a" * 64 if uid == "user_1" else "c" * 64, "updated_at": updated}


def change(aid="audit_1", kind="email", old="old@example.test", new="new@example.test",
           when="2026-01-15T00:00:00Z"):
    return {"audit_id": aid, "user_id": "user_1", "field_name": kind, "old_value": old,
            "new_value": new, "event_time": when}


@pytest.fixture
def graph():
    return IdentityGraph([snapshot(), snapshot("user_2", "new.jr@example.test")], [
        change(), change("audit_2", "email_hash", "b" * 64, "a" * 64)])


def observation(fields, when="2026-01-16T00:00:00Z", capture="2026-01-16T00:00:00Z",
                system="account_service", resource="opaque_resource", locator="/0", related=(), kind="direct"):
    builder = Builder({"file_id": "evidence_99", "file_path": "evidence/fixture.json",
                       "captured_at": capture, "origin": "fixture"}, "test-hash")
    builder.emit(locator, fields, system=system, resource=resource, observed=when, related=related, kind=kind)
    return builder.result.observations[0]


def test_current_historical_hash_phone_and_exact_boundaries(graph):
    assert graph.resolve("email", "OLD@EXAMPLE.TEST", CUTOFF) == {"user_1"}
    assert graph.resolve("email_hash", "b" * 64, CUTOFF) == {"user_1"}
    assert graph.resolve("phone", "+12125550101", CUTOFF) == {"user_1"}
    assert graph.resolve("email", "new.jr@example.test", CUTOFF) == {"user_2"}
    assert not graph.resolve("email", "prefixnew@example.test", CUTOFF)
    assert not graph.resolve("phone", "5550101", CUTOFF)
    assert not graph.resolve("name", "Same Fictional Name", CUTOFF)


def test_future_changes_do_not_reveal_old_or_new_identifiers(graph):
    early = timestamp("2026-01-10T00:00:00Z")
    assert not graph.resolve("email", "old@example.test", early)
    assert not graph.resolve("email", "new@example.test", early)
    assert graph.resolve("email", "old@example.test", timestamp("2026-01-15T00:00:00Z")) == {"user_1"}


def test_stable_user_reference_cites_the_first_admissible_source(graph):
    versions = graph.matching_versions("user_id", "user_1", timestamp("2026-01-16T00:00:00Z"))
    assert versions and versions[0].source_id == "audit_1"
    assert versions[0].known_at < timestamp("2026-01-20T00:00:00Z")


def test_known_identifier_does_not_reveal_future_transition_or_future_source():
    rows = [snapshot(email="future@example.test", updated="2026-03-01T00:00:00Z")]
    graph = IdentityGraph(rows, [change(), change("audit_3", old="new@example.test", new="future@example.test",
                                                when="2026-02-15T00:00:00Z")])
    known = graph.matching_versions("email", "new@example.test", CUTOFF)
    assert known and all(v.valid_to is None for v in known)
    assert all(v.source_id == "audit_1" for v in known)
    assert not graph.resolve("email", "future@example.test", CUTOFF)
    assert all(v.known_at <= CUTOFF for v in graph.versions_for_user("user_1", CUTOFF))


def test_stale_updated_at_cannot_reveal_audited_future_value():
    graph = IdentityGraph([snapshot(email="future@example.test", updated="2025-01-01T00:00:00Z")], [
        change(new="future@example.test", when="2026-03-01T00:00:00Z")])
    assert not graph.resolve("email", "future@example.test", CUTOFF)
    assert not graph.resolve("email", "old@example.test", CUTOFF)


def test_earlier_snapshot_knowledge_is_not_removed_by_a_future_audit():
    graph = IdentityGraph([snapshot(email="old@example.test", updated="2025-01-01T00:00:00Z")], [
        change(new="future@example.test", when="2026-03-01T00:00:00Z")])
    assert graph.resolve("email", "old@example.test", CUTOFF) == {"user_1"}
    assert not graph.resolve("email", "future@example.test", CUTOFF)
    assert graph.issues  # Global snapshot/history disagreement remains visible, without merging identities.


def test_hash_only_ownership_survives_removed_pii_and_store_is_reused(graph):
    store = EvidenceStore()
    seed = observation({"email_hash": "b" * 64})
    clean = observation({"email": None, "email_hash": None, "phone": None}, when=CUTOFF.isoformat(),
                        capture=CUTOFF.isoformat(), locator="/1")
    unrelated = observation({"email": "new.jr@example.test"}, resource="other_resource", locator="/2")
    store.add([seed, clean, unrelated])
    owned = graph.observations_for_user("user_1", store, CUTOFF)
    assert owned == [seed, clean]
    assert graph.ownership(store, CUTOFF) is graph.ownership(store, CUTOFF)
    assert graph.ownership(store, CUTOFF)[("account_service", "opaque_resource")]["user_1"][0]["identity_source"] == "audit_2"


def test_future_file_cannot_backfill_historical_ownership(graph):
    store = EvidenceStore()
    store.add([observation({"email": "old@example.test"}, capture="2026-03-01T00:00:00Z"),
               observation({"email": None}, locator="/1")])
    assert not graph.observations_for_user("user_1", store, CUTOFF)


def test_explicit_resource_links_propagate_with_their_own_provenance_time(graph):
    store = EvidenceStore()
    account = observation({"user_id": "user_1"})
    search = observation({"source_resource_id": "opaque_resource"}, system="search_service", resource="search_doc",
                         locator="/1", when=CUTOFF.isoformat(), capture=CUTOFF.isoformat(),
                         related=(("account_service", "opaque_resource"),))
    store.add([account, search])
    owner = graph.ownership(store, CUTOFF)[("search_service", "search_doc")]["user_1"][0]
    assert owner["resource_link_source"] == search.observation_id
    assert timestamp(owner["known_at"]) == CUTOFF
    assert search in graph.observations_for_user("user_1", store, CUTOFF)


def test_conflicting_exact_subjects_preserve_ambiguity_without_merging(graph):
    store = EvidenceStore()
    store.add([observation({"user_id": "user_1", "email": "new.jr@example.test"})])
    owners = graph.ownership(store, CUTOFF)[("account_service", "opaque_resource")]
    assert set(owners) == {"user_1", "user_2"}
    assert len(graph.by_user) == 2
    requests = {"case_001": Request("case_001", CUTOFF, "old@example.test")}
    report = identity_coverage(graph, requests, store)
    assert report["uniquely_resolved"] == 1
    assert report["cases"][0]["ambiguous_resource_count"] == 1


def test_duplicate_email_resolves_to_ambiguous_users_not_one_merged_subject():
    graph = IdentityGraph([snapshot(), snapshot("user_2")], [])
    report = identity_coverage(graph, {"case_001": Request("case_001", CUTOFF, "new@example.test")}, EvidenceStore())
    assert report["ambiguous"] == 1 and report["uniquely_resolved"] == 0
    assert len(graph.by_user) == 2


def test_reported_activity_identity_link_preserves_claim_strength(graph):
    store = EvidenceStore()
    store.add([observation({"details": "Linked opaque_resource to user_1."}, kind="reported_claim")])
    basis = graph.ownership(store, CUTOFF)[("account_service", "opaque_resource")]["user_1"][0]
    assert basis["evidence_kind"] == "reported_claim"


def test_replicas_remain_distinct_observations_after_ownership_link(graph):
    store = EvidenceStore()
    primary = observation({"email": "old@example.test"})
    replica = replace(observation({"email": "old@example.test"}, locator="/1"), scope={"replica": "eu_west"})
    store.add([primary, replica])
    assert len(graph.observations_for_user("user_1", store, CUTOFF)) == 2

"""Independent business evidence proves new relations/fields; no reference labels."""
import json
from dataclasses import replace

import pytest

from deletion_audit.agent_context import investigation_context
from deletion_audit.inputs import InputError
from deletion_audit.observations import EvidenceStore, identifiers
from deletion_audit.proposals import ground_fact, ground_proposal, apply_grounded_updates
from deletion_audit.source_access import pointer
from deletion_audit.solver import audit, scope_negatives
from deletion_audit.state import observed_state, reconstruct
from test_ai_foundation import api_tools, fact, proposal, chat
from test_agent_corrections import agent_with_responses, BASELINE
from test_solver import obs


def nested_source(restore=True, **overrides):
    tools = api_tools()
    record = {"system_id": "backup_service", "resource_id": "backup_fixture",
              "record_type": "BACKUP_ARCHIVE", "user_id": "user_fixture",
              "observation_type": "direct_readback",
              "observed_at": "2026-01-20T00:00:00Z", "config": {"restore_allowed": restore}, **overrides}
    raw = json.dumps({"entity": record})
    source = replace(obs(category=None, fields={"text": raw}, kind="context"),
                     system_id=None, resource_id=None, observation_id="context:entity",
                     provenance={"raw": raw, "sha256": "fixture", "file_path": "evidence/record.json"})
    tools.store.add([source])
    link = fact(source)
    link.update(system_id="backup_service", resource_id="backup_fixture", category="BACKUP_ARCHIVE",
                state="UNKNOWN", interpretation="LINK_IDENTITY", quote="record_type", attributes={"record_pointer": "/entity"})
    extract = {**link, "state": "ACTIVE" if restore else "BLOCKED", "interpretation": "EXTRACT_FIELDS",
               "quote": "restore_allowed", "attributes": {"record_pointer": "/entity", "field_pointers": {"restore_allowed": "/config/restore_allowed"}}}
    return tools, source, link, extract


def test_original_source_window_and_pointer_never_drop_content_silently():
    tools, source, _, _ = nested_source()
    first = tools.inspect_source(source.file_id, source.observation_id, "/entity", limit=30)
    assert first["shown_count"] == 30 and first["truncated"] and first["next_offset"] == 30
    rest = tools.inspect_source(source.file_id, source.observation_id, "/entity", offset=30, limit=8000)
    assert not rest["truncated"] and len(first["content"] + rest["content"]) == first["total_count"]
    assert first["sha256"] == source.provenance["sha256"]
    with pytest.raises(InputError):
        tools.inspect_source("../outside", source.observation_id)
    future = replace(source, captured_at=source.captured_at.replace(year=2030), observation_id="future")
    tools.store.add([future])
    with pytest.raises(InputError, match="CUTOFF"):
        tools.inspect_source(future.file_id, "future")


@pytest.mark.parametrize("location", ["a", "/a/-1", "/a/01", "/a/99", "/~2"])
def test_source_pointer_is_strict(location):
    with pytest.raises(InputError):
        pointer({"a": [1]}, location)


def test_source_pointer_escapes_are_exact():
    assert pointer({"a/b": {"~": 3}}, "/a~1b/~0") == 3


def test_new_exact_relationship_and_fields_are_validated_in_dependency_order():
    tools, source, link, extract = nested_source()
    before = tools.graph.ownership(tools.store, tools.request.audit_at)
    assert ("backup_service", "backup_fixture") not in before
    with pytest.raises(InputError, match="OWNERSHIP"):
        ground_fact(extract, tools)
    updates, verdicts = ground_proposal(proposal([extract, link]), tools)
    assert {v["proof_delta"] for v in verdicts} == {"new_relationship", "new_field_proof"}
    local = apply_grounded_updates(tools.store, updates, tools.request.audit_at)
    assert set(tools.graph.ownership(local, tools.request.audit_at)[("backup_service", "backup_fixture")]) == {"user_fixture"}
    assert observed_state(updates[0]) is None and observed_state(updates[1]) == "ACTIVE"
    assert source.fields == {"text": source.provenance["raw"]}  # original is immutable
    again, repeated = ground_proposal(proposal([extract, link]), replace(tools, store=local))
    assert again == [] and all(v["proof_delta"] == "duplicate" for v in repeated)


@pytest.mark.parametrize("change,reason", [
    ({"user_id": "other_user"}, "SUBJECT"),
    ({"resource_id": "backup_other"}, "RESOURCE"),
    ({"observed_at": "2030-01-01T00:00:00Z"}, "CUTOFF"),
    ({"record_type": "USER_PROFILE"}, "CATEGORY"),
])
def test_relation_requires_same_entity_subject_category_and_time(change, reason):
    tools, _, link, _ = nested_source(**change)
    with pytest.raises(InputError, match=reason):
        ground_fact(link, tools)


def test_workflow_claim_is_not_an_extraction_source():
    tools, source, link, _ = nested_source()
    tools.store.observations[-1] = replace(source, kind="reported_claim")
    with pytest.raises(InputError, match="NON_ACTIVITY"):
        ground_fact(link, tools)


def test_context_without_a_direct_readback_marker_cannot_become_current_state():
    tools, _, link, extract = nested_source(observation_type="desired_configuration")
    updates, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert len(updates) == 1 and observed_state(updates[0]) is None
    assert "DIRECT_READBACK" in verdicts[-1]["reason"]


def test_pointer_cannot_rename_arbitrary_boolean_to_restore_permission():
    tools, _, link, extract = nested_source()
    extract["attributes"]["field_pointers"]["restore_allowed"] = "/config"
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert verdicts[-1]["validation"] == "REJECTED" and "CANONICAL_FIELD" in verdicts[-1]["reason"]


def test_relationship_preserves_conflicting_direct_identifier():
    tools, _, link, _ = nested_source(email="other@example.test")
    with pytest.raises(InputError, match="CONTRADICTORY"):
        ground_fact(link, tools)


def test_foreign_key_can_ground_a_removed_subject_reference_without_fuzzy_matching():
    tools, source, link, _ = nested_source(user_id=None, source_system_id="account_service", source_resource_id="opaque")
    result = ground_fact(link, tools)
    assert result.fields["user_id"] == "user_fixture" and observed_state(result) is None
    assert result.provenance["derivation"]["join_sources"]
    assert result.provenance["derivation"]["source_captured_at"] == source.captured_at.isoformat()
    assert investigation_context(tools, {"issues": []})["total_count"] == 1


def test_incomplete_or_unknown_foreign_key_never_creates_identity():
    tools, _, link, _ = nested_source(user_id=None, source_system_id="account_service", source_resource_id="unknown")
    with pytest.raises(InputError, match="FOREIGN_KEY"):
        ground_fact(link, tools)


def test_field_pointer_cannot_take_another_resources_flag():
    tools, _, link, extract = nested_source(config={"resource_id": "backup_other", "restore_allowed": True})
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert "CROSSES_RESOURCE_BOUNDARY" in verdicts[-1]["reason"]


def test_field_pointer_cannot_take_another_subjects_flag():
    tools, _, link, extract = nested_source(config={"user_id": "user_other", "restore_allowed": True})
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert "SUBJECT_BOUNDARY" in verdicts[-1]["reason"]


def test_desired_configuration_is_not_a_current_permission_readback():
    tools, _, link, extract = nested_source(desired={"restore_allowed": False})
    extract["state"] = "BLOCKED"
    extract["attributes"]["field_pointers"]["restore_allowed"] = "/desired/restore_allowed"
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert "NONCURRENT_SCOPE" in verdicts[-1]["reason"]


def test_conflicting_nested_flags_are_not_resolved_by_selecting_a_convenient_pointer():
    tools, _, link, extract = nested_source(profile={"restore_allowed": False})
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert "CONFLICTING_VALUES" in verdicts[-1]["reason"]


def test_partial_null_fields_cannot_prove_tombstone_redaction():
    tools, source, link, _ = nested_source(record_type="ACCOUNT_TOMBSTONE", config={"email": None})
    link["category"] = "ACCOUNT_TOMBSTONE"
    field = {**link, "interpretation": "EXTRACT_FIELDS", "state": "REDACTED", "quote": "email",
             "attributes": {"record_pointer": "/entity", "field_pointers": {"email": "/config/email"}}}
    _, verdicts = ground_proposal(proposal([link, field]), tools)
    assert verdicts[-1]["validation"] == "REJECTED" and "COMPLETE_IDENTIFIER_FIELDS" in verdicts[-1]["reason"]


def test_undated_context_requires_explicit_record_time():
    tools, source, link, _ = nested_source()
    tools.store.observations[-1] = replace(source, observed_at=None)
    assert ground_fact(link, tools).observed_at == source.observed_at


def test_entity_event_time_remains_distinct_from_document_capture():
    tools, source, link, _ = nested_source()
    later = replace(source, observed_at=tools.request.audit_at, captured_at=tools.request.audit_at)
    tools.store.observations[-1] = later
    result = ground_fact(link, tools)
    assert result.observed_at == source.observed_at and result.captured_at == later.captured_at


def vision_source(text="backup_fixture\nperson@example.test\nrestore_allowed: false"):
    tools = api_tools()
    source = obs("BACKUP_ARCHIVE", {"user_id": "user_fixture", "email": "person@example.test", "text": text},
                 "backup_fixture", "backup_service")
    source = replace(source, collection="screen_readback", provenance={"raw": text, "sha256": "imagehash", "file_path": "evidence/view.png"})
    tools.store.add([source])
    value = fact(source)
    value.update(state="BLOCKED", interpretation="EXTRACT_FIELDS", quote="restore_allowed: false",
                 attributes={"email": "person@example.test", "visible_fields": {"restore_allowed": False}})
    return tools, source, value


def test_visible_field_adds_real_state_proof_not_only_a_scope_flag():
    tools, source, value = vision_source()
    assert observed_state(source) is None
    update = ground_fact(value, tools, vision=True, image_hash="imagehash", provider="gemini", model="fixture")
    local = apply_grounded_updates(tools.store, [update], tools.request.audit_at)
    states, _ = reconstruct(local.observations, tools.request.audit_at)
    assert next(r for r in states if r.resource_id == "backup_fixture").state == "BLOCKED"
    assert "restore_allowed" not in source.fields and update.source_id == source.source_id
    assert update.provenance["derivation"]["source_observation_id"] == source.observation_id


@pytest.mark.parametrize("text", [
    "backup_fixture\nperson@example.test\nBlock restore",
    "backup_fixture\nperson@example.test\nrestore_allowed: false\nrestore_allowed: true",
    "backup_fixture backup_other\nperson@example.test\nrestore_allowed: false",
    "backup_fixture\nother@example.test\nrestore_allowed: false",
])
def test_vision_cannot_infer_hidden_buttons_conflicts_or_other_subjects(text):
    tools, _, value = vision_source(text)
    with pytest.raises(InputError):
        ground_fact(value, tools, vision=True, image_hash="imagehash")


def test_new_proof_can_change_an_independent_business_verdict():
    tools, source, link, extract = nested_source()
    clean = replace(obs(fields={"user_id": "user_fixture", "result": "NOT_FOUND"}), observation_id="clean-account")
    store = EvidenceStore(); store.add([clean, source]); tools = replace(tools, store=store)
    assert audit(tools.request, store, tools.graph, tools.policy)[0] == "COMPLETE"
    updates, _ = ground_proposal(proposal([link, extract]), tools)
    local = apply_grounded_updates(store, updates, tools.request.audit_at)
    status, steps, diagnostic = audit(tools.request, local, tools.graph, tools.policy)
    assert status == "INCOMPLETE" and not diagnostic["abstained"]
    assert any(s["operation"] == "REPORT_RESTORE_RISK" and s["evidence_id"] == source.source_id for s in steps)


def test_clean_extracted_replica_cannot_clear_a_dirty_primary():
    tools, _, link, extract = nested_source(restore=False, replica="failover")
    dirty = obs("BACKUP_ARCHIVE", {"user_id": "user_fixture", "restore_allowed": True},
                "backup_fixture", "backup_service", when="2026-01-10T00:00:00Z", scope={"replica": "primary"})
    tools.store.add([dirty])
    updates, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert verdicts[-1]["validation"] == "SOURCE_GROUNDED"
    local = apply_grounded_updates(tools.store, updates, tools.request.audit_at)
    states, _ = reconstruct(local.observations, tools.request.audit_at)
    current = next(r for r in states if r.resource_id == "backup_fixture")
    assert current.state == "ACTIVE" and len(current.copies) == 2


def test_unscoped_clean_context_cannot_overwrite_a_known_copy():
    tools, _, link, extract = nested_source(restore=False)
    tools.store.add([obs("BACKUP_ARCHIVE", {"user_id": "user_fixture", "restore_allowed": True},
        "backup_fixture", "backup_service", scope={"replica": "primary"})])
    _, verdicts = ground_proposal(proposal([link, extract]), tools)
    assert "COPY_SCOPE_UNPROVEN" in verdicts[-1]["reason"]


def test_one_extracted_row_never_becomes_an_exhaustive_inventory():
    tools, source, link, extract = nested_source()
    tools.store.observations[-1] = replace(source, scope={"table": "backup_catalog", "complete_collection": True})
    tools.store.add([obs("BACKUP_ARCHIVE", {"user_id": "user_fixture", "restore_allowed": True},
                        "backup_other", "backup_service")])
    updates, _ = ground_proposal(proposal([link, extract]), tools)
    local = apply_grounded_updates(tools.store, updates, tools.request.audit_at)
    assert scope_negatives(local, [("backup_service", "backup_other")], tools.request.audit_at) == []


def test_leads_enable_identity_discovery_without_fuzzy_or_future_data():
    tools, _, _, _ = nested_source()
    info = investigation_context(tools, {"issues": [{"code": "NO_DIRECT_STATE"}]})
    assert info["shown_count"] == info["total_count"] == 1 and info["goals"]


def test_penultimate_draft_is_corrected_inside_three_turns(tmp_path, monkeypatch):
    tools = api_tools(); wrong = fact(tools.store.observations[0]); wrong["state"] = "ABSENT"
    calls = [{"id": "identity", "type": "function", "function": {"name": "trace_identity", "arguments": "{}"}}]
    agent, histories = agent_with_responses(tmp_path, monkeypatch, [chat(calls=calls),
        chat(json.dumps(proposal([wrong]))), chat(json.dumps(proposal([fact(tools.store.observations[0])])))] )
    assert agent.investigate(tools, BASELINE) == []
    assert len(histories) == 3 and "tools" not in histories[1] and "tools" not in histories[2]
    assert agent.events[-1]["rounds"][1]["draft_requested"]


def test_agent_can_discover_and_return_validated_new_proof_without_existing_resource(tmp_path, monkeypatch):
    tools, source, link, extract = nested_source()
    calls = [{"id": "source", "type": "function", "function": {"name": "inspect_source", "arguments": json.dumps({
        "file_id": source.file_id, "observation_id": source.observation_id, "pointer_path": "/entity"})}}]
    agent, _ = agent_with_responses(tmp_path, monkeypatch, [chat(calls=calls), chat(json.dumps(proposal([extract, link])))])
    updates = agent.investigate(tools, {"issues": [{"code": "NO_DIRECT_STATE"}], "resource_keys": []})
    assert len(updates) == 2 and agent.events[-1]["proof_delta_counts"]["new_relationship"] == 1
    assert agent.events[-1]["proof_delta_counts"]["new_field_proof"] == 1
    assert agent.ledger.summary()["calls"] == 2  # mocks; this is not a live accuracy claim


def test_pagination_can_use_second_retrieval_without_extra_model_rounds(tmp_path, monkeypatch):
    tools = api_tools(); first = tools.store.observations[0]
    tools.store.add([replace(first, observation_id="second")])
    cursor = tools.search_evidence("user_id", "user_fixture", limit=1)["next_cursor"]
    def call(identifier, args):
        return chat(calls=[{"id": identifier, "type": "function", "function": {"name": "search_evidence", "arguments": json.dumps(args)}}])
    agent, histories = agent_with_responses(tmp_path, monkeypatch, [
        call("page1", {"kind": "user_id", "value": "user_fixture", "limit": 1}),
        call("page2", {"kind": "user_id", "value": "user_fixture", "limit": 1, "cursor": cursor}),
        chat(json.dumps(proposal()))])
    assert agent.investigate(tools, BASELINE) == []
    assert "tools" in histories[1] and len(histories) == 3
    assert agent.events[-1]["rounds"][1]["retrieval_continuation_needed"]

"""Narrow new proof paths: literal typed records and explicit visible boolean fields."""
import hashlib
import json
import re
from dataclasses import replace

from .inputs import InputError, timestamp
from .observations import identifiers, RESOURCE
from .source_access import pointer, raw_value, raw_text
from .state import actual_fields, observed_state


FIELD_NAMES = ("enabled", "restore_allowed", "deletion_block", "email", "phone", "name",
               "email_hash", "user_id", "direct_identifiers", "retention_until", "retained_until", "hold_active")
BOOLEAN_FIELDS = {"enabled", "restore_allowed", "deletion_block", "hold_active"}


def bound_field(record, location, name, key, users):
    if not location or location.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~") != name:
        raise InputError("FIELD_POINTER_MUST_NAME_THE_CANONICAL_FIELD")
    parts = location.split("/")[1:]
    wrappers = {"config", "configuration", "settings", "permissions", "profile", "document",
                "decoded_record", "record", "fields", "state", "attributes", "data"}
    if any(part not in wrappers for part in parts[:-1]):
        raise InputError("FIELD_POINTER_UNSUPPORTED_OR_NONCURRENT_SCOPE")
    for i in range(len(parts)):
        node = pointer(record, "/" + "/".join(parts[:i])) if i else record
        if isinstance(node, dict) and (
                (node.get("resource_id") is not None and node["resource_id"] != key[1])
                or (node.get("system_id") is not None and node["system_id"] != key[0])):
            raise InputError("FIELD_POINTER_CROSSES_RESOURCE_BOUNDARY")
        if isinstance(node, dict) and any(isinstance(node.get(k), str) and node[k] not in users
                for k in ("user_id", "subject_reference", "customer_reference")):
            raise InputError("FIELD_POINTER_CROSSES_SUBJECT_BOUNDARY")
    value = pointer(record, location)
    pending = [record]
    while pending:
        node = pending.pop()
        if not isinstance(node, dict) or (node.get("resource_id") is not None and node["resource_id"] != key[1]):
            continue
        if name in node and node[name] != value:
            raise InputError("FIELD_POINTER_CONFLICTING_VALUES_IN_ENTITY")
        pending.extend(v for k, v in node.items() if k in wrappers and isinstance(v, dict))
    return value


def _time(source, record, fact, at):
    if source.captured_at > at or (source.observed_at and source.observed_at > at):
        raise InputError("EXTRACTION_SOURCE_AFTER_CUTOFF")
    if any(k in record and record[k] is not None and not isinstance(record[k], str)
           for k in ("observed_at", "recorded_at", "event_time", "updated_at")):
        raise InputError("EXTRACTION_INVALID_EMBEDDED_TIMESTAMP")
    times = [timestamp(record[k]) for k in ("observed_at", "recorded_at", "event_time", "updated_at")
             if isinstance(record.get(k), str)]
    if any(t > at for t in times):
        raise InputError("EXTRACTION_EMBEDDED_EVENT_AFTER_CUTOFF")
    if any(t > source.captured_at for t in times):
        raise InputError("EXTRACTION_EVENT_AFTER_FILE_CAPTURE")
    explicit = next((record[k] for k in ("observed_at", "recorded_at") if isinstance(record.get(k), str)), None)
    when = timestamp(explicit) if explicit else source.observed_at
    if when is None:
        raise InputError("EXTRACTION_REQUIRES_UNAMBIGUOUS_EVENT_TIME")
    if timestamp(fact["observed_at"]) != when:
        raise InputError("EXTRACTION_TIMESTAMP_NOT_IN_SOURCE")
    return when


def extract(fact, source, tools, *, vision=False, image_hash=None, provider=None, model=None):
    at, attrs = tools.request.audit_at, fact["attributes"]
    key = fact["system_id"], fact["resource_id"]
    users = tools.graph.resolve("email", tools.request.email, at)
    if len(users) != 1 or source.kind == "reported_claim" or not source.file_id:
        raise InputError("EXTRACTION_REQUIRES_UNIQUE_SUBJECT_AND_NON_ACTIVITY_SOURCE")
    quote = fact["quote"]
    if not quote.strip() or quote not in raw_text(source):
        raise InputError("EXTRACTION_QUOTE_NOT_EXACT_IN_SOURCE")
    original = raw_value(source)
    record = pointer(original, attrs.get("record_pointer", ""))
    if not isinstance(record, dict):
        record = {}
    declared_key = (record.get("system_id", record.get("origin_system", record.get("system"))), record.get("resource_id"))
    source_key = source.system_id, source.resource_id
    # A selected structured entity must bind its identifiers in the same object.
    if declared_key != key and (source_key != key or any(declared_key)):
        raise InputError("EXTRACTION_RESOURCE_NOT_BOUND_TO_RECORD")
    if attrs.get("record_pointer") and declared_key != key and not (
            source.kind in {"direct", "scoped_negative"} and attrs["record_pointer"] in {"/profile", "/document", "/decoded_record"}):
        raise InputError("EXTRACTION_RECORD_SCOPE_NOT_EXPLICIT")
    category = record.get("record_type", record.get("data_category", source.category))
    if category != fact["category"] or category not in set(tools.policy.rules) | {"DATA_FLOW"}:
        raise InputError("EXTRACTION_CATEGORY_NOT_IN_SOURCE")
    when = _time(source, record, fact, at)
    owners = tools.graph.ownership(tools.store, at).get(key, {})
    relation = fact["interpretation"] == "LINK_IDENTITY"
    join_sources = []
    if relation:
        if vision or not record or declared_key != key or fact["state"] != "UNKNOWN":
            raise InputError("IDENTITY_LINK_REQUIRES_EXPLICIT_STRUCTURED_ENTITY")
        subjects = {record[k] for k in ("user_id", "subject_reference", "customer_reference")
                    if isinstance(record.get(k), str)}
        parent_key = record.get("source_system_id"), record.get("source_resource_id")
        if any(parent_key):
            if not all(isinstance(v, str) and v for v in parent_key):
                raise InputError("IDENTITY_LINK_REQUIRES_COMPLETE_FOREIGN_KEY")
            parent_owners = tools.graph.ownership(tools.store, at).get(parent_key, {})
            if set(parent_owners) != set(users):
                raise InputError("IDENTITY_LINK_FOREIGN_KEY_NOT_UNIQUELY_GROUNDED")
            join_sources = [basis for bases in parent_owners.values() for basis in bases]
        if (subjects and subjects != set(users)) or (not subjects and not join_sources) or any(
                tools.graph.resolve("user_id", u, at) != users for u in subjects):
            raise InputError("IDENTITY_LINK_SUBJECT_NOT_EXACT_OR_CONFLICTING")
        for identifier_kind, value in identifiers({k: v for k, v in record.items() if k in {"email", "phone", "email_hash"}}):
            if tools.graph.resolve(identifier_kind, value, at) != users:
                raise InputError("IDENTITY_LINK_CONTRADICTORY_DIRECT_IDENTIFIER")
        if owners and set(owners) != set(users):
            raise InputError("IDENTITY_LINK_CONFLICTS_WITH_EXISTING_OWNERSHIP")
        fields = {"system_id": key[0], "resource_id": key[1], "user_id": next(iter(users))}
        kind = "relationship"  # ownership metadata is never resulting record state
    else:
        if set(owners) != set(users):
            raise InputError("EXTRACTION_OWNERSHIP_NOT_GROUNDED")
        join_sources = [basis for bases in owners.values() for basis in bases]
        entity_fields = record if record else actual_fields(source)
        # Keep original containers in provenance, not as competing decoded/profile
        # wrappers that would silently override the explicitly bound scalar fields.
        fields = {k: v for k, v in entity_fields.items() if not isinstance(v, (dict, list))}
        selected = attrs.get("field_pointers", {})
        visible = attrs.get("visible_fields", {})
        if bool(selected) == bool(visible):
            raise InputError("EXTRACTION_REQUIRES_EXACTLY_ONE_FIELD_BINDING_MODE")
        if selected:
            # Pointers are relative to this record, never other entities in the file.
            if not record:
                raise InputError("FIELD_POINTER_REQUIRES_STRUCTURED_RECORD")
            if source.kind not in {"direct", "scoped_negative"} and record.get("observation_type") not in {"direct_readback", "snapshot_row"}:
                raise InputError("FIELD_EXTRACTION_REQUIRES_EXPLICIT_DIRECT_READBACK")
            if any(record.get(k) is True for k in ("planned", "proposed", "simulation")):
                raise InputError("FIELD_EXTRACTION_CANNOT_PROMOTE_PROPOSED_STATE")
            values = {name: bound_field(record, location, name, key, users) for name, location in selected.items()}
        else:
            if not vision or source.collection not in {"ocr_text", "screen_readback"} or source.provenance.get("sha256") != image_hash:
                raise InputError("VISIBLE_FIELDS_REQUIRE_ORIGINAL_IMAGE")
            if ("email", attrs.get("email", "").casefold()) not in set(identifiers(raw_text(source))) or tools.graph.resolve("email", attrs.get("email", ""), at) != users:
                raise InputError("VISIBLE_IDENTIFIER_NOT_EXACTLY_CORROBORATED")
            text = raw_text(source)
            if {m[0] for m in RESOURCE.finditer(text)} != {key[1]}:
                raise InputError("VISIBLE_FIELD_RESOURCE_SCOPE_AMBIGUOUS")
            values = {}
            for name, value in visible.items():
                labels = name.replace("_", "[ _]")
                matches = re.findall(r"(?im)^\s*" + labels + r"\s*:\s*(true|false)\s*$", text)
                if len(matches) != 1 or (matches[0].lower() == "true") is not value:
                    raise InputError("VISIBLE_BOOLEAN_NOT_EXPLICIT_OR_CONTRADICTORY")
                values[name] = value
        for name, value in values.items():
            if name not in FIELD_NAMES or (name in BOOLEAN_FIELDS and type(value) is not bool):
                raise InputError("EXTRACTION_UNSUPPORTED_FIELD_OR_TYPE")
            if name in fields and fields[name] != value:
                raise InputError("EXTRACTION_CONTRADICTS_ORIGINAL_FIELD")
            if value is not None and type(value) not in {str, bool, int}:
                raise InputError("EXTRACTION_REQUIRES_LITERAL_SCALAR")
            fields[name] = value
        if fields.get("user_id") not in (None, "", "[REDACTED]") and (
                not isinstance(fields["user_id"], str) or fields["user_id"] not in users):
            raise InputError("EXTRACTION_CONFLICTING_SUBJECT")
        for identifier_kind, value in identifiers({k: v for k, v in fields.items() if k in {"email", "phone", "email_hash"}}):
            resolved = tools.graph.resolve(identifier_kind, value, at)
            if resolved != users:
                raise InputError("EXTRACTION_DIRECT_IDENTIFIER_NOT_EXACTLY_CORROBORATED")
        kind = "direct"
    binding = {"interpretation": fact["interpretation"], "record_pointer": attrs.get("record_pointer", ""),
               "field_pointers": attrs.get("field_pointers", {}), "visible_fields": attrs.get("visible_fields", {}),
               "system_id": key[0], "resource_id": key[1]}
    digest = hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()[:24]
    provenance = {**source.provenance, "derivation": {"source_observation_id": source.observation_id,
        "binding": binding, "provider": provider, "model": model, "image_sha256": image_hash,
        "source_captured_at": source.captured_at.isoformat(), "join_sources": join_sources}}
    available = max([source.captured_at] + [timestamp(basis["known_at"]) for basis in join_sources])
    scope = {**source.scope, "agent_interpretation": fact["interpretation"], "agent_row_only": True}
    replica = record.get("replica", record.get("replica_id"))
    if replica is not None:
        if not isinstance(replica, str) or not replica or len(replica) > 200:
            raise InputError("EXTRACTION_INVALID_REPLICA_SCOPE")
        if source.scope.get("replica") and source.scope["replica"] != replica:
            raise InputError("EXTRACTION_REPLICA_SCOPE_CONFLICT")
        scope["replica"] = replica
    if not relation and source.kind == "context" and not scope.get("replica") and fact["state"] in {
            "BLOCKED", "ABSENT", "REDACTED", "ANONYMIZED", "DISABLED"} and any(
                o.scope.get("replica") for o in tools.store.for_resource(*key, at)):
        raise InputError("EXTRACTION_CLEAN_READBACK_COPY_SCOPE_UNPROVEN")
    derived = replace(source, observation_id=source.observation_id + ":grounded:" + digest,
        system_id=key[0], resource_id=key[1], category=category, observed_at=when, captured_at=available, fields=fields,
        kind=kind, identifiers=identifiers({k: v for k, v in fields.items() if k in {
            "user_id", "subject_reference", "customer_reference", "email", "phone", "email_hash"}}), provenance=provenance,
        scope=scope, related_resources=())
    if not relation and fact["state"] in {"REDACTED", "ANONYMIZED"}:
        required = {"name", "email", "phone", "email_hash"}
        if fact["state"] == "ANONYMIZED":
            required.add("user_id")
        if not required <= fields.keys():
            raise InputError("EXTRACTION_COMPLIANCE_REQUIRES_COMPLETE_IDENTIFIER_FIELDS")
        if category == "ACCOUNT_TOMBSTONE" and fields.get("user_id") not in users:
            raise InputError("EXTRACTION_TOMBSTONE_REQUIRES_STABLE_SUBJECT_REFERENCE")
    if not relation and (observed_state(derived) is None or observed_state(derived) != fact["state"]):
        raise InputError("EXTRACTED_FIELDS_DO_NOT_PROVE_PROPOSED_STATE")
    return derived

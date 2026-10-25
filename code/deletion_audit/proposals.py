"""Independent proposal schema and deterministic grounding; model prose is not evidence."""
from dataclasses import replace

from .inputs import InputError, timestamp
from .observations import identifiers
from .state import actual_fields, observed_state
from .source_access import raw_text
from .grounded_extraction import FIELD_NAMES


def obj(properties, required=None):
    return {"type": "object", "properties": properties, "required": list(properties) if required is None else required,
            "additionalProperties": False}


def string(maximum=600, enum=None):
    result = {"type": "string", "maxLength": maximum}
    if enum is not None:
        result["enum"] = enum
    return result


ATTRIBUTES = obj({"asset_reference": string(200), "link_evidence_id": string(100), "email": string(200),
                  "user_id": string(100), "enabled": {"type": "boolean"}, "restore_allowed": {"type": "boolean"},
                  "record_pointer": string(512), "field_pointers": obj({k: string(512) for k in FIELD_NAMES}, []),
                  "visible_fields": obj({k: {"type": "boolean"} for k in ("enabled", "restore_allowed", "deletion_block")}, [])}, [])
POLICY_CATEGORIES = sorted(["USER_PROFILE", "SECONDARY_IDENTIFIER", "SEARCH_INDEX_ENTRY", "CACHE_ENTRY",
    "SUPPORT_MESSAGE", "SUPPORT_ATTACHMENT", "ANALYTICS_PROFILE", "PRODUCT_TELEMETRY", "USER_EXPORT",
    "MARKETING_PROFILE", "EMAIL_DELIVERY_LOG", "SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD", "BACKUP_ARCHIVE",
    "ACCOUNT_TOMBSTONE", "DATA_FLOW"])
FACT = obj({"system_id": string(100), "resource_id": string(100), "evidence_id": string(100),
            "observation_id": string(250), "observed_at": string(50), "category": string(80, POLICY_CATEGORIES),
            "state": string(30, ["PRESENT", "ABSENT", "IDENTIFIABLE", "REDACTED", "ANONYMIZED", "ACTIVE", "DISABLED", "BLOCKED", "UNKNOWN"]),
            "interpretation": string(40, ["REUSE_DIRECT", "EXTRACT_VISIBLE", "LINK_ASSET", "LINK_IDENTITY", "EXTRACT_FIELDS"]),
            "fact_or_hypothesis": string(20, ["FACT", "HYPOTHESIS"]), "quote": string(1000),
            "attributes": ATTRIBUTES, "reasoning_summary": string(700)})
PROPOSAL_SCHEMA = obj({"facts": {"type": "array", "items": FACT, "maxItems": 24},
    "hypotheses": {"type": "array", "items": string(), "maxItems": 10},
    "unresolved_questions": {"type": "array", "items": string(), "maxItems": 10}, "summary": string(1500)})


def validate_json(value, schema, path="$"):
    if "anyOf" in schema:
        for branch in schema["anyOf"]:
            try:
                validate_json(value, branch, path)
                break
            except InputError:
                pass
        else:
            raise InputError(path + ": no allowed conditional schema (resource searches require nonempty system_id)")
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
             "integer": type(value) is int, "boolean": type(value) is bool}
    if kind not in valid or not valid[kind]:
        raise InputError(path + ": unexpected JSON type")
    if "enum" in schema and value not in schema["enum"]:
        raise InputError(path + ": illegal enum value; allowed=" + ",".join(str(v) for v in schema["enum"]))
    if kind == "object":
        properties = schema.get("properties", {})
        if set(schema.get("required", [])) - value.keys():
            raise InputError(path + ": missing required fields")
        if schema.get("additionalProperties") is False and value.keys() - properties.keys():
            raise InputError(path + ": unexpected fields")
        for key in value.keys() & properties.keys():
            validate_json(value[key], properties[key], path + "." + key)
    elif kind == "array":
        if len(value) > schema.get("maxItems", 1000):
            raise InputError(path + ": too many items")
        for i, item in enumerate(value):
            validate_json(item, schema["items"], path + "[" + str(i) + "]")
    elif kind == "string":
        if len(value) > schema.get("maxLength", 10000) or len(value) < schema.get("minLength", 0):
            raise InputError(path + ": invalid string length")
    elif kind == "integer" and not schema.get("minimum", -10**9) <= value <= schema.get("maximum", 10**9):
        raise InputError(path + ": number outside limits")


def literal(needle, haystack):
    return bool(needle.strip()) and " ".join(needle.split()) in " ".join(haystack.split())


def ground_fact(fact, tools, *, vision=False, image_hash=None, provider=None, model=None):
    """Return a source-derived observation or raise a reason retained in diagnostics."""
    validate_json(fact, FACT)
    if fact["fact_or_hypothesis"] != "FACT":
        raise InputError("HYPOTHESIS_NOT_APPLIED")
    source = next((o for o in tools.store.observations if o.observation_id == fact["observation_id"]), None)
    if source is None or source.source_id != fact["evidence_id"]:
        raise InputError("UNKNOWN_OR_MISMATCHED_EVIDENCE")
    if fact["interpretation"] in {"LINK_IDENTITY", "EXTRACT_FIELDS"}:
        from .grounded_extraction import extract
        if vision and (source.provenance.get("sha256") != image_hash or not source.provenance.get("file_path", "").endswith(".png")):
            raise InputError("VISION_HASH_OR_ORIGINAL_IMAGE_MISMATCH")
        return extract(fact, source, tools, vision=vision, image_hash=image_hash, provider=provider, model=model)
    if not source.admissible(tools.request.audit_at):
        raise InputError("EVIDENCE_AFTER_CUTOFF_OR_UNDATED")
    if vision and (source.provenance.get("sha256") != image_hash
                   or not source.provenance.get("file_path", "").endswith(".png")):
        raise InputError("VISION_HASH_OR_ORIGINAL_IMAGE_MISMATCH")
    if timestamp(fact["observed_at"]) != source.observed_at:
        raise InputError("OBSERVATION_TIMESTAMP_MISMATCH")
    key = fact["system_id"], fact["resource_id"]
    ownership = tools.graph.ownership(tools.store, tools.request.audit_at)
    users = tools.graph.resolve("email", tools.request.email, tools.request.audit_at)
    if len(users) != 1 or not users.intersection(ownership.get(key, {})) or len(ownership.get(key, {})) != 1:
        raise InputError("OWNERSHIP_NOT_GROUNDED_OR_AMBIGUOUS")
    if source.kind == "reported_claim":
        raise InputError("ACTIVITY_CLAIM_NOT_DIRECT_STATE")
    if fact["interpretation"] == "LINK_ASSET":
        if fact["category"] != "SUPPORT_ATTACHMENT":
            raise InputError("LINK_ASSET_REQUIRES_SUPPORT_ATTACHMENT")
        if fact["state"] != "PRESENT":
            raise InputError("LINK_ASSET_REQUIRES_PRESENT_LISTING")
        attrs = fact["attributes"]
        reference, link_id = attrs.get("asset_reference", ""), attrs.get("link_evidence_id")
        link = next((o for o in tools.store.observations if o.source_id == link_id and o.admissible(tools.request.audit_at)
                     and (o.system_id, o.resource_id) == key), None)
        details = link.fields.get("details", "") if link else ""
        # Explicit catalog association plus a literal visible asset name. Catalog is
        # ownership metadata; the file listing, not operation SUCCESS, proves presence.
        if not link or link.fields.get("event_type") != "LINK_RESOURCE_IDENTITY":
            raise InputError("ASSET_CATALOG_LINK_NOT_ADMISSIBLE_FOR_RESOURCE")
        if ("Attachment catalog confirmed" not in details or "belongs only to" not in details
                or "no other subject is linked" not in details or "(" + reference + ")" not in details):
            raise InputError("ASSET_CATALOG_SOLE_OWNERSHIP_OR_FILENAME_UNPROVEN")
        if not literal(reference, raw_text(source)):
            raise InputError("ASSET_FILENAME_NOT_LITERAL_IN_LISTING")
        if not literal(fact["quote"], raw_text(source)):
            raise InputError("ASSET_QUOTE_NOT_LITERAL_IN_SOURCE")
        fields = {"asset_reference": reference, "shared_attachment": False, "user_id": next(iter(users))}
        return replace(source, observation_id=source.observation_id + ":asset:" + key[1], system_id=key[0], resource_id=key[1],
                       category="SUPPORT_ATTACHMENT", kind="direct", fields=fields, identifiers=identifiers(fields),
                       scope={**source.scope, "link_evidence_id": link_id, "accepted_interpretation": "exact_asset_reference"})
    if (source.system_id, source.resource_id) != key:
        raise InputError("RESOURCE_ASSOCIATION_NOT_IN_SOURCE")
    if not vision:
        if fact["interpretation"] != "REUSE_DIRECT" or not literal(fact["quote"], raw_text(source)):
            raise InputError("UNSUPPORTED_TEXT_INTERPRETATION")
        if fact["category"] != source.category or fact["state"] != observed_state(source):
            raise InputError("PROPOSED_STATE_OR_CATEGORY_NOT_IN_SOURCE")
        return source
    if source.provenance.get("sha256") != image_hash or source.collection not in {"ocr_text", "screen_readback"}:
        raise InputError("VISION_HASH_OR_ORIGINAL_IMAGE_MISMATCH")
    # Vision can corroborate a visible exact identifier; it cannot infer hidden flags
    # or infer redaction from fields that are not displayed.
    attrs = fact["attributes"]
    email = attrs.get("email")
    tokens = set(identifiers(raw_text(source)))
    if not email or ("email", email.casefold()) not in tokens or not users.intersection(tools.graph.resolve("email", email, tools.request.audit_at)):
        raise InputError("VISIBLE_IDENTIFIER_NOT_EXACTLY_CORROBORATED")
    fields = actual_fields(source)
    if source.category != fact["category"] or observed_state(source) != fact["state"]:
        raise InputError("VISION_STATE_REQUIRES_STRUCTURED_CORROBORATION")
    if fact["interpretation"] != "EXTRACT_VISIBLE" or not literal(fact["quote"], raw_text(source)):
        raise InputError("VISION_QUOTE_OR_INTERPRETATION_NOT_CORROBORATED")
    return replace(source, scope={**source.scope, "vision_corroborated": True, "provider": provider,
                                 "model": model, "vision_image_sha256": image_hash})


def fact_signature(source):
    """Count source-grounded assertions, not generated observation identifiers."""
    return (source.system_id, source.resource_id, source.category, source.source_id,
            source.observed_at, observed_state(source), source.scope.get("replica"), source.scope.get("table"))


def proof_delta(observation, tools):
    """Distinguish new relationships/field predicates from source-state duplicates."""
    if observation.kind == "relationship":
        uid = observation.fields["user_id"]
        return "new_relationship" if uid not in tools.graph.ownership(tools.store, tools.request.audit_at).get(
            (observation.system_id, observation.resource_id), {}) else "duplicate"
    if observation.scope.get("agent_interpretation") == "EXTRACT_FIELDS":
        binding = observation.provenance["derivation"]["binding"]
        names = set(binding["field_pointers"]) | set(binding["visible_fields"])
        equivalent = [o for o in tools.store.observations if fact_signature(o) == fact_signature(observation)]
        if not any(all(k in actual_fields(o) and actual_fields(o)[k] == observation.fields[k] for k in names) for o in equivalent):
            return "new_field_proof"
        return "duplicate"
    original = next((o for o in tools.store.observations if o.observation_id == observation.observation_id), None)
    if original is not None and is_metadata_enrichment(original, observation):
        return "metadata_enrichment"
    return "new_state_fact" if fact_signature(observation) not in {fact_signature(o) for o in tools.store.observations} else "duplicate"


def ground_proposal(proposal, tools, **kwargs):
    """Validate relations first, then dependent facts, in a disposable case-local store."""
    validate_json(proposal, PROPOSAL_SCHEMA)
    accepted, verdicts = [], []
    working = replace(tools, graph=tools.graph.fork())
    ordered = sorted(enumerate(proposal["facts"]), key=lambda item: item[1]["interpretation"] != "LINK_IDENTITY")
    for index, fact in ordered:
        try:
            observation = ground_fact(fact, working, **kwargs)
            delta = proof_delta(observation, working)
            verdicts.append({"fact_index": index, "observation_id": observation.observation_id,
                "validation": "SOURCE_GROUNDED", "proof_delta": delta,
                "new_fact": delta in {"new_relationship", "new_field_proof", "new_state_fact"},
                "enrichment": delta == "metadata_enrichment"})
            if delta != "duplicate":
                accepted.append(observation)
                working = replace(tools, graph=working.graph.fork(),
                                  store=apply_grounded_updates(tools.store, accepted, tools.request.audit_at))
        except (InputError, ValueError) as exc:
            verdicts.append({"fact_index": index, "validation": "REJECTED", "proposal": fact, "reason": str(exc)})
    return accepted, verdicts


def is_metadata_enrichment(original, updated):
    allowed = {"vision_corroborated", "provider", "model", "vision_image_sha256"}
    return (original != updated and replace(updated, scope=original.scope) == original
            and all(updated.scope.get(k) == v for k, v in original.scope.items())
            and (updated.scope.keys() - original.scope.keys()) <= allowed
            and updated.scope.get("vision_corroborated") is True
            and updated.scope.get("vision_image_sha256") == original.provenance.get("sha256"))


def apply_grounded_updates(store, updates, at):
    """Per-case replacement preserves IDs, original evidence, provenance and indexes."""
    from .observations import EvidenceStore
    originals = {o.observation_id: o for o in store.observations}
    replacements, additions = {}, []
    for update in updates:
        if not update.admissible(at):
            raise InputError("AI_UPDATE_AFTER_CUTOFF")
        original = originals.get(update.observation_id)
        if original is not None:
            if not is_metadata_enrichment(original, update):
                raise InputError("AI_UPDATE_IMMUTABLE_SOURCE_CHANGED")
            replacements[update.observation_id] = update
        else:
            additions.append(update)
    local = EvidenceStore(files=store.files, issues=store.issues, source_text=store.source_text)
    local.add(replacements.get(o.observation_id, o) for o in store.observations)
    local.add(additions)
    return local

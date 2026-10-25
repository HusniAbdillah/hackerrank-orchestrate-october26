"""Independent proposal schema and deterministic grounding; model prose is not evidence."""
import json
import re
from dataclasses import replace

from .inputs import InputError, timestamp
from .observations import identifiers
from .state import actual_fields, observed_state


def obj(properties, required=None):
    return {"type": "object", "properties": properties, "required": list(properties) if required is None else required,
            "additionalProperties": False}


def string(maximum=600, enum=None):
    result = {"type": "string", "maxLength": maximum}
    if enum is not None:
        result["enum"] = enum
    return result


ATTRIBUTES = obj({"asset_reference": string(200), "link_evidence_id": string(100), "email": string(200),
                  "user_id": string(100), "enabled": {"type": "boolean"}, "restore_allowed": {"type": "boolean"}}, [])
FACT = obj({"system_id": string(100), "resource_id": string(100), "evidence_id": string(100),
            "observation_id": string(250), "observed_at": string(50), "category": string(80),
            "state": string(30, ["PRESENT", "ABSENT", "IDENTIFIABLE", "REDACTED", "ANONYMIZED", "ACTIVE", "DISABLED", "BLOCKED", "UNKNOWN"]),
            "interpretation": string(40, ["REUSE_DIRECT", "EXTRACT_VISIBLE", "LINK_ASSET"]),
            "fact_or_hypothesis": string(20, ["FACT", "HYPOTHESIS"]), "quote": string(1000),
            "attributes": ATTRIBUTES, "reasoning_summary": string(700)})
PROPOSAL_SCHEMA = obj({"facts": {"type": "array", "items": FACT, "maxItems": 24},
    "hypotheses": {"type": "array", "items": string(), "maxItems": 10},
    "unresolved_questions": {"type": "array", "items": string(), "maxItems": 10}, "summary": string(1500)})


def validate_json(value, schema, path="$"):
    kind = schema.get("type")
    valid = {"object": isinstance(value, dict), "array": isinstance(value, list), "string": isinstance(value, str),
             "integer": type(value) is int, "boolean": type(value) is bool}
    if kind not in valid or not valid[kind]:
        raise InputError(path + ": unexpected JSON type")
    if "enum" in schema and value not in schema["enum"]:
        raise InputError(path + ": illegal enum value")
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


def raw_text(source):
    raw = source.provenance.get("raw", source.fields)
    return raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)


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
        attrs = fact["attributes"]
        reference, link_id = attrs.get("asset_reference", ""), attrs.get("link_evidence_id")
        link = next((o for o in tools.store.observations if o.source_id == link_id and o.admissible(tools.request.audit_at)
                     and (o.system_id, o.resource_id) == key), None)
        details = link.fields.get("details", "") if link else ""
        # Explicit catalog association plus a literal visible asset name. Catalog is
        # ownership metadata; the file listing, not operation SUCCESS, proves presence.
        if (not link or link.fields.get("event_type") != "LINK_RESOURCE_IDENTITY"
            or "Attachment catalog confirmed" not in details or "belongs only to" not in details
            or "no other subject is linked" not in details or "(" + reference + ")" not in details
            or not literal(reference, raw_text(source)) or not literal(fact["quote"], raw_text(source))
            or fact["category"] != "SUPPORT_ATTACHMENT" or fact["state"] != "PRESENT"):
            raise InputError("ASSET_REFERENCE_OR_SOLE_OWNERSHIP_UNPROVEN")
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
    return replace(source, scope={**source.scope, "vision_corroborated": True, "provider": provider, "model": model})

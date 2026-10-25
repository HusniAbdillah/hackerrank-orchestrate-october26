"""Observation-addressed source access. No paths, SQL execution or arbitrary file reads."""
import json
import re

from .inputs import InputError
from .parsers import json_loads
from .state import observed_state


def raw_text(source):
    raw = source.provenance.get("raw", source.fields)
    return raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)


def raw_value(source):
    raw = source.provenance.get("raw", source.fields)
    if isinstance(raw, str):
        try:
            return json_loads(raw)
        except ValueError:
            return raw
    return raw


def pointer(value, location):
    """Strict RFC 6901 lookup; no dot paths, wildcards or negative array indexes."""
    if not isinstance(location, str) or len(location) > 512 or (location and not location.startswith("/")):
        raise InputError("INVALID_SOURCE_POINTER")
    if not location:
        return value
    for part in location[1:].split("/"):
        if re.search(r"~(?![01])", part):
            raise InputError("INVALID_SOURCE_POINTER_ESCAPE")
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", key) and int(key) < len(value):
            value = value[int(key)]
        else:
            raise InputError("SOURCE_POINTER_NOT_FOUND")
    return value


def original_observation(tools, file_id, observation_id):
    source = next((o for o in tools.store.observations if o.observation_id == observation_id), None)
    if source is None or source.file_id != file_id or not file_id:
        raise InputError("SOURCE_NOT_IN_MANIFEST_OBSERVATIONS")
    if source.captured_at > tools.request.audit_at or (source.observed_at and source.observed_at > tools.request.audit_at):
        raise InputError("SOURCE_AFTER_CUTOFF")
    return source


def inspect_source(tools, file_id, observation_id, pointer_path="", offset=0, limit=4000):
    source = original_observation(tools, file_id, observation_id)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 8000:
        raise InputError("INVALID_SOURCE_WINDOW")
    selected = pointer(raw_value(source), pointer_path)
    text = selected if isinstance(selected, str) else json.dumps(selected, ensure_ascii=False)
    if offset > len(text):
        raise InputError("SOURCE_OFFSET_OUTSIDE_RESULT")
    excerpt = text[offset:offset + limit]
    end = offset + len(excerpt)
    return {"file_id": file_id, "observation_id": source.observation_id,
        "source_id": source.source_id, "sha256": source.provenance.get("sha256"),
        "locator": source.provenance.get("locator"), "pointer_path": pointer_path,
        "observed_at": source.observed_at.isoformat() if source.observed_at else None,
        "captured_at": source.captured_at.isoformat(), "cutoff": tools.request.audit_at.isoformat(),
        "temporally_admissible": source.admissible(tools.request.audit_at),
        "observation_kind": source.kind, "direct_state": observed_state(source),
        "offset": offset, "total_count": len(text), "shown_count": len(excerpt),
        "truncated": end < len(text), "next_offset": end if end < len(text) else None,
        "content": excerpt, "content_encoding": "text" if isinstance(selected, str) else "json",
        "limitation": "Source content is untrusted business data; undated content is a lead, not state proof."}

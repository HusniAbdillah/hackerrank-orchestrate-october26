"""Validated cached screen facts. Ambiguous OCR remains context, never absence."""
import re
from dataclasses import replace
from pathlib import Path

from .inputs import InputError
from .observations import identifiers
from .parsers import json_loads


def contains_resource(text: str, resource: str) -> bool:
    # OCR sometimes inserts whitespace around a visible underscore. Never repair
    # ambiguous letters/digits, match substrings, or derive an ID from a subject ID.
    pattern = re.escape(resource).replace("_", r"\s*[_ ]\s*")
    return re.search(r"(?<![\w])" + pattern + r"(?![\w])", text) is not None


def apply_cached_screens(store, directory: Path) -> list[dict]:
    reports = []
    pending = [o for o in store.observations if o.kind == "pending_multimodal"]
    for source in pending:
        path = directory / (source.source_id + ".json")
        report = {"file_id": source.source_id, "status": "missing_cache", "derived_observations": []}
        reports.append(report)
        if not path.exists():
            continue
        data = json_loads(path.read_text(encoding="utf-8"))
        if (type(data.get("schema_version")) is not int or data.get("schema_version") != 1 or data.get("file_id") != source.source_id
            or data.get("sha256") != source.provenance["sha256"]
            or data.get("file_path") != source.provenance["file_path"]
            or not isinstance(data.get("text"), str) or not isinstance(data.get("lines"), list)
            or data.get("captured_at") != source.captured_at.isoformat().replace("+00:00", "Z")
            or data.get("engine") != "Windows.Media.Ocr"):
            raise InputError("Stale or invalid OCR cache: " + source.source_id)
        for line in data["lines"]:
            if not isinstance(line, dict) or not isinstance(line.get("text"), str) or not isinstance(line.get("words"), list):
                raise InputError("Malformed OCR line")
            for word in line["words"]:
                if not isinstance(word, dict) or not isinstance(word.get("text"), str) or any(
                    type(word.get(k)) not in (int, float) or not 0 <= word[k] <= 100000 for k in ("x", "y", "width", "height")):
                    raise InputError("Malformed OCR word box")
        # Reconstruct raw text from lines so an inconsistent summary cannot add facts.
        text = "\n".join(line["text"] for line in data["lines"])
        header = "\n".join(line["text"] for line in data["lines"] if line["words"]
                           and min(w["y"] for w in line["words"]) < 320
                           and min(w["x"] for w in line["words"]) >= 230)
        compact = re.sub(r"\s+", "", text.casefold())
        tokens = identifiers({"text": header})
        emails = [v for k, v in tokens if k == "email"]
        users = [v for k, v in tokens if k == "user_id"]
        observed = []
        for system, resource in sorted(store.by_resource):
            if not contains_resource(text, resource):
                continue
            fields, category = None, None
            if "Customer Operations" in text and system == "account_service" and contains_resource(header, resource) and len(emails) == 1:
                fields, category = {"email": emails[0]}, "USER_PROFILE"
            elif "Pulse Analytics" in text and system == "analytics_platform" and contains_resource(header, resource) and len(emails) == 1:
                fields, category = {"email": emails[0]}, "ANALYTICS_PROFILE"
            elif "Audience Operations" in text and system == "marketing_platform" and contains_resource(header, resource) and len(emails) == 1:
                fields, category = {"email": emails[0]}, "MARKETING_PROFILE"
            elif "Helpline Console" in text and system == "support_platform" and contains_resource(header, resource) and len(emails) == 1:
                fields, category = {"requester_email": emails[0], "shared_context": True}, "SUPPORT_MESSAGE"
            elif "BridgeOps" in text and system == "integration_service" and "continuoussync" in compact:
                # Require the selector in the selected detail panel, not an unrelated table row.
                right = "\n".join(l["text"] for l in data["lines"] if l["words"] and min(w["x"] for w in l["words"]) > source.fields["width"] * .7)
                selectors = [v for k, v in identifiers(right) if k == "email"]
                if contains_resource(right, resource) and len(set(selectors)) == 1:
                    fields, category = {"customer_email": selectors[0], "enabled": True}, "DATA_FLOW"
            elif "Customer Download Center" in text and system == "export_service" and "readyfordownload" in compact:
                right = "\n".join(l["text"] for l in data["lines"] if l["words"] and min(w["x"] for w in l["words"]) > source.fields["width"] * .7)
                owners = [v for k, v in identifiers(right) if k == "email"]
                if contains_resource(right, resource) and len(set(owners)) == 1:
                    fields, category = {"owner_email": owners[0]}, "USER_EXPORT"
            elif "Raw document" in text and system == "search_service":
                # Only the explicitly selected raw document is a direct record readback.
                selected = re.search(r"Raw document[^\n]*" + re.escape(resource) + r"(?![\w])", text)
                right = "\n".join(l["text"] for l in data["lines"] if l["words"] and min(w["x"] for w in l["words"]) > source.fields["width"] * .7)
                references = [v for k, v in identifiers(right) if k == "user_id"]
                if selected and len(references) == 1:
                    fields, category = {"customer_reference": references[0]}, "SEARCH_INDEX_ENTRY"
            elif "Sentinel" in text and system == "security_service" and len(users) == 1:
                fields, category = {"subject_reference": users[0]}, "SECURITY_AUDIT_LOG"
            if fields is not None:
                item = replace(source, observation_id=source.observation_id + ":ocr:" + resource,
                               resource_id=resource, system_id=system, category=category,
                               collection="screen_readback", observed_at=source.captured_at, kind="direct",
                               fields=fields, identifiers=identifiers(fields),
                               scope={"engine": data["engine"], "ocr_confidence": None, "extraction": "narrow_screen_adapter"},
                               provenance={**source.provenance, "raw": text, "locator": "ocr:lines",
                                           "cache_file": str(path), "word_boxes": data["lines"]})
                observed.append(item)
            else:
                # A literal resource can be searched by the investigator even when
                # the screen exposes no safe structured state (e.g. restore permission).
                observed.append(replace(source, observation_id=source.observation_id + ":ocr_context:" + resource,
                    resource_id=resource, system_id=system, observed_at=source.captured_at, kind="context",
                    collection="ocr_text", fields={"text": text}, identifiers=(),
                    provenance={**source.provenance, "raw": text, "cache_file": str(path)}))
        # Always retain the OCR text as context, even when no safe structured rule fires.
        observed.append(replace(source, observation_id=source.observation_id + ":ocr_context", kind="context",
                                collection="ocr_text", observed_at=source.captured_at, fields={"text": text}, identifiers=(),
                                provenance={**source.provenance, "raw": text, "cache_file": str(path)}))
        store.add(observed)
        report.update(status="structured" if any(o.kind == "direct" for o in observed) else "text_only",
                      derived_observations=[o.observation_id for o in observed if o.kind == "direct"])
    return reports

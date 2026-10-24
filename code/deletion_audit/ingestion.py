"""Manifest-driven ingestion, resource indexing, inventory accounting, and integrity."""

import hashlib
import json
import re
import sqlite3
import struct
from collections import Counter
from pathlib import Path

from .inputs import InputError, load_evidence, read_csv, timestamp
from .observations import EvidenceStore, Observation, identifiers
from .parsers import Builder, parse_json, parse_log, parse_pdf, parse_sql, parse_text


ACTIVITY_FIELDS = ["activity_id", "event_time", "event_type", "source_system", "target_system",
                   "resource_id", "reported_result", "details"]


def dataset_hashes(dataset: Path) -> dict[str, str]:
    # Ground-truth bytes are hashed for integrity only, never decoded or used as answers.
    return {p.relative_to(dataset).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(dataset.rglob("*")) if p.is_file()}


def ingest(dataset: Path) -> EvidenceStore:
    load_evidence(dataset)  # Enforce existing authoritative ID/path/timestamp checks.
    manifest = read_csv(dataset / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"])
    store = EvidenceStore()
    paths = [r["file_path"] for r in manifest]
    if len(paths) != len(set(paths)):
        raise InputError("Duplicate manifest file path")
    physical = {p.relative_to(dataset).as_posix() for p in (dataset / "evidence").rglob("*") if p.is_file()}
    for path in sorted(physical - set(paths)):
        store.issues.append({"severity": "error", "code": "UNMANIFESTED_FILE", "file_path": path})
    for entry in manifest:
        path = dataset / entry["file_path"]
        payload = path.read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        builder = Builder(entry, digest)
        status = "parsed"
        try:
            if path.suffix == ".png":
                if payload[:8] != b"\x89PNG\r\n\x1a\n" or payload[12:16] != b"IHDR":
                    raise InputError("Invalid PNG header")
                width, height = struct.unpack(">II", payload[16:24])
                builder.result.units = 1
                builder.result.unit_kind = "images"
                builder.emit("image", {"width": width, "height": height}, kind="pending_multimodal",
                             scope={"reason": "Reliable structured multimodal extraction not implemented"})
                status = "pending_multimodal"
            elif path.suffix == ".pdf":
                parse_pdf(path, builder)
            else:
                text = payload.decode("utf-8-sig")
                store.source_text[entry["file_id"]] = text
                parser = {".json": parse_json, ".sql": parse_sql, ".log": parse_log, ".txt": parse_text}.get(path.suffix)
                if parser is None:
                    raise InputError(f"Unsupported evidence extension: {path.suffix}")
                parser(text, builder)
        except (InputError, ValueError, KeyError, TypeError, AttributeError, RecursionError,
                sqlite3.Error, UnicodeError, struct.error) as exc:
            status = "partial" if builder.result.observations else "error"
            store.issues.append({"severity": "error", "code": "PARSE_FAILURE", "file_id": entry["file_id"],
                                 "file_path": entry["file_path"], "message": str(exc)})
        parsed = builder.result
        store.add(parsed.observations)
        store.files.append({**entry, "format": path.suffix, "sha256": digest, "bytes": len(payload),
                            "status": status, "units": parsed.units, "unit_kind": parsed.unit_kind,
                            "normalized_observations": len(parsed.observations), "tables": parsed.tables,
                            "pdf_semantics": "text_pages_only" if path.suffix == ".pdf" else None})
    # Global workflow/operation outcomes remain claims, not direct readbacks.
    activity_digest = hashlib.sha256((dataset / "system_activity.csv").read_bytes()).hexdigest()
    for number, row in enumerate(read_csv(dataset / "system_activity.csv", ACTIVITY_FIELDS), 2):
        when = timestamp(row["event_time"])
        store.add([Observation(
            observation_id=row["activity_id"], source_id=row["activity_id"], file_id=None,
            system_id=row["target_system"], resource_id=row["resource_id"], collection="system_activity",
            category=None, observed_at=when, captured_at=when, kind="reported_claim", fields=row,
            scope={"source_system": row["source_system"], "target_system": row["target_system"]},
            provenance={"file_path": "system_activity.csv", "locator": f"csv_row:{number}",
                        "sha256": activity_digest, "raw": dict(row)}, identifiers=identifiers(row),
        )])
    return store


def compare_inventory(store: EvidenceStore, analysis_path: Path) -> dict:
    """Compare every manifest entry's raw unit count to the reconnaissance appendix."""
    expected = {}
    for line in analysis_path.read_text(encoding="utf-8").splitlines():
        if not re.match(r"\| evidence_[0-9]+ \|", line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        fid = cells[0]
        path = re.search(r"\[(.*?)\]", cells[1])[1]
        detail = cells[4]
        suffix = Path(path).suffix
        if suffix == ".sql":
            units = sum(int(n) for n in re.findall(r": ([0-9]+)", detail))
        elif suffix == ".json":
            units = int(re.search(r"([0-9]+) (?:records|service observations)", detail)[1])
        elif suffix == ".png":
            units = 1
        else:
            units = int(re.match(r"[0-9]+", detail)[0])
        expected[fid] = (path, units)
    if not expected:
        raise InputError("No evidence inventory found in dataset_analysis.md")
    actual = {r["file_id"]: r for r in store.files}
    mismatches = []
    for fid in sorted(expected.keys() | actual.keys()):
        if fid not in expected or fid not in actual:
            mismatches.append({"file_id": fid, "reason": "missing_or_extra_inventory_entry"})
        elif (actual[fid]["file_path"], actual[fid]["units"]) != expected[fid]:
            mismatches.append({"file_id": fid, "expected": expected[fid],
                               "actual": [actual[fid]["file_path"], actual[fid]["units"]]})
    return {"matches": not mismatches, "expected_files": len(expected),
            "compared_files": len(actual), "mismatches": mismatches}


def coverage_report(store: EvidenceStore, inventory: dict | None = None) -> dict:
    statuses = Counter(r["status"] for r in store.files)
    formats = {}
    for extension in sorted({r["format"] for r in store.files}):
        files = [r for r in store.files if r["format"] == extension]
        formats[extension] = {"files": len(files), "units": sum(r["units"] for r in files),
                              "unit_kind": files[0]["unit_kind"],
                              "statuses": dict(Counter(r["status"] for r in files))}
    errors = [i for i in store.issues if i["severity"] == "error"]
    pending = [r["file_id"] for r in store.files if r["status"] == "pending_multimodal"]
    return {
        "kind": "ingestion_coverage", "schema_version": 1,
        "supported_formats_successful": not errors,
        "complete_extraction": not errors and not pending,
        "file_count": len(store.files), "file_statuses": dict(statuses), "formats": formats,
        "observation_count": len(store.observations),
        "observation_kinds": dict(Counter(o.kind for o in store.observations)),
        "resource_keys": len(store.by_resource), "identifier_keys": len(store.by_identifier),
        "pending_multimodal": pending, "issues": store.issues, "inventory_comparison": inventory,
        "uncategorized_direct_observations": [o.observation_id for o in store.observations
                                               if o.kind == "direct" and o.category is None],
        "files": store.files,
        "limits": ["PDFs preserve page text and exact identifier tokens; business semantics are not adjudicated.",
                   "PNG files require multimodal extraction and cannot establish absence.",
                   "No deletion verdict, policy adjudication, or remediation planner is implemented."],
    }

"""Participant input loading shared by the pipeline and evaluator; no answer access."""

import csv
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REQUEST_FIELDS = [
    "case_id", "email", "requested_at", "reported_status", "reported_at",
    "audit_at", "request_text",
]
OUTPUT_FIELDS = ["case_id", "deletion_status", "steps_json"]
SPLITS = {"sample": "sample_deletion_requests.csv", "full": "deletion_requests.csv"}
CASE_ID = re.compile(r"case_[0-9]+\Z")


class InputError(ValueError):
    """An input file cannot be safely interpreted."""


def timestamp(value: str) -> datetime:
    """Require a timezone and seconds; normalize equivalent offsets to UTC."""
    if not isinstance(value, str) or not re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"
        r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:[0-9]{2})", value
    ):
        raise InputError(f"Invalid timezone-aware timestamp: {value!r}")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError as exc:
        raise InputError(f"Invalid timestamp: {value!r}") from exc


def read_csv(path: Path, fields: list[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream, strict=True)
            if reader.fieldnames != fields:
                raise InputError(f"{path.name}: expected header {fields}")
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise InputError(f"Cannot read {path}: {exc}") from exc
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise InputError(f"{path.name}: row width differs from header")
    return rows


@dataclass(frozen=True)
class Request:
    case_id: str
    audit_at: datetime
    email: str = ""


def load_requests(dataset: Path, split: str) -> dict[str, Request]:
    if split not in SPLITS:
        raise InputError(f"Unknown split: {split}")
    requests = {}
    for row in read_csv(dataset / SPLITS[split], REQUEST_FIELDS):
        cid = row["case_id"]
        if not CASE_ID.fullmatch(cid) or cid in requests:
            raise InputError(f"Invalid or duplicate request case_id: {cid!r}")
        if any(not value.strip() for value in row.values()):
            raise InputError(f"{cid}: empty request field")
        requested, reported, audit = (
            timestamp(row[k]) for k in ("requested_at", "reported_at", "audit_at")
        )
        if not requested <= reported <= audit:
            raise InputError(f"{cid}: requested_at <= reported_at <= audit_at required")
        if row["reported_status"] not in {"COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"}:
            raise InputError(f"{cid}: invalid reported_status")
        requests[cid] = Request(cid, audit, row["email"])
    if not requests:
        raise InputError("Request split is empty")
    return requests


@dataclass(frozen=True)
class Evidence:
    available_at: datetime
    source: str


def load_evidence(dataset: Path) -> dict[str, Evidence]:
    """Catalog IDs and availability only; does not interpret business evidence."""
    result = {}
    tables = [
        ("evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"],
         "file_id", "captured_at", "evidence"),
        ("system_activity.csv", ["activity_id", "event_time", "event_type", "source_system",
         "target_system", "resource_id", "reported_result", "details"],
         "activity_id", "event_time", "activity"),
        ("user_audit_log.csv", ["audit_id", "user_id", "event_time", "field_name",
         "old_value", "new_value"], "audit_id", "event_time", "audit"),
    ]
    for filename, fields, id_field, time_field, prefix in tables:
        for row in read_csv(dataset / filename, fields):
            eid = row[id_field]
            if not re.fullmatch(prefix + r"_[0-9]+", eid) or eid in result:
                raise InputError(f"{filename}: invalid or duplicate evidence ID {eid!r}")
            if id_field == "file_id":
                path = (dataset / row["file_path"]).resolve()
                if not path.is_relative_to((dataset / "evidence").resolve()) or not path.is_file():
                    raise InputError(f"{eid}: missing or out-of-scope evidence path")
            result[eid] = Evidence(timestamp(row[time_field]), filename)
    return result


def protect_output(path: Path, dataset: Path, *inputs: Path) -> None:
    resolved = path.resolve()
    if resolved.is_relative_to(dataset.resolve()) or any(resolved == p.resolve() for p in inputs):
        raise InputError("Output must be outside dataset/ and must not overwrite an input")

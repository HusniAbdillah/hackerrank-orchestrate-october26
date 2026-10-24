"""Adapters for observed participant evidence schemas, preserving original fields."""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .contract import _finite_float, _reject_constant, _unique_keys
from .inputs import InputError, timestamp
from .observations import Observation, RESOURCE, identifiers


# Only schema-specific categories: resource prefixes do not determine policy.
COLLECTIONS = {
    "customer_profiles": ("account_service", "USER_PROFILE"),
    "customer_profiles_primary": ("account_service", "USER_PROFILE"),
    "customer_profiles_failover_replica": ("account_service", "USER_PROFILE"),
    "customer_search_documents": ("search_service", "SEARCH_INDEX_ENTRY"),
    "search_documents_primary": ("search_service", "SEARCH_INDEX_ENTRY"),
    "customer_analytics_profiles": ("analytics_platform", "ANALYTICS_PROFILE"),
    "customer_analytics_reports": ("analytics_platform", "ANALYTICS_PROFILE"),
    "support_records": ("support_platform", "SUPPORT_MESSAGE"),
    "support_conversations": ("support_platform", "SUPPORT_MESSAGE"),
    "ticket_attachments": ("support_platform", "SUPPORT_ATTACHMENT"),
    "customer_exports": ("export_service", "USER_EXPORT"),
    "customer_export_jobs": ("export_service", "USER_EXPORT"),
    "connector_subscriptions": ("integration_service", "DATA_FLOW"),
    "connector_configurations": ("integration_service", "DATA_FLOW"),
    "backup_restore_entries": ("backup_service", "BACKUP_ARCHIVE"),
    "backup_catalog": ("backup_service", "BACKUP_ARCHIVE"),
    "security_audit_records": ("security_service", "SECURITY_AUDIT_LOG"),
    "security_audit_events": ("security_service", "SECURITY_AUDIT_LOG"),
    "retained_order_records": ("legal_service", "LEGAL_HOLD_RECORD"),
    "deleted_customer_references": ("identity_service", "ACCOUNT_TOMBSTONE"),
}
SERVICE_ARRAYS = {
    ("account_service", "profile_lookups"): "USER_PROFILE",
    ("analytics_platform", "profiles"): "ANALYTICS_PROFILE",
    ("backup_service", "restore_entries"): "BACKUP_ARCHIVE",
    ("export_service", "exports"): "USER_EXPORT",
    ("integration_service", "connectors"): "DATA_FLOW",
    ("search_service", "index_queries"): "SEARCH_INDEX_ENTRY",
    ("security_service", "audit_records"): "SECURITY_AUDIT_LOG",
    ("support_platform", "tickets"): "SUPPORT_MESSAGE",
}


def json_loads(text: str):
    return json.loads(text, object_pairs_hook=_unique_keys, parse_constant=_reject_constant,
                      parse_float=_finite_float)


@dataclass
class ParsedFile:
    observations: list[Observation] = field(default_factory=list)
    units: int = 0
    unit_kind: str = "records"
    tables: dict[str, int] = field(default_factory=dict)
    issues: list[dict] = field(default_factory=list)


class Builder:
    def __init__(self, manifest: dict[str, str], digest: str):
        self.manifest = manifest
        self.captured = timestamp(manifest["captured_at"])
        self.digest = digest
        self.result = ParsedFile()
        self.export_metadata = {}

    def emit(self, locator: str, fields: dict, *, system=None, resource=None,
             collection=None, category=None, observed=None, kind="direct", scope=None,
             raw=None, related=()):
        source = self.manifest["file_id"]
        self.result.observations.append(Observation(
            observation_id=f"{source}:{locator}", source_id=source, file_id=source,
            system_id=system, resource_id=resource, collection=collection, category=category,
            observed_at=timestamp(observed) if isinstance(observed, str) else observed,
            captured_at=self.captured, kind=kind, fields=fields,
            scope={**(scope or {}), **({"export_metadata": self.export_metadata} if self.export_metadata else {})},
            provenance={"file_path": self.manifest["file_path"], "locator": locator,
                        "sha256": self.digest, "raw": raw if raw is not None else json.dumps(fields, ensure_ascii=False)},
            identifiers=identifiers(fields), related_resources=tuple(related),
        ))

    def record(self, row, locator, system, collection, observed, scope=None, category=None):
        if not isinstance(row, dict):
            raise InputError(f"{locator}: record must be an object")
        target = row.get("system", row.get("origin_system", system))
        category = row.get("record_type", category or COLLECTIONS.get(collection, (None, None))[1])
        when = row.get("observed_at", row.get("recorded_at", observed))
        if when is None:
            raise InputError(f"{locator}: missing observation timestamp")
        kind = "direct"
        if row.get("result") == "NOT_FOUND" or row.get("status_code") == 404:
            kind = "scoped_negative"
        if isinstance(row.get("hits"), dict) and row["hits"].get("total") == 0:
            kind = "scoped_negative"
        resource = row.get("resource_id")
        if not isinstance(resource, str) or not resource:
            raise InputError(f"{locator}: record lacks resource_id")
        related = []
        if isinstance(row.get("source_resource_id"), str):
            # Observed search schema explicitly refers to an account source.
            related.append(("account_service", row["source_resource_id"]))
        self.emit(locator, row, system=target, resource=resource, collection=collection,
                  category=category, observed=when, scope=scope, kind=kind, related=related)


def parse_json(text: str, builder: Builder) -> ParsedFile:
    obj = json_loads(text)
    if not isinstance(obj, dict):
        raise InputError("Expected a JSON export object")
    b = builder
    b.export_metadata = {k: v for k, v in obj.items() if k not in {"snapshots", "service_exports", "records"}}
    if "snapshots" in obj:
        if not isinstance(obj["snapshots"], list):
            raise InputError("snapshots must be an array")
        for si, snap in enumerate(obj["snapshots"]):
            system, collection, when = snap["data_store"], snap["collection"], snap["captured_at"]
            if collection not in COLLECTIONS and collection != "operational_record_history":
                raise InputError(f"Unsupported snapshot collection: {collection}")
            rows = snap["records"]
            if not isinstance(rows, list):
                raise InputError("records must be an array")
            scope = {"data_store": system, "collection": collection, "snapshot_index": si,
                     "snapshot_metadata": {k: v for k, v in snap.items() if k != "records"}}
            if not rows:
                b.emit(f"/snapshots/{si}/records", {}, system=system, collection=collection,
                       observed=when, kind="scoped_negative", scope={**scope, "complete_collection": True})
            for ri, row in enumerate(rows):
                b.record(row, f"/snapshots/{si}/records/{ri}", system, collection, when, scope)
            b.result.units += len(rows)
    elif "service_exports" in obj:
        for system, exports in obj["service_exports"].items():
            for collection, rows in exports.items():
                if (system, collection) not in SERVICE_ARRAYS or not isinstance(rows, list):
                    raise InputError(f"Unsupported service export: {system}/{collection}")
                for ri, row in enumerate(rows):
                    if "observed_at" not in row:
                        raise InputError("Service observation lacks observed_at")
                    b.record(row, f"/service_exports/{system}/{collection}/{ri}", system,
                             collection, row["observed_at"], {"service": system, "array": collection},
                             SERVICE_ARRAYS[(system, collection)])
                if not rows:
                    # An empty export array is not necessarily an exhaustive service inventory.
                    b.emit(f"/service_exports/{system}/{collection}", {}, system=system,
                           collection=collection, observed=obj.get("exported_at"), kind="missing_data",
                           scope={"array": collection, "complete_collection": False})
                b.result.units += len(rows)
    elif "records" in obj:
        rows = obj["records"]
        if not isinstance(rows, list):
            raise InputError("records must be an array")
        if "record_count" in obj and obj["record_count"] != len(rows):
            raise InputError("Declared record_count differs from records array")
        collection = obj.get("collection", "record_register")
        if collection not in COLLECTIONS and collection != "record_register":
            raise InputError(f"Unsupported JSON collection: {collection}")
        system = COLLECTIONS.get(collection, (None, None))[0]
        for ri, row in enumerate(rows):
            if collection == "record_register" and not {"system", "record_type", "recorded_at"} <= row.keys():
                raise InputError("Unknown flat record schema")
            b.record(row, f"/records/{ri}", system, collection, obj.get("captured_at", obj.get("exported_at")))
        if not rows:
            b.emit("/records", {}, collection=collection, observed=obj.get("captured_at", obj.get("exported_at")),
                   kind="missing_data", scope={"complete_collection": False})
        b.result.units = len(rows)
    else:
        raise InputError("Unsupported JSON export shape")
    return b.result


def parse_sql(text: str, builder: Builder) -> ParsedFile:
    b = builder
    b.result.unit_kind = "sql_rows"
    with sqlite3.connect(":memory:") as db:
        # Restrict side effects to this disposable database even if an export is malformed.
        def authorize(action, arg1, arg2, database, trigger):
            if action in {sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH}:
                return sqlite3.SQLITE_DENY
            if action == sqlite3.SQLITE_PRAGMA and arg1 not in {"foreign_keys", "table_info"}:
                return sqlite3.SQLITE_DENY
            return sqlite3.SQLITE_OK
        db.set_authorizer(authorize)
        db.executescript(text)
        db.row_factory = sqlite3.Row
        tables = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        scope_rows = [dict(r) for r in db.execute("SELECT * FROM snapshot_scope")] if "snapshot_scope" in tables else []
        systems_in_scope = {r["origin_system"] for r in scope_rows}
        if len(systems_in_scope) != len(scope_rows):
            raise InputError("Duplicate SQL snapshot scope system")
        scope_times = {r["origin_system"]: timestamp(r["captured_at"]) for r in scope_rows}
        header = re.search(r"^-- Captured at: (\S+)", text, re.MULTILINE)
        snapshot_at = timestamp(header[1]) if header else b.captured
        for table in tables:
            quoted = '"' + table.replace('"', '""') + '"'
            rows = [dict(r) for r in db.execute(f"SELECT * FROM {quoted}")]
            b.result.tables[table] = len(rows)
            b.result.units += len(rows)
            columns = {r[1] for r in db.execute(f"PRAGMA table_info({quoted})")}
            generic = {"record_json", "origin_system", "collection_name", "resource_id"} <= columns
            if table != "snapshot_scope" and table not in COLLECTIONS and not generic:
                raise InputError(f"Unsupported SQL table: {table}")
            system, category = COLLECTIONS.get(table, (None, None))
            scope = {"table": table, "replica": table, "snapshot_scope": scope_rows,
                     "snapshot_at": snapshot_at.isoformat()}
            if not rows:
                covered = system in systems_in_scope if "snapshot_scope" in tables else True
                b.emit(f"table:{table}:empty", {}, system=system, collection=table,
                       category=category, observed=scope_times.get(system, snapshot_at),
                       kind="scoped_negative" if covered else "missing_data",
                       scope={**scope, "complete_collection": covered})
            for ri, row in enumerate(rows, 1):
                locator = f"table:{table}:row:{ri}"
                if table == "snapshot_scope":
                    b.emit(locator, row, system=row["origin_system"], collection=table,
                           observed=row["captured_at"], kind="metadata", scope=scope)
                else:
                    fields = dict(row)
                    if generic:
                        # Preserve both the original SQL cells and the decoded record.
                        fields["decoded_record"] = json_loads(row["record_json"])
                        if not isinstance(fields["decoded_record"], dict):
                            raise InputError("record_json must decode to an object")
                        if row["collection_name"] not in COLLECTIONS:
                            raise InputError(f"Unsupported SQL record collection: {row['collection_name']}")
                    b.record(fields, locator, row.get("origin_system", system),
                             row.get("collection_name", table),
                             scope_times.get(row.get("origin_system", system), snapshot_at), scope, category)
    return b.result


KV = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)=("(?:\\.|[^"\\])*"|[^\s]+)')
LOG_READS = {
    "profile_lookup_completed": "USER_PROFILE", "index_query_completed": "SEARCH_INDEX_ENTRY",
    "message_pii_scan": "SUPPORT_MESSAGE", "message_read": "SUPPORT_MESSAGE",
    "support_ticket_read_completed": "SUPPORT_MESSAGE", "attachment_pii_scan": "SUPPORT_ATTACHMENT",
    "analytics_identity_scan": "ANALYTICS_PROFILE", "analytics_profile_read": "ANALYTICS_PROFILE",
    "analytics_profile_read_completed": "ANALYTICS_PROFILE", "contact_lookup_completed": "SECONDARY_IDENTIFIER",
    "contact_query_completed": None, "connector_heartbeat": "DATA_FLOW", "connector_config_loaded": "DATA_FLOW",
    "connector_config_read_completed": "DATA_FLOW", "restore_candidate_evaluated": "BACKUP_ARCHIVE",
    "restore_authorization_completed": "BACKUP_ARCHIVE", "restore_policy_read_completed": "BACKUP_ARCHIVE",
    "audit_record_read_completed": "SECURITY_AUDIT_LOG", "retained_order_loaded": "LEGAL_HOLD_RECORD",
    "export_download_check_completed": "USER_EXPORT", "export_metadata_read_completed": "USER_EXPORT",
    "record_lookup": None, "deletion_marker_check": None,
}
LOG_AUX = {
    "export_started", "export_completed", "cache_lookup", "connection_acquired", "dependency_retry",
    "dependency_recovered", "delivery_abandoned", "pool_sample", "properties_reloaded",
    "connection_pool_pressure", "telemetry_flushed", "consumer_lag", "cache_refresh", "lease_extended",
    "lease_renewed", "flag_snapshot_loaded", "slow_call_rate", "timer_tick", "certificate_checked",
    "disk_latency", "batch_started", "checkpoint_saved", "thumbnail_failed",
}
LOG_STARTS = {
    "profile_lookup_started", "index_query_started", "message_scan_started", "attachment_scan_started",
    "analytics_profile_scan_started", "analytics_profile_read_started", "audit_record_query_started",
    "audit_record_read_started", "support_ticket_read_started", "connector_config_read_started",
    "restore_policy_check_started", "restore_policy_read_started", "retained_order_query_started",
    "export_download_check_started", "export_metadata_read_started", "contact_query_started",
}


def key_values(text: str) -> dict:
    result = {}
    for match in KV.finditer(text):
        value = match[2]
        if value.startswith('"'):
            value = json_loads(value)
        if match[1] in result:
            raise InputError(f"Duplicate log field: {match[1]}")
        result[match[1]] = value
    return result


def log_fields(line: str) -> tuple[str, dict]:
    stamp, rest = line.split(" ", 1)
    timestamp(stamp)
    rest = rest.strip()
    if rest.startswith("{"):
        fields = json_loads(rest)
    elif " | " in line:
        parts = line.split(" | ", 5)
        if len(parts) != 6:
            raise InputError("Malformed pipe log")
        fields = {**key_values(parts[5]), "service": parts[2], "trace_id": parts[3], "event": parts[4]}
    elif rest.startswith("["):
        match = re.fullmatch(r"\[([^]]+)\] \[([^]]+)\] \[([^]]+)\] ([a-z_]+): (.*)", rest)
        if not match:
            raise InputError("Malformed bracket log")
        fields = {**key_values(match[5]), "service": match[2], "trace_id": match[3], "event": match[4]}
    elif rest.startswith("<"):
        parts = rest.split(" ", 6)
        if len(parts) != 7:
            raise InputError("Malformed syslog wrapper")
        fields = {**key_values(parts[6]), "service": parts[2], "trace_id": parts[3]}
    else:
        fields = key_values(rest)
        if "function" in fields and "message" in fields:
            fields = {**fields, **key_values(fields["message"]), "service": fields["function"],
                      "trace_id": fields.get("requestId", "")}
    if not isinstance(fields, dict) or not {"event", "service"} <= fields.keys():
        raise InputError("Log lacks service/event")
    return stamp, fields


def parse_log(text: str, builder: Builder) -> ParsedFile:
    b = builder
    b.result.unit_kind = "lines"
    traces = {}
    for number, line in enumerate(text.splitlines(), 1):
        b.result.units += 1
        locator = f"line:{number}"
        if not line.strip():
            b.emit(locator, {}, observed=b.captured, kind="context", raw=line)
            continue
        stamp, fields = log_fields(line)
        event, service = fields["event"], fields["service"]
        if event not in LOG_READS and event not in LOG_AUX and event not in LOG_STARTS:
            raise InputError(f"{locator}: unsupported log event {event}")
        resource = fields.get("resource_id")
        # Preserve the reporting service separately from an explicit target system.
        system = fields.get("system", {"support_replica": "support_platform"}.get(service, service))
        kind = "direct" if event in LOG_READS else "context"
        if event in LOG_READS and (fields.get("rows") in {"0", 0} or fields.get("http_status") in {"404", 404}
                                  or fields.get("result") in {"NOT_FOUND", "miss"}):
            kind = "scoped_negative"
        if event == "thumbnail_failed":
            kind = "missing_data"
        key = (service, fields.get("trace_id"))
        scope = {"event": event, "reporting_service": service}
        enriched = dict(fields)
        if event in LOG_STARTS and key[1]:
            traces[key] = (stamp, fields, locator)
        elif key[1] and key in traces:
            start_stamp, context, start_locator = traces[key]
            if timestamp(start_stamp) <= timestamp(stamp):
                # Only an earlier lookup start in this file/service/trace can supply context.
                enriched["_correlated_lookup"] = context
                scope["correlated_start"] = start_locator
                scope["correlated_start_at"] = start_stamp
        b.emit(locator, enriched, system=system, resource=resource, collection=event,
               category=fields.get("record_type", LOG_READS.get(event)), observed=stamp,
               kind=kind, scope=scope, raw=line)
    return b.result


def parse_text(text: str, builder: Builder) -> ParsedFile:
    b = builder
    b.result.unit_kind = "lines"
    for number, line in enumerate(text.splitlines(), 1):
        b.result.units += 1
        if line.startswith("- "):
            parts = line[2:].split(" | ")
            if len(parts) != 6:
                raise InputError(f"line:{number}: malformed handover record")
            stamp, system, resource, category, result, subject = parts
            b.record({"recorded_at": stamp, "system": system, "resource_id": resource,
                      "record_type": category, "result": result, "subject_reference": subject},
                     f"line:{number}", system, "handover_records", stamp)
            # Retain exact prose formatting, not just the parsed cells.
            b.result.observations[-1].provenance["raw"] = line
        elif not line.strip() or line.startswith(("CUSTOMER PLATFORM", "Snapshot:", "Account and downstream")):
            b.emit(f"line:{number}", {"text": line}, observed=b.captured, kind="context", raw=line)
        else:
            raise InputError(f"line:{number}: unsupported handover text")
    return b.result


def parse_pdf(path: Path, builder: Builder) -> ParsedFile:
    try:
        from pypdf import PdfReader
        from pypdf.errors import PyPdfError
    except ImportError as exc:
        raise InputError("PDF ingestion requires pypdf; install requirements.txt") from exc

    b = builder
    b.result.unit_kind = "pages"
    try:
        reader = PdfReader(path)
    except PyPdfError as exc:
        raise InputError(f"PDF read failed: {exc}") from exc
    for number, page in enumerate(reader.pages, 1):
        text = page.extract_text(extraction_mode="plain") or ""
        b.result.units += 1
        if not text.strip():
            raise InputError(f"page:{number}: PDF text unavailable; OCR required")
        resources = sorted(set(RESOURCE.findall(text)))
        b.emit(f"page:{number}", {"text": text}, system=b.manifest["origin"],
               resource=resources[0] if len(resources) == 1 else None, collection="pdf_text",
               observed=b.captured, kind="context", scope={"page": number, "semantic_extraction": "text_only"}, raw=text)
    if not reader.pages:
        raise InputError("PDF has no pages")
    return b.result

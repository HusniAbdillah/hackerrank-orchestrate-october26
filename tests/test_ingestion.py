import json
import struct
from pathlib import Path

import pytest

from deletion_audit.ingestion import compare_inventory, coverage_report, dataset_hashes, ingest
from deletion_audit.inputs import InputError, read_csv, timestamp
from deletion_audit.observations import EvidenceStore, identifiers
from deletion_audit.parsers import Builder, parse_json, parse_log, parse_pdf, parse_sql, parse_text
from conftest import write_csv


CAPTURE = "2026-02-01T12:00:00Z"


def builder(extension="json"):
    return Builder({"file_id": "evidence_900", "file_path": f"evidence/test.{extension}",
                    "captured_at": CAPTURE, "origin": "fixture"}, "fixture-digest")


def record(**extra):
    return {"resource_id": "opaque_resource", "email": "exact@example.test", **extra}


@pytest.mark.parametrize("shape", ["snapshots", "service_exports", "register", "business_export"])
def test_every_json_export_family(shape):
    if shape == "snapshots":
        payload = {"source": "fixture", "snapshots": [{"captured_at": CAPTURE, "data_store": "account_service",
                    "collection": "customer_profiles", "records": [record()]}]}
    elif shape == "service_exports":
        payload = {"service_exports": {"account_service": {"profile_lookups": [record(observed_at=CAPTURE, status_code=200)]}}}
    elif shape == "register":
        payload = {"record_count": 1, "records": [record(recorded_at=CAPTURE, system="search_service",
                                                        record_type="SEARCH_INDEX_ENTRY", result="FOUND")]}
    else:
        payload = {"captured_at": CAPTURE, "collection": "customer_analytics_reports", "records": [record()]}
    result = parse_json(json.dumps(payload), builder())
    assert result.units == 1
    obs = result.observations[0]
    assert obs.file_id == "evidence_900"
    assert obs.resource_id == "opaque_resource"
    assert obs.observed_at == obs.captured_at == timestamp(CAPTURE)
    assert ("email", "exact@example.test") in obs.identifiers
    assert obs.provenance["sha256"] == "fixture-digest"
    assert obs.fields["email"] == "exact@example.test"


def test_nested_history_keeps_inner_system_category_and_observation_time():
    earlier = "2026-01-01T00:00:00Z"
    payload = {"snapshots": [{"captured_at": CAPTURE, "data_store": "history_storage",
               "collection": "operational_record_history", "records": [
                   record(recorded_at=earlier, system="account_service", record_type="USER_PROFILE", result="NOT_FOUND")]}]}
    obs = parse_json(json.dumps(payload), builder()).observations[0]
    assert obs.system_id == "account_service" and obs.category == "USER_PROFILE"
    assert obs.scope["data_store"] == "history_storage"
    assert obs.observed_at == timestamp(earlier) and obs.captured_at == timestamp(CAPTURE)
    assert obs.kind == "scoped_negative"


def test_empty_snapshot_is_scoped_but_missing_export_array_is_not_absence():
    payload = {"snapshots": [{"captured_at": CAPTURE, "data_store": "account_service",
               "collection": "customer_profiles", "records": []}]}
    result = parse_json(json.dumps(payload), builder())
    assert result.units == 0
    assert result.observations[0].kind == "scoped_negative"
    assert result.observations[0].resource_id is None
    assert result.observations[0].scope["complete_collection"]
    payload = {"exported_at": CAPTURE, "service_exports": {"account_service": {"profile_lookups": []}}}
    assert parse_json(json.dumps(payload), builder()).observations[0].kind == "missing_data"


@pytest.mark.parametrize("payload", [{"unknown": []}, {"snapshots": "bad"},
    {"service_exports": {"new_service": {"unknown": []}}},
    {"records": [], "record_count": 9},
    {"records": [record()]}, {"records": [1]}])
def test_unknown_or_malformed_json_not_silently_accepted(payload):
    with pytest.raises((InputError, TypeError, AttributeError)):
        parse_json(json.dumps(payload), builder())


def test_sql_replica_differences_preserve_scope_and_original_cells():
    text = """
    CREATE TABLE customer_data_primary(resource_id TEXT,origin_system TEXT,collection_name TEXT,record_json TEXT,updated_at TEXT);
    CREATE TABLE customer_data_replica(resource_id TEXT,origin_system TEXT,collection_name TEXT,record_json TEXT,updated_at TEXT);
    INSERT INTO customer_data_replica VALUES ('opaque_resource','account_service','customer_profiles',
      '{"email":"exact@example.test"}', '2025-01-01T00:00:00Z');
    """
    result = parse_sql(text, builder("sql"))
    assert result.units == 1
    assert result.tables == {"customer_data_primary": 0, "customer_data_replica": 1}
    absent, present = result.observations
    assert absent.kind == "scoped_negative" and absent.resource_id is None
    assert present.kind == "direct"
    assert present.scope["replica"] == "customer_data_replica"
    assert present.fields["record_json"] == '{"email":"exact@example.test"}'
    # A row's last write time is not the snapshot's observation time.
    assert present.observed_at == timestamp(CAPTURE)
    store = EvidenceStore()
    store.add(result.observations)
    assert store.for_resource("account_service", "opaque_resource", timestamp(CAPTURE)) == [present]


def test_sql_empty_tables_require_explicit_system_scope():
    text = f"""
    CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);
    INSERT INTO snapshot_scope VALUES('account_service','{CAPTURE}');
    CREATE TABLE customer_profiles(resource_id TEXT);
    CREATE TABLE customer_analytics_profiles(resource_id TEXT);
    """
    result = parse_sql(text, builder("sql"))
    by_collection = {o.collection: o for o in result.observations}
    assert by_collection["customer_profiles"].kind == "scoped_negative"
    assert by_collection["customer_analytics_profiles"].kind == "missing_data"
    assert result.units == 1  # Explicit scope metadata is accounted separately from empty tables.


def test_empty_scope_and_distinct_sql_snapshot_time_are_preserved():
    empty = parse_sql("CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);"
                      "CREATE TABLE customer_profiles(resource_id TEXT)", builder("sql"))
    assert next(o for o in empty.observations if o.collection == "customer_profiles").kind == "missing_data"
    result = parse_sql("-- Captured at: 2026-01-01T00:00:00Z\n"
                       "CREATE TABLE customer_profiles(resource_id TEXT,email TEXT);"
                       "INSERT INTO customer_profiles VALUES('profile','exact@example.test');", builder("sql"))
    assert result.observations[0].observed_at == timestamp("2026-01-01T00:00:00Z")
    assert result.observations[0].captured_at == timestamp(CAPTURE)


def test_explicit_sql_scope_timestamp_is_not_discarded():
    result = parse_sql("CREATE TABLE snapshot_scope(origin_system TEXT,captured_at TEXT);"
                       "INSERT INTO snapshot_scope VALUES('account_service','2026-02-03T00:00:00Z');"
                       "CREATE TABLE customer_profiles(resource_id TEXT,email TEXT);"
                       "INSERT INTO customer_profiles VALUES('profile','exact@example.test');", builder("sql"))
    obs = next(o for o in result.observations if o.resource_id == "profile")
    assert not obs.admissible(timestamp(CAPTURE))


def test_specialized_search_source_resource_link():
    text = """CREATE TABLE search_documents_primary(resource_id TEXT,display_name TEXT,email TEXT,source_resource_id TEXT,indexed_at TEXT);
    INSERT INTO search_documents_primary VALUES('opaque_search',NULL,NULL,'opaque_account','2026-01-01T00:00:00Z');"""
    obs = parse_sql(text, builder("sql")).observations[0]
    assert obs.related_resources == (("account_service", "opaque_account"),)
    assert obs.category == "SEARCH_INDEX_ENTRY"


def test_unknown_sql_table_and_external_attach_fail():
    with pytest.raises(InputError, match="Unsupported SQL table"):
        parse_sql("CREATE TABLE unexplained(payload TEXT)", builder("sql"))
    import sqlite3
    with pytest.raises(sqlite3.DatabaseError):
        parse_sql("ATTACH DATABASE ':memory:' AS side_effect", builder("sql"))


@pytest.mark.parametrize("wrapper", ["plain", "bracket", "pipe", "syslog", "json", "cloud"])
def test_every_log_wrapper_and_trace_correlation(wrapper):
    def wrap(event, attrs):
        kv = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        if wrapper == "plain":
            return f'{CAPTURE} level=INFO service=account_service trace_id=trace_a event={event} {kv}'
        if wrapper == "bracket":
            return f'{CAPTURE} [INFO] [account_service] [trace_a] {event}: {kv}'
        if wrapper == "pipe":
            return f'{CAPTURE} | INFO | account_service | trace_a | {event} | {kv}'
        if wrapper == "syslog":
            return f'{CAPTURE} <14>1 node account_service trace_a - - event="{event}" {kv}'
        if wrapper == "json":
            return CAPTURE + " " + json.dumps({"service": "account_service", "trace_id": "trace_a", "event": event, **attrs})
        return (f'{CAPTURE} requestId=trace_a function=account_service message=' +
                json.dumps(f'event="{event}" {kv}'))
    start = wrap("profile_lookup_started", {"lookup_key": "exact@example.test"})
    end = wrap("profile_lookup_completed", {"resource_id": "opaque_account", "rows": "0", "http_status": "404"})
    result = parse_log(start + "\n" + end, builder("log"))
    assert result.units == 2
    obs = result.observations[1]
    assert obs.kind == "scoped_negative" and obs.resource_id == "opaque_account"
    assert ("email", "exact@example.test") in obs.identifiers
    assert obs.scope["correlated_start"] == "line:1"
    assert obs.provenance["raw"] == end


def test_trace_context_is_never_shared_across_services_or_taken_from_future():
    text = f'''2026-02-01T12:00:01Z service=account_service trace_id=t event=profile_lookup_started lookup_key=wrong@example.test
{CAPTURE} service=account_service trace_id=t event=profile_lookup_completed resource_id=a rows=0
{CAPTURE} service=other_service trace_id=t event=profile_lookup_completed resource_id=b rows=0'''
    result = parse_log(text, builder("log"))
    assert all(not obs.identifiers for obs in result.observations[1:])


def test_log_unknown_event_is_visible_and_cache_miss_is_not_negative():
    with pytest.raises(InputError, match="unsupported log event"):
        parse_log(f"{CAPTURE} service=test event=unrecognized_result", builder("log"))
    obs = parse_log(f"{CAPTURE} service=test event=cache_lookup result=miss", builder("log")).observations[0]
    assert obs.kind == "context"


def test_handover_preserves_every_line_and_original_text():
    text = f"CUSTOMER PLATFORM - SHIFT HANDOVER\nSnapshot: {CAPTURE}\n\n- {CAPTURE} | account_service | opaque_account | USER_PROFILE | NOT_FOUND | exact@example.test\n"
    result = parse_text(text, builder("txt"))
    assert result.units == 4
    assert result.observations[-1].kind == "scoped_negative"
    assert result.observations[-1].provenance["raw"] == text.splitlines()[-1]
    with pytest.raises(InputError, match="unsupported handover"):
        parse_text("Unrecognized prose cannot count as a parsed handover", builder("txt"))


def test_png_gets_explicit_pending_record(foundation):
    dataset = foundation["dataset"]
    path = dataset / "evidence/test.png"
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1, 1))
    write_csv(dataset / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], [
        {"file_id": "evidence_1", "file_path": "evidence/test.png", "origin": "fixture", "captured_at": CAPTURE}])
    # Remove only fixture files omitted from this intentionally one-file manifest.
    for existing in (dataset / "evidence").glob("*.txt"):
        existing.unlink()
    store = ingest(dataset)
    obs = next(o for o in store.observations if o.file_id)
    assert obs.kind == "pending_multimodal" and obs.observed_at is None
    assert obs.fields == {"width": 1, "height": 1}
    report = coverage_report(store)
    assert report["supported_formats_successful"] and not report["complete_extraction"]
    assert report["pending_multimodal"] == ["evidence_1"]


def test_partial_parser_failure_and_unmanifested_file_are_reported(foundation):
    dataset = foundation["dataset"]
    manifest_path = dataset / "evidence_files.csv"
    fields = ["file_id", "file_path", "origin", "captured_at"]
    manifest = read_csv(manifest_path, fields)
    manifest[0]["file_path"] = "evidence/bad.log"
    (dataset / "evidence/bad.log").write_text(f"{CAPTURE} service=test event=cache_lookup result=miss\nbroken log\n")
    write_csv(manifest_path, fields, manifest)
    store = ingest(dataset)
    assert store.files[0]["status"] == "partial"
    assert not coverage_report(store)["supported_formats_successful"]
    assert {i["code"] for i in store.issues} >= {"PARSE_FAILURE", "UNMANIFESTED_FILE"}


def test_exact_token_boundaries_phone_normalization_and_no_integrity_hash():
    tokens = identifiers({"text": "Email Exact@Example.Test. Similar exact.jr@example.test; user_10.",
                          "phone": "+1 (212) 555-0101", "integrity_seal": "a" * 64})
    assert ("email", "exact@example.test") in tokens
    assert ("email", "exact.jr@example.test") in tokens
    assert ("user_id", "user_10") in tokens and ("user_id", "user_1") not in tokens
    assert ("phone", "+12125550101") in tokens
    assert not any(kind == "email_hash" for kind, _ in tokens)


def test_future_file_and_embedded_observation_excluded_independently():
    b = builder()
    b.record(record(observed_at="2026-02-02T00:00:00Z"), "/0", "account_service", "customer_profiles", CAPTURE)
    b.record(record(observed_at="2025-01-01T00:00:00Z"), "/1", "account_service", "customer_profiles", CAPTURE)
    store = EvidenceStore()
    store.add(b.result.observations)
    assert len(store.for_resource("account_service", "opaque_resource", timestamp(CAPTURE))) == 1
    assert not store.for_resource("account_service", "opaque_resource", timestamp("2026-01-31T00:00:00Z"))


def test_pdf_text_extraction_with_page_provenance_and_blank_pdf_failure(tmp_path):
    from pypdf import PdfWriter
    root = Path(__file__).resolve().parents[1]
    entry = next(r for r in read_csv(root / "dataset/evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"])
                 if r["file_path"].endswith(".pdf"))
    result = parse_pdf(root / "dataset" / entry["file_path"], Builder(entry, "test"))
    assert result.units > 0
    assert all(o.fields["text"].strip() and o.provenance["locator"].startswith("page:") for o in result.observations)
    path = tmp_path / "blank.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(path)
    with pytest.raises(InputError, match="OCR required"):
        parse_pdf(path, builder("pdf"))

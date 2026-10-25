import json
from dataclasses import replace

import pytest

from deletion_audit.extractions import apply_cached_screens, contains_resource
from deletion_audit.inputs import InputError
from deletion_audit.observations import EvidenceStore
from deletion_audit.policy import Policy
from deletion_audit.solver import audit, enrich, solve
from test_solver import ROOT, obs, graph, request


def screen(tmp_path, text="Customer Operations\naccount_opaque\nperson@example.test"):
    source = replace(obs(), kind="pending_multimodal", resource_id=None, category=None,
                     fields={"width": 1800, "height": 1200},
                     provenance={"file_path": "evidence/screen.png", "sha256": "fixture"})
    store = EvidenceStore(); store.add([source, obs(resource="account_opaque", kind="reported_claim")])
    data = {"schema_version": 1, "file_id": source.source_id, "sha256": "fixture", "file_path": "evidence/screen.png",
            "captured_at": source.captured_at.isoformat().replace("+00:00", "Z"), "engine": "Windows.Media.Ocr",
            "text": text, "lines": [{"text": line, "words": [{"text": line, "x": 250, "y": 100, "width": 200, "height": 20}]}
                                      for line in text.splitlines()]}
    path = tmp_path / (source.source_id + ".json"); path.write_text(json.dumps(data))
    return store, path, data


def test_exact_resource_matching_rejects_character_guesses():
    assert contains_resource("account _1234", "account_1234")
    assert not contains_resource("account_12345", "account_1234")
    assert not contains_resource("account_123B", "account_1238")


def test_missing_cache_keeps_explicit_pending_record(tmp_path):
    store, path, _ = screen(tmp_path); path.unlink()
    result = apply_cached_screens(store, tmp_path)
    assert result[0]["status"] == "missing_cache"
    assert any(o.kind == "pending_multimodal" for o in store.observations)


@pytest.mark.parametrize("field,value", [("sha256", "changed"), ("file_id", "invented"),
    ("schema_version", 2), ("engine", "unknown"), ("captured_at", "2030-01-01T00:00:00Z"), ("lines", [{}])])
def test_invalid_cache_never_supplies_facts(tmp_path, field, value):
    store, path, data = screen(tmp_path); data[field] = value; path.write_text(json.dumps(data))
    with pytest.raises(InputError): apply_cached_screens(store, tmp_path)
    assert not any(o.collection == "screen_readback" for o in store.observations)


def test_screen_adapter_uses_literal_identifier_and_preserves_provenance(tmp_path):
    store, _, _ = screen(tmp_path)
    result = apply_cached_screens(store, tmp_path)
    assert result[0]["status"] == "structured"
    direct = next(o for o in store.observations if o.collection == "screen_readback")
    assert direct.fields == {"email": "person@example.test"}
    assert direct.provenance["sha256"] == "fixture" and direct.provenance["word_boxes"]
    assert direct.source_id == "evidence_1"
    assert audit(request(), store, graph(), Policy.load(ROOT / "dataset"))[0] == "INCOMPLETE"


def test_unrecognized_screen_subject_cannot_borrow_catalog_identity(tmp_path):
    store, _, _ = screen(tmp_path, "Customer Operations\naccount_opaque\nlookalike@example.test")
    apply_cached_screens(store, tmp_path)
    status, steps, diagnostic = audit(request(), store, graph(), Policy.load(ROOT / "dataset"))
    assert diagnostic["abstained"] and steps == []
    assert any(i["code"] == "OCR_SUBJECT_LINK_UNCORROBORATED" for i in diagnostic["issues"])


def test_unsigned_screen_cannot_manufacture_absence(tmp_path):
    store, _, _ = screen(tmp_path, "Nothing found")
    result = apply_cached_screens(store, tmp_path)
    assert result[0]["status"] == "text_only"
    assert not any(o.kind == "scoped_negative" for o in store.observations)


def test_signed_journal_pdf_is_typed_only_with_explicit_retention():
    store = EvidenceStore()
    text = "COMPLIANCE JOURNAL - SIGNED RECORD EXTRACT\nEvent reference audit_record_x\nsubject user_fixture\nretain until 25 Aug 2027 04\n03 UTC"
    source = replace(obs(resource="audit_record_x", system="security_service"), kind="context", category=None,
                     collection="pdf_text", fields={"text": text})
    store.add([source]); enrich(store)
    evidence = next(o for o in store.observations if o.category == "SECURITY_AUDIT_LOG")
    assert evidence.fields["retention_until"] == "2027-08-25T04:03:00+00:00"
    assert evidence.identifiers == (("user_id", "user_fixture"),)


def test_uncertainty_stays_outside_submission_status(tmp_path):
    report = solve(ROOT / "dataset", "sample", tmp_path / "prediction.csv")
    unresolved = [c for c in report["cases"] if c["abstained"]]
    assert unresolved and all(c["submission_status"] is None and c["resolution"] == "UNRESOLVED" for c in unresolved)
    import csv
    rows = {r["case_id"]: r for r in csv.DictReader((tmp_path / "prediction.csv").open())}
    assert all(rows[c["case_id"]]["deletion_status"] == "" for c in unresolved)


def test_incomplete_full_run_never_overwrites_existing_submission(tmp_path):
    target = tmp_path / "output.csv"; target.write_text("previous accepted artifact")
    report = solve(ROOT / "dataset", "full", tmp_path / "preview.csv", submission_output=target)
    assert not report["submission"]["published"] and not report["submission"]["eligible"]
    assert target.read_text() == "previous accepted artifact" and report["prediction_count"] == 518


def test_sample_cannot_publish_submission(tmp_path):
    with pytest.raises(InputError):
        solve(ROOT / "dataset", "sample", tmp_path / "preview.csv", submission_output=tmp_path / "output.csv")


def test_cache_directory_cannot_be_used_as_output(tmp_path):
    with pytest.raises(InputError):
        solve(ROOT / "dataset", "sample", tmp_path / "prediction.csv", extractions=tmp_path)


def test_native_ocr_unavailable_is_reported_not_empty(foundation, tmp_path, monkeypatch):
    from deletion_audit.ocr_cache import extract
    from conftest import write_csv
    import subprocess
    dataset = foundation["dataset"]
    (dataset / "evidence" / "fixture.png").write_bytes(b"fictional image bytes")
    write_csv(dataset / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], [
        {"file_id": "evidence_1", "file_path": "evidence/fixture.png", "origin": "fixture", "captured_at": "2026-01-01T00:00:00Z"}])
    def missing(*args, **kwargs):
        raise FileNotFoundError("Windows OCR runtime unavailable")
    monkeypatch.setattr(subprocess, "run", missing)
    report = extract(dataset, tmp_path / "cache")
    assert report["files"][0]["status"] == "unavailable" and report["model_calls"] == 0
    assert not list((tmp_path / "cache").glob("*.json"))


def test_ocr_cli_routes_without_model_or_optional_runtime(tmp_path, monkeypatch):
    from deletion_audit.cli import main
    from deletion_audit import ocr_cache
    monkeypatch.setattr(ocr_cache, "extract", lambda dataset, output: {"files": [{"status": "cached"}]})
    assert main(["ocr", "--output", str(tmp_path / "cache")]) == 0

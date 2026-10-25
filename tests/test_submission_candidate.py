"""Candidate publication must not turn an epistemic gap into a fabricated verdict."""
import csv
from dataclasses import replace

import pytest

from deletion_audit import submission_candidate as candidate
from deletion_audit.inputs import InputError
from test_solver import request


def setup_run(monkeypatch, status):
    subject = replace(request("Please export my data." if status == "NOT_APPLICABLE" else "Delete my account."), case_id="case_901")
    def solve(dataset, split, output, extractions):
        assert split == "full"
        with output.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["case_id", "deletion_status", "steps_json"])
            writer.writeheader(); writer.writerow({"case_id": subject.case_id, "deletion_status": status, "steps_json": "[]"})
        return {"cases": [{"case_id": subject.case_id, "verdict_resolved": bool(status),
            "plan_scope_complete": bool(status), "submission_status": status or None,
            "issues": [] if status else [{"code": "NO_DIRECT_STATE"}]}],
            "dataset_integrity": {"unchanged": True}}
    monkeypatch.setattr(candidate, "solve", solve)
    monkeypatch.setattr(candidate, "load_requests", lambda *args: {subject.case_id: subject})
    monkeypatch.setattr(candidate, "load_evidence", lambda *args: {})


def test_unresolved_never_becomes_forced_status_and_existing_candidate_is_preserved(tmp_path, monkeypatch):
    setup_run(monkeypatch, "")
    target = tmp_path / "candidate.csv"; target.write_bytes(b"previous file")
    report = candidate.prepare(tmp_path / "dataset", tmp_path / "strict.csv", target)
    assert not report["candidate_generated"] and report["candidate_schema_valid"] is None
    assert report["strict_csv_json_well_formed"] and not report["strict_shape_validation"]["valid"]
    assert report["forced_format_judgment_count"] == 0 and report["unresolved_count"] == 1
    assert report["blocked_cases"][0]["deletion_authorized"] is True
    assert not report["blocked_cases"][0]["assumption_applied"]
    assert target.read_bytes() == b"previous file"


def test_proven_ready_rows_can_publish_independently_checked_copy(tmp_path, monkeypatch):
    setup_run(monkeypatch, "NOT_APPLICABLE")
    strict, target = tmp_path / "strict.csv", tmp_path / "candidate.csv"
    report = candidate.prepare(tmp_path / "dataset", strict, target)
    assert report["candidate_generated"] and report["candidate_schema_valid"]
    assert not report["blocked_cases"] and strict.read_bytes() == target.read_bytes()


def test_candidate_cannot_overwrite_strict_output(tmp_path):
    with pytest.raises(InputError):
        candidate.prepare(tmp_path / "dataset", tmp_path / "same.csv", tmp_path / "same.csv")


def test_observed_scope_is_explicitly_uncertain_and_empty_proof_stays_invalid(tmp_path, monkeypatch):
    setup_run(monkeypatch, "")
    target = tmp_path / "experimental.csv"
    report = candidate.prepare(tmp_path / "dataset", tmp_path / "strict.csv", target,
                               candidate_policy="observed-scope")
    assert target.exists() and report["candidate_generated"]
    assert report["candidate_csv_json_schema_valid"]
    assert not report["candidate_schema_valid"] and not report["candidate_evidence_validated"]
    assert report["forced_format_judgment_count"] == 1
    assert report["candidate_assumptions"][0]["false_complete_risk"]
    assert report["candidate_assumptions"][0]["known_verification_count"] == 0
    rows = list(csv.DictReader(target.open(encoding="utf-8")))
    assert rows[0]["deletion_status"] == "COMPLETE" and rows[0]["steps_json"] == "[]"
    assert report["candidate_contract_validation"]["issues"][0]["code"] == "STATUS_SHAPE"


def test_experimental_cannot_be_named_final_output(tmp_path):
    with pytest.raises(InputError, match="distinct filename"):
        candidate.prepare(tmp_path / "dataset", tmp_path / "strict.csv", tmp_path / "output.csv",
                          candidate_policy="observed-scope")


def test_explicit_format_only_publication_retains_strict_failures(tmp_path, monkeypatch):
    setup_run(monkeypatch, "")
    report=candidate.prepare(tmp_path/'dataset',tmp_path/'strict.csv',tmp_path/'experimental.csv',candidate_policy='observed-scope')
    result=candidate.publish_best_effort(report,tmp_path/'dataset',tmp_path/'output.csv')
    assert (tmp_path/'output.csv').exists() and result['format_valid']
    assert not result['strict_contract_valid'] and not result['evidence_validated']
    assert result['strict_failures'][0]['code']=='STATUS_SHAPE'


def test_tampered_candidate_cannot_replace_existing_output(tmp_path, monkeypatch):
    setup_run(monkeypatch, "")
    report=candidate.prepare(tmp_path/'dataset',tmp_path/'strict.csv',tmp_path/'experimental.csv',candidate_policy='observed-scope')
    (tmp_path/'experimental.csv').write_text('tampered',encoding='utf-8')
    target=tmp_path/'output.csv';target.write_bytes(b'previous best')
    with pytest.raises(InputError,match='hash mismatch'):
        candidate.publish_best_effort(report,tmp_path/'dataset',target)
    assert target.read_bytes()==b'previous best'

import json
from pathlib import Path
import subprocess
import sys

import pytest

from deletion_audit.cli import main
from deletion_audit.inputs import InputError, REQUEST_FIELDS, load_evidence, load_requests, timestamp
from deletion_audit.pipeline import run
from conftest import write_csv


def test_pipeline_has_no_reference_access_and_no_predictions(foundation, monkeypatch):
    original = Path.open

    def guard(path, *args, **kwargs):
        if path.name == "sample_output.csv":
            pytest.fail("Prediction pipeline accessed sample ground truth")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    sample = run(foundation["dataset"], "sample")
    full = run(foundation["dataset"], "full")
    assert sample["request_count"] == sample["unresolved_count"] == 3
    assert full["request_count"] == full["unresolved_count"] == 2
    assert sample["prediction_count"] == full["prediction_count"] == 0
    assert {r["case_id"] for r in sample["cases"]}.isdisjoint(r["case_id"] for r in full["cases"])


def test_cli_evaluation_exit_codes_and_report(foundation, tmp_path, capsys):
    base = ["evaluate", "--dataset", str(foundation["dataset"]), "--split", "sample",
            "--predictions", str(foundation["predictions"])]
    report = tmp_path / "report.json"
    assert main(base + ["--report", str(report)]) == 0
    assert json.loads(report.read_text())["metrics"]["exact_case_accuracy"] == 1
    foundation["predictions"].write_text("broken\n")
    assert main(base) == 1
    assert main(["evaluate", "--dataset", str(foundation["dataset"]), "--split", "full",
                 "--predictions", str(foundation["predictions"])]) == 2
    assert "only for --split sample" in capsys.readouterr().err


def test_cli_cannot_write_into_dataset_or_overwrite_predictions(foundation):
    original = foundation["reference"].read_bytes()
    assert main(["run", "--dataset", str(foundation["dataset"]), "--split", "sample",
                 "--report", str(foundation["reference"])]) == 2
    assert foundation["reference"].read_bytes() == original
    assert main(["validate", "--dataset", str(foundation["dataset"]), "--split", "sample",
                 "--predictions", str(foundation["predictions"]),
                 "--report", str(foundation["predictions"])]) == 2


def test_cli_validation_and_run_report(foundation, tmp_path):
    assert main(["validate", "--dataset", str(foundation["dataset"]), "--split", "sample",
                 "--predictions", str(foundation["predictions"])]) == 0
    output = tmp_path / "nested" / "readiness.json"
    assert main(["run", "--dataset", str(foundation["dataset"]), "--split", "full",
                 "--report", str(output)]) == 0
    assert json.loads(output.read_text())["request_count"] == 2


@pytest.mark.parametrize("bad", ["2026-02-01T12:00:00", "tomorrow", "2026-02-30T12:00:00Z"])
def test_timezone_aware_valid_timestamps_required(bad):
    with pytest.raises(InputError):
        timestamp(bad)


def test_timezone_offsets_normalized():
    assert timestamp("2026-02-01T19:00:00+07:00") == timestamp("2026-02-01T12:00:00Z")


def test_input_duplicates_and_time_inversions(foundation):
    path = foundation["dataset"] / "sample_deletion_requests.csv"
    from deletion_audit.inputs import read_csv
    rows = read_csv(path, REQUEST_FIELDS)
    write_csv(path, REQUEST_FIELDS, rows + [rows[0]])
    with pytest.raises(InputError, match="duplicate"):
        load_requests(foundation["dataset"], "sample")
    rows[0]["reported_at"] = "2025-01-01T00:00:00Z"
    write_csv(path, REQUEST_FIELDS, rows)
    with pytest.raises(InputError, match="requested_at"):
        load_requests(foundation["dataset"], "sample")


def test_manifest_missing_file_is_an_input_error(foundation):
    (foundation["dataset"] / "evidence" / "1.txt").unlink()
    with pytest.raises(InputError, match="missing or out-of-scope"):
        load_evidence(foundation["dataset"])


def test_real_sample_self_test_and_both_entry_points(tmp_path):
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "self_test.json"
    result = subprocess.run([sys.executable, str(root / "code/main.py"), "self-test",
                             "--report", str(output)], cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["passed"]
    alternate = subprocess.run([sys.executable, str(root / "code/evaluation/main.py"), "validate",
                                "--split", "sample", "--predictions", str(root / "dataset/sample_output.csv")],
                               cwd=tmp_path, capture_output=True, text=True)
    assert alternate.returncode == 0, alternate.stderr

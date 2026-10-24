"""Controlled evaluator tests. Public reference access is evaluation-only."""

import csv
import json
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from .contract import STEP_FIELDS
from .evaluator import evaluate
from .inputs import OUTPUT_FIELDS, load_evidence, load_requests, read_csv


def _write(path, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_self_test(dataset: Path) -> dict:
    requests, evidence = load_requests(dataset, "sample"), load_evidence(dataset)
    reference = dataset / "sample_output.csv"
    raw = read_csv(reference, OUTPUT_FIELDS)
    results = {}
    with TemporaryDirectory(prefix="deletion-evaluator-") as temporary:
        path = Path(temporary) / "controlled_predictions.csv"

        def measure(name, rows):
            _write(path, rows)
            report = evaluate(path, reference, requests, evidence)
            results[name] = {"metrics": report["metrics"], "counts": report["counts"],
                             "contract_valid": report["validation"]["valid"],
                             "issue_codes": sorted({i["code"] for i in report["validation"]["issues"]})}
            return report

        # Object-key order and whitespace must have no impact.
        equivalent = deepcopy(raw)
        for row in equivalent:
            steps = json.loads(row["steps_json"])
            row["steps_json"] = json.dumps([
                {k: step[k] for k in reversed(STEP_FIELDS)} for step in steps
            ], indent=2)
        perfect = measure("reference_with_reordered_object_keys", equivalent)
        assert perfect["validation"]["valid"] and all(v == 1.0 for v in perfect["metrics"].values())

        # Choose by structure, never by a hardcoded case ID or expected label.
        reordered = deepcopy(equivalent)
        candidate = next(row for row in reordered if len(json.loads(row["steps_json"])) > 1)
        steps = list(reversed(json.loads(candidate["steps_json"])))
        for number, step in enumerate(steps, start=1):
            step["step_no"] = number
        candidate["steps_json"] = json.dumps(steps)
        order = measure("reversed_step_array", reordered)
        n = len(raw)
        assert not order["validation"]["valid"] and order["metrics"]["step_f1"] == 1.0
        assert order["metrics"]["sequence_accuracy"] == (n - 1) / n
        assert "STEP_ORDER" in results["reversed_step_array"]["issue_codes"]

        missing = measure("missing_case", equivalent[:-1])
        assert not missing["validation"]["valid"]
        assert missing["metrics"]["case_status_accuracy"] == (n - 1) / n

        duplicate = measure("duplicate_case", sorted(equivalent + [equivalent[0]], key=lambda r: r["case_id"]))
        assert not duplicate["validation"]["valid"]
        assert duplicate["metrics"]["exact_case_accuracy"] == (n - 1) / n

        bad_citation = deepcopy(equivalent)
        selected = next(row for row in bad_citation if any(s["evidence_id"] for s in json.loads(row["steps_json"])))
        steps = json.loads(selected["steps_json"])
        next(s for s in steps if s["evidence_id"])["evidence_id"] = "evidence_does_not_exist"
        selected["steps_json"] = json.dumps(steps)
        citation = measure("unknown_evidence_id", bad_citation)
        assert not citation["validation"]["valid"] and citation["metrics"]["step_f1"] < 1.0
    return {"kind": "controlled_evaluator_self_test", "passed": True,
            "warning": "Reference-derived test inputs exercise the evaluator only; these are not solver predictions or solver accuracy.",
            "scenarios": results}

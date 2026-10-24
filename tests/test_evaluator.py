import json
from copy import deepcopy
from dataclasses import replace

import pytest

from deletion_audit.contract import STEP_FIELDS, validate
from deletion_audit.evaluator import evaluate
from deletion_audit.inputs import OUTPUT_FIELDS, InputError, timestamp
from conftest import step, write_csv


def measure(foundation, rows=None):
    if rows is not None:
        write_csv(foundation["predictions"], OUTPUT_FIELDS, rows)
    return evaluate(foundation["predictions"], foundation["reference"],
                    foundation["requests"], foundation["evidence"])


def codes(report):
    return {issue["code"] for issue in report["validation"]["issues"]}


def change_step(foundation, field, value, row_index=0, step_index=0):
    rows = deepcopy(foundation["rows"])
    steps = json.loads(rows[row_index]["steps_json"])
    steps[step_index][field] = value
    rows[row_index]["steps_json"] = json.dumps(steps)
    return rows


def test_perfect_and_reordered_object_keys(foundation):
    rows = foundation["rows"]
    for row in rows:
        row["steps_json"] = json.dumps([
            {k: s[k] for k in reversed(STEP_FIELDS)} for s in json.loads(row["steps_json"])
        ], indent=3)
    report = measure(foundation, rows)
    assert report["validation"]["valid"]
    assert set(report["metrics"].values()) == {1.0}
    assert report["counts"]["true_positive_steps"] == 8


def test_array_order_matters_but_multiset_f1_does_not(foundation):
    rows = foundation["rows"]
    steps = list(reversed(json.loads(rows[0]["steps_json"])))
    for index, s in enumerate(steps, 1):
        s["step_no"] = index
    rows[0]["steps_json"] = json.dumps(steps)
    report = measure(foundation, rows)
    assert "STEP_ORDER" in codes(report)
    assert report["metrics"]["step_f1"] == 1
    assert report["metrics"]["sequence_accuracy"] == pytest.approx(2 / 3)
    assert report["metrics"]["exact_case_accuracy"] == pytest.approx(2 / 3)
    assert report["fields"]["step_no"]["accuracy"] == pytest.approx(6 / 8)


def test_missing_cases_remain_in_denominators(foundation):
    rows = [foundation["rows"][0], foundation["rows"][2]]
    report = measure(foundation, rows)
    assert "MISSING_CASE" in codes(report)
    assert report["metrics"]["case_status_accuracy"] == pytest.approx(2 / 3)
    assert report["metrics"]["step_precision"] == 1
    assert report["metrics"]["step_recall"] == pytest.approx(2 / 8)
    assert report["metrics"]["step_f1"] == pytest.approx(0.4)
    assert report["metrics"]["field_accuracy"] == pytest.approx(2 / 8)


def test_duplicate_cases_quarantined_and_penalized(foundation):
    rows = sorted(foundation["rows"] + [foundation["rows"][0]], key=lambda r: r["case_id"])
    report = measure(foundation, rows)
    assert "DUPLICATE_CASE" in codes(report)
    assert report["counts"]["true_positive_steps"] == 6
    assert report["counts"]["predicted_steps"] == 10
    assert report["metrics"]["case_status_accuracy"] == pytest.approx(2 / 3)
    assert report["metrics"]["field_accuracy"] == pytest.approx(0.5)


@pytest.mark.parametrize("payload", ["{", "{}", "null", '[{"a":1,"a":2}]', "[NaN]", "[Infinity]", "[1e999]"])
def test_malformed_or_nonstandard_json_is_not_silently_empty(foundation, payload):
    rows = foundation["rows"]
    rows[0]["steps_json"] = payload
    report = measure(foundation, rows)
    assert "JSON" in codes(report)
    assert report["counts"]["predicted_steps"] == 7  # six real + one opaque malformed row
    assert report["counts"]["true_positive_steps"] == 6
    assert report["metrics"]["case_status_accuracy"] == 1
    assert report["metrics"]["exact_case_accuracy"] == pytest.approx(2 / 3)


@pytest.mark.parametrize("field,value,error", [
    ("phase", "FINDING", "OPERATION_STATE"),
    ("phase", "SOMETHING", "OPERATION_STATE"),
    ("operation", "RETAIN_RECORD", "OPERATION_STATE"),
    ("state", "PRESENT", "OPERATION_STATE"),
    ("step_no", 0, "STEP_NUMBER"),
    ("step_no", True, "STEP_NUMBER"),
    ("step_no", 1.0, "STEP_NUMBER"),
    ("system_id", " ", "RESOURCE_ID"),
    ("resource_id", None, "STEP_TYPES"),
    ("evidence_id", "evidence_99999", "EVIDENCE_ID"),
    ("evidence_id", "evidence_3", "FUTURE_EVIDENCE"),
    ("evidence_id", "", "CITATION_REQUIRED"),
    ("evidence_id", {"bad": "type"}, "STEP_TYPES"),
])
def test_contract_violations(foundation, field, value, error):
    assert error in codes(measure(foundation, change_step(foundation, field, value)))


@pytest.mark.parametrize("eid", ["evidence_1", "activity_1", "audit_1"])
def test_all_evidence_id_namespaces_and_inclusive_cutoff(foundation, eid):
    report = measure(foundation, change_step(foundation, "evidence_id", eid))
    assert report["validation"]["valid"]


@pytest.mark.parametrize("eid", ["evidence_1", "activity_1", "audit_1"])
def test_future_evidence_in_all_namespaces(foundation, eid):
    foundation["evidence"][eid] = replace(foundation["evidence"][eid], available_at=timestamp("2026-02-01T12:00:01Z"))
    write_csv(foundation["predictions"], OUTPUT_FIELDS, change_step(foundation, "evidence_id", eid))
    result = validate(foundation["predictions"], foundation["requests"], foundation["evidence"])
    assert "FUTURE_EVIDENCE" in {issue.code for issue in result.issues}


def test_existing_but_wrong_evidence_is_scored_not_claimed_semantically_invalid(foundation):
    report = measure(foundation, change_step(foundation, "evidence_id", "evidence_2"))
    assert report["validation"]["valid"]
    assert report["metrics"]["step_precision"] == pytest.approx(7 / 8)
    assert report["metrics"]["step_recall"] == pytest.approx(7 / 8)
    assert report["metrics"]["step_f1"] == pytest.approx(7 / 8)
    assert report["metrics"]["field_accuracy"] == pytest.approx(55 / 56)
    assert report["fields"]["evidence_id"]["correct"] == 7


@pytest.mark.parametrize("step_index", [2, 4])
def test_incomplete_future_steps_cannot_cite_evidence(foundation, step_index):
    report = measure(foundation, change_step(foundation, "evidence_id", "evidence_1", 1, step_index))
    assert "CITATION_FORBIDDEN" in codes(report)


@pytest.mark.parametrize("payload", ["[1]", '[{"step_no":1}]'])
def test_non_object_and_inexact_step_fields(foundation, payload):
    rows = foundation["rows"]
    rows[0]["steps_json"] = payload
    assert "STEP_FIELDS" in codes(measure(foundation, rows))


def test_extra_key_and_duplicate_steps(foundation):
    assert "STEP_FIELDS" in codes(measure(foundation, change_step(foundation, "extra", "bad")))
    rows = foundation["rows"]
    steps = json.loads(rows[0]["steps_json"])
    steps.insert(1, deepcopy(steps[0]))
    for index, s in enumerate(steps, 1):
        s["step_no"] = index
    rows[0]["steps_json"] = json.dumps(steps)
    report = measure(foundation, rows)
    assert "DUPLICATE_STEP" in codes(report)
    assert report["counts"]["predicted_steps"] == 9
    assert report["counts"]["true_positive_steps"] == 8


@pytest.mark.parametrize("status", ["UNKNOWN", "", "complete"])
def test_status_enum(foundation, status):
    rows = foundation["rows"]
    rows[0]["deletion_status"] = status
    assert "STATUS" in codes(measure(foundation, rows))


def test_empty_complete_and_nonempty_not_applicable(foundation):
    rows = foundation["rows"]
    rows[0]["steps_json"] = "[]"
    assert "STATUS_SHAPE" in codes(measure(foundation, rows))
    rows[0]["steps_json"] = foundation["rows"][1]["steps_json"]
    rows[0]["deletion_status"] = "NOT_APPLICABLE"
    assert "STATUS_SHAPE" in codes(measure(foundation, rows))


@pytest.mark.parametrize("remove", [0, 2, 4])
def test_incomplete_plan_coverage(foundation, remove):
    rows = foundation["rows"]
    steps = json.loads(rows[1]["steps_json"])
    del steps[remove]
    for index, s in enumerate(steps, 1):
        s["step_no"] = index
    rows[1]["steps_json"] = json.dumps(steps)
    assert "PLAN_COVERAGE" in codes(measure(foundation, rows))


def test_row_order_is_file_error_not_case_sequence_error(foundation):
    report = measure(foundation, list(reversed(foundation["rows"])))
    assert "CASE_ORDER" in codes(report)
    assert report["metrics"]["case_status_accuracy"] == 1
    assert report["metrics"]["sequence_accuracy"] == 1
    assert report["metrics"]["exact_case_accuracy"] == 0


def test_unexpected_cases_cannot_inflate_step_scores(foundation):
    rows = deepcopy(foundation["rows"])
    extra = deepcopy(rows[0])
    extra["case_id"] = "case_999"
    rows.append(extra)
    report = measure(foundation, rows)
    assert "CASE_ID" in codes(report)
    assert report["metrics"]["step_precision"] == pytest.approx(8 / 10)
    assert report["metrics"]["step_recall"] == 1
    assert report["metrics"]["field_accuracy"] == pytest.approx(8 / 10)


@pytest.mark.parametrize("header", ["case_id,steps_json,deletion_status\n", "case_id,deletion_status,steps_json,extra\n"])
def test_exact_csv_header_required(foundation, header):
    foundation["predictions"].write_text(header, encoding="utf-8")
    assert "CSV_SCHEMA" in codes(measure(foundation))


def test_bad_csv_width_and_empty_prediction_file(foundation):
    foundation["predictions"].write_text("case_id,deletion_status,steps_json\ncase_001,COMPLETE\n", encoding="utf-8")
    assert "CSV_SCHEMA" in codes(measure(foundation))
    write_csv(foundation["predictions"], OUTPUT_FIELDS, [])
    report = measure(foundation)
    assert "MISSING_CASE" in codes(report)
    assert all(report["metrics"][m] == 0 for m in ("case_status_accuracy", "step_precision", "step_recall", "step_f1"))


def test_corrupt_reference_is_rejected_not_scored(foundation):
    foundation["reference"].write_text("broken\n", encoding="utf-8")
    with pytest.raises(InputError, match="Reference violates"):
        measure(foundation)


def test_empty_step_metrics_are_defined_for_not_applicable(foundation):
    rows = [foundation["rows"][2]]
    write_csv(foundation["reference"], OUTPUT_FIELDS, rows)
    foundation["requests"] = {"case_003": foundation["requests"]["case_003"]}
    assert set(measure(foundation, rows)["metrics"].values()) == {1.0}


def test_system_then_resource_tie_break_order(foundation):
    rows = foundation["rows"]
    steps = [step(1, "VERIFICATION", "z_system", "a", "VERIFY_RECORD_ABSENT", "ABSENT", "evidence_1"),
             step(2, "VERIFICATION", "a_system", "z", "VERIFY_RECORD_ABSENT", "ABSENT", "evidence_1")]
    rows[0]["steps_json"] = json.dumps(steps)
    assert "STEP_ORDER" in codes(measure(foundation, rows))
    steps[0]["system_id"] = "a_system"
    steps[0]["resource_id"] = "z"
    steps[1]["resource_id"] = "a"
    rows[0]["steps_json"] = json.dumps(steps)
    assert "STEP_ORDER" in codes(measure(foundation, rows))

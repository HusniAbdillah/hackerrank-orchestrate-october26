"""Reference access and diagnostic scoring live exclusively in this module."""

from collections import Counter, defaultdict, deque
from pathlib import Path

from .contract import STEP_FIELDS, Prediction, Validation, canonical, validate
from .inputs import Evidence, InputError, Request


MATCHING_DEFINITIONS = {
    "case_universe": "All case_ids in the selected requests. Missing and duplicate cases earn no case credit. Unexpected/duplicate rows contribute extra predicted steps and unmatched field slots.",
    "status_accuracy": "Unique predicted row with the correct deletion_status / expected cases; independent of step validity.",
    "exact_case_accuracy": "Unique row with correct status and identical ordered seven-field step objects, no case issues, and no file-level schema/order issues / expected cases.",
    "step_precision_recall_f1": "Micro multiset matching within case_id on every step field except step_no. Order ignored, evidence_id included, extra keys included. Duplicate case rows are quarantined (no true positives). A malformed/unparseable steps_json contributes one opaque false-positive step.",
    "field_accuracy": "Align by (case_id, phase, system_id, resource_id), pairing repeated anchors in occurrence order. Compare all seven fields with strict types. Missing, extra, malformed, duplicate-case, and unexpected-case steps each add an unmatched seven-field slot. Overall is correct fields / (all slots * 7); status has its own metric.",
    "sequence_accuracy": "Unique row with the identical ordered step array including step_no, excluding deletion_status / expected cases. JSON key order and whitespace ignored; independent of contract validity.",
    "empty_convention": "Precision/recall/F1 and field accuracy are 1 for genuinely empty expected and predicted steps. No predictions against nonempty reference yields precision=recall=F1=0.",
    "chronology_scope": "file_id uses manifest captured_at; activity_id/audit_id use event_time, inclusively <= audit_at. Artifact contents, identity relevance, embedded observation times, and evidentiary entailment are not inferred by this foundation.",
}


def _items(row: Prediction) -> list:
    # Malformed JSON is not an empty answer and must not disappear from precision.
    return row.steps if row.steps is not None else [None]


def _token(step) -> str:
    if isinstance(step, dict):
        return canonical({key: value for key, value in step.items() if key != "step_no"})
    return "opaque:" + canonical(step)


def _anchor(step):
    fields = ("phase", "system_id", "resource_id")
    if isinstance(step, dict) and all(isinstance(step.get(k), str) for k in fields):
        return tuple(step[k] for k in fields)
    return None


def score(predictions: Validation, reference: Validation) -> dict:
    if not reference.valid:
        raise InputError("Reference violates the contract: " + "; ".join(
            f"{i.case_id or 'file'}:{i.code}" for i in reference.issues
        ))
    truth = {row.case_id: row for row in reference.rows}
    if not truth:
        raise InputError("Reference is empty")
    grouped = defaultdict(list)
    for row in predictions.rows:
        grouped[row.case_id].append(row)
    bad_cases = {i.case_id for i in predictions.issues}
    file_bad = None in bad_cases
    status_correct = exact_correct = sequence_correct = tp = 0
    predicted_steps = sum(len(_items(row)) for row in predictions.rows)
    reference_steps = sum(len(row.steps) for row in truth.values())
    field_correct = Counter({key: 0 for key in STEP_FIELDS})
    field_slots = 0
    cases = []

    for cid in sorted(truth.keys() | grouped.keys()):
        expected = truth.get(cid)
        rows = grouped.get(cid, [])
        unique = rows[0] if len(rows) == 1 and expected is not None else None
        expected_steps = expected.steps if expected else []
        if unique is not None:
            status_ok = unique.status == expected.status
            sequence_ok = unique.steps is not None and canonical(unique.steps) == canonical(expected_steps)
            exact_ok = status_ok and sequence_ok and cid not in bad_cases and not file_bad
            status_correct += status_ok
            sequence_correct += sequence_ok
            exact_correct += exact_ok
            predicted = _items(unique)
            tp += sum((Counter(map(_token, predicted)) & Counter(map(_token, expected_steps))).values())
            available = defaultdict(deque)
            for index, step in enumerate(predicted):
                anchor = _anchor(step)
                if anchor is not None:
                    available[anchor].append((index, step))
            consumed = set()
            for step in expected_steps:
                field_slots += 1
                candidates = available[_anchor(step)]
                if not candidates:
                    continue
                index, actual = candidates.popleft()
                consumed.add(index)
                for field in STEP_FIELDS:
                    if field in actual and type(actual[field]) is type(step[field]) and actual[field] == step[field]:
                        field_correct[field] += 1
            field_slots += len(predicted) - len(consumed)
        else:
            status_ok = sequence_ok = exact_ok = False
            field_slots += len(expected_steps) + sum(len(_items(row)) for row in rows)
        if expected is not None:
            cases.append({"case_id": cid, "status_correct": bool(status_ok),
                          "exact_case": bool(exact_ok), "sequence_correct": bool(sequence_ok)})

    precision = tp / predicted_steps if predicted_steps else float(reference_steps == 0)
    recall = tp / reference_steps if reference_steps else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    total_cases = len(truth)
    metrics = {
        "case_status_accuracy": status_correct / total_cases,
        "exact_case_accuracy": exact_correct / total_cases,
        "step_precision": precision, "step_recall": recall, "step_f1": f1,
        "field_accuracy": sum(field_correct.values()) / (field_slots * len(STEP_FIELDS)) if field_slots else 1.0,
        "sequence_accuracy": sequence_correct / total_cases,
    }
    return {
        "kind": "reference_evaluation", "metrics": metrics,
        "counts": {"expected_cases": total_cases, "prediction_rows": len(predictions.rows),
                   "correct_status_cases": status_correct, "exact_cases": exact_correct,
                   "correct_sequences": sequence_correct, "true_positive_steps": tp,
                   "predicted_steps": predicted_steps, "reference_steps": reference_steps,
                   "false_positive_steps": predicted_steps - tp, "false_negative_steps": reference_steps - tp,
                   "field_slots": field_slots},
        "fields": {field: {"correct": field_correct[field], "total": field_slots,
                           "accuracy": field_correct[field] / field_slots if field_slots else 1.0}
                   for field in STEP_FIELDS},
        "validation": predictions.report(), "cases": cases,
        "matching_definitions": MATCHING_DEFINITIONS,
    }


def evaluate(predictions: Path, reference: Path, requests: dict[str, Request],
             evidence: dict[str, Evidence]) -> dict:
    truth = validate(reference, requests, evidence)
    actual = validate(predictions, requests, evidence)
    return score(actual, truth)

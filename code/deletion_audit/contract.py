"""Strict output grammar, evidence availability, and canonical ordering checks."""

import json
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .inputs import CASE_ID, OUTPUT_FIELDS, Evidence, InputError, Request, read_csv


STEP_FIELDS = ["step_no", "phase", "system_id", "resource_id", "operation", "state", "evidence_id"]
# Insertion order is the operation order in problem_statement.md.
OPERATIONS = {
    "REPORT_REMAINING_RECORD": ("FINDING", "PRESENT"),
    "REPORT_EXPOSED_PII": ("FINDING", "PRESENT"),
    "REPORT_ACTIVE_DATA_FLOW": ("FINDING", "ACTIVE"),
    "REPORT_RESTORE_RISK": ("FINDING", "ACTIVE"),
    "DISABLE_DATA_FLOW": ("REMEDIATION", "DISABLED"),
    "BLOCK_RESTORE": ("REMEDIATION", "BLOCKED"),
    "DELETE_RECORD": ("REMEDIATION", "ABSENT"),
    "REDACT_RECORD": ("REMEDIATION", "REDACTED"),
    "ANONYMIZE_RECORD": ("REMEDIATION", "ANONYMIZED"),
    "VERIFY_RECORD_ABSENT": ("VERIFICATION", "ABSENT"),
    "VERIFY_RECORD_PRESENT": ("VERIFICATION", "PRESENT"),
    "VERIFY_RECORD_REDACTED": ("VERIFICATION", "REDACTED"),
    "VERIFY_RECORD_ANONYMIZED": ("VERIFICATION", "ANONYMIZED"),
    "VERIFY_DATA_FLOW_DISABLED": ("VERIFICATION", "DISABLED"),
    "VERIFY_RESTORE_BLOCKED": ("VERIFICATION", "BLOCKED"),
}
PHASES = ["FINDING", "REMEDIATION", "VERIFICATION"]
RANK = {op: i for i, op in enumerate(OPERATIONS)}
TREATMENTS = {
    "REPORT_REMAINING_RECORD": [("DELETE_RECORD", "VERIFY_RECORD_ABSENT")],
    "REPORT_EXPOSED_PII": [("REDACT_RECORD", "VERIFY_RECORD_REDACTED"),
                           ("ANONYMIZE_RECORD", "VERIFY_RECORD_ANONYMIZED")],
    "REPORT_ACTIVE_DATA_FLOW": [("DISABLE_DATA_FLOW", "VERIFY_DATA_FLOW_DISABLED")],
    "REPORT_RESTORE_RISK": [("BLOCK_RESTORE", "VERIFY_RESTORE_BLOCKED")],
}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _unique_keys(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"Duplicate JSON object key: {key}")
        obj[key] = value
    return obj


def _reject_constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


def _finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("JSON number exceeds finite range")
    return number


@dataclass(frozen=True)
class Issue:
    code: str
    message: str
    case_id: str | None = None
    row_no: int | None = None
    step_no: int | None = None


@dataclass
class Prediction:
    case_id: str
    status: str
    steps: list | None
    row_no: int


@dataclass
class Validation:
    rows: list[Prediction]
    issues: list[Issue]

    @property
    def valid(self) -> bool:
        return not self.issues

    def report(self) -> dict:
        return {"valid": self.valid, "row_count": len(self.rows),
                "issues": [asdict(issue) for issue in self.issues]}


def order_key(step: dict) -> tuple:
    return (PHASES.index(step["phase"]), RANK[step["operation"]],
            step["system_id"], step["resource_id"])


def validate(path: Path, requests: dict[str, Request], evidence: dict[str, Evidence]) -> Validation:
    result = Validation([], [])
    try:
        raw_rows = read_csv(path, OUTPUT_FIELDS)
    except InputError as exc:
        result.issues.append(Issue("CSV_SCHEMA", str(exc)))
        return result

    for row_no, raw in enumerate(raw_rows, start=2):
        cid = raw["case_id"]
        try:
            steps = json.loads(raw["steps_json"], object_pairs_hook=_unique_keys,
                               parse_constant=_reject_constant, parse_float=_finite_float)
            if not isinstance(steps, list):
                raise ValueError("steps_json must be an array")
        except (ValueError, RecursionError) as exc:
            steps = None
            result.issues.append(Issue("JSON", str(exc), cid, row_no))
        result.rows.append(Prediction(cid, raw["deletion_status"], steps, row_no))

    counts = Counter(row.case_id for row in result.rows)
    for cid in sorted(requests.keys() - counts.keys()):
        result.issues.append(Issue("MISSING_CASE", "Expected case is missing", cid))
    if [row.case_id for row in result.rows] != sorted(row.case_id for row in result.rows):
        result.issues.append(Issue("CASE_ORDER", "Rows must be sorted lexicographically by case_id"))
    for row in result.rows:
        cid = row.case_id

        def issue(code, message, step_no=None):
            result.issues.append(Issue(code, message, cid, row.row_no, step_no))

        if not CASE_ID.fullmatch(cid) or cid not in requests:
            issue("CASE_ID", "case_id must be an exact member of the selected request split")
        if counts[cid] > 1:
            issue("DUPLICATE_CASE", "Every case must appear exactly once")
        if row.status not in {"COMPLETE", "INCOMPLETE", "NOT_APPLICABLE"}:
            issue("STATUS", "Illegal deletion_status")
        if row.steps is None:
            continue
        if row.status == "NOT_APPLICABLE" and row.steps:
            issue("STATUS_SHAPE", "NOT_APPLICABLE requires []")
        if row.status == "COMPLETE" and not row.steps:
            issue("STATUS_SHAPE", "COMPLETE requires evidence-backed verification")

        sortable = True
        signatures = set()
        well_formed = []
        for index, step in enumerate(row.steps, start=1):
            if not isinstance(step, dict) or set(step) != set(STEP_FIELDS):
                issue("STEP_FIELDS", "Each step must contain exactly the seven contract fields", index)
                sortable = False
                continue
            if type(step["step_no"]) is not int or step["step_no"] != index:
                issue("STEP_NUMBER", "step_no must be consecutive integers starting at 1", index)
            if any(not isinstance(step[k], str) for k in STEP_FIELDS if k != "step_no"):
                issue("STEP_TYPES", "All fields except step_no must be strings", index)
                sortable = False
                continue
            if any(not step[k].strip() or step[k] != step[k].strip()
                   for k in ("system_id", "resource_id")):
                issue("RESOURCE_ID", "system_id and resource_id must be nonempty, unpadded strings", index)
            op, phase, state = step["operation"], step["phase"], step["state"]
            if op not in OPERATIONS or OPERATIONS[op] != (phase, state):
                issue("OPERATION_STATE", "Illegal phase/operation/state combination", index)
                sortable = False
            else:
                well_formed.append(step)
            signature = (phase, step["system_id"], step["resource_id"], op)
            if signature in signatures:
                issue("DUPLICATE_STEP", "Duplicate operation on the same resource and phase", index)
            signatures.add(signature)
            if row.status == "COMPLETE" and phase != "VERIFICATION":
                issue("STATUS_SHAPE", "COMPLETE permits verification steps only", index)
            needs_citation = phase == "FINDING" or (row.status == "COMPLETE" and phase == "VERIFICATION")
            eid = step["evidence_id"]
            if needs_citation and not eid:
                issue("CITATION_REQUIRED", "This step requires participant-visible evidence", index)
            if not needs_citation and eid:
                issue("CITATION_FORBIDDEN", "Proposed remediation/future verification requires empty evidence_id", index)
            if eid:
                if eid not in evidence:
                    issue("EVIDENCE_ID", "Unknown participant-visible evidence ID", index)
                elif cid in requests and evidence[eid].available_at > requests[cid].audit_at:
                    issue("FUTURE_EVIDENCE", "Evidence availability is after audit_at", index)
        if sortable and row.steps != sorted(row.steps, key=order_key):
            issue("STEP_ORDER", "Expected phase, specified operation rank, system_id, resource_id order")
        if row.status == "INCOMPLETE":
            present = {step["phase"] for step in well_formed}
            if present != set(PHASES):
                issue("STATUS_SHAPE", "INCOMPLETE requires findings, remediation, and verification")
            # Structural plan coverage only; category/content/dependency inference belongs to the solver.
            justified = set()
            for step in well_formed:
                if step["operation"] not in TREATMENTS:
                    continue
                system, resource = step["system_id"], step["resource_id"]
                actions = {s["operation"] for s in well_formed
                           if (s["system_id"], s["resource_id"]) == (system, resource)}
                for treatment, verification in TREATMENTS[step["operation"]]:
                    justified.add((system, resource, treatment))
                if not any(t in actions and v in actions for t, v in TREATMENTS[step["operation"]]):
                    issue("PLAN_COVERAGE", "Finding lacks corresponding remediation and final-state check")
            for step in well_formed:
                if step["phase"] == "REMEDIATION" and (
                    step["system_id"], step["resource_id"], step["operation"]
                ) not in justified:
                    issue("PLAN_COVERAGE", "Remediation has no corresponding finding")
    return result

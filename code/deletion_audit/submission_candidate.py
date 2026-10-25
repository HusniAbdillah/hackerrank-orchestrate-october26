"""Explicit candidate preflight; never weakens the strict solver or fills unknowns."""
import hashlib
import csv
import json
from pathlib import Path
import tempfile


def publish_best_effort(report, dataset: Path, destination: Path):
    """Explicit format-only publication, never a strict certification.

    Only the evidence-required/nonempty COMPLETE check may remain unsatisfied,
    and only for rows already disclosed as assumption-based in this fresh run.
    All other schema, ordering, operation and citation checks must still pass.
    """
    source = Path(report["candidate_output"])
    if destination.suffix.lower() != ".csv":
        raise InputError("Best-effort publication must be a CSV")
    protect_output(destination, dataset, source, Path(report["strict_output"]))
    if not report["candidate_generated"] or hashlib.sha256(source.read_bytes()).hexdigest() != report["candidate_sha256"]:
        raise InputError("Candidate missing or hash mismatch")
    checked = validate(source, load_requests(dataset, "full"), load_evidence(dataset)).report()
    assumed = {r["case_id"] for r in report.get("candidate_assumptions", []) if not r["evidence_established"]}
    allowed = lambda i: (i["code"] == "STATUS_SHAPE" and i["case_id"] in assumed and
                         i["message"] == "COMPLETE requires evidence-backed verification")
    if any(not allowed(i) for i in checked["issues"]):
        raise InputError("Best-effort publication failed independent format/citation checks")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as stream:
        temporary = Path(stream.name); stream.write(source.read_bytes())
    try:
        destination.unlink(missing_ok=True)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    report["publication"] = {"path": str(destination), "role": "EXPERIMENTAL_BEST_EFFORT",
        "format_valid": True, "strict_contract_valid": checked["valid"], "evidence_validated": False,
        "strict_failures": checked["issues"], "assumption_case_ids": sorted(assumed),
        "sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
    return report["publication"]

from .authorization import authorize
from .contract import validate
from .inputs import InputError, load_evidence, load_requests, protect_output
from .solver import solve


def prepare(dataset: Path, strict_output: Path, candidate_output: Path,
            extractions: Path | None = None, *, candidate_policy: str = "strict", ai=None) -> dict:
    if candidate_policy not in {"strict", "observed-scope"}:
        raise InputError("Unsupported candidate policy")
    if candidate_policy != "strict" and candidate_output.name == "output.csv":
        raise InputError("Experimental candidate must have a distinct filename, not output.csv")
    for output, other in ((strict_output, candidate_output), (candidate_output, strict_output)):
        protect_output(output, dataset, other)
        if extractions and output.resolve().is_relative_to(extractions.resolve()):
            raise InputError("Candidate outputs must not overwrite extraction caches")
    # Always recompute: never certify an unrelated/stale CSV using a trusted-looking report.
    run = (solve(dataset, "full", strict_output, extractions, ai=ai) if ai is not None else
           solve(dataset, "full", strict_output, extractions))
    requests = load_requests(dataset, "full")
    validation = validate(strict_output, requests, load_evidence(dataset)).report()
    reference_codes = {"EVIDENCE_ID", "FUTURE_EVIDENCE"}
    shape_issues = [i for i in validation["issues"] if i["code"] not in reference_codes]
    rows = {c["case_id"]: c for c in run["cases"]}
    blockers = []
    for cid, case in sorted(rows.items()):
        if case["verdict_resolved"] and case["plan_scope_complete"]:
            continue
        authorization = authorize(requests[cid].request_text).authorized
        unresolved = not case["verdict_resolved"]
        blockers.append({"case_id": cid, "audit_at": requests[cid].audit_at.isoformat(),
            "deletion_authorized": authorization, "strict_status": case["submission_status"],
            "kind": "UNRESOLVED_VERDICT" if unresolved else "CONDITIONAL_PLAN_GAP",
            "issues": case["issues"], "assumption_applied": False,
            "rejected_forced_format_options": ({
                "COMPLETE": "Would assume missing/conflicting required final-state proof is compliant; not established by sources.",
                "INCOMPLETE": "Would require a demonstrated violation and grounded finding/remediation/verification, not merely failure to prove COMPLETE.",
                "NOT_APPLICABLE": "Not an uncertainty status; forbidden for an authorized deletion request."
            } if unresolved else {"plan_complete": "Would assume an unproved resource-specific policy condition or invent a treatment."})})
    coverage = set(rows) == set(requests) and len(rows) == len(run["cases"])
    eligible = validation["valid"] and coverage and not blockers and run["dataset_integrity"]["unchanged"]
    report = {"kind": "submission_candidate_preflight", "strict_run": run,
        "strict_output": str(strict_output), "candidate_output": str(candidate_output),
        "candidate_generated": False, "candidate_schema_valid": None,
        "existing_candidate_preserved": candidate_output.exists(),
        "expected_row_count": len(requests), "strict_diagnostic_coverage_valid": coverage,
        "strict_csv_json_well_formed": not any(i["code"] in {"CSV_SCHEMA", "JSON"} for i in validation["issues"]),
        "strict_shape_validation": {"valid": not shape_issues, "issues": shape_issues},
        "strict_contract_validation": validation,
        "grounding_assessment": {"source": "Deterministic sufficiency checks, not hidden-label correctness",
            "grounded_verdict_count": sum(c["verdict_resolved"] for c in rows.values()),
            "complete_proof_plan_count": sum(c["verdict_resolved"] and c["plan_scope_complete"] for c in rows.values()),
            "eligible": eligible},
        "unresolved_count": sum(not c["verdict_resolved"] for c in rows.values()),
        "decided_plan_gap_count": sum(c["verdict_resolved"] and not c["plan_scope_complete"] for c in rows.values()),
        "forced_format_judgment_count": 0, "low_confidence_candidate_row_count": 0,
        "blocked_cases": blockers,
        "status": "READY" if eligible else "BLOCKED_WITHOUT_UNSUPPORTED_CLAIMS",
        "limitation": None if eligible else "Three-status serialization has no UNKNOWN. Changing a verdict cannot supply missing proof, findings, ownership or an allowed remediation operation."}
    report["candidate_policy"] = candidate_policy
    if not eligible and candidate_policy == "observed-scope":
        # Explicit experimental judgment, NEVER an evidence-strict decision.
        # Missing obligations are assumed compliant; no new resource, record
        # state, operation or citation is created. An empty partial proof stays
        # empty and fails the independent contract check visibly.
        if any(b["kind"] == "UNRESOLVED_VERDICT" and b["deletion_authorized"] is not True for b in blockers):
            report["limitation"] = "Observed-scope policy cannot override uncertain or absent deletion consent."
            return report
        with strict_output.open(encoding="utf-8", newline="") as stream:
            candidate_rows = list(csv.DictReader(stream))
        assumptions = []
        for row in candidate_rows:
            case = rows[row["case_id"]]
            if case["verdict_resolved"]:
                continue
            partial = case.get("grounded_partial_steps", [])
            if any(s["phase"] != "VERIFICATION" or not s["evidence_id"] for s in partial):
                raise InputError("Observed-scope candidate requires grounded partial verification only")
            row["deletion_status"] = "COMPLETE"
            row["steps_json"] = json.dumps(partial, separators=(",", ":"))
            assumptions.append({"case_id": row["case_id"], "candidate_status": "COMPLETE",
                "evidence_established": False, "strict_status": None,
                "assumption": "Observed-scope completion only: unresolved obligations are assumed compliant. This does not prove global COMPLETE.",
                "known_verification_count": len(partial), "issues": case["issues"],
                "false_complete_risk": True})
        candidate_output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=candidate_output.parent, delete=False, mode="w", encoding="utf-8", newline="") as stream:
            temporary = Path(stream.name)
            writer = csv.DictWriter(stream, fieldnames=["case_id", "deletion_status", "steps_json"])
            writer.writeheader(); writer.writerows(candidate_rows)
        try:
            checked = validate(temporary, requests, load_evidence(dataset)).report()
            temporary.replace(candidate_output)
        finally:
            temporary.unlink(missing_ok=True)
        bad = {i["case_id"] for i in checked["issues"]}
        report.update(candidate_generated=True, candidate_schema_valid=checked["valid"],
            candidate_csv_json_schema_valid=True, candidate_contract_validation=checked,
            candidate_contract_valid_rows=0 if None in bad else len(candidate_rows) - len(bad),
            candidate_evidence_validated=False, candidate_assumptions=assumptions,
            forced_format_judgment_count=len(assumptions), low_confidence_candidate_row_count=len(assumptions),
            candidate_sha256=hashlib.sha256(candidate_output.read_bytes()).hexdigest(),
            existing_candidate_preserved=False, status="EXPERIMENTAL_OBSERVED_SCOPE_NOT_EVIDENCE_VALIDATED",
            limitation="Candidate uses explicitly uncertain COMPLETE judgments. Empty partial proofs remain contract-invalid; this workflow never certifies or publishes a strict output.csv.")
        return report
    if eligible:
        candidate_output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=candidate_output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(strict_output.read_bytes())
        try:
            candidate_validation = validate(temporary, requests, load_evidence(dataset)).report()
            if not candidate_validation["valid"]:
                raise InputError("Candidate failed independent validation")
            temporary.replace(candidate_output)
        finally:
            temporary.unlink(missing_ok=True)
        report.update(candidate_generated=True, candidate_schema_valid=True,
                      candidate_sha256=hashlib.sha256(candidate_output.read_bytes()).hexdigest(),
                      existing_candidate_preserved=False)
    return report

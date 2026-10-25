"""Evaluation-only explanation: reference steps never flow back into prediction logic."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.evaluator import evaluate
from deletion_audit.identity import IdentityGraph
from deletion_audit.ingestion import ingest
from deletion_audit.inputs import load_evidence, load_requests, protect_output
from deletion_audit.solver import enrich
from deletion_audit.contract import validate, STEP_FIELDS


def field_breakdown(predictions, reference, requests, evidence):
    """Evaluation-only anchored field/position errors, separate from root causes."""
    actual = {r.case_id: r for r in validate(predictions, requests, evidence).rows}
    expected = {r.case_id: r for r in validate(reference, requests, evidence).rows}
    result = {}
    for cid, truth in expected.items():
        row = actual.get(cid)
        given = row.steps or [] if row else []
        anchor = lambda s: (s.get("phase"), s.get("system_id"), s.get("resource_id"))
        by_anchor = {}
        for step in given:
            if isinstance(step, dict): by_anchor.setdefault(anchor(step), []).append(step)
        mismatches = []
        for step in truth.steps:
            matches = by_anchor.get(anchor(step), [])
            if matches:
                paired = matches.pop(0)
                for key in STEP_FIELDS:
                    if paired.get(key) != step[key]:
                        mismatches.append({"anchor": list(anchor(step)), "field": key,
                                           "expected": step[key], "actual": paired.get(key)})
        result[cid] = mismatches
    return result


def diagnose(dataset, predictions, run, extractions=None):
    requests = load_requests(dataset, "sample")
    measured = evaluate(predictions, dataset / "sample_output.csv", requests, load_evidence(dataset))
    fields = field_breakdown(predictions, dataset / "sample_output.csv", requests, load_evidence(dataset))
    store = ingest(dataset); enrich(store)
    if extractions:
        from deletion_audit.extractions import apply_cached_screens
        apply_cached_screens(store, extractions)
    graph = IdentityGraph.load(dataset)
    diagnostics = {c["case_id"]: c for c in run["cases"]}
    aggregate = Counter()
    for case in measured["cases"]:
        request = requests[case["case_id"]]
        user = graph.resolve("email", request.email, request.audit_at)
        ownership = graph.ownership(store, request.audit_at)
        reasons = []
        for step in case["missing_steps"]:
            key = step["system_id"], step["resource_id"]
            observations = store.by_resource.get(key, [])
            if user.intersection(ownership.get(key, {})):
                reason = ("verification_withheld_on_incomplete_proof" if diagnostics[case["case_id"]]["abstained"]
                          else "linked_resource_state_or_planning_gap")
            else:
                matched = [o for o in observations if any(user.intersection(graph.resolve(k, v, request.audit_at))
                            for k, v in o.identifiers)]
                if matched and not any(o.admissible(request.audit_at) for o in matched):
                    reason = "subject_link_available_only_after_cutoff"
                elif step["operation"] == "VERIFY_RECORD_ANONYMIZED":
                    reason = "anonymized_record_without_historical_resource_link"
                elif step["operation"] == "VERIFY_RECORD_PRESENT":
                    reason = "retained_record_without_admissible_subject_link"
                else:
                    reason = "no_grounded_subject_link_in_parsed_evidence"
            reasons.append({"step": step, "root_cause": reason,
                            "available_source_ids": sorted({o.source_id for o in observations if o.admissible(request.audit_at)}),
                            "excluded_source_ids": sorted({o.source_id for o in observations if not o.admissible(request.audit_at)})})
            aggregate[reason] += 1
        for step in case["extra_steps"]:
            aggregate["additional_grounded_resource_outside_reference_scope"] += 1
        if diagnostics[case["case_id"]]["abstained"]:
            aggregate["insufficient_evidence_abstention"] += 1
        case["missing_step_causes"] = reasons
        case["solver_issues"] = diagnostics[case["case_id"]]["issues"]
        case["anchored_field_mismatches"] = fields[case["case_id"]]
    measured["root_cause_counts"] = dict(aggregate.most_common())
    measured["exact_failure_case_contributions"] = dict(Counter(
        cause for case in measured["cases"] if not case["exact_case"]
        for cause in ({r["root_cause"] for r in case["missing_step_causes"]} |
                      ({"additional_grounded_resource_outside_reference_scope"} if case["extra_steps"] else set()) |
                      ({"status_mismatch"} if not case["status_correct"] else set()))))
    measured["anchored_field_error_counts"] = dict(Counter(
        error["field"] for case in measured["cases"] for error in case["anchored_field_mismatches"]))
    measured["root_cause_caveat"] = "Reference discrepancies are diagnostic, not proof the solver should bypass cutoff or invent links. Only supplied validated extraction caches are applied."
    return measured


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[2] / "dataset")
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--solver-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extractions", type=Path)
    args = parser.parse_args()
    protect_output(args.output, args.dataset, args.predictions, args.solver_report)
    result = diagnose(args.dataset, args.predictions, json.loads(args.solver_report.read_text(encoding="utf-8")), args.extractions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"metrics": result["metrics"], "root_cause_counts": result["root_cause_counts"]}, indent=2))


if __name__ == "__main__":
    main()

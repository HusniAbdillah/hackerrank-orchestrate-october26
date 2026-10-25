"""Render real application traces in Markdown visible to the code judge/interviewer."""
import argparse
import json
from pathlib import Path


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(runs):
    lines = ["# Actual runtime AI audit investigations", "",
        "Generated from recorded application runs, not a scripted demonstration. No hidden chain-of-thought is logged.",
        "The model chooses tools and recommends intent/verdict/plan; independent source, cutoff, policy and planner checks retain final authority.",
        "Agreement with the baseline is not an accuracy gain. Unresolved/global scope questions are retained, not promoted into facts.", ""]
    for label, run in runs:
        lines += ["## " + label, "", "Request count: " + str(run["request_count"]), "",
            "Usage: `" + json.dumps(run["model_usage"], sort_keys=True) + "`", "",
            "Case execution counts: `" + json.dumps(run.get("ai_case_counts", {}), sort_keys=True) + "`", ""]
        for event in run.get("ai_investigations", []):
            if "audit_recommendation" not in event:
                if event.get("tool_trace"):
                    lines += ["### " + event["case_id"] + " — no validated final recommendation", "",
                        "Execution: **" + event.get("status", "UNKNOWN") + "**; error: `" + event.get("error", "") + "`.",
                        "Partial model output is not repaired or counted as an accepted recommendation.", "",
                        "| Round | Tool | Arguments | Validation / result |", "| --- | --- | --- | --- |"]
                    for tool in event["tool_trace"]:
                        result = tool["result"]
                        detail = {k: result[k] for k in ("error", "observation_id", "file_id", "shown_count", "total_count", "truncated") if k in result}
                        lines.append("| " + " | ".join(map(cell, [tool["round_id"], tool["name"],
                            json.dumps(tool["arguments"], ensure_ascii=False), json.dumps(detail, ensure_ascii=False)])) + " |")
                    lines += [""]
                continue
            rec, validation = event["audit_recommendation"], event["recommendation_validation"]
            lines += ["### " + event["case_id"], "",
                f"Provider/model: {event['provider']}/{event['model']}; execution: {event['status']}.", "",
                f"Model verdict: **{rec['recommended_deletion_status']}**; independent result: **{validation['validation']}**.", "",
                "Component checks: `" + json.dumps(validation.get("component_validation", {}), sort_keys=True) + "`", "",
                "Model's concise justification: " + rec["verdict_justification"], "",
                "Uncertainty: " + ("; ".join(rec["unresolved_obligations"]) or "None reported by model; independent checks still apply."), "",
                "| Round | Model-selected tool | Arguments | Result / coverage |", "| --- | --- | --- | --- |"]
            for tool in event.get("tool_trace", []):
                result = tool["result"]
                summary = {k: result[k] for k in ("error", "total_count", "shown_count", "truncated", "file_id", "observation_id", "observed_at", "captured_at", "temporally_admissible") if k in result}
                observations = result.get("observations", [])
                if observations:
                    summary["returned_observation_ids"] = [o["observation_id"] for o in observations]
                lines.append("| " + " | ".join(map(cell, [tool["round_id"], tool["name"],
                    json.dumps(tool["arguments"], ensure_ascii=False), json.dumps(summary, ensure_ascii=False)])) + " |")
            lines += ["", "Model-proposed plan (original citations, before any canonical synthesis):", "",
                "| Phase | System | Resource | Operation | State | Evidence |", "| --- | --- | --- | --- | --- | --- |"]
            for step in rec["proposed_findings"] + rec["proposed_remediations"] + rec["proposed_verifications"]:
                lines.append("| " + " | ".join(cell(step[k]) for k in ("phase", "system_id", "resource_id", "operation", "state", "evidence_id")) + " |")
            lines += ["", "Independent errors: `" + json.dumps(validation["issues"], ensure_ascii=False) + "`", "",
                "Proof deltas: `" + json.dumps(event.get("proof_delta_counts", {}), sort_keys=True) + "`", "",
                "Corrections/validation attempts: " + str(sum("recommendation_validation" in r for r in event.get("rounds", []))) + ".", ""]
            if validation.get("proof_ledger"):
                lines += ["Proof Ledger (model assertions independently checked, never treated as evidence):", "",
                    "| Goal | Required proof | Inspected observations | Accepted source references | Model coverage | Independent result | Prediction changed |",
                    "| --- | --- | --- | --- | --- | --- | --- |"]
                for goal in validation["proof_ledger"]:
                    lines.append("| " + " | ".join(map(cell, [goal["kind"] + ":" + goal["goal_id"],
                        goal["required_proof"], ", ".join(goal["tool_evidence_inspected"]),
                        json.dumps(goal["accepted_source_references"]),goal["coverage_status"],
                        goal["independent_validation"],goal["canonical_prediction_changed"]])) + " |")
                lines += [""]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    from sys import path
    path.insert(0, str(Path(__file__).resolve().parents[1]))
    from deletion_audit.inputs import protect_output
    protect_output(args.output, Path(__file__).resolve().parents[2] / "dataset", *args.run)
    runs = [(p.parent.name + "/" + p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in args.run]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(runs), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()

"""Offline replay of recorded proposals; no provider client, API calls or gold labels."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.agent_context import investigation_context
from deletion_audit.identity import IdentityGraph
from deletion_audit.ingestion import ingest, dataset_hashes
from deletion_audit.inputs import InputError, load_requests, protect_output
from deletion_audit.investigator import AuditTools
from deletion_audit.policy import Policy
from deletion_audit.proposals import ground_proposal, apply_grounded_updates
from deletion_audit.solver import enrich, decide_case


def replay(dataset, runs, extractions=None):
    before = dataset_hashes(dataset)
    store = ingest(dataset); enrich(store)
    if extractions:
        from deletion_audit.extractions import apply_cached_screens
        apply_cached_screens(store, extractions)
    graph, policy = IdentityGraph.load(dataset), Policy.load(dataset)
    cases, counts = [], Counter()
    for path in runs:
        recorded = json.loads(path.read_text(encoding="utf-8"))
        requests = load_requests(dataset, recorded["split"])
        for event in recorded["ai_investigations"]:
            if "proposal" not in event:
                continue
            request = requests[event["case_id"]]
            tools = AuditTools(request, store, graph, policy)
            baseline = decide_case(request, store, graph, policy)
            try:
                kwargs = {"vision": True, "image_hash": event["image_sha256"],
                          "provider": event["provider"], "model": event["model"]} if event.get("kind") == "vision" else {}
                accepted, verdicts = ground_proposal(event["proposal"], tools, **kwargs)
            except (InputError, ValueError, KeyError) as exc:
                accepted, verdicts = [], [{"validation": "REJECTED", "reason": str(exc)}]
            current = decide_case(request, apply_grounded_updates(store, accepted, request.audit_at), graph, policy) if accepted else baseline
            for verdict in verdicts:
                counts[verdict.get("proof_delta", "rejected")] += 1
            cases.append({"run": str(path), "split": recorded["split"], "case_id": request.case_id,
                "baseline_status": baseline.status, "replay_status": current.status,
                "status_changed": current.status != baseline.status, "steps_changed": current.steps != baseline.steps,
                "accepted_update_count": len(accepted), "validation_results": verdicts,
                "investigation_context": investigation_context(tools, baseline.diagnostic)})
    return {"kind": "offline_recorded_proposal_replay", "cases": cases, "proof_delta_counts": dict(counts),
        "status_changes": sum(c["status_changed"] for c in cases), "step_changes": sum(c["steps_changed"] for c in cases),
        "model_calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0,
        "dataset_integrity": {"file_count": len(before), "unchanged": before == dataset_hashes(dataset)},
        "limitation": "Recorded proposals only: not a new live-model evaluation or a measurement of current prompt/tool-choice behavior."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[2] / "dataset")
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--extractions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protect_output(args.output, args.dataset, *args.run)
    if args.extractions and args.output.resolve().is_relative_to(args.extractions.resolve()):
        raise InputError("Replay report must not overwrite extraction caches")
    result = replay(args.dataset, args.run, args.extractions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"cases", "limitation"}}))

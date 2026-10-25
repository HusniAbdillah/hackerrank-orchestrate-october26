"""Candidate preflight. Exit 1 means no fully contract-valid candidate was produced."""
import argparse
import json
from pathlib import Path
import sys

from deletion_audit.inputs import InputError, protect_output
from deletion_audit.submission_candidate import prepare, publish_best_effort


def main(argv=None):
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=root / "dataset")
    parser.add_argument("--strict-output", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="Separate candidate path; experimental policy may write an invalid candidate with diagnostics")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--extractions", type=Path)
    parser.add_argument("--candidate-policy", choices=["strict", "observed-scope"], default="strict",
                        help="observed-scope is an experimental completion assumption, never evidence validation")
    parser.add_argument("--ai", choices=["none", "auto", "deepseek", "gemini", "agent-led"], default="none")
    parser.add_argument("--ai-cache", type=Path, default=root / "artifacts/ai_cache")
    parser.add_argument("--max-ai-cases", type=int, default=3)
    parser.add_argument("--max-model-calls", type=int, default=12)
    parser.add_argument("--max-cost-usd", type=float, default=.45)
    parser.add_argument("--ai-max-rounds", type=int, default=4)
    parser.add_argument("--ai-case-id", action="append", default=[])
    parser.add_argument("--publish-best-effort", type=Path,
        help="Explicit format-only publication; preserves all strict failures and uncertainty in report")
    args = parser.parse_args(argv)
    if args.ai == "agent-led" and args.publish_best_effort:
        parser.error("Experimental agent-led mode cannot publish before promotion")
    try:
        protect_output(args.report, args.dataset, args.strict_output, args.output)
        if args.extractions and args.report.resolve().is_relative_to(args.extractions.resolve()):
            raise InputError("Report must not overwrite extraction caches")
        ai = None
        if args.ai != "none":
            from deletion_audit.ai_auditor import AuditInvestigator
            for path in (args.report, args.strict_output, args.output):
                if path.resolve().is_relative_to(args.ai_cache.resolve()):
                    raise InputError("Outputs must not overwrite investigator cache")
            ai = AuditInvestigator(args.dataset, args.ai, cache=args.ai_cache, max_cases=args.max_ai_cases,
                max_calls=args.max_model_calls, max_cost_usd=args.max_cost_usd,
                max_rounds=args.ai_max_rounds, audit_mode=True, case_ids=args.ai_case_id)
        report = prepare(args.dataset, args.strict_output, args.output, args.extractions,
                         candidate_policy=args.candidate_policy, ai=ai)
        if args.publish_best_effort:
            protect_output(args.publish_best_effort, args.dataset, args.report, args.output, args.strict_output)
            if args.extractions and args.publish_best_effort.resolve().is_relative_to(args.extractions.resolve()):
                raise InputError("Publication cannot overwrite OCR cache")
            if args.publish_best_effort.resolve().is_relative_to(args.ai_cache.resolve()):
                raise InputError("Publication cannot overwrite investigator cache")
            publish_best_effort(report, args.dataset, args.publish_best_effort)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: report[k] for k in ("status", "candidate_generated", "candidate_schema_valid",
            "unresolved_count", "decided_plan_gap_count", "forced_format_judgment_count")}))
        return 0 if report["candidate_generated"] and report["candidate_schema_valid"] else 1
    except (InputError, OSError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

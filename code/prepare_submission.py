"""Candidate preflight. Exit 1 means no fully contract-valid candidate was produced."""
import argparse
import json
from pathlib import Path
import sys

from deletion_audit.inputs import InputError, protect_output
from deletion_audit.submission_candidate import prepare


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
    args = parser.parse_args(argv)
    try:
        protect_output(args.report, args.dataset, args.strict_output, args.output)
        if args.extractions and args.report.resolve().is_relative_to(args.extractions.resolve()):
            raise InputError("Report must not overwrite extraction caches")
        report = prepare(args.dataset, args.strict_output, args.output, args.extractions,
                         candidate_policy=args.candidate_policy)
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

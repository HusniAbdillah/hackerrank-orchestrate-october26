"""CLI routing; reference-scoring modules are imported only on evaluation commands."""

import argparse
import json
import sys
from pathlib import Path

from .inputs import InputError, load_evidence, load_requests, protect_output


ROOT = Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deletion-audit evaluation foundation (no solver yet)")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "validate", "evaluate", "self-test"):
        command = commands.add_parser(name)
        command.add_argument("--dataset", type=Path, default=ROOT / "dataset")
        if name != "self-test":
            command.add_argument("--split", choices=("sample", "full"), required=True)
        command.add_argument("--report", type=Path, help="Optional JSON report outside dataset/")
        if name in ("validate", "evaluate"):
            command.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.report:
            protect_output(args.report, args.dataset,
                           *([args.predictions] if hasattr(args, "predictions") else []))
        if args.command == "run":
            from .pipeline import run
            report = run(args.dataset, args.split)
            exit_code = 0
        elif args.command == "self-test":
            from .selftest import run_self_test
            report = run_self_test(args.dataset)
            exit_code = 0
        else:
            requests, evidence = load_requests(args.dataset, args.split), load_evidence(args.dataset)
            if args.command == "validate":
                from .contract import validate
                report = validate(args.predictions, requests, evidence).report()
                exit_code = 0 if report["valid"] else 1
            else:
                if args.split != "sample":
                    raise InputError("Reference evaluation is available only for --split sample; use validate for full inputs")
                from .evaluator import evaluate
                report = evaluate(args.predictions, args.dataset / "sample_output.csv", requests, evidence)
                exit_code = 0 if report["validation"]["valid"] else 1
        rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(rendered, encoding="utf-8", newline="\n")
        print(rendered, end="")
        return exit_code
    except (InputError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""CLI routing; reference-scoring modules are imported only on evaluation commands."""

import argparse
import json
import sys
from pathlib import Path

from .inputs import InputError, load_evidence, load_requests, protect_output


ROOT = Path(__file__).resolve().parents[2]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic deletion audit, ingestion, and evaluation")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "validate", "evaluate", "self-test", "ingest", "solve", "ocr"):
        command = commands.add_parser(name)
        command.add_argument("--dataset", type=Path, default=ROOT / "dataset")
        if name not in {"self-test", "ingest", "ocr"}:
            command.add_argument("--split", choices=("sample", "full"), required=True)
        command.add_argument("--report", type=Path, help="Optional JSON report outside dataset/")
        if name in ("validate", "evaluate"):
            command.add_argument("--predictions", type=Path, required=True)
        if name == "solve":
            command.add_argument("--output", type=Path, required=True)
            command.add_argument("--extractions", type=Path, help="Optional SHA-256-bound local OCR cache")
            command.add_argument("--submission-output", type=Path, help="Publish only when all full-split verdicts, proof scopes and contract checks pass")
        if name == "ocr":
            command.add_argument("--output", type=Path, required=True, help="Extraction cache directory outside dataset/")
        if name == "ingest":
            command.add_argument("--inventory-doc", type=Path, default=ROOT / "docs/dataset_analysis.md")
            command.add_argument("--normalized", type=Path, help="Optional normalized observation JSONL")
            command.add_argument("--identity-report", type=Path, help="Optional per-case identity coverage JSON")
    args = parser.parse_args(argv)
    try:
        if args.report:
            protect_output(args.report, args.dataset,
                           *([args.predictions] if hasattr(args, "predictions") else []))
        if args.command == "ocr":
            if args.report and args.report.resolve().is_relative_to(args.output.resolve()):
                raise InputError("OCR report must be outside the extraction cache directory")
            from .ocr_cache import extract
            report = extract(args.dataset, args.output)
            exit_code = 0 if all(f["status"] != "unavailable" for f in report["files"]) else 1
        elif args.command == "solve":
            if args.report and args.extractions and args.report.resolve().is_relative_to(args.extractions.resolve()):
                raise InputError("Report output must not overwrite the extraction cache")
            if args.report:
                protect_output(args.report, args.dataset, args.output)
                if args.submission_output:
                    protect_output(args.report, args.dataset, args.submission_output)
            from .solver import solve
            report = solve(args.dataset, args.split, args.output, args.extractions, args.submission_output)
            exit_code = 0 if report["validation"]["valid"] and report["dataset_integrity"]["unchanged"] else 1
        elif args.command == "ingest":
            outputs = [p for p in (args.report, args.normalized, args.identity_report) if p]
            if len({p.resolve() for p in outputs}) != len(outputs):
                raise InputError("Report and normalized-output paths must be distinct")
            for output in outputs:
                protect_output(output, args.dataset, args.inventory_doc)
            from .diagnostics import diagnose
            report, identity, store = diagnose(args.dataset, args.inventory_doc)
            if args.normalized:
                args.normalized.parent.mkdir(parents=True, exist_ok=True)
                with args.normalized.open("w", encoding="utf-8", newline="\n") as stream:
                    for observation in store.observations:
                        stream.write(json.dumps(observation.to_dict(), ensure_ascii=False, allow_nan=False) + "\n")
            if args.identity_report:
                args.identity_report.parent.mkdir(parents=True, exist_ok=True)
                args.identity_report.write_text(json.dumps(identity, indent=2, ensure_ascii=False) + "\n",
                                                encoding="utf-8", newline="\n")
            exit_code = 0 if (report["supported_formats_successful"] and
                              report["inventory_comparison"]["matches"] and
                              report["csv_inventory_comparison"]["matches"] and
                              report["dataset_integrity"]["unchanged"]) else 1
        elif args.command == "run":
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

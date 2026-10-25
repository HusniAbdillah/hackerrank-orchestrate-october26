"""Sum explicitly selected, non-overlapping application run ledgers (never labels)."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.inputs import InputError, protect_output
from deletion_audit.providers import UsageLedger


def aggregate(paths):
    resolved = [path.resolve() for path in paths]
    if len(set(resolved)) != len(resolved):
        raise InputError("Duplicate usage report path")
    ledger = UsageLedger()
    runs = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        records = data["model_call_records"]
        ledger.records.extend(records)
        ledger.cache_hits += data["model_usage"].get("cache_hits", 0)
        runs.append({"path": str(path), "calls": len(records),
                     "limits": data["model_usage"].get("limits", {}),
                     "latency_seconds": sum(r.get("latency_seconds", 0) for r in records)})
    summary = ledger.summary()
    summary.pop("limits")  # Each physical run has its own limits; these are not shared.
    return {"runs": runs, "observed_usage": summary,
            "recorded_usage_cost_usd": sum(r["estimated_cost_usd"] for r in ledger.records if r.get("usage_reported")),
            "unreported_usage_reserved_usd": sum(r["estimated_cost_usd"] for r in ledger.records if not r.get("usage_reported")),
            "caveat": "Only listed run records are counted. Missing usage is unknown, not zero; its conservative budget reservation is retained. Select one report per physical run, excluding duplicate stdout copies. Interrupted runs without journals require separate disclosure."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protect_output(args.output, Path(__file__).resolve().parents[2] / "dataset", *args.run)
    value = aggregate(args.run)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(value["observed_usage"], indent=2))

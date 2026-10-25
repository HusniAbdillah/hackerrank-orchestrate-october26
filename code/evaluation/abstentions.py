"""Compare abstentions from diagnostic runs; never reads expected answers."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.inputs import protect_output
from deletion_audit.sufficiency import abstention_comparison


def review(before, after):
    result = abstention_comparison(before, after)
    result.update(
        previous_issue_patterns=[{"issues": list(pattern), "case_count": count} for pattern, count in Counter(
            tuple(sorted({i["code"] for i in c["issues"]})) for c in before["cases"] if c["abstained"]).most_common()],
        contract_valid_before=len(before["cases"]) - len({i["case_id"] for i in before["validation"]["issues"]}),
        contract_valid_after=after["contract_valid_rows"],
        currently_unresolved=after["unresolved_cases"],
        current_unresolved_causes=dict(Counter(cause for c in after["cases"] if not c["verdict_resolved"]
                                              for cause in c["uncertainty_causes"])),
        all_cases=after["cases"],
        units="Root-cause counts count cases once per cause and can overlap; issue-pattern groups are disjoint.")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protect_output(args.output, Path(__file__).resolve().parents[2] / "dataset", args.before, args.after)
    result = review(json.loads(args.before.read_text(encoding="utf-8")), json.loads(args.after.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"cases", "all_cases"}}, indent=2))

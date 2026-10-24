"""Reproducible ingestion and identity diagnostics, with no reference-answer reads."""

import hashlib
import json
import re
from pathlib import Path

from .identity import IdentityGraph, identity_coverage
from .ingestion import compare_inventory, coverage_report, dataset_hashes, ingest
from .inputs import OUTPUT_FIELDS, load_requests, read_csv
from .observations import EvidenceStore


def diagnose(dataset: Path, analysis: Path) -> tuple[dict, dict, EvidenceStore]:
    before = dataset_hashes(dataset)
    store = ingest(dataset)
    inventory = compare_inventory(store, analysis)
    graph = IdentityGraph.load(dataset)
    request_splits = {split: load_requests(dataset, split) for split in ("sample", "full")}
    identity = {
        "kind": "identity_resolution_coverage", "identity_rows": graph.snapshot_rows,
        "audit_rows": graph.audit_rows, "identifier_versions": sum(map(len, graph.by_user.values())),
        "identity_issues": graph.issues,
        "splits": {split: identity_coverage(graph, requests, store)
                   for split, requests in request_splits.items()},
        "limits": ["Coverage is unique exact-identifier resolution, not deletion-status accuracy.",
                   "Resource ownership may be ambiguous or based on a reported catalog claim; provenance is retained.",
                   "Names never create identity or ownership matches."],
    }
    report = coverage_report(store, inventory)
    counts = {
        "deletion_requests.csv": len(request_splits["full"]),
        "sample_deletion_requests.csv": len(request_splits["sample"]),
        "user_identities.csv": graph.snapshot_rows, "user_audit_log.csv": graph.audit_rows,
        "system_activity.csv": sum(o.kind == "reported_claim" for o in store.observations),
        "evidence_files.csv": len(store.files),
        "deletion_rules.csv": len(read_csv(dataset / "deletion_rules.csv",
                                         ["rule_id", "data_category", "condition", "required_action"])),
        "output.csv": len(read_csv(dataset / "output.csv", OUTPUT_FIELDS)),
    }
    documented = {name: int(count.replace(",", "")) for name, count in re.findall(
        r"^\| `([^`]+\.csv)` \| ([0-9,]+) \|", analysis.read_text(encoding="utf-8"), re.MULTILINE)}
    report["csv_inventory_comparison"] = {
        "matches": all(documented.get(name) == count for name, count in counts.items()),
        "observed_counts": counts,
        "excluded": ["sample_output.csv is not parsed; bytes are hashed only for integrity"],
    }
    report["identity_summary"] = {
        split: {k: v for k, v in result.items() if k != "cases"}
        for split, result in identity["splits"].items()
    }
    after = dataset_hashes(dataset)
    report["dataset_integrity"] = {
        "file_count": len(before), "unchanged": before == after,
        "fingerprint_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
        "changed_files": sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k)),
    }
    return report, identity, store

"""Executable ingestion milestone. Deliberately contains no prediction logic."""

from collections import Counter
from pathlib import Path

from .inputs import load_evidence, load_requests


def run(dataset: Path, split: str) -> dict:
    requests = load_requests(dataset, split)
    evidence = load_evidence(dataset)
    return {
        "kind": "pipeline_readiness",
        "split": split,
        "request_count": len(requests),
        "evidence_catalog_counts": dict(sorted(Counter(e.source for e in evidence.values()).items())),
        "prediction_count": 0,
        "unresolved_count": len(requests),
        "reason": "Audit engine is not implemented; no deletion status has been inferred.",
        "cases": [{"case_id": cid, "audit_at": requests[cid].audit_at.isoformat(),
                   "ready_for_audit": True} for cid in sorted(requests)],
    }

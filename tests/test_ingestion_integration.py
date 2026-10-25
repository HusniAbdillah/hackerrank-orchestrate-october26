import json
from pathlib import Path

import pytest

from deletion_audit.cli import main
from deletion_audit.identity import IdentityGraph, identity_coverage
from deletion_audit.ingestion import compare_inventory, coverage_report, dataset_hashes, ingest
from deletion_audit.inputs import load_requests


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def real_store():
    return ingest(ROOT / "dataset")


def test_all_manifest_files_and_units_match_actual_documented_inventory(real_store):
    report = coverage_report(real_store, compare_inventory(real_store, ROOT / "docs/dataset_analysis.md"))
    assert report["inventory_comparison"]["matches"]
    assert report["file_count"] == 94
    assert report["file_statuses"] == {"parsed": 83, "pending_multimodal": 11}
    assert report["formats"][".json"]["units"] == 890
    assert report["formats"][".sql"]["units"] == 969
    assert report["formats"][".log"]["units"] == 2211
    assert report["formats"][".txt"]["units"] == 46
    assert report["formats"][".pdf"]["units"] == 7
    assert report["observation_kinds"]["reported_claim"] == 4011
    assert not report["issues"]
    assert all(o.provenance["locator"] for o in real_store.observations)


def test_actual_request_identity_coverage_is_temporally_grounded(real_store):
    graph = IdentityGraph.load(ROOT / "dataset")
    assert graph.snapshot_rows == 850 and graph.audit_rows == 306
    assert not graph.issues
    for split, count, historical in [("sample", 32, 3), ("full", 518, 100)]:
        report = identity_coverage(graph, load_requests(ROOT / "dataset", split), real_store)
        assert report["uniquely_resolved"] == report["request_count"] == count
        assert report["historical_email_only"] == historical
        assert report["ambiguous"] == report["unresolved"] == 0


def test_ingestion_and_resolution_do_not_open_sample_ground_truth(monkeypatch):
    original = Path.open

    def guard(path, *args, **kwargs):
        if path.name == "sample_output.csv":
            pytest.fail("Ground-truth access in evidence or identity path")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guard)
    store = ingest(ROOT / "dataset")
    graph = IdentityGraph.load(ROOT / "dataset")
    assert identity_coverage(graph, load_requests(ROOT / "dataset", "sample"), store)["coverage"] == 1


def test_machine_reports_reproduce_and_dataset_hashes_unchanged(tmp_path):
    dataset = ROOT / "dataset"
    before = dataset_hashes(dataset)
    coverage = tmp_path / "coverage.json"
    identity = tmp_path / "identity.json"
    normalized = tmp_path / "normalized.jsonl"
    assert main(["ingest", "--dataset", str(dataset), "--report", str(coverage),
                 "--identity-report", str(identity), "--normalized", str(normalized)]) == 0
    report = json.loads(coverage.read_text())
    assert report["dataset_integrity"]["unchanged"]
    assert report["inventory_comparison"]["matches"]
    assert report["csv_inventory_comparison"]["matches"]
    assert report["csv_inventory_comparison"]["observed_counts"]["deletion_rules.csv"] == 15
    observations = [json.loads(line) for line in normalized.read_text(encoding="utf-8").splitlines()]
    assert len(observations) == report["observation_count"]
    assert len({o["observation_id"] for o in observations}) == len(observations)
    assert json.loads(identity.read_text())["splits"]["full"]["request_count"] == 518
    assert dataset_hashes(dataset) == before


def test_inventory_mismatch_and_parse_failure_are_nonzero(tmp_path):
    # Real parsing succeeds, but a truncated inventory must fail visibly.
    inventory = tmp_path / "wrong_inventory.md"
    inventory.write_text("| evidence_01 | [evidence/logs/absent.log](x) | origin | time | 0 lines |\n")
    report = tmp_path / "mismatch.json"
    assert main(["ingest", "--inventory-doc", str(inventory), "--report", str(report)]) == 1
    assert not json.loads(report.read_text())["inventory_comparison"]["matches"]

import csv
import json
from copy import deepcopy

import pytest

from deletion_audit.inputs import OUTPUT_FIELDS, REQUEST_FIELDS, load_evidence, load_requests


def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def step(number, phase, system, resource, operation, state, evidence=""):
    return {"step_no": number, "phase": phase, "system_id": system,
            "resource_id": resource, "operation": operation, "state": state, "evidence_id": evidence}


@pytest.fixture
def foundation(tmp_path):
    dataset = tmp_path / "dataset"
    (dataset / "evidence").mkdir(parents=True)
    manifest = []
    for number, captured in enumerate(("2026-02-01T12:00:00Z", "2026-01-01T00:00:00Z", "2026-02-01T12:00:01Z"), 1):
        (dataset / "evidence" / f"{number}.txt").write_text("Fictional evidence fixture", encoding="utf-8")
        manifest.append({"file_id": f"evidence_{number}", "file_path": f"evidence/{number}.txt",
                         "origin": "fixture", "captured_at": captured})
    write_csv(dataset / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"], manifest)
    write_csv(dataset / "system_activity.csv", ["activity_id", "event_time", "event_type", "source_system",
              "target_system", "resource_id", "reported_result", "details"], [
        {"activity_id": "activity_1", "event_time": "2026-02-01T12:00:00Z", "event_type": "CHECK",
         "source_system": "fixture", "target_system": "security", "resource_id": "journal",
         "reported_result": "SUCCESS", "details": "Fictional test event"}])
    write_csv(dataset / "user_audit_log.csv", ["audit_id", "user_id", "event_time", "field_name", "old_value", "new_value"], [
        {"audit_id": "audit_1", "user_id": "fictional_user", "event_time": "2026-01-01T00:00:00Z",
         "field_name": "email", "old_value": "old@example.test", "new_value": "new@example.test"}])
    def request(cid):
        return {"case_id": cid, "email": "fixture@example.test", "requested_at": "2026-01-01T00:00:00Z",
                "reported_status": "COMPLETE", "reported_at": "2026-01-02T00:00:00Z",
                "audit_at": "2026-02-01T12:00:00Z", "request_text": "Fictional request; semantics outside evaluator scope."}
    write_csv(dataset / "sample_deletion_requests.csv", REQUEST_FIELDS, [request(f"case_00{i}") for i in range(1, 4)])
    write_csv(dataset / "deletion_requests.csv", REQUEST_FIELDS, [request("case_101"), request("case_102")])
    rows = [
        {"case_id": "case_001", "deletion_status": "COMPLETE", "steps_json": json.dumps([
            step(1, "VERIFICATION", "accounts", "profile", "VERIFY_RECORD_ABSENT", "ABSENT", "evidence_1"),
            step(2, "VERIFICATION", "security", "journal", "VERIFY_RECORD_PRESENT", "PRESENT", "activity_1")])},
        {"case_id": "case_002", "deletion_status": "INCOMPLETE", "steps_json": json.dumps([
            step(1, "FINDING", "search", "document", "REPORT_REMAINING_RECORD", "PRESENT", "evidence_1"),
            step(2, "FINDING", "integration", "connector", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", "evidence_1"),
            step(3, "REMEDIATION", "integration", "connector", "DISABLE_DATA_FLOW", "DISABLED"),
            step(4, "REMEDIATION", "search", "document", "DELETE_RECORD", "ABSENT"),
            step(5, "VERIFICATION", "search", "document", "VERIFY_RECORD_ABSENT", "ABSENT"),
            step(6, "VERIFICATION", "integration", "connector", "VERIFY_DATA_FLOW_DISABLED", "DISABLED")])},
        {"case_id": "case_003", "deletion_status": "NOT_APPLICABLE", "steps_json": "[]"},
    ]
    reference = dataset / "sample_output.csv"
    write_csv(reference, OUTPUT_FIELDS, rows)
    predictions = tmp_path / "predictions.csv"
    write_csv(predictions, OUTPUT_FIELDS, rows)
    return {"dataset": dataset, "requests": load_requests(dataset, "sample"), "evidence": load_evidence(dataset),
            "reference": reference, "predictions": predictions, "rows": deepcopy(rows)}

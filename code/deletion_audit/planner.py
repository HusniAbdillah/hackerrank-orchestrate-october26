"""Canonical output steps from grounded resource decisions; no effectful deletion."""

from .contract import OPERATIONS, order_key


def plan(resources, decisions):
    incomplete = any(d.finding for d in decisions)
    steps = []
    for resource, decision in zip(resources, decisions):
        for operation in (decision.finding, decision.remediation, decision.verification):
            if operation is None:
                continue
            phase, state = OPERATIONS[operation]
            steps.append({"step_no": 0, "phase": phase, "system_id": resource.system_id,
                          "resource_id": resource.resource_id, "operation": operation, "state": state,
                          "evidence_id": resource.evidence.source_id if phase == "FINDING" or not incomplete else ""})
    steps.sort(key=order_key)
    for number, step in enumerate(steps, 1):
        step["step_no"] = number
    return ("INCOMPLETE" if incomplete else "COMPLETE"), steps

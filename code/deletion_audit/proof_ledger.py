"""Per-goal AI claims are diagnostics, never new evidence or policy authority."""
from .proposals import obj, string
from .state import actual_fields
from .inputs import timestamp, InputError

KINDS = ["AUTHORIZATION", "IDENTITY", "OWNERSHIP", "STATE", "TREATMENT", "RECREATION", "RETENTION", "PLAN"]
REF = obj({"evidence_id": string(100), "observation_id": string(250)})
LEDGER_ENTRY = obj({"goal_id": string(80), "kind": string(30, KINDS),
    "system_id": string(100), "resource_id": string(100), "required_proof": string(500),
    "tool_evidence_inspected": {"type": "array", "items": string(250), "maxItems": 12},
    "accepted_source_references": {"type": "array", "items": REF, "maxItems": 12},
    "coverage_status": string(20, ["proven", "violated", "unresolved"]),
    "agent_recommendation": string(700),
    "admissible_source_leads": {"type": "array", "items": REF, "maxItems": 8}})


def validate_ledger(entries, tools, decision, sources, evidence_results, trace=None, plan_matches=True):
    """Check proof goals against independent identity/state/condition/plan results."""
    known = {(r["system_id"], r["resource_id"]): r for r in decision.diagnostic.get("resource_states", [])}
    users = tools.graph.resolve("email", tools.request.email, tools.request.audit_at)
    ownership = tools.graph.ownership(tools.store, tools.request.audit_at)
    valid_refs = {(r["evidence_id"], r["observation_id"]) for r in evidence_results if r["validation"] == "SOURCE_GROUNDED"}
    inspected = set()
    for call in trace or []:
        result = call["result"]
        if result.get("observation_id") and not result.get("error"):
            inspected.add(result["observation_id"])
        inspected.update(o["observation_id"] for o in result.get("observations", []))
    findings = {(s["system_id"], s["resource_id"]) for s in decision.steps if s["phase"] == "FINDING"}
    results, errors, ids = [], [], set()
    for entry in entries:
        kind, key = entry["kind"], (entry["system_id"], entry["resource_id"])
        row_errors = []
        if entry["goal_id"] in ids:
            row_errors.append("DUPLICATE_PROOF_GOAL")
        ids.add(entry["goal_id"])
        refs = {(r["evidence_id"], r["observation_id"]) for r in entry["accepted_source_references"]}
        if refs - valid_refs:
            row_errors.append("LEDGER_SOURCE_NOT_ACCEPTED")
        if trace is not None and set(entry["tool_evidence_inspected"]) - inspected:
            row_errors.append("LEDGER_OBSERVATION_NOT_TOOL_INSPECTED")
        for lead in entry["admissible_source_leads"]:
            source = sources.get(lead["observation_id"])
            if source is None or source.source_id != lead["evidence_id"] or source.captured_at > tools.request.audit_at or (
                    source.observed_at is not None and source.observed_at > tools.request.audit_at):
                row_errors.append("LEDGER_LEAD_NOT_ADMISSIBLE")
        expected = None
        if kind == "AUTHORIZATION":
            expected = "proven" if decision.diagnostic["authorization"] is not None else None
        elif kind == "IDENTITY":
            expected = "proven" if len(users) == 1 else None
        elif kind == "OWNERSHIP":
            expected = "proven" if users and set(ownership.get(key, {})) == set(users) else None
        elif kind == "PLAN":
            expected = "proven" if decision.diagnostic["plan_scope_complete"] and plan_matches else None
        elif kind in {"STATE", "TREATMENT", "RECREATION"} and key in known:
            state = known[key]
            if kind != "RECREATION" or state["category"] in {"DATA_FLOW", "BACKUP_ARCHIVE"}:
                expected = "violated" if key in findings else "proven"
                if any(i.get("resource_id") == key[1] or i.get("resource") == list(key)
                       for i in decision.diagnostic["issues"]):
                    expected = None
        elif kind == "RETENTION" and key in known:
            state = known[key]; source = sources.get(state["observation_id"])
            fields = actual_fields(source) if source else {}
            deadline = fields.get("retention_until", fields.get("retained_until"))
            try:
                active = (bool(deadline) and timestamp(deadline) >= tools.request.audit_at) or fields.get("hold_active") is True
            except InputError:
                active = False
            if state["category"] in {"SECURITY_AUDIT_LOG", "LEGAL_HOLD_RECORD"} and active:
                expected = "proven" if state["state"] == "PRESENT" else "violated"
        if kind in {"STATE", "TREATMENT", "RECREATION", "RETENTION"} and expected and entry["coverage_status"] != "unresolved":
            selected = known[key]["observation_id"]
            if selected not in {r[1] for r in refs}:
                row_errors.append("LEDGER_SELECTED_STATE_PROOF_MISSING")
            projected_parent = selected.rsplit(":negative:", 1)[0] if sources.get(selected) and sources[selected].scope.get("projected_negative") else selected
            if trace is not None and selected not in inspected and projected_parent not in inspected:
                row_errors.append("LEDGER_STATE_PROOF_NOT_INSPECTED")
        if entry["coverage_status"] != "unresolved" and entry["coverage_status"] != expected:
            row_errors.append("LEDGER_COVERAGE_NOT_INDEPENDENTLY_ESTABLISHED")
        outcome = "REJECTED" if row_errors else "UNRESOLVED" if entry["coverage_status"] == "unresolved" else "ACCEPTED"
        results.append({**entry, "independent_validation": outcome,
            "independent_coverage": expected or "unresolved", "errors": row_errors,
            "canonical_prediction_changed": False, "novel_fact": False})
        errors.extend({"code": code, "goal_id": entry["goal_id"]} for code in row_errors)
    missing = set(KINDS) - {e["kind"] for e in entries}
    if missing:
        errors.append({"code": "PROOF_LEDGER_CATEGORIES_MISSING", "categories": sorted(missing)})
    return results, errors

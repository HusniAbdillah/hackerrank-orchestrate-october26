"""Evidence-driven investigation goals; no reference labels or model verdicts."""
from .observations import identifiers
from .source_access import raw_text, raw_value


def references_owned(value, owned):
    pending = [value]
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            pair = node.get("source_system_id"), node.get("source_resource_id")
            if all(isinstance(v, str) for v in pair) and pair in owned:
                return True
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)
    return False


NEEDS = {
    "NO_DIRECT_STATE": "Inspect original source for explicit record fields; activity success is not state.",
    "PRIMARY_PROFILE_VERIFICATION_UNGROUNDED": "Find an exact primary resource/subject relation and admissible final-state readback; retained records alone do not prove it.",
    "OCR_SUBJECT_LINK_UNCORROBORATED": "Resolve conflicting literal identifiers. Do not merge names or repair OCR without corroboration.",
    "RETENTION_CONDITION_UNPROVEN": "Find the resource-specific retention deadline; another row's deadline cannot establish it.",
}


def investigation_context(tools, baseline):
    at = tools.request.audit_at
    users = tools.graph.resolve("email", tools.request.email, at)
    owned = {key for key, owners in tools.graph.ownership(tools.store, at).items() if set(owners) == set(users) and users}
    candidates = []
    for source in tools.store.observations:
        if source.captured_at > at or (source.observed_at and source.observed_at > at):
            continue
        if source.kind not in {"context", "missing_data"} and source.category is not None:
            continue
        if not source.file_id or not (any(users.intersection(tools.graph.resolve(k, v, at)) for k, v in identifiers(raw_text(source)))
                                      or references_owned(raw_value(source), owned)):
            continue
        candidates.append({"file_id": source.file_id, "observation_id": source.observation_id,
            "system_id": source.system_id, "resource_id": source.resource_id,
            "observed_at": source.observed_at.isoformat() if source.observed_at else None,
            "captured_at": source.captured_at.isoformat(),
            "limitation": "An exact identifier or owned-parent reference in untyped source is a lead, not ownership/state proof."})
    candidates.sort(key=lambda c: (c["captured_at"], c["observation_id"]), reverse=True)
    goals = [{**issue, "needed_proof": NEEDS.get(issue["code"], "Inspect applicable policy and an exact dated source; preserve missing proof.")}
             for issue in baseline.get("issues", [])]
    obligations = [{"system_id": state["system_id"], "resource_id": state["resource_id"],
        "category": state["category"], "state": state["state"],
        "policy": tools.policy.rules.get(state["category"], {"required_action":
            "DISABLE_DATA_FLOW" if state["category"] == "DATA_FLOW" else "UNKNOWN"}),
        "limitation": "Inspect every grounded replica; a compliant copy does not clear another copy."}
        for state in baseline.get("resource_states", [])]
    return {"goals": goals, "source_leads": candidates[:12], "total_count": len(candidates),
        "obligations": obligations,
        "shown_count": min(12, len(candidates)), "truncated": len(candidates) > 12,
        "retrieval": "Use paginated search_evidence with exact subject identifiers for additional observations.",
        "workflow": "Identity is already supplied. Retrieve the narrow sources needed, then submit a draft on the penultimate turn when possible; reserve final turn for one correction."}

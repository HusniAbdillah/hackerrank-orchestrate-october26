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


def route_case(tools, baseline, context):
    """Prioritize admissible actionable leads; missing facts are not model tasks."""
    codes = {i["code"] for i in baseline.get("issues", [])}
    common = {"eligible": False, "irreducible": False, "priority": 0,
              "lead_count": context["total_count"], "reason": "GROUNDED_UNAMBIGUOUS"}
    if "OCR_SUBJECT_LINK_UNCORROBORATED" in codes or "AMBIGUOUS_RESOURCE_OWNERSHIP" in codes:
        return {**common, "irreducible": True, "reason": "CONTRADICTORY_IDENTITY_REQUIRES_INDEPENDENT_EVIDENCE"}
    wanted = {i.get("resource_id") for i in baseline.get("issues", []) if i.get("resource_id")}
    fields = {"retention_until", "retained_until", "hold_active"} if codes & {
        "RETENTION_CONDITION_UNPROVEN", "LEGAL_HOLD_CONDITION_UNPROVEN"} else {
        "name", "email", "phone", "email_hash", "restore_allowed", "deletion_block", "enabled"}
    actionable = []
    for lead in context["source_leads"]:
        source = next(o for o in tools.store.observations if o.observation_id == lead["observation_id"])
        pending = [raw_value(source)]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                resource = value.get("resource_id")
                if resource and (not wanted or resource in wanted) and fields.intersection(value):
                    actionable.append(lead["observation_id"])
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
    if actionable:
        return {**common, "eligible": True, "priority": 100, "reason": "ADMISSIBLE_LITERAL_FIELD_OR_RESOURCE_LEAD",
                "actionable_observation_ids": sorted(set(actionable))}
    if context.get("truncated"):
        return {**common, "eligible": True, "priority": 80, "reason": "UNREVIEWED_ADMISSIBLE_SOURCE_PAGES",
                "unreviewed_source_count": context["total_count"] - context["shown_count"]}
    if codes & {"NO_DIRECT_STATE", "PRIMARY_PROFILE_VERIFICATION_UNGROUNDED", "NO_GROUNDED_RESOURCE_LINK",
                "RETENTION_CONDITION_UNPROVEN", "LEGAL_HOLD_CONDITION_UNPROVEN"}:
        return {**common, "irreducible": True, "reason": "NO_ACTIONABLE_ADMISSIBLE_PROOF_LEAD",
                "excluded_late_source_count": len(baseline.get("excluded_subject_link_sources", []))}
    # Natural-language shared-record conditions can warrant review of the original
    # conversation, even when the current deterministic treatment is already safe.
    for state in baseline.get("resource_states", []):
        if state["category"] != "SUPPORT_MESSAGE":
            continue
        source = next((o for o in tools.store.observations if o.observation_id == state["observation_id"]), None)
        if source:
            from .state import actual_fields
            f = actual_fields(source)
            body = f.get("message_text", f.get("message_excerpt", ""))
            if body and body not in {"[REDACTED]", "REDACTED"} and "shared_context" not in f:
                return {**common, "eligible": True, "priority": 50, "reason": "ORIGINAL_SHARED_SUPPORT_POLICY_CONTEXT",
                        "actionable_observation_ids": [source.observation_id]}
    return common


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

"""Internal uncertainty diagnostics, deliberately outside the submission vocabulary."""
from collections import Counter

CAUSES = {
    "NO_GROUNDED_RESOURCE_LINK": ("missing_ownership", "Find an exact subject identifier or explicit source-resource link available before audit_at; never derive an ID from case numbers."),
    "IDENTITY_GAP": ("missing_ownership", "Resolve conflicting or missing temporal identity versions."),
    "OCR_SUBJECT_LINK_UNCORROBORATED": ("missing_ownership", "Verify the screenshot's literal subject identifier; do not repair OCR characters or trust a contradictory catalog identity claim."),
    "AMBIGUOUS_RESOURCE_OWNERSHIP": ("missing_ownership", "Inspect direct identifiers and catalog claims separately; withhold treatment until ownership is established."),
    "AMBIGUOUS_RESOURCE_TREATMENT_WITHHELD": ("policy_ambiguity", "Establish sole ownership or permitted shared-record treatment."),
    "PRIMARY_PROFILE_VERIFICATION_UNGROUNDED": ("absent_verification_evidence", "Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal."),
    "NO_DIRECT_STATE": ("absent_verification_evidence", "Inspect the named resource in original evidence, OCR or PDF extraction; a worker/catalog claim is not resulting state."),
    "DIRECT_STATE_CONTRADICTION": ("invalid_temporal_join", "Reconcile timestamp, copy topology and observation scope without discarding conflicting direct evidence."),
    "INGESTION_COVERAGE_INCOMPLETE": ("unsupported_source_parsing", "Repair the reported source parser before using its scope as proof."),
    "REQUIRED_KEPT_RECORD_MISSING": ("policy_ambiguity", "Check whether the absence is truly subject/copy scoped and whether policy requires continued retention; no restoration operation is allowed by the output contract."),
    "REQUIRED_RETAINED_RECORD_MISSING": ("policy_ambiguity", "Confirm the negative scope and retention obligation; do not invent an unsupported restore operation."),
    "RETENTION_CONDITION_UNPROVEN": ("policy_ambiguity", "Locate an admissible retention period for this exact resource; do not borrow another record's deadline or infer a restore obligation from absence alone."),
    "LEGAL_HOLD_CONDITION_UNPROVEN": ("policy_ambiguity", "Establish an active legal hold on this exact resource at audit_at before asserting a retention breach."),
    "UNKNOWN_INTENT": ("authorization_uncertain", "Read the original request language and resolve explicit deletion authorization before any destructive plan."),
}


def explain_uncertainty(diagnostic, request, store, graph):
    issues = diagnostic["issues"]
    causes, actions = set(), set()
    for issue in issues:
        category, action = CAUSES.get(issue["code"], ("policy_ambiguity", "Inspect the supplied condition and original evidence; do not invent a fallback rule."))
        causes.add(category); actions.add(action)
        if issue["code"] in {"REQUIRED_KEPT_RECORD_MISSING", "REQUIRED_RETAINED_RECORD_MISSING"}:
            causes.add("inadequate_scoped_negative_evidence")
    users = set(diagnostic.get("identity", []))
    tokens = { (v.kind, v.value) for uid in users for v in graph.versions_for_user(uid, request.audit_at) }
    possible = {o.observation_id: o for token in tokens for o in store.by_identifier.get(token, []) if o.resource_id}
    excluded = [o for o in possible.values() if not o.admissible(request.audit_at)]
    late_links = sorted({o.source_id for o in excluded})
    if diagnostic["abstained"] and late_links:
        causes.add("temporal_admissibility_gap")
        actions.add("Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.")
    missing = {(i.get("system_id"), i.get("resource_id")) for i in issues if i["code"] == "NO_DIRECT_STATE"}
    if any(o.kind == "context" and (o.system_id, o.resource_id) in missing for o in store.observations if o.admissible(request.audit_at)):
        causes.add("unsupported_source_parsing")
    return {"resolution": "UNRESOLVED" if diagnostic["abstained"] else "DECIDED_WITH_GAPS" if causes else "DECIDED",
            "uncertainty_causes": sorted(causes), "proposed_next_actions": sorted(actions),
            "excluded_subject_link_sources": late_links,
            "plan_scope_complete": not issues,
            "cutoff": request.audit_at.isoformat()}


def abstention_comparison(before, after):
    old = {c["case_id"]: c for c in before["cases"] if c["abstained"]}
    new = {c["case_id"]: c for c in after["cases"]}
    rows = [{"case_id": cid, "previous_issues": case["issues"], "resolution": new[cid]["resolution"],
             "causes": new[cid]["uncertainty_causes"], "next_actions": new[cid]["proposed_next_actions"],
             "submission_status": new[cid]["submission_status"]} for cid, case in sorted(old.items())]
    return {"previous_abstentions": len(old), "now_resolved": sum(r["submission_status"] is not None for r in rows),
            "remaining_causes": dict(Counter(c for r in rows if r["submission_status"] is None for c in r["causes"])),
            "cases": rows}

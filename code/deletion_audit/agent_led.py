"""Experimental blind-first source certificates and independently enumerated obligations.

No decide_case invocation and no baseline plan in acceptance checks. Baseline comparison
is attached by the caller only after this verifier has finished. Not a promotion gate.
"""
from dataclasses import replace

from .authorization import authorize
from .contract import OPERATIONS, order_key, canonical
from .inputs import InputError, timestamp
from .proposals import FACT, PROPOSAL_SCHEMA, obj, string, validate_json, ground_proposal, apply_grounded_updates
from .recommendations import AUDIT_PROPOSAL_SCHEMA
from .state import reconstruct, actual_fields, observed_state
from .source_access import raw_text

CLAIMS = ["RESOURCE_OWNERSHIP", "LITERAL_FIELDS", "EXPLICIT_STATE", "RETENTION_OPERANDS",
          "DATA_FLOW", "RESTORE_PERMISSION", "NEGATIVE_SCOPE"]
CERTIFICATE = obj({"claim_type": string(40, CLAIMS), "fact": FACT,
    "subject_user_id": string(100), "captured_at": string(50), "limitations": string(700)})
SCHEMA = obj({**AUDIT_PROPOSAL_SCHEMA["properties"], "proof_certificates": {
    "type": "array", "items": CERTIFICATE, "maxItems": 12}})

INSTRUCTIONS = """
EXPERIMENTAL BLIND-FIRST AUDIT. No baseline conclusion is supplied on your first pass.
Lead investigation using the request, supplied policy table, source index and read-only tools.
Policy is preloaded: reserve tool capacity for inspect_source and concrete follow-up leads.
Do not pass activity_id/audit_id as file_id to inspect_source: that tool accepts manifest
files only. Retrieve activity/audit observations via exact resource/identifier search instead.
Return proof_certificates (empty if no supported certificate) plus the required audit fields.
Each certificate carries claim_type, existing fact protocol, exact subject_user_id, original
captured_at and limitations. The fact carries exact source ID, observation time and literal
quote; EXTRACT_FIELDS/LINK_IDENTITY also carry resource-bound structured pointers.
RESOURCE_OWNERSHIP requires LINK_IDENTITY. LITERAL_FIELDS, RETENTION_OPERANDS, DATA_FLOW and
RESTORE_PERMISSION require EXTRACT_FIELDS with explicit canonical field pointers. EXPLICIT_STATE
and NEGATIVE_SCOPE require REUSE_DIRECT; negative scope cannot be broadened by interpretation.
Historical identity and unsupported natural-language conditions remain hypotheses: no new
certificate type for them. Never equate omitted fields with explicit null or global coverage.
Individual steps are verified independently. Missing steps do not invalidate a supported step,
but an incomplete audit plan cannot be promoted. Final status and serialization stay verified.
Keep the final response concise enough for the existing output-token budget. Do not duplicate
existing readbacks in facts and certificates. Use empty facts/certificates when nothing is new;
at most eight concise ledger entries, four investigation goals, and brief explanations.
"""


def blind_context(tools):
    users = tools.graph.resolve("email", tools.request.email, tools.request.audit_at)
    ownership = tools.graph.ownership(tools.store, tools.request.audit_at)
    keys = {k for k, v in ownership.items() if users and set(v) == set(users)}
    sources = [o for o in tools.store.observations if o.admissible(tools.request.audit_at)
               and (o.system_id, o.resource_id) in keys]
    sources.sort(key=lambda o: (o.observed_at, o.observation_id), reverse=True)
    return {"case_id": tools.request.case_id, "request": tools.request.request_text,
        "email": tools.request.email, "audit_at": tools.request.audit_at.isoformat(),
        "identity": tools.trace_identity(), "policy_definitions": tools.policy.rules,
        "proof_goals": ["authorization", "historical identity", "ownership", "state and PII coverage",
                        "retention conditions", "replicas and recreation", "complete remediation and verification"],
        "source_index": [{"observation_id": o.observation_id, "evidence_id": o.source_id,
            "file_id": o.file_id, "source_kind": o.kind,
            "inspect_source_available": bool(o.file_id),
            "system_id": o.system_id, "resource_id": o.resource_id,
            "observed_at": o.observed_at.isoformat(), "captured_at": o.captured_at.isoformat()}
            for o in sources[:24]],
        "coverage": {"total_count": len(sources), "shown_count": min(24, len(sources)),
            "truncated": len(sources) > 24,
            "retrieval": "Page search_evidence using supplied exact identifiers/resources; index is not exhaustive proof."}}


def grounded(proposal, tools):
    """Validate typed claims first; only original-source-derived facts can enter a clone."""
    validate_json(proposal, SCHEMA)
    facts = list(proposal["facts"])
    certificates = []
    for cert in proposal["proof_certificates"]:
        fact = cert["fact"]
        try:
            source = next((o for o in tools.store.observations if o.observation_id == fact["observation_id"]), None)
            if source is None or timestamp(cert["captured_at"]) != source.captured_at:
                raise InputError("CERTIFICATE_CAPTURE_NOT_ORIGINAL")
            if not fact["quote"].strip() or fact["quote"] not in raw_text(source):
                raise InputError("CERTIFICATE_SOURCE_SPAN_NOT_EXACT")
            users = tools.graph.resolve("email", tools.request.email, tools.request.audit_at)
            if users != {cert["subject_user_id"]}:
                raise InputError("CERTIFICATE_SUBJECT_NOT_EXACT")
            kind, interpretation = cert["claim_type"], fact["interpretation"]
            expected = "LINK_IDENTITY" if kind == "RESOURCE_OWNERSHIP" else (
                "REUSE_DIRECT" if kind in {"EXPLICIT_STATE", "NEGATIVE_SCOPE"} else "EXTRACT_FIELDS")
            if interpretation != expected:
                raise InputError("CERTIFICATE_INTERPRETATION_MISMATCH")
            names = set(fact["attributes"].get("field_pointers", {}))
            required = {"RETENTION_OPERANDS": {"retention_until", "retained_until", "hold_active"},
                        "DATA_FLOW": {"enabled"}, "RESTORE_PERMISSION": {"restore_allowed", "deletion_block"}}
            if kind in required and not names.intersection(required[kind]):
                raise InputError("CERTIFICATE_LITERAL_OPERAND_REQUIRED")
            if kind == "LITERAL_FIELDS" and not names:
                raise InputError("CERTIFICATE_LITERAL_FIELDS_REQUIRED")
            if kind == "DATA_FLOW" and fact["category"] != "DATA_FLOW":
                raise InputError("CERTIFICATE_CATEGORY_MISMATCH")
            if kind == "RESTORE_PERMISSION" and fact["category"] != "BACKUP_ARCHIVE":
                raise InputError("CERTIFICATE_CATEGORY_MISMATCH")
            if kind == "NEGATIVE_SCOPE" and source.kind != "scoped_negative":
                raise InputError("CERTIFICATE_NEGATIVE_SCOPE_NOT_DECLARED")
            if kind == "EXPLICIT_STATE" and observed_state(source) is None:
                raise InputError("CERTIFICATE_STATE_UNPROVEN")
            index = len(facts); facts.append(fact)
            certificates.append({"claim_type": kind, "fact_index": index, "validation": "PENDING",
                "observation_id": source.observation_id, "evidence_id": source.source_id,
                "captured_at": source.captured_at.isoformat(), "original_scope": source.scope,
                "literal_fields_present": sorted(actual_fields(source)),
                "coverage_limitations": "Only original scope and explicitly present fields; omitted fields remain unknown"})
        except (InputError, ValueError) as exc:
            certificates.append({"claim_type": cert["claim_type"], "validation": "REJECTED", "reason": str(exc)})
    # Existing fact schema bounds remain enforced, even with certificates.
    if len(facts) > 24:
        raise InputError("CERTIFICATE_COMBINED_FACT_LIMIT")
    combined = {k: proposal[k] for k in PROPOSAL_SCHEMA["properties"]}; combined["facts"] = facts
    updates, results = ground_proposal(combined, tools)
    by_index = {r["fact_index"]: r for r in results}
    for cert in certificates:
        if cert["validation"] == "PENDING":
            result = by_index[cert["fact_index"]]
            cert.update(validation=result["validation"], reason=result.get("reason"),
                        proof_delta=result.get("proof_delta"))
    return updates, results, certificates


def verify(proposal, tools):
    """Check source claims, per-resource policy, per-step proof and whole known scope.

    Reuses source reconstruction and policy primitives, never baseline verdict/step equality.
    Conservative coverage blockers cannot be overridden by model commentary.
    """
    updates, facts, certificates = grounded(proposal, tools)
    local = apply_grounded_updates(tools.store, updates, tools.request.audit_at) if updates else tools.store
    graph = tools.graph.fork(); at = tools.request.audit_at
    users = graph.resolve("email", tools.request.email, at)
    authorization = authorize(tools.request.request_text).authorized
    ownership = graph.ownership(local, at)
    keys = {k for k, owners in ownership.items() if users and set(owners).intersection(users)}
    blockers = []
    if authorization is None or (authorization is True and len(users) != 1):
        blockers.append("AUTHORIZATION_OR_IDENTITY_UNPROVEN")
    if authorization is True and not keys:
        blockers.append("NO_GROUNDED_RESOURCE_LINK")
    if any(len(ownership[k]) != 1 for k in keys):
        blockers.append("AMBIGUOUS_RESOURCE_OWNERSHIP")
    from .solver import scope_negatives, profile_scope_proofs
    observations = [o for uid in users for o in graph.observations_for_user(uid, local, at)]
    observations += scope_negatives(local, keys, at)
    resources, state_issues = reconstruct(observations, at)
    blockers += [i["code"] for i in state_issues]
    if any(i.get("severity") == "error" for i in local.issues):
        blockers.append("INGESTION_COVERAGE_INCOMPLETE")
    obligations = []
    unsafe_keys = {key for key in keys if set(ownership[key]) != users or len(ownership[key]) != 1}
    for resource in resources:
        if resource.contradictions:
            blockers.append("DIRECT_STATE_CONTRADICTION")
            unsafe_keys.add((resource.system_id, resource.resource_id))
        if resource.evidence.scope.get("extraction") == "narrow_screen_adapter" and not any(
                users.intersection(graph.resolve(k, v, at)) for k, v in resource.evidence.identifiers):
            blockers.append("OCR_SUBJECT_LINK_UNCORROBORATED")
            unsafe_keys.add((resource.system_id, resource.resource_id))
        decision = tools.policy.decide(resource, at)
        if decision.issue:
            blockers.append(decision.issue)
        obligations.append((resource, decision))
    known = {(r.system_id, r.resource_id) for r in resources}
    if keys - known:
        blockers.append("KNOWN_RESOURCE_STATE_UNPROVEN")
    incomplete = any(d.finding for _, d in obligations)
    if authorization is True and not incomplete and not any(
            r.category in {"USER_PROFILE", "ACCOUNT_TOMBSTONE"} for r in resources):
        if len(users) != 1 or not profile_scope_proofs(local, at, graph, next(iter(users))):
            blockers.append("PRIMARY_SCOPE_UNPROVEN")
    required = []
    for resource, decision in obligations:
        for op in (decision.finding, decision.remediation, decision.verification):
            if op:
                phase, state = OPERATIONS[op]
                required.append({"phase": phase, "system_id": resource.system_id,
                    "resource_id": resource.resource_id, "operation": op, "state": state,
                    "evidence_id": resource.evidence.source_id if phase == "FINDING" or not incomplete else ""})
    rec = proposal["audit_recommendation"]
    reference_sources = {o.observation_id: o for o in [*local.observations, *observations]}
    reference_results = []
    for ref in rec["evidence_references"]:
        source = reference_sources.get(ref["observation_id"])
        reason = None
        if source is None or source.source_id != ref["evidence_id"]:
            reason = "UNKNOWN_OR_MISMATCHED_EVIDENCE"
        elif not source.admissible(at) or timestamp(ref["observed_at"]) != source.observed_at:
            reason = "EVIDENCE_TIME_NOT_ADMISSIBLE"
        elif (source.system_id, source.resource_id) not in keys:
            reason = "EVIDENCE_SUBJECT_SCOPE_UNPROVEN"
        reference_results.append({**ref, "validation": "REJECTED" if reason else "SOURCE_GROUNDED", "reason": reason})
        if reason: blockers.append(reason)
    proposed = rec["proposed_findings"] + rec["proposed_remediations"] + rec["proposed_verifications"]
    required_by_key = {tuple(s[k] for k in ("phase", "system_id", "resource_id", "operation", "state")): s for s in required}
    step_results = []; accepted_keys = set()
    for step in proposed:
        key = tuple(step[k] for k in ("phase", "system_id", "resource_id", "operation", "state"))
        expected = required_by_key.get(key)
        # Citation is checked against independent selected original-source proof, not baseline.
        reason = "RESOURCE_SOURCE_SCOPE_UNPROVEN" if (step["system_id"], step["resource_id"]) in unsafe_keys else (
            "OPERATION_STATE_MISMATCH" if OPERATIONS[step["operation"]] != (step["phase"], step["state"]) else (
            "NO_SOURCE_POLICY_OBLIGATION" if expected is None else
            "CITATION_NOT_INDEPENDENT_PROOF" if step["evidence_id"] != expected["evidence_id"] else
            "DUPLICATE_STEP" if key in accepted_keys else None))
        if reason is None:
            accepted_keys.add(key)
        step_results.append({"step": step, "validation": "REJECTED" if reason else "SOURCE_POLICY_GROUNDED", "reason": reason})
    missing = [s for k, s in required_by_key.items() if k not in accepted_keys]
    if authorization is False:
        required = []; missing = []
        status = "NOT_APPLICABLE"
        if proposed: blockers.append("NON_DELETION_HAS_STEPS")
    else:
        status = "INCOMPLETE" if incomplete else "COMPLETE"
    if authorization is True and not required:
        blockers.append("NO_REQUIRED_STATE_PROOF")
    intent = "NON_DELETION" if authorization is False else "DELETE" if authorization else "UNCERTAIN"
    if rec["request_intent"]["kind"] != intent or not rec["request_intent"]["quote"].strip() or rec["request_intent"]["quote"] not in tools.request.request_text:
        blockers.append("INTENT_NOT_SOURCE_ESTABLISHED")
    if rec["recommended_deletion_status"] != status:
        blockers.append("VERDICT_NOT_SUPPORTED_BY_OBLIGATIONS")
    rejected = any(r["validation"] == "REJECTED" for r in facts + certificates + step_results)
    complete = not blockers and not missing and not rejected
    steps = sorted(required, key=lambda s: order_key({**s, "step_no": 0}))
    steps = [{"step_no": n, **s} for n, s in enumerate(steps, 1)]
    return {"validation": "ACCEPTED" if complete else "REJECTED_OR_UNRESOLVED",
        "independent_status": status if not blockers else None, "canonical_steps": steps,
        "plan_scope_complete": complete, "issues": [{"code": c} for c in sorted(set(blockers))]
            + ([{"code": "MISSING_POLICY_OBLIGATIONS", "missing": missing}] if missing else [])
            + [{"code": r.get("reason") or "CLAIM_REJECTED"} for r in facts + certificates + step_results if r["validation"] == "REJECTED"],
        "certificate_validation": certificates, "fact_validation": facts, "step_validation": step_results,
        "evidence_validation": reference_results,
        "missing_obligations": missing, "authority": "Source/identity/time; per-resource policy; independent known-obligation coverage",
        "baseline_agreement_is_acceptance_rule": False}

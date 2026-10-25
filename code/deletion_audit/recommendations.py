"""Runtime AI audit recommendations, checked independently of model assertions."""
import json

from .contract import OPERATIONS, STEP_FIELDS, canonical
from .inputs import InputError, timestamp
from .proposals import PROPOSAL_SCHEMA, obj, string, validate_json, ground_proposal, apply_grounded_updates


def array(item, limit=32):
    return {"type": "array", "items": item, "maxItems": limit}


def proposed_step(phase):
    operations = [op for op, (p, _) in OPERATIONS.items() if p == phase]
    return obj({"phase": string(20, [phase]), "system_id": string(100), "resource_id": string(100),
        "operation": string(60, operations), "state": string(30, sorted({OPERATIONS[o][1] for o in operations})),
        "evidence_id": string(100, [""]) if phase == "REMEDIATION" else string(100)})


AUDIT_RECOMMENDATION = obj({
    "request_intent": obj({"kind": string(20, ["DELETE", "NON_DELETION", "UNCERTAIN"]),
        "target": string(30, ["ACCOUNT", "PERSONAL_DATA", "OTHER"]), "quote": string(700), "explanation": string(700)}),
    "investigation_goals": array(obj({"goal": string(), "system_id": string(100), "resource_id": string(100),
        "status": string(20, ["SATISFIED", "UNRESOLVED", "CONTRADICTED"])})),
    "investigated_resources": array(obj({"system_id": string(100), "resource_id": string(100),
        "policy_rule_id": string(100), "interpretation": string(700)})),
    "evidence_references": array(obj({"evidence_id": string(100), "observation_id": string(250),
        "observed_at": string(50), "scope": string(500)})),
    "unresolved_obligations": array(string(700)),
    "recommended_deletion_status": string(30, ["COMPLETE", "INCOMPLETE", "NOT_APPLICABLE", "UNRESOLVED"]),
    "verdict_justification": string(1500),
    "proposed_findings": array(proposed_step("FINDING")),
    "proposed_remediations": array(proposed_step("REMEDIATION")),
    "proposed_verifications": array(proposed_step("VERIFICATION")),
    "alternative_interpretations": array(string(700), 10), "confidence_rationale": string(1000)})

from .proof_ledger import LEDGER_ENTRY
AUDIT_RECOMMENDATION["properties"]["proof_ledger"] = array(LEDGER_ENTRY, 24)
AUDIT_RECOMMENDATION["required"].append("proof_ledger")
AUDIT_PROPOSAL_SCHEMA = obj({**PROPOSAL_SCHEMA["properties"], "audit_recommendation": AUDIT_RECOMMENDATION})

AUDIT_INSTRUCTIONS = """
You are responsible for a complete evidence-grounded AuditRecommendation as well as fact proposals.
Interpret request intent and its negation target; enumerate proof goals, investigate identity,
replicas, policy conditions, retained records, tombstones, backup permissions and recreation risks.
Recommend a verdict and complete finding/remediation/verification draft, never execute it.
Use internal UNRESOLVED when the evidence cannot establish a permitted verdict; it is not a CSV status.
Use the exact structured audit_recommendation schema. Each proposed step has six fields,
without step_no; the independent canonical planner numbers and orders accepted steps.
For INCOMPLETE all proposed remediation AND verification citations are empty; findings cite proof.
Never put the source that motivated future work into a future-work citation. DELETE policy
violations use REPORT_REMAINING_RECORD, not REPORT_EXPOSED_PII. Every proposed treatment
needs its corresponding future verification. Also verify every grounded compliant/retained
resource in an INCOMPLETE plan, with empty citations, including primary resources linked
from downstream records even if their current state is unknown. See baseline resource_keys.
COMPLETE verification cites current compliant proof. A missing primary link is not a violation.
Every evidence reference names an existing observation and its exact event timestamp.
Identity metadata/catalog claims establish links only, never resulting state. Stable subject
links prevent unsupported anonymization; blank omitted fields do not prove redaction.
Policy interpretation is a proposal: extract supporting literal fields with the existing fact
protocol when newly useful. The independent engine will reject unsupported conditions or plans.
Do not merely repeat the baseline verdict. Assess its obligations and scope, retrieve evidence
for gaps, identify contradictions, then explain agreement or disagreement concisely.
If a tool reveals a new useful identifier/resource/source, follow it on the next turn when budget
permits. Return final JSON when proof goals are answered or evidence is genuinely unavailable.
Do not waste calls on data that does not exist. Keep all uncertainty explicit.
Include a proof_ledger covering AUTHORIZATION, IDENTITY, OWNERSHIP, STATE, TREATMENT,
RECREATION, RETENTION and PLAN. Use concise entries with actual inspected observation IDs
and source references also listed in evidence_references. A source lead is not proof.
Coverage proven/violated describes the required obligation, not merely finding some data.
For STATE/TREATMENT, a dirty resource is violated. For PLAN, proven requires complete
independent scope. Record omitted fields, unknown retention deadlines and global copy
coverage as unresolved. Never claim an observation was tool-inspected unless returned.
Use empty system/resource for global questions, and unresolved when no scoped proof exists.
"""


def assess_recommendation(proposal, tools, trace=None):
    """Ground new facts, then recompute authorization/policy/plan from immutable sources.

    Model text never changes ownership, policy, verdict or the canonical step array.
    Facts have the existing independent checks and are applied only in a case clone.
    """
    from .solver import decide_case, scope_negatives
    validate_json(proposal, AUDIT_PROPOSAL_SCHEMA)
    facts_only = {k: proposal[k] for k in PROPOSAL_SCHEMA["properties"]}
    accepted, fact_results = ground_proposal(facts_only, tools)
    local = apply_grounded_updates(tools.store, accepted, tools.request.audit_at) if accepted else tools.store
    graph = tools.graph.fork()
    decision = decide_case(tools.request, local, graph, tools.policy)
    rec = proposal["audit_recommendation"]
    problems = []
    authorization = decision.diagnostic["authorization"]
    intent = "DELETE" if authorization is True else "NON_DELETION" if authorization is False else "UNCERTAIN"
    if rec["request_intent"]["kind"] != intent:
        problems.append({"code": "INTENT_NOT_INDEPENDENTLY_ESTABLISHED", "expected": intent})
    quote = rec["request_intent"]["quote"]
    if not quote.strip() or quote not in tools.request.request_text:
        problems.append({"code": "INTENT_QUOTE_NOT_LITERAL"})
    users = graph.resolve("email", tools.request.email, tools.request.audit_at)
    ownership = graph.ownership(local, tools.request.audit_at)
    scoped = scope_negatives(local, {key for key, owners in ownership.items() if set(owners) == set(users) and users},
                             tools.request.audit_at)
    reference_sources = {o.observation_id: o for o in [*local.observations, *scoped]}
    known = {(r["system_id"], r["resource_id"]): r for r in decision.diagnostic.get("resource_states", [])}
    for resource in rec["investigated_resources"]:
        key = resource["system_id"], resource["resource_id"]
        if len(users) != 1 or set(ownership.get(key, {})) != set(users):
            problems.append({"code": "RESOURCE_OWNERSHIP_UNPROVEN", "resource": list(key)})
        if key in known and resource["policy_rule_id"] != known[key]["rule_id"]:
            problems.append({"code": "POLICY_RULE_MISMATCH", "resource": list(key), "expected": known[key]["rule_id"]})
    evidence_results = []
    for ref in rec["evidence_references"]:
        source = reference_sources.get(ref["observation_id"])
        reason = None
        if source is None or source.source_id != ref["evidence_id"]:
            reason = "UNKNOWN_OR_MISMATCHED_EVIDENCE"
        elif not source.admissible(tools.request.audit_at):
            reason = "EVIDENCE_AFTER_CUTOFF_OR_UNDATED"
        else:
            try:
                if timestamp(ref["observed_at"]) != source.observed_at:
                    reason = "OBSERVATION_TIMESTAMP_MISMATCH"
            except InputError:
                reason = "OBSERVATION_TIMESTAMP_MISMATCH"
            key = source.system_id, source.resource_id
            if reason is None and (not source.resource_id or set(ownership.get(key, {})) != set(users) or not users):
                reason = "EVIDENCE_SUBJECT_SCOPE_UNPROVEN"
        evidence_results.append({**ref, "validation": "REJECTED" if reason else "SOURCE_GROUNDED", "reason": reason})
        if reason:
            problems.append({"code": reason, "observation_id": ref["observation_id"]})
    expected_status = decision.status or "UNRESOLVED"
    if rec["recommended_deletion_status"] != expected_status:
        problems.append({"code": "VERDICT_NOT_INDEPENDENTLY_ESTABLISHED", "expected": expected_status,
                         "recommended": rec["recommended_deletion_status"]})
    expected = decision.steps if decision.status else decision.diagnostic.get("grounded_partial_steps", [])
    expected = [{k: step[k] for k in STEP_FIELDS if k != "step_no"} for step in expected]
    given = rec["proposed_findings"] + rec["proposed_remediations"] + rec["proposed_verifications"]
    # Compare complete obligations, including canonical citations, as multisets.
    # Array numbering/order is the independent planner's responsibility.
    from collections import Counter
    wanted, supplied = Counter(map(canonical, expected)), Counter(map(canonical, given))
    if wanted != supplied:
        problems.append({"code": "PLAN_OBLIGATION_OR_CITATION_MISMATCH",
            "missing": [json.loads(k) for k in (wanted - supplied).elements()],
            "unsupported": [json.loads(k) for k in (supplied - wanted).elements()]})
    # Reject mislabeled operation/state even for an empty/partial expected plan.
    for step in given:
        if OPERATIONS[step["operation"]] != (step["phase"], step["state"]):
            problems.append({"code": "OPERATION_STATE_MISMATCH", "operation": step["operation"]})
    if decision.diagnostic["issues"] and not rec["unresolved_obligations"]:
        problems.append({"code": "UNRESOLVED_OBLIGATIONS_OMITTED", "issues": decision.diagnostic["issues"]})
    from dataclasses import replace
    from .proof_ledger import validate_ledger
    ledger, ledger_errors = validate_ledger(rec["proof_ledger"], replace(tools, store=local, graph=graph),
        decision, reference_sources, evidence_results, trace, wanted == supplied)
    problems += ledger_errors
    verdict = ("REJECTED" if problems else "UNRESOLVED" if decision.status is None else
               "ACCEPTED_WITH_UNRESOLVED_OBLIGATIONS" if not decision.diagnostic["plan_scope_complete"] else "ACCEPTED")
    grounded_findings = set(map(canonical, rec["proposed_findings"])) <= set(map(canonical, expected))
    components = {"intent": "ACCEPTED" if not any(i["code"].startswith("INTENT") for i in problems) else "REJECTED",
        "verdict": "ACCEPTED" if rec["recommended_deletion_status"] == decision.status and grounded_findings
            and (bool(rec["proposed_findings"]) if decision.status == "INCOMPLETE" else not problems) else
            "UNRESOLVED" if decision.status is None else "REJECTED",
        "complete_plan": "ACCEPTED" if wanted == supplied and decision.diagnostic["plan_scope_complete"] else "REJECTED_OR_UNRESOLVED"}
    return {"validation": verdict, "component_validation": components, "proof_ledger": ledger,
        "recommended_status": rec["recommended_deletion_status"],
        "independent_status": decision.status, "canonical_steps": decision.steps,
        "issues": problems, "evidence_validation": evidence_results,
        "fact_validation": fact_results, "new_fact_count": len(accepted),
        "plan_scope_complete": decision.diagnostic["plan_scope_complete"],
        "authority": "Independent source grounding, authorization, policy and canonical planner"}

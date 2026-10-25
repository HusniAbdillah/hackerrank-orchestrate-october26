"""First deterministic audit solver. Never reads or imports evaluation answers."""

import csv
import json
import re
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from datetime import datetime, timezone
from time import perf_counter

from .authorization import authorize
from .identity import IdentityGraph
from .ingestion import dataset_hashes, ingest
from .inputs import OUTPUT_FIELDS, InputError, load_evidence, load_requests, protect_output
from .observations import Observation, identifiers
from .parsers import COLLECTIONS
from .planner import plan
from .policy import Decision, Policy
from .state import ResourceState, reconstruct


def enrich(store):
    """Narrow business adapters on raw extracted facts, retaining original provenance."""
    extra = []
    by_file = {}
    for obs in store.observations:
        if obs.collection == "pdf_text":
            by_file.setdefault(obs.file_id, []).append(obs)
        if obs.collection == "contact_query_completed":
            context = obs.fields.get("_correlated_lookup", {})
            source = obs.fields.get("source", context.get("source"))
            if source == "legacy_contact_index":
                extra.append(replace(obs, observation_id=obs.observation_id + ":typed",
                                     category="SECONDARY_IDENTIFIER", kind="direct"))
    for pages in by_file.values():
        text = "\n".join(o.fields["text"] for o in pages)
        resources = {(o.system_id, o.resource_id) for o in pages if o.resource_id}
        if len(resources) == 1 and "COMPLIANCE JOURNAL - SIGNED RECORD EXTRACT" in text:
            source = next(o for o in pages if o.resource_id)
            subjects = [value for kind, value in identifiers(text) if kind == "user_id"]
            deadline = re.search(r"retain until\s+(\d{2} \w{3} \d{4}) (\d{2})\s+(\d{2}) UTC", text)
            if len(subjects) == 1 and deadline:
                until = datetime.strptime(" ".join(deadline.groups()), "%d %b %Y %H %M").replace(tzinfo=timezone.utc)
                extra.append(replace(source, observation_id=source.observation_id + ":journal",
                    category="SECURITY_AUDIT_LOG", kind="direct", system_id="security_service",
                    fields={"subject_reference": subjects[0], "retention_until": until.isoformat(), "document_text": text},
                    identifiers=identifiers({"subject_reference": subjects[0]})))
        if len(resources) == 1 and "uploader customer" in " ".join(text.casefold().split()):
            source = next(o for o in pages if o.resource_id)
            extra.append(replace(source, observation_id=source.observation_id + ":attachment",
                                 collection="customer_owned_document", category="SUPPORT_ATTACHMENT", kind="direct",
                                 fields={"document_text": text, "uploaded_by": "customer", "shared_attachment": False},
                                 identifiers=identifiers({"text": text})))
    store.add(extra)

    from .artifact_links import enrich_artifacts
    enrich_artifacts(store)


def scope_negatives(store, keys, at):
    """Project an exhaustive captured collection onto an already grounded resource ID."""
    extra = []
    scopes = {}
    for obs in store.observations:
        if not obs.admissible(at) or obs.file_id is None or obs.scope.get("agent_row_only"):
            continue
        table = obs.scope.get("table")
        if table and table != "snapshot_scope" and obs.kind != "missing_data":
            # A heterogeneous SQL export proves its rows, not an exhaustive
            # inventory of every origin service. Require declared service scope
            # before projecting other resources absent from that mixed table.
            if "decoded_record" in obs.fields and not any(
                row.get("origin_system") == obs.system_id for row in obs.scope.get("snapshot_scope", [])
            ):
                continue
            category = obs.category or COLLECTIONS.get(obs.collection, (None, None))[1]
            key = (obs.file_id, obs.system_id, obs.collection, table)
            entry = scopes.setdefault(key, {"source": obs, "category": category, "resources": set()})
            if obs.resource_id:
                entry["resources"].add(obs.resource_id)
        if obs.resource_id is None and obs.kind == "scoped_negative" and obs.scope.get("complete_collection"):
            scopes.setdefault((obs.file_id, obs.system_id, obs.collection, "collection"),
                              {"source": obs, "category": COLLECTIONS.get(obs.collection, (None, None))[1], "resources": set()})
    for system, resource in keys:
        # Only categories already established by this resource's admissible contents.
        categories = {o.category for o in store.for_resource(system, resource, at) if o.category}
        for entry in scopes.values():
            source, category = entry["source"], entry["category"]
            if source.system_id == system and category in categories and resource not in entry["resources"]:
                extra.append(replace(source, observation_id=f"{source.observation_id}:negative:{resource}",
                                     resource_id=resource, category=category, kind="scoped_negative",
                                     fields={"result": "NOT_FOUND", "predicate": "grounded resource absent from captured complete table"},
                                     identifiers=(), scope={**source.scope, "grounded_resource": resource,
                                                            "projected_negative": True}))
    return extra


def profile_scope_proofs(store, at, graph=None, user=None):
    """A declared empty account snapshot needs no invented per-user resource ID.

    This covers only the explicitly captured primary service. Known independent
    replicas and active flows still participate in reconstruction and policy.
    """
    proofs = [o for o in store.observations if o.admissible(at)
            and o.kind == "scoped_negative" and o.resource_id is None
            and o.category == "USER_PROFILE" and o.system_id == "account_service"
            and o.scope.get("complete_collection") is True
            and any(row.get("origin_system") == "account_service"
                    for row in o.scope.get("snapshot_scope", []))]
    if graph is not None and user is not None:
        inventories = {}
        for observation in store.observations:
            if (observation.admissible(at) and observation.category == "USER_PROFILE"
                and not observation.scope.get("agent_row_only")
                and observation.resource_id and observation.scope.get("table") == "customer_profiles"
                and any(r.get("origin_system") == "account_service" for r in observation.scope.get("snapshot_scope", []))):
                inventories.setdefault((observation.file_id, observation.observed_at), []).append(observation)
        for rows in inventories.values():
            # Every row in the declared primary inventory must have a unique exact
            # subject binding to someone else. Anonymous/ambiguous rows cannot certify
            # absence, and no resource ID is synthesized for the missing subject.
            owners = [{uid for kind, value in row.identifiers for uid in graph.resolve(kind, value, at)} for row in rows]
            if all(len(subjects) == 1 and user not in subjects for subjects in owners):
                source = rows[0]
                proofs.append(replace(source, observation_id=source.observation_id + ":subject_scope",
                    resource_id=None, kind="scoped_negative", fields={"predicate": "all captured profile rows belong exactly to other subjects"},
                    scope={**source.scope, "examined_observations": [r.observation_id for r in rows],
                           "excluded_subject": user, "scope_proof": "declared_inventory_exact_subject_filter"}))
    return proofs


def audit(request, store, graph, policy):
    authorization = authorize(request.request_text)
    users = graph.resolve("email", request.email, request.audit_at)
    diagnostic = {"case_id": request.case_id, "authorization": authorization.authorized,
                  "authorization_reason": authorization.reason, "identity": sorted(users),
                  "issues": [], "gap_classification": None, "abstained": False}
    if authorization.authorized is False:
        diagnostic["gap_classification"] = "justified_empty" if not any(
            user in values for values in graph.ownership(store, request.audit_at).values() for user in users
        ) else None
        return "NOT_APPLICABLE", [], diagnostic
    if authorization.authorized is None or len(users) != 1:
        diagnostic["issues"].append({"code": "UNKNOWN_INTENT" if authorization.authorized is None else "IDENTITY_GAP"})
        diagnostic.update(abstained=True, gap_classification="identity_gap" if len(users) != 1 else "unresolved")
        return "INCOMPLETE", [], diagnostic
    user = next(iter(users))
    ownership = graph.ownership(store, request.audit_at)
    keys = {key for key, subjects in ownership.items() if user in subjects}
    observations = graph.observations_for_user(user, store, request.audit_at)
    diagnostic["resource_keys"] = [list(key) for key in sorted(keys)]
    if not keys:
        diagnostic.update(abstained=True, gap_classification="unresolved")
        diagnostic["issues"].append({"code": "NO_GROUNDED_RESOURCE_LINK", "detail": "No admissible subject-to-resource link; suffix/timing joins prohibited"})
        return "INCOMPLETE", [], diagnostic
    for key in sorted(keys):
        if len(ownership[key]) > 1:
            diagnostic["issues"].append({"code": "AMBIGUOUS_RESOURCE_OWNERSHIP", "resource": list(key)})
    observations += scope_negatives(store, keys, request.audit_at)
    for issue in store.issues:
        if issue.get("severity") == "error":
            diagnostic["issues"].append({"code": "INGESTION_COVERAGE_INCOMPLETE", "source": issue})
    resources, issues = reconstruct(observations, request.audit_at)
    diagnostic["issues"] += issues
    decisions = []
    for resource in resources:
        if len(ownership.get((resource.system_id, resource.resource_id), {})) > 1:
            decision = Decision("", None, None, None, "AMBIGUOUS_RESOURCE_TREATMENT_WITHHELD")
        elif resource.evidence.scope.get("extraction") == "narrow_screen_adapter" and not any(
            user in graph.resolve(kind, value, request.audit_at) for kind, value in resource.evidence.identifiers
        ):
            decision = Decision("", None, None, None, "OCR_SUBJECT_LINK_UNCORROBORATED")
        else:
            decision = policy.decide(resource, request.audit_at)
        decisions.append(decision)
    for resource, decision in zip(resources, decisions):
        if decision.issue:
            diagnostic["issues"].append({"code": decision.issue, "resource_id": resource.resource_id})
        if resource.contradictions:
            diagnostic["issues"].append({"code": "DIRECT_STATE_CONTRADICTION", "resource_id": resource.resource_id,
                                          "details": list(resource.contradictions)})
    usable = [(r, d) for r, d in zip(resources, decisions) if d.verification]
    if any(d.finding for _, d in usable):
        # An explicit search source link grounds a profile that must be checked after
        # cleanup, even when it supplies no readback of that profile's current state.
        known_states = {(r.system_id, r.resource_id) for r in resources}
        for source in observations:
            for key in source.related_resources:
                if key in keys and key not in known_states and key[0] == "account_service":
                    usable.append((ResourceState(*key, "USER_PROFILE", "UNKNOWN", source, (source,)),
                                   Decision(policy.rules["USER_PROFILE"]["rule_id"], None, None, "VERIFY_RECORD_ABSENT")))
                    known_states.add(key)
    status, steps = plan([r for r, d in usable], [d for r, d in usable])
    scope_proofs = profile_scope_proofs(store, request.audit_at, graph, user)
    diagnostic["scope_proofs"] = [{"observation_id": o.observation_id, "evidence_id": o.source_id,
                                  "observed_at": o.observed_at.isoformat(), "scope": o.scope,
                                  "limitation": "Declared primary service only; does not clear independent replicas"}
                                 for o in scope_proofs]
    if status == "COMPLETE" and not any(r.category in {"USER_PROFILE", "ACCOUNT_TOMBSTONE"}
                                        for r, _ in usable) and not scope_proofs:
        diagnostic["issues"].append({"code": "PRIMARY_PROFILE_VERIFICATION_UNGROUNDED",
                                      "detail": "Known retained/downstream resources do not prove the account's required final state"})
    diagnostic["resource_states"] = [{"system_id": r.system_id, "resource_id": r.resource_id,
        "category": r.category, "state": r.state, "evidence_id": r.evidence.source_id,
        "observation_id": r.evidence.observation_id, "rule_id": d.rule_id,
        "copies": [{"observation_id": o.observation_id, "scope": o.scope} for o in r.copies]}
        for r, d in zip(resources, decisions)]
    if diagnostic["issues"] or not steps:
        # The output vocabulary has no UNKNOWN. Emit a visible abstention rather than
        # fabricated findings or a COMPLETE claim. Validator failures remain observable.
        if status == "COMPLETE":
            # Preserve only already grounded partial checks for an explicitly
            # separate candidate workflow. They do not establish full completion.
            diagnostic["grounded_partial_steps"] = steps
            status = "INCOMPLETE"
            steps = []
            diagnostic["abstained"] = True
    return status, steps, diagnostic


@dataclass
class AuditDecision:
    status: str | None
    steps: list[dict]
    diagnostic: dict


def decide_case(request, store, graph, policy) -> AuditDecision:
    """Public decision boundary: unresolved proof is None, never a guessed verdict."""
    from .sufficiency import explain_uncertainty
    status, steps, diagnostic = audit(request, store, graph, policy)
    status = None if diagnostic["abstained"] else status
    diagnostic.update(submission_status=status, verdict_resolved=status is not None)
    diagnostic.update(explain_uncertainty(diagnostic, request, store, graph))
    return AuditDecision(status, steps, diagnostic)


def solve(dataset: Path, split: str, output: Path, extractions: Path | None = None,
          submission_output: Path | None = None, ai=None) -> dict:
    protect_output(output, dataset)
    if extractions and output.resolve().is_relative_to(extractions.resolve()):
        raise InputError("Prediction output must not overwrite the extraction cache")
    if submission_output:
        protect_output(submission_output, dataset, output)
        if extractions and submission_output.resolve().is_relative_to(extractions.resolve()):
            raise InputError("Submission output must not overwrite the extraction cache")
        if split != "full":
            raise InputError("Submission publication requires the full request split")
    start = perf_counter()
    before = dataset_hashes(dataset)
    store = ingest(dataset)
    enrich(store)
    screen_extractions = []
    if extractions is not None:
        from .extractions import apply_cached_screens
        screen_extractions = apply_cached_screens(store, extractions)
    graph, policy = IdentityGraph.load(dataset), Policy.load(dataset)
    requests = load_requests(dataset, split)
    rows, cases = [], []
    for cid, request in sorted(requests.items()):
        decision = decide_case(request, store, graph, policy)
        if ai is not None:
            from .investigator import AuditTools
            accepted = ai.investigate(AuditTools(request, store, graph, policy), decision.diagnostic)
            if accepted:
                from .proposals import apply_grounded_updates
                local = apply_grounded_updates(store, accepted, request.audit_at)
                updated = decide_case(request, local, graph.fork(), policy)
                updated.diagnostic["baseline_status"] = decision.status
                updated.diagnostic["accepted_ai_observations"] = [o.observation_id for o in accepted]
                old_issues = {i["code"] for i in decision.diagnostic["issues"]}
                new_issues = {i["code"] for i in updated.diagnostic["issues"]}
                updated.diagnostic["ai_effects"] = {
                    "status_changed": updated.status != decision.status,
                    "steps_changed": updated.steps != decision.steps,
                    "resolved_issue_codes": sorted(old_issues - new_issues),
                    "introduced_issue_codes": sorted(new_issues - old_issues),
                    "resource_links_added": sorted(set(map(tuple, updated.diagnostic["resource_keys"])) -
                                                   set(map(tuple, decision.diagnostic["resource_keys"]))) }
                decision = updated
        rows.append({"case_id": cid, "deletion_status": decision.status or "", "steps_json": json.dumps(decision.steps, separators=(",", ":"))})
        cases.append(decision.diagnostic)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    from .contract import validate
    validation = validate(output, requests, load_evidence(dataset)).report()
    after = dataset_hashes(dataset)
    submission_ready = validation["valid"] and before == after and all(c["plan_scope_complete"] for c in cases)
    publication = {"requested": str(submission_output) if submission_output else None,
                   "published": False, "eligible": submission_ready}
    if submission_output and submission_ready:
        import tempfile
        submission_output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=submission_output.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(output.read_bytes())
        try:
            temporary.replace(submission_output)
            publication["published"] = True
        finally:
            temporary.unlink(missing_ok=True)
    elif submission_output:
        publication["reason"] = "Unresolved verdicts, incomplete proof/plan scope, or contract/integrity failures; existing submission preserved"
    return {"kind": "audit_solver_run", "split": split, "prediction_file": str(output),
            "request_count": len(requests), "prediction_count": len(rows),
            "status_counts": dict(Counter(row["deletion_status"] or "UNRESOLVED" for row in rows)),
            "abstentions": sum(c["abstained"] for c in cases), "cases": cases,
            "issue_counts": dict(Counter(i["code"] for c in cases for i in c["issues"])),
            "resource_link_gap_cases": [{"case_id": c["case_id"], "classification": c["gap_classification"]}
                                        for c in cases if c["gap_classification"]],
            "validation": validation,
            "contract_valid_rows": (0 if any(i["case_id"] is None for i in validation["issues"])
                                    else len(rows) - len({i["case_id"] for i in validation["issues"]})),
            "unresolved_cases": sum(not c["verdict_resolved"] for c in cases),
            "uncertainty_counts": dict(Counter(cause for c in cases for cause in c["uncertainty_causes"])),
            "screen_extractions": screen_extractions,
            "incomplete_plan_scope_cases": sum(not c["plan_scope_complete"] for c in cases),
            "submission": publication,
            "ingestion_issues": store.issues,
            "pending_multimodal": [f for f in store.files if f["status"] == "pending_multimodal"],
            "uncategorized_readbacks": [o.observation_id for o in store.observations
                                        if o.kind == "direct" and not o.category],
            "typed_readback_adapters": [{"original_observation": o.observation_id.rsplit(":typed", 1)[0],
                                         "category": o.category, "basis": "correlated legacy_contact_index source"}
                                        for o in store.observations if o.observation_id.endswith(":typed")],
            "ai_investigations": ai.events if ai is not None else [],
            "model_usage": ai.ledger.summary() if ai is not None else {"calls": 0, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0},
            "model_call_records": ai.ledger.records if ai is not None else [],
            "runtime_seconds": perf_counter() - start,
            "dataset_integrity": {"unchanged": before == after, "file_count": len(after)}}

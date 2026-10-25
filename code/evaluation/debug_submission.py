"""Source-grounded case matrix and policy obligation ledger; no reference answers read."""
import argparse
import json
import re
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.extractions import apply_cached_screens
from deletion_audit.identity import IdentityGraph
from deletion_audit.ingestion import ingest
from deletion_audit.inputs import load_requests, protect_output
from deletion_audit.policy import Policy
from deletion_audit.solver import decide_case, enrich, scope_negatives
from deletion_audit.state import reconstruct, observed_state


def diagnose(dataset, before, extractions=None, include_file_context=False):
    store = ingest(dataset); enrich(store)
    if extractions:
        apply_cached_screens(store, extractions)
    graph, policy = IdentityGraph.load(dataset), Policy.load(dataset)
    requests = load_requests(dataset, "full")
    rows = []
    for previous in before["cases"]:
        if not previous["issues"]:
            continue
        request = requests[previous["case_id"]]
        decision = decide_case(request, store, graph, policy)
        ownership = graph.ownership(store, request.audit_at)
        users = graph.resolve("email", request.email, request.audit_at)
        keys = {key for key, owners in ownership.items() if users.intersection(owners)}
        candidates = {}
        for key in keys:
            for observation in store.by_resource.get(key, []):
                candidates[observation.observation_id] = observation
        # Include future exact-identifier leads without admitting them as evidence.
        for uid in users:
            for version in graph.versions_for_user(uid, request.audit_at):
                for observation in store.by_identifier.get((version.kind, version.value), []):
                    candidates[observation.observation_id] = observation
        # Literal catalog aliases can occur in image/PDF context without resource IDs.
        aliases = set()
        for observation in candidates.values():
            if observation.fields.get("event_type") == "LINK_RESOURCE_IDENTITY":
                aliases.update(re.findall(r"\(([^()]+)\)", observation.fields.get("details", "")))
        for observation in store.observations:
            if observation.collection in {"ocr_text", "pdf_text"} and any(
                    alias in observation.fields.get("text", "") for alias in aliases):
                candidates[observation.observation_id] = observation
        observations = graph.observations_for_user(next(iter(users)), store, request.audit_at) if len(users) == 1 else []
        observations += scope_negatives(store, keys, request.audit_at)
        for observation in observations:
            candidates[observation.observation_id] = observation
        if include_file_context:
            files = {o.file_id for o in candidates.values() if o.file_id and o.admissible(request.audit_at)}
            for observation in store.observations:
                if observation.file_id in files:
                    candidates[observation.observation_id] = observation
        resources, _ = reconstruct(observations, request.audit_at)
        selected = {o.observation_id for resource in resources for o in resource.copies}
        candidate_rows = []
        for observation in sorted(candidates.values(), key=lambda o: (o.captured_at, o.observation_id)):
            reasons = []
            if observation.captured_at > request.audit_at: reasons.append("FILE_NOT_AVAILABLE_AT_CUTOFF")
            if observation.observed_at is None: reasons.append("OBSERVATION_TIME_UNKNOWN")
            elif observation.observed_at > request.audit_at: reasons.append("EVENT_AFTER_CUTOFF")
            if not reasons:
                unlinked = observation.resource_id and (observation.system_id, observation.resource_id) not in keys
                reasons.append("NO_EXACT_SUBJECT_OWNERSHIP_LINK" if unlinked else
                    "SELECTED_COPY_STATE" if observation.observation_id in selected else
                    "ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA" if observation.kind == "reported_claim" else
                    "SCOPED_CONTEXT_NOT_DIRECT_STATE" if observed_state(observation) is None else
                    "ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE")
            candidate_rows.append({"observation": observation.to_dict(), "admissible": observation.admissible(request.audit_at),
                                   "state": observed_state(observation), "acceptance_or_exclusion": reasons})
        ledger = []
        for resource in resources:
            obligation = policy.decide(resource, request.audit_at)
            required = [op for op in (obligation.finding, obligation.remediation, obligation.verification) if op]
            actual = [step for step in decision.steps if (step["system_id"], step["resource_id"]) ==
                      (resource.system_id, resource.resource_id)]
            blocked = [i["code"] for i in decision.diagnostic["issues"] if i.get("resource_id") == resource.resource_id]
            if decision.status is None:
                blocked.append("CASE_VERDICT_UNRESOLVED")
            ledger.append({"system_id": resource.system_id, "resource_id": resource.resource_id,
                "category": resource.category, "state": resource.state, "policy": asdict(obligation),
                "source_id": resource.evidence.source_id, "source_observation": resource.evidence.observation_id,
                "copy_observations": [o.observation_id for o in resource.copies], "required_operations": required,
                "emitted_steps": actual, "blocked_by": blocked,
                "withheld_operations": required if blocked else [],
                "missing_operations": [] if blocked else sorted(set(required)-{s["operation"] for s in actual})})
        rows.append({"case_id": request.case_id, "request": request.request_text, "email": request.email,
            "audit_at": request.audit_at.isoformat(), "original_abstention": previous["abstained"],
            "previous_issues": previous["issues"], "current_status": decision.status,
            "current_diagnostic": decision.diagnostic,
            "identity_versions": [{**asdict(v), "known_at": v.known_at.isoformat(),
                "valid_from": v.valid_from.isoformat() if v.valid_from else None,
                "valid_to": v.valid_to.isoformat() if v.valid_to else None}
                for uid in users for v in graph.versions_for_user(uid, request.audit_at)],
            "ownership_links": [{"system_id": key[0], "resource_id": key[1], "owners": ownership[key]} for key in sorted(keys)],
            "candidate_observations": candidate_rows, "obligation_ledger": ledger})
    return {"baseline_unresolved": sum(c["abstained"] for c in before["cases"]),
            "baseline_decided_with_issues": sum(bool(c["issues"]) and not c["abstained"] for c in before["cases"]),
            "cases": rows, "note": "Every original gap case is included. Post-cutoff candidates are diagnostic leads only. Ledger requirements are deterministic policy obligations, never golden answers."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[2]/"dataset")
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--extractions", type=Path)
    parser.add_argument("--include-file-context", action="store_true", help="Include anonymous/other-subject rows from relevant admissible files as rejected join candidates")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    protect_output(args.output, args.dataset, args.before)
    report = diagnose(args.dataset, json.loads(args.before.read_text()), args.extractions, args.include_file_context)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"original_unresolved": report["baseline_unresolved"], "original_incomplete_plans": report["baseline_decided_with_issues"], "cases_examined": len(report["cases"])}))

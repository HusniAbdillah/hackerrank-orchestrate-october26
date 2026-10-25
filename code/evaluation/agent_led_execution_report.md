# Actual runtime AI audit investigations

Generated from recorded application runs, not a scripted demonstration. No hidden chain-of-thought is logged.
The model chooses tools and recommends intent/verdict/plan; independent source, cutoff, policy and planner checks retain final authority.
Agreement with the baseline is not an accuracy gain. Unresolved/global scope questions are retained, not promoted into facts.

## agent_led/informed_run

Request count: 32

Usage: `{"by_model": {}, "cache_hits": 1, "calls": 0, "errors": 0, "estimated_cost_usd": 0, "input_tokens": 0, "limits": {"max_calls": 0, "max_cost_usd": 0.0}, "output_tokens": 0, "usage_missing_calls": 0}`

Case execution counts: `{"cached": 1, "changed_output": 0, "events": 32, "live_called": 0, "recommendation_results": {"REJECTED": 1}, "recommendations": 1, "selected": 1, "skipped_by_reason": {"SKIPPED_PILOT_SELECTION": 31}}`

### case_29

Provider/model: deepseek/deepseek-flash; execution: CACHE_HIT.

Model verdict: **INCOMPLETE**; independent result: **REJECTED**.

Component checks: `{"complete_plan": "REJECTED_OR_UNRESOLVED", "intent": "ACCEPTED", "verdict": "ACCEPTED"}`

Model's concise justification: Direct evidence shows an identifiable analytics profile and an active copying connector, both violating their policy obligations; search and support resources remain dirty per baseline. Remediation has not occurred, so the deletion is INCOMPLETE.

Uncertainty: Search index entry search_1993 must be deleted (rule_03) but content/identifiers unverified.; Support message support_5281 must be redacted (rule_05) but content unverified.; Legal retention lead evidence_27:page:2 not inspected; hold/retention status unknown.; Backup/archive copies and restore permissions not enumerated.

| Round | Model-selected tool | Arguments | Result / coverage |
| --- | --- | --- | --- |
| 1 | explain_policy | {"category": "ANALYTICS_PROFILE"} | {} |
| 1 | explain_policy | {"category": "DATA_FLOW"} | {} |
| 1 | explain_policy | {"category": "SEARCH_INDEX_ENTRY"} | {} |
| 1 | explain_policy | {"category": "SUPPORT_MESSAGE"} | {} |
| 2 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"} | {"total_count": 210, "shown_count": 210, "truncated": false, "file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4", "observed_at": "2026-09-15T11:38:32+00:00", "captured_at": "2026-09-15T11:44:55+00:00", "temporally_admissible": true} |
| 2 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"} | {"total_count": 247, "shown_count": 247, "truncated": false, "file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2", "observed_at": "2026-09-15T08:56:38+00:00", "captured_at": "2026-09-15T11:44:55+00:00", "temporally_admissible": true} |
| 2 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/search_service/index_queries/0"} | {"error": "TOOL_BUDGET_EXHAUSTED"} |
| 2 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/support_platform/tickets/3"} | {"error": "TOOL_BUDGET_EXHAUSTED"} |

Model-proposed plan (original citations, before any canonical synthesis):

| Phase | System | Resource | Operation | State | Evidence |
| --- | --- | --- | --- | --- | --- |
| FINDING | analytics_platform | analytics_5208 | REPORT_EXPOSED_PII | PRESENT | evidence_92 |
| FINDING | integration_service | data_flow_3827 | REPORT_ACTIVE_DATA_FLOW | ACTIVE | evidence_92 |
| FINDING | support_platform | support_5281 | REPORT_EXPOSED_PII | PRESENT | evidence_92 |
| REMEDIATION | integration_service | data_flow_3827 | DISABLE_DATA_FLOW | DISABLED |  |
| REMEDIATION | analytics_platform | analytics_5208 | ANONYMIZE_RECORD | ANONYMIZED |  |
| REMEDIATION | search_service | search_1993 | DELETE_RECORD | ABSENT |  |
| REMEDIATION | support_platform | support_5281 | REDACT_RECORD | REDACTED |  |
| VERIFICATION | integration_service | data_flow_3827 | VERIFY_DATA_FLOW_DISABLED | DISABLED |  |
| VERIFICATION | analytics_platform | analytics_5208 | VERIFY_RECORD_ANONYMIZED | ANONYMIZED |  |
| VERIFICATION | search_service | search_1993 | VERIFY_RECORD_ABSENT | ABSENT |  |
| VERIFICATION | support_platform | support_5281 | VERIFY_RECORD_REDACTED | REDACTED |  |

Independent errors: `[{"code": "PLAN_OBLIGATION_OR_CITATION_MISMATCH", "missing": [{"evidence_id": "evidence_92", "operation": "REPORT_REMAINING_RECORD", "phase": "FINDING", "resource_id": "search_1993", "state": "PRESENT", "system_id": "search_service"}], "unsupported": []}]`

Proof deltas: `{"duplicate": 2, "metadata_enrichment": 0, "new_field_proof": 0, "new_relationship": 0, "new_state_fact": 0}`

Corrections/validation attempts: 2.

Proof Ledger (model assertions independently checked, never treated as evidence):

| Goal | Required proof | Inspected observations | Accepted source references | Model coverage | Independent result | Prediction changed |
| --- | --- | --- | --- | --- | --- | --- |
| AUTHORIZATION:AUTH | Explicit deletion request |  | [] | proven | ACCEPTED | False |
| IDENTITY:ID | Stable subject link across both emails |  | [] | proven | ACCEPTED | False |
| OWNERSHIP:OWN-AN | Direct identifier link | evidence_92:/service_exports/analytics_platform/profiles/4 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"}] | proven | ACCEPTED | False |
| OWNERSHIP:OWN-INT | Direct identifier link | evidence_92:/service_exports/integration_service/connectors/2 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"}] | proven | ACCEPTED | False |
| STATE:STATE-AN | Attributable profile | evidence_92:/service_exports/analytics_platform/profiles/4 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"}] | violated | ACCEPTED | False |
| STATE:STATE-INT | Active copy path | evidence_92:/service_exports/integration_service/connectors/2 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"}] | violated | ACCEPTED | False |
| STATE:STATE-SRCH | Index entry presence |  | [] | unresolved | UNRESOLVED | False |
| STATE:STATE-SUP | Support message content |  | [] | unresolved | UNRESOLVED | False |
| TREATMENT:TREAT-AN | Anonymization applied | evidence_92:/service_exports/analytics_platform/profiles/4 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"}] | violated | ACCEPTED | False |
| TREATMENT:TREAT-INT | Data flow disabled | evidence_92:/service_exports/integration_service/connectors/2 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"}] | violated | ACCEPTED | False |
| RETENTION:RET | Hold/retention status |  | [] | unresolved | UNRESOLVED | False |
| RECREATION:REC | Copy path disabled | evidence_92:/service_exports/integration_service/connectors/2 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"}] | violated | ACCEPTED | False |
| PLAN:PLAN | Complete remediation+verification scope | evidence_92:/service_exports/analytics_platform/profiles/4, evidence_92:/service_exports/integration_service/connectors/2 | [{"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"}, {"evidence_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"}] | unresolved | UNRESOLVED | False |

## agent_led/blind_run

Request count: 32

Usage: `{"by_model": {"deepseek/deepseek-flash": {"calls": 4, "errors": 0, "estimated_cost_usd": 0.0191949, "input_tokens": 45023, "output_tokens": 4740}}, "cache_hits": 0, "calls": 4, "errors": 0, "estimated_cost_usd": 0.0191949, "input_tokens": 45023, "limits": {"max_calls": 4, "max_cost_usd": 0.35}, "output_tokens": 4740, "usage_missing_calls": 0}`

Case execution counts: `{"cached": 0, "changed_output": 0, "events": 32, "live_called": 1, "recommendation_results": {}, "recommendations": 0, "selected": 1, "skipped_by_reason": {"SKIPPED_PILOT_SELECTION": 31}}`

### case_29 — no validated final recommendation

Execution: **INVESTIGATION_FAILED**; error: `INVALID_FINAL_JSON`.
Partial model output is not repaired or counted as an accepted recommendation.

| Round | Tool | Arguments | Validation / result |
| --- | --- | --- | --- |
| 1 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4"} | {"observation_id": "evidence_92:/service_exports/analytics_platform/profiles/4", "file_id": "evidence_92", "shown_count": 210, "total_count": 210, "truncated": false} |
| 1 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/integration_service/connectors/2"} | {"observation_id": "evidence_92:/service_exports/integration_service/connectors/2", "file_id": "evidence_92", "shown_count": 247, "total_count": 247, "truncated": false} |
| 1 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/search_service/index_queries/0"} | {"observation_id": "evidence_92:/service_exports/search_service/index_queries/0", "file_id": "evidence_92", "shown_count": 297, "total_count": 297, "truncated": false} |
| 1 | inspect_source | {"file_id": "evidence_92", "observation_id": "evidence_92:/service_exports/support_platform/tickets/3"} | {"observation_id": "evidence_92:/service_exports/support_platform/tickets/3", "file_id": "evidence_92", "shown_count": 260, "total_count": 260, "truncated": false} |
| 2 | inspect_source | {"file_id": "activity_3544", "observation_id": "activity_3544"} | {"error": "SOURCE_NOT_IN_MANIFEST_OBSERVATIONS"} |
| 2 | inspect_source | {"file_id": "activity_3543", "observation_id": "activity_3543"} | {"error": "SOURCE_NOT_IN_MANIFEST_OBSERVATIONS"} |
| 2 | inspect_source | {"file_id": "activity_3542", "observation_id": "activity_3542"} | {"error": "SOURCE_NOT_IN_MANIFEST_OBSERVATIONS"} |
| 2 | inspect_source | {"file_id": "activity_3541", "observation_id": "activity_3541"} | {"error": "SOURCE_NOT_IN_MANIFEST_OBSERVATIONS"} |
| 3 | search_evidence | {"kind": "email", "value": "noah.f4380@outlook.com", "limit": 50} | {"shown_count": 0, "total_count": 0, "truncated": false} |
| 3 | search_evidence | {"kind": "email", "value": "noah.f438085@outlook.com", "limit": 50} | {"shown_count": 4, "total_count": 4, "truncated": false} |


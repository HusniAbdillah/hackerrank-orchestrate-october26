> Provenance: proof_quality/agent_sample_run is the CURRENT four-call Proof Ledger pilot. active_agent/agent_full_run is the HISTORICAL nine-call full audit from the preceding iteration. Neither is falsely attributed to the current root-output materialization, which used zero model calls after the stop decision. See usage_report.md.

# Actual runtime AI audit investigations

Generated from recorded application runs, not a scripted demonstration. No hidden chain-of-thought is logged.
The model chooses tools and recommends intent/verdict/plan; independent source, cutoff, policy and planner checks retain final authority.
Agreement with the baseline is not an accuracy gain. Unresolved/global scope questions are retained, not promoted into facts.

## proof_quality/agent_sample_run

Request count: 32

Usage: `{"by_model": {"deepseek/deepseek-flash": {"calls": 4, "errors": 0, "estimated_cost_usd": 0.025324199999999998, "input_tokens": 52098, "output_tokens": 8079}}, "cache_hits": 0, "calls": 4, "errors": 0, "estimated_cost_usd": 0.025324199999999998, "input_tokens": 52098, "limits": {"max_calls": 8, "max_cost_usd": 0.35}, "output_tokens": 8079, "usage_missing_calls": 0}`

Case execution counts: `{"cached": 0, "changed_output": 0, "events": 32, "live_called": 1, "recommendation_results": {"REJECTED": 1}, "recommendations": 1, "selected": 1, "skipped_by_reason": {"SKIPPED_DETERMINISTIC_SUFFICIENT": 4, "SKIPPED_PROOF_ROUTING:GROUNDED_UNAMBIGUOUS": 22, "SKIPPED_PROOF_ROUTING:NO_ACTIONABLE_ADMISSIBLE_PROOF_LEAD": 5}}`

### case_29

Provider/model: deepseek/deepseek-flash; execution: LIVE_COMPLETED.

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

## active_agent/agent_full_run

Request count: 518

Usage: `{"by_model": {"deepseek/deepseek-flash": {"calls": 9, "errors": 0, "estimated_cost_usd": 0.0375762, "input_tokens": 96938, "output_tokens": 7079}}, "cache_hits": 0, "calls": 9, "errors": 0, "estimated_cost_usd": 0.0375762, "input_tokens": 96938, "limits": {"max_calls": 12, "max_cost_usd": 0.45}, "output_tokens": 7079, "usage_missing_calls": 0}`

Case execution counts: `{"cached": 0, "changed_output": 0, "events": 518, "live_called": 3, "recommendation_results": {"ACCEPTED": 3}, "recommendations": 3, "selected": 3, "skipped_by_reason": {"DISABLED_OR_CASE_BUDGET_EXHAUSTED": 149, "SKIPPED_DETERMINISTIC_SUFFICIENT": 356, "SKIPPED_NON_DELETION": 10}}`

### case_113

Provider/model: deepseek/deepseek-flash; execution: LIVE_COMPLETED.

Model verdict: **COMPLETE**; independent result: **ACCEPTED**.

Component checks: `{"complete_plan": "ACCEPTED", "intent": "ACCEPTED", "verdict": "ACCEPTED"}`

Model's concise justification: The primary user profile account_6697 is directly observed absent (rows=0, 404) at 2026-08-22T08:41:31Z, satisfying rule_01. The only other grounded resource, audit_record_1127, is a security audit log within its retention period (retention_until 2032-06-30) and is therefore compliantly retained under rule_12, not a deletion violation. No grounded evidence shows a remaining deletable record, so the deletion is COMPLETE for the grounded scope; replica and backup coverage remain unresolved but are not contradicted.

Uncertainty: Independent replica coverage for user_111 across analytics, backup, search, export, integration and support systems was not retrieved.; Backup restore permission for account_6697 was not established.

| Round | Model-selected tool | Arguments | Result / coverage |
| --- | --- | --- | --- |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:17"} | {"total_count": 157, "shown_count": 157, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:17", "observed_at": "2026-08-22T08:41:31+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:15"} | {"total_count": 250, "shown_count": 250, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:15", "observed_at": "2026-08-22T08:39:55+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | explain_policy | {"category": "USER_PROFILE"} | {} |
| 1 | explain_policy | {"category": "SECURITY_AUDIT_LOG"} | {} |
| 2 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:16"} | {"total_count": 167, "shown_count": 167, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:16", "observed_at": "2026-08-22T08:41:31+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 2 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:14"} | {"total_count": 162, "shown_count": 162, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:14", "observed_at": "2026-08-22T08:39:55+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 2 | search_evidence | {"kind": "email", "value": "sami-elsayed@gmail.com", "limit": 50} | {"error": "TOOL_BUDGET_EXHAUSTED"} |

Model-proposed plan (original citations, before any canonical synthesis):

| Phase | System | Resource | Operation | State | Evidence |
| --- | --- | --- | --- | --- | --- |
| VERIFICATION | account_service | account_6697 | VERIFY_RECORD_ABSENT | ABSENT | evidence_88 |
| VERIFICATION | security_service | audit_record_1127 | VERIFY_RECORD_PRESENT | PRESENT | evidence_88 |

Independent errors: `[]`

Proof deltas: `{"duplicate": 2, "metadata_enrichment": 0, "new_field_proof": 0, "new_relationship": 0, "new_state_fact": 0}`

Corrections/validation attempts: 1.

### case_114

Provider/model: deepseek/deepseek-flash; execution: LIVE_COMPLETED.

Model verdict: **INCOMPLETE**; independent result: **ACCEPTED**.

Component checks: `{"complete_plan": "ACCEPTED", "intent": "ACCEPTED", "verdict": "ACCEPTED"}`

Model's concise justification: The request is an authorized deletion of the account and associated personal data. Two grounded resources remain non-compliant at the audit cutoff: search_5696 is a present search index entry subject to an unconditional DELETE rule, and support_3786 is an identifiable support message still holding the subject's plaintext email under a REDACT rule. Because neither obligation is satisfied, the deletion cannot be COMPLETE. Baseline scope proofs cover only the declared primary customer_profiles table and explicitly do not clear independent replicas, so remaining systems are treated as unresolved rather than compliant.

Uncertainty: No evidence retrieved for account_service, analytics_platform, backup_service, export_service, integration_service or security_service replicas of user_112; baseline scope proofs are declared-primary-only and do not clear independent replicas.; rule_05 retention condition for support_3786 (shared customer/agent/order context) is not evidenced, so REDACT vs DELETE treatment is not fully grounded.; Restore permission and retention windows for any backup/archive copies of the two grounded resources are unknown.

| Round | Model-selected tool | Arguments | Result / coverage |
| --- | --- | --- | --- |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:7"} | {"total_count": 234, "shown_count": 234, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:7", "observed_at": "2026-08-22T08:03:57+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:9"} | {"total_count": 244, "shown_count": 244, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:9", "observed_at": "2026-08-22T08:13:32+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | explain_policy | {"category": "SEARCH_INDEX_ENTRY"} | {} |
| 1 | explain_policy | {"category": "SUPPORT_MESSAGE"} | {} |
| 2 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:6"} | {"total_count": 162, "shown_count": 162, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:6", "observed_at": "2026-08-22T08:03:57+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 2 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:8"} | {"total_count": 173, "shown_count": 173, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:8", "observed_at": "2026-08-22T08:13:32+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 2 | search_evidence | {"kind": "email", "value": "oadeyemi1657@gmail.com", "limit": 50} | {"error": "TOOL_BUDGET_EXHAUSTED"} |

Model-proposed plan (original citations, before any canonical synthesis):

| Phase | System | Resource | Operation | State | Evidence |
| --- | --- | --- | --- | --- | --- |
| FINDING | search_service | search_5696 | REPORT_REMAINING_RECORD | PRESENT | evidence_88 |
| FINDING | support_platform | support_3786 | REPORT_EXPOSED_PII | PRESENT | evidence_88 |
| REMEDIATION | search_service | search_5696 | DELETE_RECORD | ABSENT |  |
| REMEDIATION | support_platform | support_3786 | REDACT_RECORD | REDACTED |  |
| VERIFICATION | search_service | search_5696 | VERIFY_RECORD_ABSENT | ABSENT |  |
| VERIFICATION | support_platform | support_3786 | VERIFY_RECORD_REDACTED | REDACTED |  |

Independent errors: `[]`

Proof deltas: `{"duplicate": 2, "metadata_enrichment": 0, "new_field_proof": 0, "new_relationship": 0, "new_state_fact": 0}`

Corrections/validation attempts: 1.

### case_115

Provider/model: deepseek/deepseek-flash; execution: LIVE_COMPLETED.

Model verdict: **INCOMPLETE**; independent result: **ACCEPTED**.

Component checks: `{"complete_plan": "ACCEPTED", "intent": "ACCEPTED", "verdict": "ACCEPTED"}`

Model's concise justification: Both grounded resources are governed by Always-DELETE rules (rule_01, rule_03). Deletion-worker activities from 2026-08-02 claim SUCCESS, but those are reported claims, not state proof. Direct observations on 2026-08-22 show account_1785 still returning a profile row and search_4417 still returning an index hit, both carrying the subject email. Therefore the deletion obligation is not satisfied and the status is INCOMPLETE. No evidence of legal hold or retention was found, and independent replicas were not evidenced, so those remain unresolved rather than assumed clear.

Uncertainty: Verify absence of account_1785 in account_service after remediation.; Verify absence of search_4417 in search_service after remediation.; Establish whether legal hold or retention obligations apply to user_113 records.; Establish whether backup, analytics, export, integration, security or support replicas hold user_113 data and whether they are in policy scope.

| Round | Model-selected tool | Arguments | Result / coverage |
| --- | --- | --- | --- |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:11"} | {"total_count": 221, "shown_count": 221, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:11", "observed_at": "2026-08-22T08:15:24+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | inspect_source | {"file_id": "evidence_88", "observation_id": "evidence_88:line:41"} | {"total_count": 234, "shown_count": 234, "truncated": false, "file_id": "evidence_88", "observation_id": "evidence_88:line:41", "observed_at": "2026-08-22T10:35:13+00:00", "captured_at": "2026-08-22T10:39:10+00:00", "temporally_admissible": true} |
| 1 | explain_policy | {"category": "USER_PROFILE"} | {} |
| 1 | explain_policy | {"category": "SEARCH_INDEX_ENTRY"} | {} |
| 2 | inspect_timeline | {"system_id": "account_service", "resource_id": "account_1785"} | {"total_count": 3, "shown_count": 3, "truncated": false, "returned_observation_ids": ["evidence_88:line:11", "evidence_88:line:10", "activity_3062"]} |
| 2 | inspect_timeline | {"system_id": "search_service", "resource_id": "search_4417"} | {"total_count": 3, "shown_count": 3, "truncated": false, "returned_observation_ids": ["evidence_88:line:41", "evidence_88:line:40", "activity_3073"]} |

Model-proposed plan (original citations, before any canonical synthesis):

| Phase | System | Resource | Operation | State | Evidence |
| --- | --- | --- | --- | --- | --- |
| FINDING | account_service | account_1785 | REPORT_REMAINING_RECORD | PRESENT | evidence_88 |
| FINDING | search_service | search_4417 | REPORT_REMAINING_RECORD | PRESENT | evidence_88 |
| REMEDIATION | account_service | account_1785 | DELETE_RECORD | ABSENT |  |
| REMEDIATION | search_service | search_4417 | DELETE_RECORD | ABSENT |  |
| VERIFICATION | account_service | account_1785 | VERIFY_RECORD_ABSENT | ABSENT |  |
| VERIFICATION | search_service | search_4417 | VERIFY_RECORD_ABSENT | ABSENT |  |

Independent errors: `[]`

Proof deltas: `{"duplicate": 2, "metadata_enrichment": 0, "new_field_proof": 0, "new_relationship": 0, "new_state_fact": 0}`

Corrections/validation attempts: 1.


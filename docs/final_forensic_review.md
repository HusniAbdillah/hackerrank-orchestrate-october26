# Final forensic correctness review

Scope: official participant statement, repository evidence contract, all 15 supplied rules, the eight unresolved cases, case_34, every non-exact sample, and actual agent traces. No organizer truth or reference answers enter prediction. Facts and interpretations are distinguished below.

## Exact contract passages and interpretation

> "A deletion is complete only when:"
> "records that must be retained remain available."

Source: problem_statement.md:24–29 (completeness conditions).

> "For `COMPLETE`, include only verification steps proving the current state. For `INCOMPLETE`, include findings, the complete remediation plan, and the checks that must pass afterward."

Source: problem_statement.md:91.

> "A record that should have been deleted still exists."

Source: problem_statement.md:105, meaning of REPORT_REMAINING_RECORD. The other allowed findings concern exposed identifiers, active data flows and active restore risk, not an unknown state.

> "Determine the resource state at `audit_at` using the available evidence. Reported workflow statuses and operation results are claims."

Source: problem_statement.md:124.

> "Proposed remediation and future verification steps for `INCOMPLETE` cases use an empty `evidence_id`."

Source: problem_statement.md:127.

> "Use only information available at or before `audit_at` when deciding the case. Evidence created later must not change the answer for that case."

Source: AGENTS.md:224, the repository input/time contract.

**Fact:** the output vocabulary has only COMPLETE, INCOMPLETE, NOT_APPLICABLE. There is no participant-authorized UNKNOWN row. **Interpretation:** absence of proof of COMPLETE is not proof of a policy violation. The official text supplies no epistemic fallback converting unknown state into INCOMPLETE, and requires evidence-backed findings and a representable plan. Consequently null/blank verdicts remain deliberately invalid diagnostic outputs, not an authorized submission workaround. No 518-row compliant submission can be claimed here.

**Fact:** rule_12 is conditional: "Record is within the supplied retention period", action RETAIN. rule_13 requires "A supplied legal hold is active". A proven violation of a proven retention obligation prevents COMPLETE, but the allowed remediation operations are only DISABLE_DATA_FLOW, BLOCK_RESTORE, DELETE_RECORD, REDACT_RECORD and ANONYMIZE_RECORD. There is no RESTORE_RECORD operation. Missing evidence of the condition does not create an actionable restore obligation.

## Case_34: corrected overbroad policy diagnosis

Subject user_11, haruka.s1838@zoho.com; audit_at 2026-09-27T13:00:00Z. evidence_01:line:59 directly reads audit_record_3753 (rows=1, integrity_check=passed) on 15 September. Its fields supply no retention_until/retained_until. The later evidence_93 inventory omits that resource, producing a negative scoped to the captured security table. It does not supply a deadline for that missing resource or prove absence from every possible copy. Retention dates on other rows cannot be assigned to it.

**Corrected conclusion:** a required-retention breach at audit_at is not established. The old REQUIRED_RETAINED_RECORD_MISSING diagnosis was overbroad; it is now RETENTION_CONDITION_UNPROVEN. The general guard also distinguishes an absent legal record without an explicitly active hold. A real absent record with a valid supplied deadline/active hold still reports REQUIRED_RETAINED_RECORD_MISSING; expiry/inactive-hold diagnostics are preserved. No restoration, deletion fallback or fabricated PRESENT verification is added.

case_34 remains independently INCOMPLETE because account_5762 and support_9538 are directly present and subject-linked. Its plan is still marked incomplete pending a resource-specific retention condition or official clarification. Removing the unproved retention diagnosis does not justify silently calling the entire plan complete.

## Eight-case forensic matrix

All candidate observations, original fields, timestamps, identity intervals, ownership links and accepted/excluded reasons are preserved in artifacts/final_forensic/evidence_matrix.json. The include-file-context option also lists anonymous and other-subject rows from relevant files; temporally available rows are not thereby attributed to this subject. Every such failed join is marked NO_EXACT_SUBJECT_OWNERSHIP_LINK. No false identity edge is admitted.

### case_46

**Subject/cutoff:** user_17 / `leonie.g9352@outlook.com` / `2026-03-11T08:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_01 (USER_PROFILE); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `account_service/account_6523`: ABSENT; `evidence_67` / `evidence_67:line:3`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| activity_3850 | EVENT_AFTER_CUTOFF=1; FILE_NOT_AVAILABLE_AT_CUTOFF=1 |
| activity_4011 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| evidence_01 | EVENT_AFTER_CUTOFF=11; FILE_NOT_AVAILABLE_AT_CUTOFF=11 |
| evidence_27 | EVENT_AFTER_CUTOFF=1; FILE_NOT_AVAILABLE_AT_CUTOFF=1 |
| evidence_63 | ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE=1; NO_EXACT_SUBJECT_OWNERSHIP_LINK=17; SCOPED_CONTEXT_NOT_DIRECT_STATE=8 |
| evidence_66 | ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE=2; NO_EXACT_SUBJECT_OWNERSHIP_LINK=23; SCOPED_CONTEXT_NOT_DIRECT_STATE=8 |
| evidence_67 | SCOPED_CONTEXT_NOT_DIRECT_STATE=3; SELECTED_COPY_STATE=1 |

**Blocker class:** Missing field data; not an OCR typo or a valid completeness inference.

**Smallest safe evidence-grounded fix:** A direct, complete tombstone field readback is needed. The original evidence_42 pixels show a retained customer key and linked records, not name/email/phone/hash values or their removal. No safe automatic redaction proof exists.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_506

**Subject/cutoff:** user_504 / `ayanda.molefe@gmail.com` / `2026-02-08T07:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_12 (SECURITY_AUDIT_LOG); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `security_service/audit_record_1361`: PRESENT; `evidence_47` / `evidence_47:table:customer_data_reporting_replica:row:4`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| evidence_47 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=47; SELECTED_COPY_STATE=2 |

**Blocker class:** Missing primary-state/ownership proof; partial mixed snapshot.

**Smallest safe evidence-grounded fix:** evidence_47 proves the retained audit record, not which anonymous/missing account belongs to user_504. Require an exact account link and state, or genuinely exhaustive subject-scoped primary evidence.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_512

**Subject/cutoff:** user_510 / `hannah.carter@outlook.com` / `2026-02-08T07:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_12 (SECURITY_AUDIT_LOG); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `security_service/audit_record_4219`: PRESENT; `evidence_47` / `evidence_47:table:customer_data_reporting_replica:row:8`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| evidence_47 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=47; SELECTED_COPY_STATE=2 |

**Blocker class:** Missing primary-state/ownership proof; partial mixed snapshot.

**Smallest safe evidence-grounded fix:** evidence_47 proves the retained audit record, not an account deletion for user_510. Anonymous rows cannot be assigned through ordering, suffixes or nearby activity.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_524

**Subject/cutoff:** user_522 / `mateo.castillo@outlook.com` / `2026-01-29T12:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_12 (SECURITY_AUDIT_LOG); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `security_service/audit_record_5429`: PRESENT; `evidence_62` / `evidence_62:/service_exports/security_service/audit_records/2`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| evidence_49 | FILE_NOT_AVAILABLE_AT_CUTOFF=1 |
| evidence_62 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=28; SELECTED_COPY_STATE=1 |

**Blocker class:** Missing primary-state proof in a partial service export.

**Smallest safe evidence-grounded fix:** evidence_62 contains partial observations and anonymous 404s. A retained record is not an account-to-resource link. Require an admissible explicit link/readback; do not use later evidence.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_530

**Subject/cutoff:** user_528 / `chidi.oladipo78@gmail.com` / `2026-01-29T12:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_12 (SECURITY_AUDIT_LOG); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `security_service/audit_record_2152`: PRESENT; `evidence_62` / `evidence_62:/service_exports/security_service/audit_records/0`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| evidence_49 | FILE_NOT_AVAILABLE_AT_CUTOFF=1 |
| evidence_62 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=28; SELECTED_COPY_STATE=1 |

**Blocker class:** Missing primary-state proof in a partial service export.

**Smallest safe evidence-grounded fix:** Same boundary as case_524 for user_528: the supplied audit record establishes its own presence only, not deletion of an unidentified account.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_532

**Subject/cutoff:** user_530 / `mahlangu.thabo80@gmail.com` / `2026-01-29T12:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; contract:data_flow (DATA_FLOW), rule_05 (SUPPORT_MESSAGE), rule_12 (SECURITY_AUDIT_LOG), rule_14 (BACKUP_ARCHIVE); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `backup_service/backup_6344`: BLOCKED; `evidence_62` / `evidence_62:/service_exports/backup_service/restore_entries/1`.
- `integration_service/data_flow_6987`: DISABLED; `evidence_62` / `evidence_62:/service_exports/integration_service/connectors/2`.
- `security_service/audit_record_4828`: PRESENT; `evidence_62` / `evidence_62:/service_exports/security_service/audit_records/1`.
- `support_platform/support_7724`: REDACTED; `evidence_62` / `evidence_62:/service_exports/support_platform/tickets/3`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| activity_94 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| activity_95 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| activity_96 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| evidence_49 | FILE_NOT_AVAILABLE_AT_CUTOFF=4 |
| evidence_62 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=25; SELECTED_COPY_STATE=4 |

**Blocker class:** Missing primary-state proof despite compliant downstream observations.

**Smallest safe evidence-grounded fix:** The retained audit record, redacted support, blocked backup and disabled flow in evidence_62 do not identify or establish the final state of the primary account. Require its admissible link/readback; do not synthesize an account ID.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_55

**Subject/cutoff:** user_16 / `areed1433@gmail.com` / `2026-04-30T11:00:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; the catalog-linked resource additionally invokes rule_14 (backup) or rule_15 (tombstone) where applicable, subject to proof of its required state. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- No usable direct state. Catalog metadata or image context does not establish the required treatment.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| activity_4006 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| evidence_01 | EVENT_AFTER_CUTOFF=11; FILE_NOT_AVAILABLE_AT_CUTOFF=11 |
| evidence_32 | NO_EXACT_SUBJECT_OWNERSHIP_LINK=1; OBSERVATION_TIME_UNKNOWN=1; SCOPED_CONTEXT_NOT_DIRECT_STATE=1 |

**Blocker class:** Missing restore-policy data.

**Smallest safe evidence-grounded fix:** The original evidence_32 pixels show archive, path, retention end and other archives' restores, but no restore_allowed/deletion_block for backup_9287. Retention end is not a restore permission. Later restore/log evidence must remain excluded.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

### case_63

**Subject/cutoff:** user_09 / `kwame-mensah@proton.me` / `2026-09-17T09:20:00+00:00`.

**Applicable obligations:** rule_01 for an identifiable primary profile; rule_10 (MARKETING_PROFILE); catalog-linked tombstone/backup/marketing obligations additionally follow rules 15/14/10 respectively when their conditions/state are established. No unobserved resource ID is instantiated.

**Current admissible subject-linked state:**
- `marketing_platform/marketing_001`: PRESENT; `evidence_60` / `evidence_60:image:ocr:marketing_001`.

**All candidate source IDs, with observation counts/reasons** (individual observations and times are in the JSON matrix):

| Evidence ID | Candidate observation disposition |
| --- | --- |
| activity_4008 | ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA=1 |
| evidence_60 | OBSERVATION_TIME_UNKNOWN=1; SCOPED_CONTEXT_NOT_DIRECT_STATE=1; SELECTED_COPY_STATE=1 |

**Blocker class:** Contradictory identity, confirmed in original pixels.

**Smallest safe evidence-grounded fix:** The screenshot names Soo-jin Park and shows sj.park@naver.com with a Korean phone. activity_4008 links the resource to Kwame/user_09. Neither fuzzy name matching nor OCR repair can resolve this; require independent exact identity evidence.

**Final status under the contract:** not established from the supplied admissible evidence; internal UNRESOLVED retained. No supported violation finding can substitute for the missing proof, and no additional safe code-only join was identified.

## Sample step correctness and measurements

All 23 non-exact cases were re-evaluated using the existing evaluator and anchored-field diagnostics. Three status mismatches, 34 missing verification steps and four extra steps remain. Forty-five aligned step_no differences follow from missing/extra preceding steps; no other aligned wrong-field/wrong-citation differences were found. Missing/extra citations remain visible per step in artifacts/sample_mismatches.json. All cases and root-cause counts remain in docs/submission_debugging.md; no sample output is read by prediction logic.

The three newer object-storage steps for object_19 remain evidence-grounded: rule_06 requires DELETE for an attachment belonging only to the subject; activity_4007 explicitly provides sole ownership and the exact delivery_confirmation_19.pdf alias; evidence_46 displays that file and positive version/size/content-type metadata. The catalog is used for ownership, not proof of presence. There is no supplied later direct deletion readback. The planner preserves the last admissible positive observation until superseded; this is a temporal persistence inference, not a fresh September readback. No arbitrary pre-request-age cutoff is supplied by the contract, so removing these steps merely to match the sample would be label-dependent. Their reference mismatch remains disclosed and requires clarification if the intended scope differs.

| Metric | Before | After |
| --- | ---: | ---: |
| case_status_accuracy | 90.625000% | 90.625000% |
| exact_case_accuracy | 28.125000% | 28.125000% |
| step_precision | 97.546012% | 97.546012% |
| step_recall | 82.383420% | 82.383420% |
| step_f1 | 89.325843% | 89.325843% |
| field_accuracy | 77.447426% | 77.447426% |
| sequence_accuracy | 28.125000% | 28.125000% |
| Sample contract-valid | 29/32 | 29/32 |
| Full contract-valid | 510/518 | 510/518 |
| Full unresolved | 8 | 8 |
| Decided incomplete/conditional plans | 1 | 1 |

The only implementation change is the resource-specific conditional-retention guard and its diagnostics; the CSV predictions remain unchanged. No solver accuracy gain is claimed.

## Actual agent contribution

Reviewed actual Gemini/DeepSeek case_17 traces for the same user as full case_46: later sample-cutoff account/backup observations cannot be transferred into the March full case. The case_63 live vision proposal is rejected for the same identity conflict confirmed manually in the pixels. The historical case_07 catalog lead is now deterministically extracted and is not a new agent gain. Read-only tools expose no missing tombstone fields or archive permission; a model cannot infer them from display omission. No new paid calls are justified; this iteration has zero application model calls, tokens and estimated model cost. Prior live usage and its missing-accounting caveat remain in usage_report.md.

## Clarification routes and exact questions

Repository-prescribed challenge/submission URL: https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

The browsing tool could not access either this prescribed address or the usual www-host variant. No live Discussions tab, organizer contact address or newer rule clarification was verified. Use the authenticated contest page's official discussion/organizer channel **if available**, or the event channel actually supplied by the organizers. No message was sent and no contact/deadline was invented.

Questions to ask through a verified organizer channel:
1. How should a request be serialized when admissible evidence proves neither COMPLETE nor an allowed violation finding? Is additional evidence or a prescribed abstention policy available?
2. Are the security table snapshots exhaustive across all record/copy scope? Where is the supplied retention period for a resource omitted from the later table, such as audit_record_3753?
3. If a required retained record is demonstrably absent within an active period, which allowed finding/remediation is intended, given that no restoration operation exists?
4. Should the literal object_19 catalog/listing observation remain in scope for the later sample request when no later direct deletion readback is supplied?
5. Are complete tombstone fields, backup restore-policy flags and primary-resource identity links available for the eight blocked cases?

No fully compliant output.csv is published. Best diagnostic candidates remain artifacts/sample_predictions.csv and artifacts/full_predictions.csv. Exact final run, validation, package and reproducibility results are linked from docs/submission_readiness.md.

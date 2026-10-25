# Submission debugging: source matrix and obligation ledger

Measured 25 October 2026. All rows below come from participant evidence and actual solver diagnostics. Reference answers are used only by the separate evaluator. Full candidate fields, identity validity intervals, acceptance/exclusion reasons and per-resource obligations are in artifacts/submission_debug/case_matrix.json.

## Measured changes

| Stage | Full valid | Unresolved | Decided incomplete plans | Sample F1 |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 505/518 | 13 | 21 | 90.085% |
| Literal contact details in support bodies | 508/518 | 10 | 1 | 90.085% |
| Catalog/document and listing joins | 510/518 | 8 | 1 | 89.326% |
| Restrict mixed-SQL negative scope | 510/518 | 8 | 1 | 89.326% |

The support fix is an actual readback-semantics correction, not a policy relaxation. Every admitted body contact is literal; stable internal references alone are not PII. Anonymous messages do not prove redaction. Mixed SQL rows without declared service coverage no longer certify absence of other resources. Declared typed snapshots still participate; an actual retained-record absence remains blocked.

The catalog join requires an exact original alias and validated positive document/listing context, retains both source provenances, and is unavailable before the catalog link. Statements additionally require exact subject tokens; attachment listings require explicit sole ownership and visible file metadata. No identifier suffix, fuzzy name, or future event is used.

**Measured tradeoff:** object_19 is explicitly sole-owned in activity_4007 and visibly present in evidence_46. The public case_07 answer omits that older object; the supplied evidence has no admissible later deletion readback. The three grounded finding/remediation/verification steps are retained rather than suppressed using the label. This lowers precision from 99.375% to 97.546%, F1 from 90.085% to 89.326%, and field accuracy from 78.792% to 77.447%. Recall, status and exact/sequence are unchanged. This is a reference discrepancy, not a claimed sample accuracy improvement.

## Every original abstention

### case_160

**Request:** Please erase the account linked to this email address. Please review the account data that is eligible for deletion or de-identification. Please contact me if you need information to verify the request.

**Identity and cutoff:** `navarro.sofia82@gmail.com`, 2026-08-02T07:00:00+00:00. Current verdict: **INCOMPLETE**.

**Original issue:** REQUIRED_KEPT_RECORD_MISSING.

**Grounded resource links:** `security_service/audit_record_9882`, `support_platform/support_4148`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_2713`.
- ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE: `evidence_63`, `evidence_66`, `evidence_69`, `evidence_72`, `evidence_75`, `evidence_78`, `evidence_81`, `evidence_84`.
- SELECTED_COPY_STATE: `evidence_15`.

- Obligation `security_service/audit_record_9882`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_15`; operations: VERIFY_RECORD_PRESENT.
- Obligation `support_platform/support_4148`: SUPPORT_MESSAGE / IDENTIFIABLE / rule_05; source `evidence_15`; operations: REPORT_EXPOSED_PII, REDACT_RECORD, VERIFY_RECORD_REDACTED.

**Result and next action:** Resolved from the original direct observations and catalog links listed above; canonical plan and future blank citations emitted.

### case_33

**Request:** Please close my account and process the associated personal-data deletion. Please handle any copies that fall within the scope of the deletion request. Please confirm when the review is complete.

**Identity and cutoff:** `ingrid.dahl@outlook.com`, 2026-07-19T13:00:00+00:00. Current verdict: **INCOMPLETE**.

**Original issue:** NO_DIRECT_STATE.

**Grounded resource links:** `export_service/export_1260`, `export_service/export_1842`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_4004`, `activity_4009`.
- ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE: `evidence_23`, `evidence_66`, `evidence_69`, `evidence_75`, `evidence_78`, `evidence_81`.
- EVENT_AFTER_CUTOFF: `activity_3328`, `evidence_01`.
- FILE_NOT_AVAILABLE_AT_CUTOFF: `activity_3328`, `evidence_01`.
- SCOPED_CONTEXT_NOT_DIRECT_STATE: `evidence_18`, `evidence_23`.
- SELECTED_COPY_STATE: `evidence_18`, `evidence_81`.

- Obligation `export_service/export_1260`: USER_EXPORT / ABSENT / rule_09; source `evidence_81`; operations: VERIFY_RECORD_ABSENT.
- Obligation `export_service/export_1842`: USER_EXPORT / PRESENT / rule_09; source `evidence_18`; operations: REPORT_REMAINING_RECORD, DELETE_RECORD, VERIFY_RECORD_ABSENT.

**Result and next action:** Resolved from the original direct observations and catalog links listed above; canonical plan and future blank citations emitted.

### case_46

**Request:** I am requesting deletion of the account registered to this email address. Please follow the applicable retention and deletion requirements for the account. I would appreciate confirmation of the final outcome.

**Identity and cutoff:** `leonie.g9352@outlook.com`, 2026-03-11T08:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** NO_DIRECT_STATE.

**Grounded resource links:** `account_service/account_6523`, `identity_service/tombstone_17`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_4011`.
- ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE: `evidence_63`, `evidence_66`.
- EVENT_AFTER_CUTOFF: `activity_3850`, `evidence_01`, `evidence_27`.
- FILE_NOT_AVAILABLE_AT_CUTOFF: `activity_3850`, `evidence_01`, `evidence_27`.
- SCOPED_CONTEXT_NOT_DIRECT_STATE: `evidence_67`.
- SELECTED_COPY_STATE: `evidence_67`.

- Obligation `account_service/account_6523`: USER_PROFILE / ABSENT / rule_01; source `evidence_67`; operations: VERIFY_RECORD_ABSENT.

**Result and next action:** Inspect the named resource in original evidence, OCR or PDF extraction; a worker/catalog claim is not resulting state.; Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.

### case_460

**Request:** I would like to submit a request to delete this account and its personal data. Please ensure the request is applied to the relevant account records. Please confirm the result after completing the required checks.

**Identity and cutoff:** `parker.grace@gmail.com`, 2026-03-05T12:00:00+00:00. Current verdict: **INCOMPLETE**.

**Original issue:** REQUIRED_KEPT_RECORD_MISSING.

**Grounded resource links:** `legal_service/legal_hold_5622`, `security_service/audit_record_1369`, `support_platform/support_4146`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_478`, `activity_480`.
- ADMISSIBLE_HISTORY_OR_OTHER_RESOURCE: `evidence_63`.
- SELECTED_COPY_STATE: `evidence_43`.

- Obligation `legal_service/legal_hold_5622`: LEGAL_HOLD_RECORD / PRESENT / rule_13; source `evidence_43`; operations: VERIFY_RECORD_PRESENT.
- Obligation `security_service/audit_record_1369`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_43`; operations: VERIFY_RECORD_PRESENT.
- Obligation `support_platform/support_4146`: SUPPORT_MESSAGE / IDENTIFIABLE / rule_05; source `evidence_43`; operations: REPORT_EXPOSED_PII, REDACT_RECORD, VERIFY_RECORD_REDACTED.

**Result and next action:** Resolved from the original direct observations and catalog links listed above; canonical plan and future blank citations emitted.

### case_506

**Request:** I would like to submit a request to delete this account and its personal data. Please review the account data that is eligible for deletion or de-identification. A short confirmation when the process is complete is sufficient.

**Identity and cutoff:** `ayanda.molefe@gmail.com`, 2026-02-08T07:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `security_service/audit_record_1361`.

- SELECTED_COPY_STATE: `evidence_47`.

- Obligation `security_service/audit_record_1361`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_47`; operations: VERIFY_RECORD_PRESENT.

**Result and next action:** Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal.

### case_508

**Request:** I am asking you to remove my account and the personal information linked to it. Please apply the request across the systems covered by your deletion policy. Please confirm the result after completing the required checks.

**Identity and cutoff:** `kang.junseo@gmail.com`, 2026-02-08T07:00:00+00:00. Current verdict: **INCOMPLETE**.

**Original issue:** NO_DIRECT_STATE, PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `security_service/audit_record_8154`, `support_platform/support_2691`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_299`.
- SELECTED_COPY_STATE: `evidence_47`.

- Obligation `security_service/audit_record_8154`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_47`; operations: VERIFY_RECORD_PRESENT.
- Obligation `support_platform/support_2691`: SUPPORT_MESSAGE / IDENTIFIABLE / rule_05; source `evidence_47`; operations: REPORT_EXPOSED_PII, REDACT_RECORD, VERIFY_RECORD_REDACTED.

**Result and next action:** Resolved from the original direct observations and catalog links listed above; canonical plan and future blank citations emitted.

### case_512

**Request:** Please erase the account linked to this email address. Please check the records connected to the account before confirming completion. Please contact me if you need information to verify the request.

**Identity and cutoff:** `hannah.carter@outlook.com`, 2026-02-08T07:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `security_service/audit_record_4219`.

- SELECTED_COPY_STATE: `evidence_47`.

- Obligation `security_service/audit_record_4219`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_47`; operations: VERIFY_RECORD_PRESENT.

**Result and next action:** Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal.

### case_524

**Request:** Please process a permanent account-deletion request for this email address. Please handle any copies that fall within the scope of the deletion request. I would appreciate confirmation of the final outcome.

**Identity and cutoff:** `mateo.castillo@outlook.com`, 2026-01-29T12:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `security_service/audit_record_5429`.

- FILE_NOT_AVAILABLE_AT_CUTOFF: `evidence_49`.
- SELECTED_COPY_STATE: `evidence_62`.

- Obligation `security_service/audit_record_5429`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_62`; operations: VERIFY_RECORD_PRESENT.

**Result and next action:** Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal.; Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.

### case_530

**Request:** Please permanently delete the account associated with this email address. Please include information linked through current or earlier account identifiers. Please contact me if you need information to verify the request.

**Identity and cutoff:** `chidi.oladipo78@gmail.com`, 2026-01-29T12:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `security_service/audit_record_2152`.

- FILE_NOT_AVAILABLE_AT_CUTOFF: `evidence_49`.
- SELECTED_COPY_STATE: `evidence_62`.

- Obligation `security_service/audit_record_2152`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_62`; operations: VERIFY_RECORD_PRESENT.

**Result and next action:** Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal.; Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.

### case_532

**Request:** I am asking you to remove my account and the personal information linked to it. Please review any identifiers connected to this account as part of the request. Let me know when the request has been completed.

**Identity and cutoff:** `mahlangu.thabo80@gmail.com`, 2026-01-29T12:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** PRIMARY_PROFILE_VERIFICATION_UNGROUNDED.

**Grounded resource links:** `backup_service/backup_6344`, `integration_service/data_flow_6987`, `security_service/audit_record_4828`, `support_platform/support_7724`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_94`, `activity_95`, `activity_96`.
- FILE_NOT_AVAILABLE_AT_CUTOFF: `evidence_49`.
- SELECTED_COPY_STATE: `evidence_62`.

- Obligation `backup_service/backup_6344`: BACKUP_ARCHIVE / BLOCKED / rule_14; source `evidence_62`; operations: VERIFY_RESTORE_BLOCKED.
- Obligation `integration_service/data_flow_6987`: DATA_FLOW / DISABLED / contract:data_flow; source `evidence_62`; operations: VERIFY_DATA_FLOW_DISABLED.
- Obligation `security_service/audit_record_4828`: SECURITY_AUDIT_LOG / PRESENT / rule_12; source `evidence_62`; operations: VERIFY_RECORD_PRESENT.
- Obligation `support_platform/support_7724`: SUPPORT_MESSAGE / REDACTED / rule_05; source `evidence_62`; operations: VERIFY_RECORD_REDACTED.

**Result and next action:** Find a subject-scoped profile readback, explicit tombstone, or documented exhaustive identity lookup; retained data alone cannot prove account removal.; Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.

### case_55

**Request:** Please treat this message as a request for permanent account deletion. Please include information linked through current or earlier account identifiers. A short confirmation when the process is complete is sufficient.

**Identity and cutoff:** `areed1433@gmail.com`, 2026-04-30T11:00:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** NO_DIRECT_STATE.

**Grounded resource links:** `backup_service/backup_9287`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_4006`.
- EVENT_AFTER_CUTOFF: `evidence_01`.
- FILE_NOT_AVAILABLE_AT_CUTOFF: `evidence_01`.
- SCOPED_CONTEXT_NOT_DIRECT_STATE: `evidence_32`.


**Result and next action:** Inspect the named resource in original evidence, OCR or PDF extraction; a worker/catalog claim is not resulting state.; Potential subject links exist only in excluded evidence; locate an admissible source instead of backfilling from later captures/events.

### case_61

**Request:** Please treat this message as a request for permanent account deletion. Please check the records connected to the account before confirming completion. I would appreciate confirmation of the final outcome.

**Identity and cutoff:** `priya.raman@gmail.com`, 2026-02-14T10:00:00+00:00. Current verdict: **INCOMPLETE**.

**Original issue:** NO_DIRECT_STATE.

**Grounded resource links:** `object_storage/object_19`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_4007`.
- EVENT_AFTER_CUTOFF: `evidence_58`.
- FILE_NOT_AVAILABLE_AT_CUTOFF: `evidence_58`.
- SCOPED_CONTEXT_NOT_DIRECT_STATE: `evidence_46`.
- SELECTED_COPY_STATE: `evidence_46`.

- Obligation `object_storage/object_19`: SUPPORT_ATTACHMENT / PRESENT / rule_06; source `evidence_46`; operations: REPORT_REMAINING_RECORD, DELETE_RECORD, VERIFY_RECORD_ABSENT.

**Result and next action:** Resolved from the original direct observations and catalog links listed above; canonical plan and future blank citations emitted.

### case_63

**Request:** Please permanently delete the account associated with this email address. Please apply the correct treatment to records covered by the request. Please confirm when the review is complete.

**Identity and cutoff:** `kwame-mensah@proton.me`, 2026-09-17T09:20:00+00:00. Current verdict: **UNRESOLVED**.

**Original issue:** OCR_SUBJECT_LINK_UNCORROBORATED.

**Grounded resource links:** `marketing_platform/marketing_001`.

- ACTIVITY_IS_CLAIM_OR_OWNERSHIP_METADATA: `activity_4008`.
- SCOPED_CONTEXT_NOT_DIRECT_STATE: `evidence_60`.
- SELECTED_COPY_STATE: `evidence_60`.

- Obligation `marketing_platform/marketing_001`: MARKETING_PROFILE / PRESENT / rule_10; source `evidence_60`; blocked: [{'code': 'OCR_SUBJECT_LINK_UNCORROBORATED', 'resource_id': 'marketing_001'}].

**Result and next action:** Verify the screenshot's literal subject identifier; do not repair OCR characters or trust a contradictory catalog identity claim.

## All 21 originally decided incomplete plans

| Case | Original issue | Current issue | Missing unblocked operations |
| --- | --- | --- | ---: |
| case_104 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_208 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_209 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_210 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_256 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_258 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_306 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_310 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_34 | REQUIRED_RETAINED_RECORD_MISSING | REQUIRED_RETAINED_RECORD_MISSING | 0 |
| case_353 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_356 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_358 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_404 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_406 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_407 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_461 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_474 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_478 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_510 | NO_DIRECT_STATE | none | 0 |
| case_54 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |
| case_62 | REQUIRED_KEPT_RECORD_MISSING | none | 0 |

Twenty plans are now complete through supported REDACT/VERIFY_REDACTED obligations. case_34 remains decided INCOMPLETE with an unplannable retained-record gap: evidence_01 proves audit_record_3753 earlier, while the later declared security inventory evidence_93 projects it absent at cutoff. Rule_12 requires retention, but the output operation table has no restore/recover-record operation. No unsupported operation or future PRESENT verification is fabricated.

## Every sample exact-case discrepancy

All 32 predictions were evaluated; 23 differ from the reference. There are three status mismatches, 34 missing verification steps and four extra steps (one prior grounded profile verification plus three object steps). Among steps with matching phase/system/resource anchors, 45 step_no differences arise from missing/extra earlier steps; no additional aligned operation/state/evidence mismatch was found. The evaluator still separately checks JSON keys, strict types, ordering and citations.

**Missing-step causes:** {"no_grounded_subject_link_in_parsed_evidence": 17, "subject_link_available_only_after_cutoff": 8, "anonymized_record_without_historical_resource_link": 7, "additional_grounded_resource_outside_reference_scope": 4, "insufficient_evidence_abstention": 3, "retained_record_without_admissible_subject_link": 2}.

**Exact-failure case contributions (overlap):** {"status_mismatch": 3, "no_grounded_subject_link_in_parsed_evidence": 17, "anonymized_record_without_historical_resource_link": 7, "additional_grounded_resource_outside_reference_scope": 2, "subject_link_available_only_after_cutoff": 7, "retained_record_without_admissible_subject_link": 2}.

| Case | Status mismatch | Missing steps | Extra steps | Anchored field differences |
| --- | ---: | ---: | ---: | ---: |
| case_01 | True | 1 | 0 | 0 |
| case_02 | True | 1 | 0 | 0 |
| case_03 | False | 1 | 0 | 0 |
| case_04 | True | 2 | 0 | 0 |
| case_07 | False | 1 | 3 | 3 |
| case_08 | False | 1 | 0 | 1 |
| case_09 | False | 2 | 0 | 1 |
| case_10 | False | 1 | 0 | 1 |
| case_17 | False | 0 | 1 | 2 |
| case_18 | False | 2 | 0 | 4 |
| case_20 | False | 2 | 0 | 2 |
| case_21 | False | 2 | 0 | 1 |
| case_22 | False | 1 | 0 | 3 |
| case_23 | False | 2 | 0 | 2 |
| case_24 | False | 1 | 0 | 0 |
| case_25 | False | 2 | 0 | 1 |
| case_26 | False | 2 | 0 | 4 |
| case_27 | False | 2 | 0 | 4 |
| case_28 | False | 2 | 0 | 4 |
| case_29 | False | 2 | 0 | 4 |
| case_30 | False | 2 | 0 | 4 |
| case_31 | False | 1 | 0 | 2 |
| case_32 | False | 1 | 0 | 2 |

Three sample requests have no admissible resource link; identifiers removed from anonymous records cannot be reconstructed using case numbers or sample labels. Seventeen missing steps lack ownership links, eight have useful links only after cutoff, seven anonymized records lack historical ownership, and two retained records lack admissible links. Counts are missing steps and overlap with the status category. All before/after reports and every per-case missing/extra/field discrepancy are retained under artifacts/.

## Targeted AI review

Existing rejected DeepSeek/Gemini proposals were inspected. Invalid quotes, wrong category/state, activity-as-state and timestamp mismatches remain rejected. The catalog/listing category gap is addressed by the deterministic adapter with independent tests. The flagged screenshot was reinvestigated through the existing Gemini vision cache with a zero-call, zero-cost budget: cache hit; its subject proposal still fails exact identifier corroboration. No new paid calls were justified by the remaining absent/undisplayed evidence. Cross-subject identity-index reassignment check found zero reused email/hash/phone identifiers in this supplied dataset; no fuzzy merge was introduced.

## Reproduce diagnostics

```text
python code/evaluation/debug_submission.py --before artifacts/submission_debug/before/full_solver_report.json --extractions artifacts/ocr_cache --output artifacts/submission_debug/case_matrix.json
python code/evaluation/diagnose_solver.py --predictions artifacts/sample_predictions.csv --solver-report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache --output artifacts/sample_mismatches.json
```

The before report must be preserved before rerunning the solver. Diagnostic tooling never feeds labels into prediction. Fresh-environment verification and packaging results are recorded in docs/submission_readiness.md.

# Dataset analysis: Ghost Data Still Exists

Inspected 24 October 2026. Scope: `problem_statement.md`, the repository instructions, and all 103 files under `dataset/`. No solution, predictions, or submission archive were created. Dataset files were read only; SQL exports were loaded into temporary in-memory SQLite databases. All JSON files were parsed recursively, all log/text files were read, all four PDFs were text-extracted and visually reviewed across seven pages, and all eleven screenshots were visually reviewed. SHA-256 hashes of every dataset file were recorded before inspection and compared afterward.

**Evidence labels:** **Fact** means observed in the supplied files or required explicitly by the participant contract. **Interpretation** means a proposed way to reconcile those facts. **Hypothesis** means an assumption that still needs validation. Sample answers are public evaluation references, not evidence of the hidden evaluation answers. No organizer truth, generator internals, or private review material was consulted.

## 1. Findings that determine the baseline

- **Fact:** There are 518 evaluation requests, 32 public sample requests, 850 identity rows, 306 identity-change rows, 4,011 activity rows, 15 policy rules, and 94 evidence files. The prediction template has a header and no data rows.
- **Fact:** Evaluation requests have 517 distinct email strings. `case_33` and `case_52` use the same email but different request and audit times. Cache extraction by file, but decide state separately for every case and cutoff.
- **Fact:** Request emails resolve through the current snapshot for 418 evaluation requests and through historical email changes only for another 100. Sample counts are 29 and 3 respectively. None are unresolved by this structural lookup. This is identity coverage, not proof that all resource relationships have been resolved.
- **Fact:** Public samples include 22 `INCOMPLETE` and 10 `COMPLETE` answers, with no `NOT_APPLICABLE` answer. Non-deletion requests nevertheless exist in the evaluation inputs, including correction, portability, access, login assistance, and marketing-only requests.
- **Fact:** The manifest supplies location, origin, and capture time, not case membership. Evidence must be joined through actual contents, historical identifiers, trace correlation, and resource relationships.
- **Recommendation:** Start with one Python command-line program, normalized in-memory observations, deterministic policy/planning/serialization, and a narrowly scoped model adapter for multilingual intent and visual/ambiguous evidence. A vector database, orchestration framework, service deployment, and multi-agent system are unnecessary for a roughly 4 MB input corpus.

## 2. Inventory and CSV contracts

### 2.1 Top-level files

Counts exclude CSV headers. Each schema below is the actual header, in order. All populated CSV tables have zero empty-string cells; embedded JSON contains meaningful nulls and empty arrays.

| File under `dataset/` | Rows | Actual columns |
| --- | ---: | --- |
| `deletion_requests.csv` | 518 | `case_id,email,requested_at,reported_status,reported_at,audit_at,request_text` |
| `sample_deletion_requests.csv` | 32 | `case_id,email,requested_at,reported_status,reported_at,audit_at,request_text` |
| `sample_output.csv` | 32 | `case_id,deletion_status,steps_json` |
| `user_identities.csv` | 850 | `user_id,name,email,phone,email_hash,updated_at` |
| `user_audit_log.csv` | 306 | `audit_id,user_id,event_time,field_name,old_value,new_value` |
| `system_activity.csv` | 4,011 | `activity_id,event_time,event_type,source_system,target_system,resource_id,reported_result,details` |
| `deletion_rules.csv` | 15 | `rule_id,data_category,condition,required_action` |
| `evidence_files.csv` | 94 | `file_id,file_path,origin,captured_at` |
| `output.csv` | 0 | `case_id,deletion_status,steps_json` |

Evaluation case IDs run from `case_33` through `case_550`; public samples are `case_01` through `case_32`. Both sets have unique case IDs and are disjoint. Do not generate the evaluation list from numeric ranges: read the input rows. CSV data are strings until explicitly parsed; `steps_json` requires a second JSON parse, and the multilingual request text requires UTF-8 handling. Console encoding artifacts observed during inspection were avoided by explicitly using UTF-8.

**Fact:** Evaluation input order is not lexicographic case-ID order. Sort the output explicitly; distinguish string ordering from natural numeric ordering rather than assuming the input file already satisfies the submission rule.

Evaluation workflow claims are `COMPLETE` (254), `PARTIALLY_COMPLETE` (152), and `NOT_STARTED` (112). Activity results are `SUCCESS` (2,914), `FAILED` (721), and `PARTIAL` (376). These distributions describe claims, not verified deletion status. The 17 observed activity types are `DELETE_RECORD`, `UPDATE_RECORD`, `SYNC_RECORD`, `INDEX_RECORD`, `SEND_EMAIL`, `REFRESH_CACHE`, `RETAIN_RECORD`, `ANONYMIZE_RECORD`, `REDACT_RECORD`, `CREATE_EXPORT`, `CHECK_DATA_FLOW`, `DISABLE_DATA_FLOW`, `BLOCK_RESTORE`, `CHECK_RESTORE_ACCESS`, `LINK_RESOURCE_IDENTITY`, `CLASSIFY_REQUEST`, and `RESTORE_BACKUP`.

### 2.2 Evidence formats

| Directory / format | Files | Bytes | Structural count |
| --- | ---: | ---: | --- |
| `evidence/records/*.json` | 28 | 331,815 | Nested snapshots, service exports, and flat record arrays; per-file counts in Appendix A |
| `evidence/databases/*.sql` | 24 | 334,058 | 969 inserted rows across all tables, including snapshot-scope metadata and repeated replicas |
| `evidence/logs/*.log` | 26 | 516,200 | 2,211 physical lines, including control/debug/noise lines |
| `evidence/images/*.png` | 11 | 1,499,214 | 1,500–1,800 pixels wide; ordinary application screens |
| `evidence/documents/*.pdf` | 4 | 262,447 | Seven pages total; selectable text |
| `evidence/records/*.txt` | 1 | 4,534 | 46 physical lines; shift handover |
| Top-level CSVs | 9 | 1,049,832 | Nine distinct file roles listed above |
| **Total** | **103** | **3,998,100** | **94 evidence files plus 9 CSVs** |

**Fact:** Every manifest path exists, all 94 manifest IDs and paths are unique, and every physical evidence file is manifested. There are 30 distinct manifest origins. Resolve `file_path` relative to `dataset/`, not the repository root. Cite the manifest `file_id`, not a filename or extracted page-image name.

Physical rows, snapshot records, replicas, and observations are different units. Adding their counts does not yield a count of unique people, unique resources, or violations.

## 3. Identity and evidence relationships

### 3.1 Identifier history

`user_identities.csv` is a lookup snapshot, not proof that an account still exists in an operational system. It has unique current email addresses. All 306 audit rows refer to an existing snapshot user. The audit covers 196 users and contains 107 email changes, 107 email-hash changes, and 92 phone changes; no name-change rows occur in this file.

**Fact:** SHA-256 of the exact current email string matches `email_hash` for all 850 snapshot rows. Historical hash changes are also explicitly supplied. **Recommendation:** prefer supplied hashes, retain the original strings, and index normalized email/phone forms as additional lookup keys. Do not assume provider-specific email equivalence, remove dots or plus tags, or merge similar names. Uppercase email variants occur in actual service exports and SQL rows, for example `service_resource_export_20260807_074104.json` and `customer_data_inventory_20260213.sql`.

Build an identity timeline from `user_id`, current values, and each audit row's old/new values and `event_time`. For each case, distinguish identifier values valid at the cutoff from later knowledge. Old values remain search keys for copies created before a change. Do not silently use a post-cutoff identity change as knowledge available at audit time.

### 3.2 Join map

| From | To | Grounded link |
| --- | --- | --- |
| Request | Identity snapshot / history | Request email equals current email or an audited historical email |
| Identity | Evidence content | `user_id`, `subject_reference`, `customer_reference`, name, email, phone, hash, `subject_selector`, `uploaded_by`, `owner_email`, or nested document fields |
| Identity | Global activity | Identifier text in `details`, or a resource already linked through evidence |
| Activity | Evidence resource | `resource_id` plus the relevant source/target system and time |
| Lookup start log | Lookup completion log | `trace_id` or equivalent request ID; identity can occur only on the start line |
| Resource | Later redacted/anonymized/absent observation | Same resource identity and system, with an established earlier ownership link |
| File | Provenance and admissibility | `file_id`, manifest capture time, embedded observation time, and source scope |

**Fact:** `system_activity.csv` has no dedicated `user_id`, email, or evidence-file foreign key. Its `details` is free text. It includes 12 `LINK_RESOURCE_IDENTITY` events and 10 `CLASSIFY_REQUEST` events, but those names do not make their results authoritative. In particular, activity IDs are not chronological: the appended `activity_4000` onward include older event dates. Sort by `event_time`, not ID or CSV position.

**Fact:** `resource_id` prefixes are useful hints, not policy types. Public `case_12` requires deleting `analytics_9914` in `analytics_platform`, whereas other analytics records require anonymization. In `evidence_01`, the record is a contact lookup linked through an email hash (`contact_lookup_completed`, line 92), rather than an anonymous aggregate. A blanket “analytics prefix means anonymize” rule contradicts the public answer. **Interpretation:** classify the actual collection/event and fields before applying policy; calibrate this distinction against public samples without hardcoding their resource IDs.

### 3.3 Preserve links after identifiers disappear

`customer_analytics_report_20260907.json` (`evidence_56`) has `analytics_901` with null `user_id`, email, phone, and hash, while metrics remain. Public `case_04` verifies it as anonymized. Finding it requires a resource relationship; searching only for the subject's current email would miss the compliant record entirely. The second record belongs to another person and must not be merged merely because it shares the collection.

`customer_data_snapshot_bundle_20260915.json` (`evidence_51`) contrasts:

- `tombstone_440`: stable `subject_reference=user_541`, `account_status=DELETED`, direct identifier fields null.
- `tombstone_9178`: stable reference plus populated name, email, phone, and email hash, despite the same deleted status.

Samples `case_31` and `case_32` demonstrate the different required outcomes. A stable permitted reference is not itself a deletion violation; a hash remains a prohibited identifier for this tombstone policy.

## 4. Evidence structures and what they establish

### 4.1 JSON: inspect structure rather than filenames

There are four major shapes:

1. **Snapshot bundles (12 files):** `exported_at`, `source`, `snapshots[]`; each snapshot has `captured_at`, `data_store`, `collection`, `records[]`. Actual collections include customer profiles, search documents, analytics reports, support conversations/attachments, connector configurations, backup catalogs, legal retained-order records, security audit events, and deleted-customer references. Some have `operational_record_history` with their own `recorded_at`, `system`, `record_type`, `result`, and `lookup_value`. Nested historical records must not inherit the bundle capture time as their event time or the enclosing data store as their target system.
2. **Service exports (11 files):** `exported_at`, `region`, `source`, `service_exports` keyed by service. Arrays include `profile_lookups`, `profiles`, `restore_entries`, `exports`, `connectors`, `index_queries`, `audit_records`, and `tickets`. Each observation carries `observed_at`. Profile lookups explicitly include `status_code=404` and `profile=null`; search queries include nested `hits.total` and `hits.documents`.
3. **Flat record registers (3 files):** connector configurations, customer export manifest, and security audit ledger use `records[]` with `recorded_at,system,resource_id,record_type,result,subject_reference`. Despite their file titles, these can describe several systems. Do not route exclusively by manifest origin or filename.
4. **Business-specific exports (2 files):** analytics report and export jobs use `captured_at,source,collection,records[]`, with domain fields such as null identifiers, aggregate metrics, download availability, creation/expiry dates, and included sections.

**Fact:** Some arrays are empty. An empty array proves only what the documented captured collection covers. Missing data, a failed parser, and an explicit scoped empty snapshot are not equivalent.

### 4.2 SQL: 24 successfully loaded snapshots

All supplied SQL scripts executed successfully using Python's SQLite in-memory database. There are three structural groups:

| Structure | Files | Schema / use |
| --- | ---: | --- |
| General topology snapshots | 11 | Tables named `customer_data_primary` and read/reporting/regional/failover replica variants. Columns: `resource_id,origin_system,collection_name,record_json,updated_at`. Parse `record_json` recursively. |
| Typed inventory snapshots | 11 | `snapshot_scope` plus eight typed tables below. Scope is explicit per origin system. |
| Specialized account and search snapshots | 2 | `customer_profiles_primary`, `customer_profiles_failover_replica`, and `search_documents_primary`, with direct business fields. |

Typed inventory tables all include `resource_id` and `updated_at`, except the scope table:

| Table | Other columns |
| --- | --- |
| `snapshot_scope` | `origin_system,captured_at` |
| `customer_profiles` | `customer_reference,full_name,email,phone,email_hash,account_status` |
| `customer_search_documents` | `customer_reference,display_name,email,phone,email_hash,index_name` |
| `customer_analytics_profiles` | `customer_reference,email,phone,email_hash,audience_cohort` |
| `support_records` | `customer_reference,requester_name,requester_email,requester_phone,message_excerpt` |
| `customer_exports` | `customer_reference,owner_email,owner_phone,object_key` |
| `connector_subscriptions` | `customer_reference,customer_email,connector_name,enabled,last_delivery_status` |
| `backup_restore_entries` | `customer_reference,customer_email,archive_key,restore_allowed` |
| `security_audit_records` | `subject_reference,event_code,retention_until` |

The specialized profile tables use `resource_id,user_id,full_name,email,phone,account_status,updated_at`. Read the specialized search table's declared schema directly rather than forcing it into the inventory-table shape.

The specialized `search_documents_primary` schema is `resource_id,display_name,email,source_resource_id,indexed_at`; its source-resource link can connect a search document to its account.

**Fact:** `customer_accounts_failover_replica_20260902.sql` (`evidence_54`) has four replica rows and three primary rows. `account_005` remains in failover. Sample `case_05` is incomplete despite a reported complete workflow. General snapshots likewise have replica differences: `customer_data_regional_replicas_20260424.sql` has 29 primary rows, 29 AP South rows, and 31 EU West rows. Row counts locate discrepancies; inspect matching records to establish their meaning.

**Fact:** `customer_data_inventory_20260905.sql` (`evidence_90`) declares all eight typed resource tables but populates only one scope row for `account_service`; all resource tables are empty. Do not treat this as an exhaustive clean bill for all eight services. This is a concrete test for scope-aware negative evidence.

### 4.3 Logs: heterogeneous syntax and correlated reads

Observed syntaxes include plain key/value lines, quoted key/value lines in syslog wrappers, pipe-delimited event headers, bracketed application traces, timestamp-prefixed JSON objects, and cloud-runtime lines with escaped key/value data inside `message`. A single regex extracting `event=` misses entire syntaxes. Normalize wrappers first, then parse their payload fields and correlate starts/completions.

Business readbacks include profile rows/HTTP status, search hits, PII scans, analytics profile fields, connector configurations/heartbeats, export download checks, audit record reads, and restore authorizations/candidate evaluations. Noise includes cache misses, connection pools, retries, queue lag, leases, and exporter control lines. A transient error or cache miss is not proof of resource absence or an active data flow.

`support_replica.log` (`evidence_61`) links a lookup start for a historical email to a completion for `support_002` through `trace_id=tr-rp-002`; another similar-looking email belongs to `support_5914`. Public `case_10` cites this file for the remaining record. Preserve exact identity links and avoid substring/fuzzy joins.

`resource_lookup_trace_20260310_061801.log` (`evidence_67`) is only four lines and covers one account lookup. Export completion with `dropped=0` establishes completeness of that export's stated queries, not completeness of every system for every subject.

### 4.4 PDFs, screenshots, and handover

All PDF pages were inspected. These are business artifacts, not explicit case verdicts:

| Evidence | Actual content | Audit implication |
| --- | --- | --- |
| `evidence_18`, `account_history_report_20260718.pdf` | Two-page customer statement with `user_18`, email, order, charges, payment suffix, and delivery address | Links identity to a persisted business document; a filename about account history does not imply absence or a deletion outcome |
| `evidence_27`, `legal_retention_register_20260529.pdf` | Two-page register with six disputed/tax-order entries and retain-until dates in May 2033 | Evaluate applicable retention rather than deleting every matched record |
| `evidence_55`, `security_retention_extract.pdf` | One-page journal extract: `audit_record_003`, `user_03`, recorded date, retention through August 2027, integrity details | A retained audit record is not automatically a violation; relevance must still match the actual case subject |
| `evidence_58`, `delivery_correction_attachment.pdf` | Two-page customer-uploaded attachment with `support_001`, contact details, order, and upload/capture details | Sample `case_07` requires deleting the subject-owned attachment |

All eleven PNGs were reviewed. Their subjects are account administration, analytics, backup recovery, connector management, customer exports, deleted-account references, marketing, object storage, search inspection, security audits, and support tickets. They contain contextual details, other people's rows, system/resource IDs, and timestamps. Examples:

- `evidence_14` shows connector `data_flow_1121` in continuous sync with delivered events, alongside unrelated connectors.
- `evidence_23` shows `export_1260` ready and downloadable, with owner and expiry details.
- `evidence_42` shows a stable customer reference and relationships to orders/support/finance; reference existence alone does not prove prohibited direct identifiers remain.
- `evidence_09` shows two search hits with related-looking emails; membership must be resolved per result. `evidence_04` is the account administration screen.
- `evidence_60` shows a populated live marketing profile, but public `case_09` is linked to other resources and uses `evidence_93`. Do not assume an early sample's person or resource from a familiar filename.
- `evidence_46` lists storage objects and versions, but an object listing alone does not establish that each object belongs to the deletion subject or exposes their identifiers.

`customer_account_handover_20261001.txt` (`evidence_03`) has pipe-separated timestamp, system, resource, category, result, and subject fields inside ordinary prose. It includes absence, identifiable/anonymized, active/disabled flow, blocked backup, retained audit, and support records. Samples `case_11`, `case_13`, and `case_14` cite it. Treat each line as a provenance-preserving observation, with the same cutoff rules as structured files.

## 5. Deletion policy

These are the fifteen actual rows from `deletion_rules.csv`; they are supplied challenge policy, not advice about external privacy law.

| Rule | Category | Condition | Required treatment |
| --- | --- | --- | --- |
| `rule_01` | `USER_PROFILE` | Always | DELETE |
| `rule_02` | `SECONDARY_IDENTIFIER` | Always | DELETE |
| `rule_03` | `SEARCH_INDEX_ENTRY` | Always | DELETE |
| `rule_04` | `CACHE_ENTRY` | Always | DELETE |
| `rule_05` | `SUPPORT_MESSAGE` | Shared customer, agent, or order context must be retained | REDACT |
| `rule_06` | `SUPPORT_ATTACHMENT` | Attachment belongs only to the deletion subject | DELETE |
| `rule_07` | `ANALYTICS_PROFILE` | Still attributable to a user | ANONYMIZE |
| `rule_08` | `PRODUCT_TELEMETRY` | Still attributable to a user | ANONYMIZE |
| `rule_09` | `USER_EXPORT` | Always | DELETE |
| `rule_10` | `MARKETING_PROFILE` | Always | DELETE |
| `rule_11` | `EMAIL_DELIVERY_LOG` | Contains a user email address | REDACT |
| `rule_12` | `SECURITY_AUDIT_LOG` | Within supplied retention period | RETAIN |
| `rule_13` | `LEGAL_HOLD_RECORD` | Supplied legal hold active | RETAIN |
| `rule_14` | `BACKUP_ARCHIVE` | Restore access can be blocked | RETAIN, with unsafe restore access blocked |
| `rule_15` | `ACCOUNT_TOMBSTONE` | Deleted account needs stable internal reference for retained records | REDACT direct identifiers; preserve reference |

There are seven DELETE rules, three REDACT rules, two ANONYMIZE rules, and three RETAIN rules. Active data flow is a required risk concept in the problem and allowed operations, even though `DATA_FLOW` is not a row in this policy CSV. Restore blocking similarly supplements retention: retaining a backup does not mean leaving it restorable.

**Interpretation:** Model policy as conditional predicates over actual resource content, not an unconditional category-to-verb dictionary. The CSV does not prescribe a fallback for every failed condition, nor a universal list of redaction fields for every category. Where evidence does not establish sole ownership, retention, or active legal hold, preserve that uncertainty in diagnostics rather than inventing a rule. For tombstones the contract is explicit: remove name, email, phone, hash, and prohibited direct identifiers while preserving stable linkage.

**Fact:** There is no allowed `RETAIN_RECORD` remediation step, although that event name appears in activity. Retention is ordinarily represented in output with `VERIFY_RECORD_PRESENT`. Activity event vocabulary and output operation vocabulary are different contracts.

## 6. Timestamp and audit semantics

### 6.1 Observed ranges (UTC)

| Source / field | Earliest | Latest |
| --- | --- | --- |
| Evaluation `requested_at` | 2026-01-05 06:00:00 | 2026-09-24 08:00:00 |
| Evaluation `reported_at` | 2026-01-06 06:00:00 | 2026-09-26 02:00:00 |
| Evaluation `audit_at` | 2026-01-29 12:00:00 | 2026-10-01 12:00:00 |
| Sample `audit_at` | 2026-09-03 11:30:00 | 2026-10-01 12:00:00 |
| Identity `updated_at` | 2023-06-22 10:59:00 | 2026-08-30 01:02:00 |
| Identity audit `event_time` | 2024-12-14 16:31:44 | 2026-06-03 08:42:31 |
| Activity `event_time` | 2026-01-04 14:56:29 | 2026-10-01 10:18:34 |
| Manifest `captured_at` | 2026-01-29 11:44:59 | 2026-10-01 12:00:00 |

Observed request timestamps obey `requested_at <= reported_at <= audit_at` in all 550 public/evaluation request rows. No current-email-matched request has an identity snapshot update later than its audit cutoff in the direct lookup check; that check does not replace temporal handling of historical aliases.

### 6.2 Required handling

1. Parse timezone-aware instants; supplied machine-readable timestamps use ISO-8601 `Z`. Screens can contain human-formatted UTC or local-zone dates (the account admin screenshot includes JST). Keep original strings and normalized UTC values.
2. Treat `audit_at` as inclusive. Evidence at exactly the cutoff is eligible, as shown by `case_31`/`case_32` and `evidence_51` at `2026-09-15T12:00:00Z`.
3. Enforce file availability and observation time separately. Under the explicit contract, a file captured after the cutoff cannot be cited, even if it embeds an earlier event. An eligible file can contain stale history; use each embedded `recorded_at`, `observed_at`, snapshot timestamp, SQL snapshot time, and event time appropriately.
4. Distinguish observation time from a row's last modification time, creation time, expiry, and retention deadline. A record modified earlier but present in a later eligible snapshot is observed present at snapshot time. A retention deadline in 2034 does not mean the evidence was collected in 2034.
5. Reconstruct per resource, system, and replica. A newer empty primary does not erase an older-but-currently-unresolved replica finding; a deleted profile can be recreated through synchronization or restore. Later direct readbacks can supersede earlier presence for the same scoped resource.
6. Never use `reported_status`, `reported_result`, a delete submission, an HTTP success for a job, or an exporter completion as sole proof of the resulting data state.

**Fact:** Some logs contain observations days before their filename/export date. For example `search_index_diagnostic_20260906.log` includes `account_8473` FOUND on 31 August and NOT_FOUND on 6 September. Some bundles contain historical states in `operational_record_history`. A file-level “latest capture wins” rule loses these differences.

**Open question:** The specification does not define a full tie-break rule when equally authoritative observations at the same timestamp disagree, or which of several equivalent valid citations a canonical answer selects. **Recommendation:** retain contradictory observations with provenance, prefer direct content/readback over workflow claims, use a documented deterministic citation tie-break, and measure citation mismatches separately on samples. Do not claim this heuristic is a specified rule.

## 7. Sample output patterns and serialization

All 32 sample outputs parse as JSON arrays. They contain 193 steps: 41 findings, 41 remediation steps, and 111 verifications. All fifteen allowed operations occur somewhere in the samples. Step counts range from 1 to 14. Every nonempty citation in the sample is a manifest `file_id` (75 cited steps); none demonstrates an `activity_id` or `audit_id` citation, although both are allowed. No sample citation is captured after its case's cutoff.

### 7.1 Decision patterns

| Public cases | Demonstrated behavior |
| --- | --- |
| `case_01`, `case_02` | One evidence-backed account-absence verification can suffice when that is the grounded scope; partial workflow reporting does not force an incomplete verdict |
| `case_03`, `case_04`, `case_21`, `case_25` | Account absent, analytics anonymized, and retained security record where applicable; inspect the actual subject/resource mapping |
| `case_05` | Replica record remains despite COMPLETE claim: finding, deletion, future absence check |
| `case_06`–`case_08`, `case_10` | Remaining search, support attachment/replica, or export; verification also covers already-absent accounts |
| `case_09`, `case_14`, `case_17` | Backup risk requires `BLOCK_RESTORE` and `VERIFY_RESTORE_BLOCKED`, not deletion of the archive |
| `case_11`, `case_18`, `case_29`, `case_30` | Search deletion, support redaction, analytics anonymization, and active flow disabling in one plan |
| `case_12` | Contact/secondary identity resource in analytics requires whole-record deletion, not automatic anonymization |
| `case_15`, `case_20` | Active integration can make an otherwise deleted account incomplete |
| `case_26`–`case_28` | COMPLETE can require six verification operations spanning absence, retention, redaction, anonymization, disabled flow, and blocked restore |
| `case_31`, `case_32` | Correct versus exposed account tombstones: preserve stable reference and redact prohibited identifiers |

The 17 samples reported COMPLETE split into six actual COMPLETE and eleven INCOMPLETE. Of five reported PARTIALLY_COMPLETE, one is COMPLETE and four INCOMPLETE. Of ten reported NOT_STARTED, three are COMPLETE and seven INCOMPLETE. These are public-sample observations, not a prediction distribution for the 518 requests.

### 7.2 Exact output rules

Final output belongs at repository-root `output.csv`, with exactly `case_id,deletion_status,steps_json`, one row per evaluation input, sorted by case ID. Use a CSV writer to quote JSON correctly. Do not emit commentary, extra JSON keys, or a diagnostic fourth status in this file.

Every step has exactly `step_no,phase,system_id,resource_id,operation,state,evidence_id`. Step numbers start at one and are consecutive. Object key order and JSON whitespace are insignificant; array order is significant. Preserve resource strings exactly, including zero padding. `NOT_APPLICABLE` requires `[]` and authorizes no deletion verification.

Canonical ordering specified in `problem_statement.md`, and observed in all sample arrays:

| Phase | Operation order, each with its required state |
| --- | --- |
| FINDING | `REPORT_REMAINING_RECORD/PRESENT`, `REPORT_EXPOSED_PII/PRESENT`, `REPORT_ACTIVE_DATA_FLOW/ACTIVE`, `REPORT_RESTORE_RISK/ACTIVE` |
| REMEDIATION | `DISABLE_DATA_FLOW/DISABLED`, `BLOCK_RESTORE/BLOCKED`, `DELETE_RECORD/ABSENT`, `REDACT_RECORD/REDACTED`, `ANONYMIZE_RECORD/ANONYMIZED` |
| VERIFICATION | `VERIFY_RECORD_ABSENT/ABSENT`, `VERIFY_RECORD_PRESENT/PRESENT`, `VERIFY_RECORD_REDACTED/REDACTED`, `VERIFY_RECORD_ANONYMIZED/ANONYMIZED`, `VERIFY_DATA_FLOW_DISABLED/DISABLED`, `VERIFY_RESTORE_BLOCKED/BLOCKED` |

Within each operation, sort by ascending `system_id`, then `resource_id`; operation order is the table order, not alphabetical order. For COMPLETE, emit only cited verification steps. For INCOMPLETE, cite findings but leave `evidence_id` empty for every proposed remediation and future verification, including checks of already-compliant resources. Samples show that verification covers the full relevant final-state scope, including mandatory retained records, rather than only resources being changed.

**Ordering ambiguity:** Repository instructions also say to process downstream copies before source records where dependency requires it. The problem specifies canonical operation/system/resource ordering, and samples `case_16` and `case_24` put account deletion before search deletion under that ordering. Do not invent a universal search-before-account rule. **Recommendation:** stop copying/restoring processes first as specified; keep an internal dependency model for actual execution planning, serialize the sample-backed canonical order, and explicitly diagnose any demonstrated dependency that cannot be represented consistently. The supplied files do not resolve every possible ordering conflict.

## 8. Ambiguous cases, failure modes, and targeted checks

| Concern | Grounding | Implementation consequence |
| --- | --- | --- |
| Non-deletion intent with deletion words | Evaluation text includes “not a request to erase it”, “don't delete”, and marketing-only removal; multilingual affirmative requests include French, Spanish, Portuguese, Japanese, and Korean | Semantic authorization gate before resource planning; never use one keyword or event classification alone |
| Repeated subject at different audit times | `case_33` versus `case_52` | Per-case temporal reconstruction; no email-to-answer cache |
| Historical address and hash-only copies | 100 evaluation requests need historical-email lookup; `evidence_01` contact lookup correlates via hash | Index old/new identifiers, exact hashes, and trace/resource links |
| Similar-looking people / unrelated records | `support_replica.log`, search screenshot, and analytics report include other subjects | Require grounded joins; no broad substring or fuzzy name ownership |
| Sanitized records lose join identifiers | `analytics_901` has all linking identifier fields null | Maintain provenance of prior ownership by resource ID; absence of an email is not absence of a resource |
| Primary clean, replica dirty | `evidence_54` and multi-table replica SQL | Evaluate all scoped copies before concluding absent |
| Recreated data after deletion | Sync, indexing, and restore events exist; one `RESTORE_BACKUP` activity | Treat actions as timeline events and inspect actual later state; stop relevant active paths |
| Deleted flag with exposed identifiers | `tombstone_9178` | Inspect fields, preserve stable reference, redact direct identifiers |
| Shared support content versus owned attachment | `rule_05`/`rule_06`, sample `case_07`, mixed plans | Determine ownership/context before selecting redaction versus deletion |
| Retention is conditional | Security extract, legal register, explicit retention fields | Check hold/retention at audit; do not invent an indefinite retention policy |
| Missing scope versus negative result | `evidence_90`, `evidence_67` | Empty collection is evidence only for established scope; don't mistake parser omissions for absence |
| Source title differs from actual target | Cross-system JSON registers and nested histories | Use embedded system/collection, not origin or filename, as target semantics |
| Activity vocabulary differs from output | 17 activity event types versus 15 allowed operations | Explicit mapping; no raw copying of event names into output |
| Evidence choice affects scoring | Public samples select particular IDs; equivalent-citation policy unspecified | Compare evidence field accuracy independently and investigate alternative sources |

**Hypothesis:** Structured evidence plus trace correlation should resolve most observations without sending the entire corpus to a model. No coverage or accuracy result has been established for that proposed parser.

**Hypothesis:** A narrow multimodal extraction pass can cover the eleven screenshots at modest cost, with cached structured facts rather than repeated case-by-case image calls. OCR alone may be sufficient for some fields, but exact OCR reliability has not been measured. All four PDFs expose text, so image interpretation is not the default PDF path.

**Open questions:** How to resolve simultaneous contradictory direct observations; how to prove ownership of an object when only storage metadata are visible; how to handle missing mandatory retained records when the output vocabulary has no restore-retained-record action; and how to select among equally valid citations. Record these limitations explicitly rather than filling them with fabricated evidence or new operations.

## 9. Prioritized implementation plan (proposed, not implemented)

### P0: Make the contract and ingestion observable

1. Create one Python CLI with repository-relative input/output paths, UTF-8 CSV/JSON handling, and no network dependency except an optional configured model provider. Document one setup command and one run command, for example `python code/main.py --dataset dataset --output output.csv`; these are proposed interfaces, not existing commands.
2. Validate case IDs, manifests, allowed enums, timestamps, and all parser coverage counts. Keep public samples separate from prediction inputs. Load SQL into isolated in-memory SQLite databases and preserve table/replica provenance.
3. Normalize evidence into observations containing source ID, file path/locator, availability time, observation time, target system, collection/category, resource ID, identifiers, field content, scope, and evidence strength. Keep raw source spans so every claim is auditable. This is internal data, not extra output-step fields.
4. Implement parsers for all JSON shapes, SQL tables, log wrappers and trace joins, PDF text, screenshots, and the handover text. Unknown shapes must produce diagnostics; they must not silently disappear.

### P1: Smallest end-to-end audit baseline

5. Resolve identity histories, retaining raw and normalized values with validity intervals. Establish resource ownership through identifiers and evidence-backed links, including resources now anonymized or absent.
6. Add a deletion-authorization gate. Use explicit negation/action logic for straightforward text and a cached structured model call for multilingual/ambiguous requests. Require a reason grounded in request text; `CLASSIFY_REQUEST` is corroboration only. No mappings from case number ranges or recurring prose to golden statuses.
7. Reconstruct admissible resource state at each cutoff; separate claims from direct observations, include all replicas, and retain contradictions. Apply all fifteen supplied policy rules and active-flow/restore requirements.
8. Generate findings, the full remediation plan, and final-state verification scope. Canonicalize operations/states, ordering, numbering, citations, and CSV serialization. Validate exact 518-row coverage. A baseline that skips images, history, replicas, or non-deletion intent is only a parser milestone, not an adequate challenge solution.

**Smallest runnable baseline:** one process, standard-library `csv/json/datetime/hashlib/sqlite3`, one PDF text dependency such as `pypdf`, and one narrow model interface that can handle text intent plus screenshot extraction when needed. Keep extraction caches outside `dataset/`, keyed by file content and extraction version. Use dictionaries/in-memory tables and a small relationship graph represented by ordinary data structures. Prefer typed deterministic adapters for observed evidence shapes over asking an LLM to infer every case from a giant prompt. Model calls and extractions must use participant-visible content only.

If evidence remains unresolved, retain an internal uncertainty/error record and investigate it before submission. The contract has no `UNKNOWN` status; neither `COMPLETE` nor `NOT_APPLICABLE` is an honest substitute for an ingestion failure. Deterministic ordering does not guarantee deterministic model reasoning, so cache model outputs and record configuration/usage.

### P2: Evaluate before expanding architecture

9. Run on all 32 public samples and compare status, full step sets, each field (especially category-dependent operation and evidence ID), and exact sequence. Do not report hidden-evaluation accuracy: its ground truth is not participant-facing.
10. Add at least three independent custom tests. Priorities: (a) negated deletion / marketing-only request that leaves the account untouched; (b) clean primary plus dirty replica with an active connector and a mandatory retained security record; (c) identical subject at two cutoffs, including future evidence exclusion and compliant/exposed tombstone versions. Add a fourth for scoped-empty SQL versus an unobserved service and a fifth for history-only/hash-only linkage if feasible.
11. Use failures to improve extraction, joins, temporal selection, category decisions, and evidence selection separately. Re-evaluate the same public cases without hardcoding outputs. Measure parser coverage before model tuning.
12. For a future final run, write `evaluation/evaluation_report.md` with measured sample/custom status, step/field, and sequence metrics plus failures/improvements. Write `evaluation/usage_report.md` with provider/model names, actual calls, input/output tokens, per-model/overall totals, averages across the 518 requests, and cost assumptions. Include extraction/cache accounting so reported usage represents the run that produced predictions. No such run or metrics exist from this analysis task.

### P3: Package only after a clean run

Document exact dependencies and commands, verify fresh-run 518-row output, and produce the required code and reports. Keep `dataset/`, secrets, caches, virtual environments, and nested archives out of `code.zip`. Preserve the root `log.txt` as the required conversation log and follow `agent_trace_instructions.md` separately when preparing the final structured trace archive. This analysis does not package or submit anything.

## Appendix A. Full evidence inventory

Paths in the following table are relative to `dataset/`. JSON counts are domain observation records: snapshot record totals, top-level flat record counts, or service-export array items. Nested search hit documents and metric/activity children are not counted again. SQL counts include scope metadata and all replicas; log/text counts are physical lines. These counts measure inspected structure, not unique subjects or violations.

| ID | File | Origin | Captured at (UTC) | Inspected structure |
| --- | --- | --- | --- | --- |
| evidence_01 | [evidence/logs/service_events_ap_south_20260915.log](../dataset/evidence/logs/service_events_ap_south_20260915.log) | central_observability_export | 2026-09-15T11:59:39Z | 104 lines |
| evidence_02 | [evidence/records/customer_data_snapshot_bundle_20260917.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260917.json) | records_assurance_snapshot_bundle | 2026-09-17T12:00:00Z | 11 snapshots / 41 records |
| evidence_03 | [evidence/records/customer_account_handover_20261001.txt](../dataset/evidence/records/customer_account_handover_20261001.txt) | customer_account_service | 2026-10-01T12:00:00Z | 46 lines |
| evidence_04 | [evidence/images/account_admin_console_20260926.png](../dataset/evidence/images/account_admin_console_20260926.png) | account_admin_portal | 2026-09-26T11:00:00Z | 1800 x 1200 px; visually reviewed |
| evidence_05 | [evidence/databases/customer_data_read_replica_20260921.sql](../dataset/evidence/databases/customer_data_read_replica_20260921.sql) | customer_data_read_replica_capture | 2026-09-21T10:00:00Z | customer_data_primary: 30; customer_data_read_replica: 31 |
| evidence_06 | [evidence/logs/structured_service_events_eu_west_20260918.log](../dataset/evidence/logs/structured_service_events_eu_west_20260918.log) | central_observability_export | 2026-09-18T11:55:24Z | 112 lines |
| evidence_07 | [evidence/records/customer_data_snapshot_bundle_20260913.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260913.json) | records_assurance_snapshot_bundle | 2026-09-13T08:00:00Z | 9 snapshots / 30 records |
| evidence_08 | [evidence/logs/search_index_diagnostic_20260906.log](../dataset/evidence/logs/search_index_diagnostic_20260906.log) | search_index_service | 2026-09-06T07:00:00Z | 36 lines |
| evidence_09 | [evidence/images/search_index_inspector_20260901.png](../dataset/evidence/images/search_index_inspector_20260901.png) | search_index_admin | 2026-09-01T06:00:00Z | 1800 x 1100 px; visually reviewed |
| evidence_10 | [evidence/databases/customer_data_read_replica_20260827.sql](../dataset/evidence/databases/customer_data_read_replica_20260827.sql) | customer_data_read_replica_capture | 2026-08-27T12:00:00Z | customer_data_primary: 29; customer_data_read_replica: 30 |
| evidence_11 | [evidence/logs/syslog_archive_us_east_20260824.log](../dataset/evidence/logs/syslog_archive_us_east_20260824.log) | central_observability_export | 2026-08-24T13:56:43Z | 118 lines |
| evidence_12 | [evidence/records/customer_data_snapshot_bundle_20260819.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260819.json) | records_assurance_snapshot_bundle | 2026-08-19T10:00:00Z | 11 snapshots / 29 records |
| evidence_13 | [evidence/records/connector_configurations_20260812.json](../dataset/evidence/records/connector_configurations_20260812.json) | integration_management_service | 2026-08-12T09:00:00Z | 39 records |
| evidence_14 | [evidence/images/connector_management_console_20260807.png](../dataset/evidence/images/connector_management_console_20260807.png) | integration_admin | 2026-08-07T08:00:00Z | 1800 x 1150 px; visually reviewed |
| evidence_15 | [evidence/databases/customer_data_read_replica_20260802.sql](../dataset/evidence/databases/customer_data_read_replica_20260802.sql) | customer_data_read_replica_capture | 2026-08-02T07:00:00Z | customer_data_primary: 24; customer_data_read_replica: 25 |
| evidence_16 | [evidence/logs/application_trace_ap_northeast_20260730.log](../dataset/evidence/logs/application_trace_ap_northeast_20260730.log) | central_observability_export | 2026-07-30T08:53:12Z | 93 lines |
| evidence_17 | [evidence/records/customer_data_snapshot_bundle_20260725.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260725.json) | records_assurance_snapshot_bundle | 2026-07-25T15:00:00Z | 11 snapshots / 36 records |
| evidence_18 | [evidence/documents/account_history_report_20260718.pdf](../dataset/evidence/documents/account_history_report_20260718.pdf) | account_history_service | 2026-07-18T11:00:00Z | 2 pages |
| evidence_19 | [evidence/images/analytics_profile_view_20260713.png](../dataset/evidence/images/analytics_profile_view_20260713.png) | analytics_platform | 2026-07-13T10:00:00Z | 1800 x 1150 px; visually reviewed |
| evidence_20 | [evidence/databases/customer_data_read_replica_20260708.sql](../dataset/evidence/databases/customer_data_read_replica_20260708.sql) | customer_data_read_replica_capture | 2026-07-08T09:00:00Z | customer_data_primary: 31; customer_data_read_replica: 32 |
| evidence_21 | [evidence/logs/operations_stream_eu_central_20260705.log](../dataset/evidence/logs/operations_stream_eu_central_20260705.log) | central_observability_export | 2026-07-05T07:54:27Z | 128 lines |
| evidence_22 | [evidence/records/customer_data_snapshot_bundle_20260630.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260630.json) | records_assurance_snapshot_bundle | 2026-06-30T07:00:00Z | 11 snapshots / 71 records |
| evidence_23 | [evidence/images/customer_export_console_20260618.png](../dataset/evidence/images/customer_export_console_20260618.png) | export_service | 2026-06-18T12:00:00Z | 1800 x 1100 px; visually reviewed |
| evidence_24 | [evidence/databases/customer_data_read_replica_20260613.sql](../dataset/evidence/databases/customer_data_read_replica_20260613.sql) | customer_data_read_replica_capture | 2026-06-13T11:00:00Z | customer_data_primary: 24; customer_data_read_replica: 26 |
| evidence_25 | [evidence/logs/cloud_runtime_export_us_west_20260608.log](../dataset/evidence/logs/cloud_runtime_export_us_west_20260608.log) | central_observability_export | 2026-06-08T09:58:28Z | 128 lines |
| evidence_26 | [evidence/records/customer_data_snapshot_bundle_20260605.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260605.json) | records_assurance_snapshot_bundle | 2026-06-05T12:00:00Z | 9 snapshots / 32 records |
| evidence_27 | [evidence/documents/legal_retention_register_20260529.pdf](../dataset/evidence/documents/legal_retention_register_20260529.pdf) | legal_retention_service | 2026-05-29T08:00:00Z | 2 pages |
| evidence_28 | [evidence/images/support_ticket_console_20260524.png](../dataset/evidence/images/support_ticket_console_20260524.png) | support_platform | 2026-05-24T07:00:00Z | 1800 x 1200 px; visually reviewed |
| evidence_29 | [evidence/databases/customer_data_regional_replicas_20260519.sql](../dataset/evidence/databases/customer_data_regional_replicas_20260519.sql) | customer_data_regional_replicas_capture | 2026-05-19T06:00:00Z | customer_data_primary: 28; customer_data_replica_ap_south: 29; customer_data_replica_eu_west: 28 |
| evidence_30 | [evidence/logs/service_events_sa_east_20260516.log](../dataset/evidence/logs/service_events_sa_east_20260516.log) | central_observability_export | 2026-05-16T11:58:25Z | 110 lines |
| evidence_31 | [evidence/records/customer_data_snapshot_bundle_20260511.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260511.json) | records_assurance_snapshot_bundle | 2026-05-11T11:00:00Z | 10 snapshots / 74 records |
| evidence_32 | [evidence/images/backup_restore_console_20260429.png](../dataset/evidence/images/backup_restore_console_20260429.png) | backup_service | 2026-04-29T09:00:00Z | 1800 x 1150 px; visually reviewed |
| evidence_33 | [evidence/databases/customer_data_regional_replicas_20260424.sql](../dataset/evidence/databases/customer_data_regional_replicas_20260424.sql) | customer_data_regional_replicas_capture | 2026-04-24T08:00:00Z | customer_data_primary: 29; customer_data_replica_ap_south: 29; customer_data_replica_eu_west: 31 |
| evidence_34 | [evidence/logs/structured_service_events_ca_central_20260419.log](../dataset/evidence/logs/structured_service_events_ca_central_20260419.log) | central_observability_export | 2026-04-19T06:59:43Z | 136 lines |
| evidence_35 | [evidence/records/customer_data_snapshot_bundle_20260416.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260416.json) | records_assurance_snapshot_bundle | 2026-04-16T06:00:00Z | 8 snapshots / 28 records |
| evidence_36 | [evidence/records/customer_export_manifest_20260409.json](../dataset/evidence/records/customer_export_manifest_20260409.json) | customer_export_service | 2026-04-09T12:00:00Z | 46 records |
| evidence_37 | [evidence/images/security_audit_explorer_20260905.png](../dataset/evidence/images/security_audit_explorer_20260905.png) | security_service | 2026-09-05T07:00:00Z | 1800 x 1100 px; visually reviewed |
| evidence_38 | [evidence/databases/customer_data_regional_replicas_20260330.sql](../dataset/evidence/databases/customer_data_regional_replicas_20260330.sql) | customer_data_regional_replicas_capture | 2026-03-30T10:00:00Z | customer_data_primary: 28; customer_data_replica_ap_south: 29; customer_data_replica_eu_west: 28 |
| evidence_39 | [evidence/logs/syslog_archive_ap_southeast_20260325.log](../dataset/evidence/logs/syslog_archive_ap_southeast_20260325.log) | central_observability_export | 2026-03-25T08:59:44Z | 114 lines |
| evidence_40 | [evidence/records/customer_data_snapshot_bundle_20260322.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260322.json) | records_assurance_snapshot_bundle | 2026-03-22T08:00:00Z | 12 snapshots / 31 records |
| evidence_41 | [evidence/logs/notification_delivery_20260315.log](../dataset/evidence/logs/notification_delivery_20260315.log) | downstream_delivery_service | 2026-03-15T07:00:00Z | 39 lines |
| evidence_42 | [evidence/images/deleted_account_reference_20260310.png](../dataset/evidence/images/deleted_account_reference_20260310.png) | identity_service | 2026-03-10T06:00:00Z | 1800 x 1100 px; visually reviewed |
| evidence_43 | [evidence/databases/customer_data_reporting_replica_20260305.sql](../dataset/evidence/databases/customer_data_reporting_replica_20260305.sql) | customer_data_reporting_replica_capture | 2026-03-05T12:00:00Z | customer_data_primary: 25; customer_data_reporting_replica: 26 |
| evidence_44 | [evidence/logs/application_trace_eu_north_20260302.log](../dataset/evidence/logs/application_trace_eu_north_20260302.log) | central_observability_export | 2026-03-02T10:59:23Z | 125 lines |
| evidence_45 | [evidence/records/customer_data_snapshot_bundle_20260223.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260223.json) | records_assurance_snapshot_bundle | 2026-02-23T10:00:00Z | 11 snapshots / 75 records |
| evidence_46 | [evidence/images/object_storage_browser_20260213.png](../dataset/evidence/images/object_storage_browser_20260213.png) | object_storage | 2026-02-13T08:00:00Z | 1800 x 1150 px; visually reviewed |
| evidence_47 | [evidence/databases/customer_data_reporting_replica_20260208.sql](../dataset/evidence/databases/customer_data_reporting_replica_20260208.sql) | customer_data_reporting_replica_capture | 2026-02-08T07:00:00Z | customer_data_primary: 24; customer_data_reporting_replica: 25 |
| evidence_48 | [evidence/logs/operations_stream_me_central_20260203.log](../dataset/evidence/logs/operations_stream_me_central_20260203.log) | central_observability_export | 2026-02-03T05:59:42Z | 103 lines |
| evidence_49 | [evidence/records/customer_data_snapshot_bundle_20260131.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260131.json) | records_assurance_snapshot_bundle | 2026-01-31T15:00:00Z | 10 snapshots / 34 records |
| evidence_50 | [evidence/records/security_audit_ledger_20261001.json](../dataset/evidence/records/security_audit_ledger_20261001.json) | security_audit_service | 2026-10-01T12:00:00Z | 20 records |
| evidence_51 | [evidence/records/customer_data_snapshot_bundle_20260915.json](../dataset/evidence/records/customer_data_snapshot_bundle_20260915.json) | records_assurance_snapshot_bundle | 2026-09-15T12:00:00Z | 3 snapshots / 4 records |
| evidence_52 | [evidence/databases/customer_data_failover_replica_20260920.sql](../dataset/evidence/databases/customer_data_failover_replica_20260920.sql) | customer_data_failover_replica_capture | 2026-09-20T12:00:00Z | customer_data_failover_replica: 16; customer_data_primary: 16 |
| evidence_53 | [evidence/logs/cloud_runtime_export_af_south_20260930.log](../dataset/evidence/logs/cloud_runtime_export_af_south_20260930.log) | central_observability_export | 2026-09-30T11:59:44Z | 305 lines |
| evidence_54 | [evidence/databases/customer_accounts_failover_replica_20260902.sql](../dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql) | customer_account_failover_replica_capture | 2026-09-02T23:00:00Z | customer_profiles_failover_replica: 4; customer_profiles_primary: 3 |
| evidence_55 | [evidence/documents/security_retention_extract.pdf](../dataset/evidence/documents/security_retention_extract.pdf) | security_service | 2026-09-05T06:30:00Z | 1 pages |
| evidence_56 | [evidence/records/customer_analytics_report_20260907.json](../dataset/evidence/records/customer_analytics_report_20260907.json) | analytics_platform | 2026-09-07T09:45:00Z | 2 records |
| evidence_57 | [evidence/databases/customer_search_primary_20260910.sql](../dataset/evidence/databases/customer_search_primary_20260910.sql) | customer_search_primary_capture | 2026-09-10T08:45:00Z | search_documents_primary: 3 |
| evidence_58 | [evidence/documents/delivery_correction_attachment.pdf](../dataset/evidence/documents/delivery_correction_attachment.pdf) | support_platform | 2026-09-12T07:30:00Z | 2 pages |
| evidence_59 | [evidence/records/customer_export_jobs_20260914.json](../dataset/evidence/records/customer_export_jobs_20260914.json) | export_service | 2026-09-14T15:40:00Z | 2 records |
| evidence_60 | [evidence/images/marketing_profile_console.png](../dataset/evidence/images/marketing_profile_console.png) | marketing_platform | 2026-09-16T07:20:00Z | 1500 x 920 px; visually reviewed |
| evidence_61 | [evidence/logs/support_replica.log](../dataset/evidence/logs/support_replica.log) | support_platform | 2026-09-17T22:00:19Z | 10 lines |
| evidence_62 | [evidence/records/service_resource_export_20260129_114459.json](../dataset/evidence/records/service_resource_export_20260129_114459.json) | service_resource_export | 2026-01-29T11:44:59Z | 29 service observations |
| evidence_63 | [evidence/databases/customer_data_inventory_20260213.sql](../dataset/evidence/databases/customer_data_inventory_20260213.sql) | customer_data_inventory_capture | 2026-02-13T07:43:27Z | snapshot_scope: 7; customer_profiles: 2; customer_search_documents: 4; customer_analytics_profiles: 3; support_records: 2; customer_exports: 0; connector_subscriptions: 1; backup_restore_entries: 1; security_audit_records: 4 |
| evidence_64 | [evidence/logs/resource_lookup_trace_20260218_083911.log](../dataset/evidence/logs/resource_lookup_trace_20260218_083911.log) | service_readback_logs | 2026-02-18T08:39:11Z | 54 lines |
| evidence_65 | [evidence/records/service_resource_export_20260228_103637.json](../dataset/evidence/records/service_resource_export_20260228_103637.json) | service_resource_export | 2026-02-28T10:36:37Z | 27 service observations |
| evidence_66 | [evidence/databases/customer_data_inventory_20260310.sql](../dataset/evidence/databases/customer_data_inventory_20260310.sql) | customer_data_inventory_capture | 2026-03-10T05:38:48Z | snapshot_scope: 8; customer_profiles: 0; customer_search_documents: 7; customer_analytics_profiles: 5; support_records: 3; customer_exports: 1; connector_subscriptions: 4; backup_restore_entries: 1; security_audit_records: 2 |
| evidence_67 | [evidence/logs/resource_lookup_trace_20260310_061801.log](../dataset/evidence/logs/resource_lookup_trace_20260310_061801.log) | service_readback_logs | 2026-03-10T06:18:01Z | 4 lines |
| evidence_68 | [evidence/records/service_resource_export_20260320_072349.json](../dataset/evidence/records/service_resource_export_20260320_072349.json) | service_resource_export | 2026-03-20T07:23:49Z | 25 service observations |
| evidence_69 | [evidence/databases/customer_data_inventory_20260404.sql](../dataset/evidence/databases/customer_data_inventory_20260404.sql) | customer_data_inventory_capture | 2026-04-04T10:04:19Z | snapshot_scope: 8; customer_profiles: 0; customer_search_documents: 5; customer_analytics_profiles: 4; support_records: 2; customer_exports: 1; connector_subscriptions: 2; backup_restore_entries: 1; security_audit_records: 3 |
| evidence_70 | [evidence/logs/resource_lookup_trace_20260414_054007.log](../dataset/evidence/logs/resource_lookup_trace_20260414_054007.log) | service_readback_logs | 2026-04-14T05:40:07Z | 50 lines |
| evidence_71 | [evidence/records/service_resource_export_20260429_083222.json](../dataset/evidence/records/service_resource_export_20260429_083222.json) | service_resource_export | 2026-04-29T08:32:22Z | 28 service observations |
| evidence_72 | [evidence/databases/customer_data_inventory_20260504.sql](../dataset/evidence/databases/customer_data_inventory_20260504.sql) | customer_data_inventory_capture | 2026-05-04T09:41:47Z | snapshot_scope: 7; customer_profiles: 1; customer_search_documents: 6; customer_analytics_profiles: 3; support_records: 3; customer_exports: 0; connector_subscriptions: 4; backup_restore_entries: 1; security_audit_records: 3 |
| evidence_73 | [evidence/logs/resource_lookup_trace_20260509_104353.log](../dataset/evidence/logs/resource_lookup_trace_20260509_104353.log) | service_readback_logs | 2026-05-09T10:43:53Z | 68 lines |
| evidence_74 | [evidence/records/service_resource_export_20260514_114454.json](../dataset/evidence/records/service_resource_export_20260514_114454.json) | service_resource_export | 2026-05-14T11:44:54Z | 25 service observations |
| evidence_75 | [evidence/databases/customer_data_inventory_20260524.sql](../dataset/evidence/databases/customer_data_inventory_20260524.sql) | customer_data_inventory_capture | 2026-05-24T06:39:55Z | snapshot_scope: 8; customer_profiles: 0; customer_search_documents: 5; customer_analytics_profiles: 6; support_records: 3; customer_exports: 1; connector_subscriptions: 4; backup_restore_entries: 1; security_audit_records: 4 |
| evidence_76 | [evidence/logs/resource_lookup_trace_20260529_074313.log](../dataset/evidence/logs/resource_lookup_trace_20260529_074313.log) | service_readback_logs | 2026-05-29T07:43:13Z | 48 lines |
| evidence_77 | [evidence/records/service_resource_export_20260603_083457.json](../dataset/evidence/records/service_resource_export_20260603_083457.json) | service_resource_export | 2026-06-03T08:34:57Z | 27 service observations |
| evidence_78 | [evidence/databases/customer_data_inventory_20260618.sql](../dataset/evidence/databases/customer_data_inventory_20260618.sql) | customer_data_inventory_capture | 2026-06-18T11:44:03Z | snapshot_scope: 7; customer_profiles: 2; customer_search_documents: 6; customer_analytics_profiles: 4; support_records: 3; customer_exports: 1; connector_subscriptions: 1; backup_restore_entries: 0; security_audit_records: 2 |
| evidence_79 | [evidence/logs/resource_lookup_trace_20260623_053726.log](../dataset/evidence/logs/resource_lookup_trace_20260623_053726.log) | service_readback_logs | 2026-06-23T05:37:26Z | 60 lines |
| evidence_80 | [evidence/records/service_resource_export_20260628_062556.json](../dataset/evidence/records/service_resource_export_20260628_062556.json) | service_resource_export | 2026-06-28T06:25:56Z | 24 service observations |
| evidence_81 | [evidence/databases/customer_data_inventory_20260703.sql](../dataset/evidence/databases/customer_data_inventory_20260703.sql) | customer_data_inventory_capture | 2026-07-03T07:43:56Z | snapshot_scope: 8; customer_profiles: 0; customer_search_documents: 5; customer_analytics_profiles: 5; support_records: 5; customer_exports: 1; connector_subscriptions: 2; backup_restore_entries: 1; security_audit_records: 5 |
| evidence_82 | [evidence/logs/resource_lookup_trace_20260713_093359.log](../dataset/evidence/logs/resource_lookup_trace_20260713_093359.log) | service_readback_logs | 2026-07-13T09:33:59Z | 54 lines |
| evidence_83 | [evidence/records/service_resource_export_20260718_104335.json](../dataset/evidence/records/service_resource_export_20260718_104335.json) | service_resource_export | 2026-07-18T10:43:35Z | 29 service observations |
| evidence_84 | [evidence/databases/customer_data_inventory_20260723.sql](../dataset/evidence/databases/customer_data_inventory_20260723.sql) | customer_data_inventory_capture | 2026-07-23T11:43:30Z | snapshot_scope: 8; customer_profiles: 1; customer_search_documents: 7; customer_analytics_profiles: 5; support_records: 5; customer_exports: 1; connector_subscriptions: 4; backup_restore_entries: 1; security_audit_records: 2 |
| evidence_85 | [evidence/logs/resource_lookup_trace_20260728_054417.log](../dataset/evidence/logs/resource_lookup_trace_20260728_054417.log) | service_readback_logs | 2026-07-28T05:44:17Z | 46 lines |
| evidence_86 | [evidence/records/service_resource_export_20260807_074104.json](../dataset/evidence/records/service_resource_export_20260807_074104.json) | service_resource_export | 2026-08-07T07:41:04Z | 23 service observations |
| evidence_87 | [evidence/databases/customer_data_inventory_20260817.sql](../dataset/evidence/databases/customer_data_inventory_20260817.sql) | customer_data_inventory_capture | 2026-08-17T09:42:50Z | snapshot_scope: 8; customer_profiles: 1; customer_search_documents: 5; customer_analytics_profiles: 4; support_records: 4; customer_exports: 1; connector_subscriptions: 1; backup_restore_entries: 1; security_audit_records: 2 |
| evidence_88 | [evidence/logs/resource_lookup_trace_20260822_103910.log](../dataset/evidence/logs/resource_lookup_trace_20260822_103910.log) | service_readback_logs | 2026-08-22T10:39:10Z | 46 lines |
| evidence_89 | [evidence/records/service_resource_export_20260901_053316.json](../dataset/evidence/records/service_resource_export_20260901_053316.json) | service_resource_export | 2026-09-01T05:33:16Z | 23 service observations |
| evidence_90 | [evidence/databases/customer_data_inventory_20260905.sql](../dataset/evidence/databases/customer_data_inventory_20260905.sql) | customer_data_inventory_capture | 2026-09-05T07:18:01Z | snapshot_scope: 1; customer_profiles: 0; customer_search_documents: 0; customer_analytics_profiles: 0; support_records: 0; customer_exports: 0; connector_subscriptions: 0; backup_restore_entries: 0; security_audit_records: 0 |
| evidence_91 | [evidence/logs/resource_lookup_trace_20260911_074253.log](../dataset/evidence/logs/resource_lookup_trace_20260911_074253.log) | service_readback_logs | 2026-09-11T07:42:53Z | 62 lines |
| evidence_92 | [evidence/records/service_resource_export_20260915_114455.json](../dataset/evidence/records/service_resource_export_20260915_114455.json) | service_resource_export | 2026-09-15T11:44:55Z | 36 service observations |
| evidence_93 | [evidence/databases/customer_data_inventory_20260916.sql](../dataset/evidence/databases/customer_data_inventory_20260916.sql) | customer_data_inventory_capture | 2026-09-16T08:37:39Z | snapshot_scope: 8; customer_profiles: 1; customer_search_documents: 3; customer_analytics_profiles: 2; support_records: 3; customer_exports: 1; connector_subscriptions: 2; backup_restore_entries: 2; security_audit_records: 3 |
| evidence_94 | [evidence/logs/resource_lookup_trace_20260926_103856.log](../dataset/evidence/logs/resource_lookup_trace_20260926_103856.log) | service_readback_logs | 2026-09-26T10:38:56Z | 58 lines |

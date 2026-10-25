# First deterministic audit solver

Historical baseline. Current uncertainty handling, OCR and readiness results are in
[submission_readiness.md](submission_readiness.md).

Measured 25 October 2026. This is a runnable audit baseline with explicit evidence abstentions,
not a solved challenge or submission-ready output. All 32 public sample predictions and all
518 evaluation predictions were generated. Public expected answers are read only by the
explicit evaluator and evaluation-only mismatch explainer. They never enter intent, identity,
state, policy, or planning modules. The solver hashes reference bytes only for dataset integrity.

## Reproduce

From the repository root, Python 3.11+:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/evaluation/diagnose_solver.py --predictions artifacts/sample_predictions.csv --solver-report artifacts/sample_solver_report.json --output artifacts/sample_mismatches.json
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json
python code/main.py validate --split full --predictions artifacts/full_predictions.csv --report artifacts/full_validation.json
python code/main.py self-test --report artifacts/evaluator_self_test.json
python code/main.py ingest --report artifacts/ingestion_coverage.json --identity-report artifacts/identity_coverage.json
```

`solve`, `validate`, and `evaluate` return **1** when predictions contain contract-invalid
abstentions; they still write their complete CSV/JSON artifacts. Exit 2 indicates fatal input
or configuration failure. The mismatch explanation command succeeds independently of schema
validity so failed rows can be investigated. No API key is needed. Original `run`, `ingest`,
`validate`, `evaluate`, and `self-test` commands retain their responsibilities.

## Measured sample results

These are actual solver predictions scored against `dataset/sample_output.csv`, not a
reference self-comparison or evaluator self-test.

| Metric | Value |
| --- | ---: |
| case_status_accuracy | 75.000000% |
| exact_case_accuracy | 28.125000% |
| step_precision | 99.315068% |
| step_recall | 75.129534% |
| step_f1 | 85.545723% |
| field_accuracy | 72.606775% |
| sequence_accuracy | 28.125000% |

Counts: **145** true-positive steps / **146** predicted / **193** reference; one extra step,
48 missing reference steps. Status correct **24/32**; exact cases and sequences **9/32**.
All rows have valid CSV/JSON serialization and valid case IDs. Full contract validity is
**24/32 rows (75%)**, so the file as a whole is invalid. The eight failures are `STATUS_SHAPE`:
the output contract has no UNKNOWN value. The solver uses `INCOMPLETE,[]` as a visible
abstention, and intentionally leaves the strict validator unchanged. This is not a claim
that a violation or a remediation plan has been established for those cases.

Three abstentions (`case_01`, `case_02`, `case_04`) have no admissible grounded resource link.
Five (`case_21`, `case_25` through `case_28`) have retained/downstream resources but lack a
grounded primary profile or tombstone proof. Treating these latter five as COMPLETE would
raise status accuracy to 90.625%, but would overstate proof coverage; that permissive candidate
was rejected. Final predictions are 30 INCOMPLETE (including eight abstentions), two COMPLETE.

Matching definitions are unchanged: status is exact label equality, independent of validity;
exact case requires matching status, the complete ordered step array, and a valid case;
step precision/recall/F1 use a per-case multiset of all step fields except `step_no`;
field accuracy aligns by `(case_id, phase, system_id, resource_id)` with deterministic occurrence
matching and missing/extra slots penalized; sequence accuracy compares the full ordered array,
including numbering and citations. JSON object key order/whitespace are ignored, array order
is preserved. `artifacts/sample_evaluation.json` records every field numerator and denominator.

## Implementation and safety boundaries

- `authorization.py` normalizes Unicode and recognizes explicit account/data deletion,
  historical cleanup and verification intent in English, Spanish, French, Portuguese,
  Japanese, Korean, Chinese, and Indonesian. Negation, access, correction and marketing-only
  requests do not authorize account deletion. Unknown text abstains. This is a tested narrow
  grammar, not comprehensive multilingual natural-language understanding.
- `state.py` filters on **both** manifest capture availability and embedded observation time
  against `audit_at`. Direct readbacks outrank claims by eligibility: workflow claims cannot
  create direct state. Latest direct state is reconstructed per explicit replica; clean
  primary/replica observations cannot erase another dirty copy. Simultaneous contradictions
  remain diagnostic and prevent an unsupported COMPLETE claim. Query identifiers are not
  mistaken for PII stored in a redacted body.
- SQL table negatives are projected only onto already grounded resources/categories. Empty
  collection snapshots retain their collection scope separately from explicit readbacks;
  they cannot silently clear a positive service readback. This matters for the positive
  account readback in `evidence_92` alongside the later empty collection in `evidence_51`.
- `policy.py` loads all **15 CSV rules**, validates action vocabulary and applies DELETE,
  REDACT, ANONYMIZE or RETAIN. It handles stable tombstone references, shared support context,
  attachment ownership, supplied retention expiry, inactive legal holds, and backup restore
  blocking. Active connectors use the explicit contract flow rule. Unsupported conditional
  treatment has an issue rather than an invented deletion fallback. Category-level retention
  context is accepted when a supplied row lacks an explicit deadline; that remains a limitation.
- `planner.py` produces all findings, remediation and final-state checks for the known scope,
  with canonical phase/operation/system/resource ordering and consecutive numbering. Disable
  flows and block restores precede destructive changes. Incomplete future steps have empty
  citations; direct findings and complete checks use original participant-visible IDs.
  Explicit search source links also receive future account checks even without account state;
  they do not invent an account finding. General dependency DAG ordering beyond the required
  canonical contract is not implemented.
- `solver.py` reuses one parsed store and indexed identity graph. Ambiguous ownership withholds
  treatment. Missing current state, parser errors and inadequate primary proof are surfaced.
  COMPLETE is limited to established known resources plus grounded profile/tombstone proof;
  the baseline still cannot prove the absence of undiscovered copies or unknown PNG content.

The narrow PDF adapter joins pages of one document only when they identify a single resource
and explicitly say the uploader is the customer. It preserves provenance and yields a
subject-owned support attachment. The legacy contact adapter uses the correlated lookup's
`source=legacy_contact_index` to type that readback as a secondary identifier. Neither adapter
contains sample IDs or expected steps.

## Evidence and resource gaps

Raw inventory remains **94 evidence files: 83 parsed and 11 PNG pending**, with **8,163** raw
normalized observations. Two derived adapters add one typed contact readback and one typed
PDF attachment (8,165 stored observations before per-case scope projections). No unsupported
source is treated as absence. All 103 dataset SHA-256 hashes match the turn-start inventory.
All parsed file/row counts still match `docs/dataset_analysis.md` through `ingest` diagnostics.

The four original uncategorized readbacks remain explicitly listed:

| Observation | Disposition |
| --- | --- |
| `evidence_61:line:3` | Parser/semantic gap: contact completion lacks the legacy source classification |
| `evidence_61:line:5` | Resolved by derived SECONDARY_IDENTIFIER adapter using its correlated legacy source |
| `evidence_61:line:6` | Parser/semantic gap: replica marker alone does not identify a safe policy treatment |
| `evidence_61:line:8` | Parser/semantic gap: case archive contact completion lacks a policy category |

All 11 PNG file IDs, paths, capture dates, hashes and pending reasons are present in both run
reports. A visual check of the marketing console confirms an ordinary live profile screen,
not a deletion verdict. No public sample reference step cites a PNG. The measured missing
steps point primarily to absent/late resource ownership links, so no demonstrated sample
blocker justified introducing a paid vision adapter in this iteration. It is **not proven**
that PNGs are irrelevant to every missing link or to full-run accuracy; reliable extraction
remains required work. No vision facts have been hardcoded from manual review.

Identity resolution remains **32/32 sample and 518/518 evaluation**. Raw grounded-resource
coverage remains **29/32 and 509/518**; unique identity does not imply complete resource scope.
Each of the three sample gaps is **unresolved**, not justified empty, parser-proven absence,
or identity failure. For example the primary profile identifiers suggested by public expected
steps occur only in generic worker claims, with no subject identifier establishing ownership.
`case_04` also lacks a historical link to the already-anonymized analytics record. Numeric
suffixes, activity adjacency and expected steps are not legitimate join evidence.

Each evaluation gap, `case_534` through `case_542`, is **justified_empty**: its supplied request
asks for a non-deletion action and receives NOT_APPLICABLE with `[]`. This classification uses
request text and identity/resource diagnostics, not hidden labels. The reports retain all nine
case IDs and classifications. It does not imply all full-run non-deletion classifications
have been independently validated against unavailable ground truth.

## Per-case mismatch breakdown

`artifacts/sample_mismatches.json` contains every missing/extra step, source IDs available or
excluded at the cutoff, solver issues and root-cause classification. Cases below include all
32 predictions; zero step differences does not waive a status/schema mismatch.

| Case | Predicted | Reference | Exact | Missing steps | Extra steps |
| --- | --- | --- | --- | ---: | ---: |
| case_01 | INCOMPLETE | COMPLETE | no | 1 | 0 |
| case_02 | INCOMPLETE | COMPLETE | no | 1 | 0 |
| case_03 | COMPLETE | COMPLETE | no | 1 | 0 |
| case_04 | INCOMPLETE | COMPLETE | no | 2 | 0 |
| case_05 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_06 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_07 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |
| case_08 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |
| case_09 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_10 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |
| case_11 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_12 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_13 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_14 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_15 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_16 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_17 | INCOMPLETE | INCOMPLETE | no | 0 | 1 |
| case_18 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_19 | INCOMPLETE | INCOMPLETE | yes | 0 | 0 |
| case_20 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_21 | INCOMPLETE | COMPLETE | no | 3 | 0 |
| case_22 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |
| case_23 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_24 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |
| case_25 | INCOMPLETE | COMPLETE | no | 3 | 0 |
| case_26 | INCOMPLETE | COMPLETE | no | 6 | 0 |
| case_27 | INCOMPLETE | COMPLETE | no | 6 | 0 |
| case_28 | INCOMPLETE | COMPLETE | no | 6 | 0 |
| case_29 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_30 | INCOMPLETE | INCOMPLETE | no | 2 | 0 |
| case_31 | COMPLETE | COMPLETE | no | 1 | 0 |
| case_32 | INCOMPLETE | INCOMPLETE | no | 1 | 0 |

| Root cause | Count |
| --- | ---: |
| no_grounded_subject_link_in_parsed_evidence | 17 |
| verification_withheld_on_incomplete_proof | 14 |
| insufficient_evidence_abstention | 8 |
| subject_link_available_only_after_cutoff | 8 |
| anonymized_record_without_historical_resource_link | 7 |
| retained_record_without_admissible_subject_link | 2 |
| additional_grounded_resource_outside_reference_scope | 1 |

Step-cause counts total the missing/extra steps; abstention counts are additional case counts
and overlap those causes. These labels describe parsed-evidence discrepancies, not a proof
that reference answers are wrong. In particular no future evidence is admitted to repair a
reference mismatch. The extra check follows an exact historical email link to another account;
that association is broader than the public reference scope and needs validity investigation.

## Validation and usage

**152 tests passed**, including all prior 112 and 40 new intent/state/policy/solver tests.
The unchanged evaluator controlled self-test also passed all five scenarios. The three
independently specified custom business cases are:

1. Dirty regional replica, clean primary, active connector and retained audit record: stop
   copying before deleting and verify every known final state, including retained evidence.
2. Tombstone with stable reference: a later captured dirty document is inadmissible; an
   admissible dirty tombstone requires redaction, never deletion of its stable reference.
3. Access-only request versus worker-success-only deletion claim: access is NOT_APPLICABLE;
   a claim without direct state produces a visible abstention.

Additional regressions cover historical search links, missing links, unknown intent, Unicode
languages, negation, future embedded timestamps, simultaneous contradictions, later empty
collection scopes, clean replicas versus dirty primaries, policy condition failures and all
15 supplied rule categories. A guarded sample integration run forbids decoding sample output.
The new mismatch renderer initially crashed on malformed JSON sentinel values; the original
malformed-input tests exposed this and it was fixed before the final passing test run.

Latest sample runtime: 6.171s; full runtime: 12.107s
(local measurements vary). Full run writes 518 rows: {'INCOMPLETE': 453, 'COMPLETE': 55, 'NOT_APPLICABLE': 10}. **110** full cases
abstain and fail contract shape; **408/518** rows pass validation. No hidden full accuracy can
be claimed. Thus **a full run is executable today, but valid final submission is blocked**.
Application providers/models: none; calls 0; input/output/total tokens 0; total and average
cost USD 0.00. Development-assistant usage is separate from application usage. No credentials
are read. Active harness traces remain in their original location; package them only after
closing the session, following `agent_trace_instructions.md`.

## Next changes, ranked by expected accuracy improvement

1. Recover exact subject/resource links from admissible participant evidence, especially
   removed profile records and already-anonymized analytics. Do not relax cutoff or infer IDs.
   If no public link exists, record the dataset-contract ambiguity explicitly.
2. Add validated, cached PNG extraction with file hash, raw provenance and application usage
   accounting, then measure whether it resolves currently unknown ownership/state scope.
3. Refine collection/SQL completeness and copy topology, reconcile explicit contradictions,
   and attach proof scope to account and retained-record checks before allowing COMPLETE.
4. Resolve historical identifier validity/reassignment and the additional linked account,
   while preserving legitimate historical PII ownership and avoiding joins between subjects.
5. Extend conditional policy context (retention deadlines, shared support/attachment ownership),
   general dependency constraints, and multilingual negation/intent on independently authored
   tests. Keep unknown cases explicit until their evidence is sufficient.

## Files changed in this iteration

Added `code/deletion_audit/authorization.py`, `state.py`, `policy.py`, `planner.py`, `solver.py`,
`code/evaluation/diagnose_solver.py`, `tests/test_solver.py`, and this document. Updated
`code/deletion_audit/inputs.py`, `cli.py`, `evaluator.py`, `README.md`,
`docs/evaluation_foundation.md`, `docs/ingestion_identity.md`,
`code/evaluation/evaluation_report.md`, `code/evaluation/usage_report.md`, and append-only `log.txt`.
Generated reports/predictions live outside dataset in ignored `artifacts/`. No commit or
submission archive was created; no dataset file was edited.

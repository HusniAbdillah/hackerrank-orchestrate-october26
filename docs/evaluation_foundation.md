# Evaluation foundation

This document describes the evaluator milestone: input loading, contract validation, and
reference comparison. A subsequent evidence-normalization and temporal identity module is
now available through `ingest`; see `ingestion_identity.md`. Actual prediction generation
is available through `solve`; see `audit_solver.md`. Evaluation now also reports per-case
missing/extra steps and mismatch categories without altering matching definitions. The evaluator itself does not
interpret business evidence, classify deletion intent, infer resource state, or generate
remediation plans. No model provider or framework is required.

## Separation of responsibilities

- `code/deletion_audit/inputs.py` reads only the chosen request split, evidence manifest,
  activity catalog, and identity-audit catalog. It validates their schemas and metadata.
- `pipeline.py` uses those loaders to produce a readiness report with sorted case IDs,
  cutoffs, counts, and unresolved totals. It has no reference-answer import or access.
- `contract.py` validates prediction CSVs against the chosen requests and catalog.
- `evaluator.py` reads the sample reference only for explicit evaluation. The CLI limits
  this command to the sample split. It never uses reference data to generate predictions.
- `selftest.py` generates temporary reference-derived evaluator fixtures. This path is
  explicitly labeled test data and is never invoked by `run`.
- `cli.py` imports evaluation/self-test modules only for their respective commands.

The default dataset is resolved relative to the source checkout, so absolute entry-point
commands also work from another current directory. Reports cannot overwrite any dataset
file or the supplied predictions. Tests use disposable synthetic fixtures outside the
original dataset. The pipeline has zero prediction rows by design; `ready_for_audit` means
input metadata loaded, not that a deletion decision has been established.

## Contract validation

The CSV must have exactly `case_id,deletion_status,steps_json` in that order, with no extra
or missing cells. Case IDs must exactly match the chosen request IDs, appear once each,
and be sorted lexicographically as strings. Request filenames are selected explicitly:
sample uses `sample_deletion_requests.csv`; full uses `deletion_requests.csv`.

Statuses are exactly COMPLETE, INCOMPLETE, or NOT_APPLICABLE. The JSON must be a strict
array; duplicate object keys, NaN/Infinity, numeric overflow, and malformed JSON are
rejected. Every step must have exactly the seven contract fields. `step_no` is an integer
(not a boolean or float), numbered consecutively from one. Other fields are strings;
system/resource IDs must be nonempty and have no surrounding whitespace.

Phase/operation/state combinations come from the fifteen allowed operations in
`problem_statement.md`. Ordering is phase, explicit operation-table rank, system ID, then
resource ID. Alphabetical operation sorting is incorrect. Repeated operations for the
same resource/phase are rejected even if their evidence strings differ.

COMPLETE requires at least one verification and allows verification only. INCOMPLETE
requires all three phases; every finding needs its corresponding remediation and final
check for the same system/resource. Exposed PII may map to either redaction plus a
redaction check or anonymization plus an anonymization check. Remediation without a
corresponding finding is rejected. Extra verification of already-compliant or retained
resources remains allowed. NOT_APPLICABLE requires an empty array. These are structural
checks; deciding which resources should be present in the answer is outside this milestone.

Findings and COMPLETE verifications need evidence. INCOMPLETE remediation and verification
must use the empty string. Evidence IDs must exist in `evidence_files.csv` (`file_id`),
`system_activity.csv` (`activity_id`), or `user_audit_log.csv` (`audit_id`). IDs are not
accepted merely because their prefix looks plausible. Manifest files must exist beneath
the dataset evidence directory. Availability is the file's manifest `captured_at` or the
activity/audit row's `event_time`. It must be at or before that request's `audit_at`;
equal instants and equivalent timezone offsets are allowed. Request timestamps must be
timezone-aware and satisfy requested <= reported <= audit.

**Chronological scope:** this catalog check rejects future files/events. It does not
extract embedded business observation times from PDFs, images, SQL, logs, or JSON, prove
that evidence supports the stated resource/state, or reconstruct competing versions.
An existing but semantically wrong evidence ID can pass structural validation and will
lose evidence-field/step/exact credit against the reference. Embedded observation-time
checks, identity relevance, policy correctness, and evidence entailment belong to the
later audit engine. Passing this validator is not proof that deletion is complete.

## Matching and metrics

All metric values are fractions in [0, 1]. The report includes raw numerators/counts,
per-field results, per-case comparisons, validation issues with row/step locations, and
the matching definitions below. The evaluator validates the reference first and refuses
to score corrupt reference data. Its definitions are local diagnostics; the hidden grader's
precise matching formula is not supplied.

### Case-level metrics

The denominator is every case in the selected request/reference set, including missing
predictions. A duplicate case is quarantined: none of its rows receives case-level or
matched-step credit. Unknown cases do not add to this case denominator, but invalidate
the file and add false-positive steps and unmatched field slots.

- **Status accuracy:** unique predicted rows with the correct status / expected cases.
  Step validity is independent, so a correct status with broken JSON may earn status credit.
- **Sequence accuracy:** unique rows whose entire ordered step array equals the reference
  / expected cases. Includes all seven fields and step numbers, excludes case status.
  JSON key order and whitespace are ignored. This is independent of contract validity.
- **Exact-case accuracy:** unique rows with correct status, an identical ordered array,
  and no case validation issue / expected cases. Any file-level schema or row-order error
  makes all exact-case credit zero. Unexpected cases alone do not remove correct expected
  cases' exact credit; the separate `validation.valid=false` must still be enforced.

### Step precision, recall, and F1

Micro-average multiset matching within each case on the step's six non-number fields:
phase, system, resource, operation, state, and evidence. Extra keys are retained in the
matching token and therefore prevent an exact step match. `step_no` and array position
are excluded here so order mistakes can be distinguished from missing facts. JSON value
types are preserved. Count repeated steps with their multiplicities, never as a set.

`precision = TP / predicted steps`, `recall = TP / reference steps`,
`F1 = 2 * precision * recall / (precision + recall)`.

All unexpected and duplicate-case rows add predicted steps but cannot contribute TP.
Unparseable/non-array JSON contributes one opaque false-positive step instead of being
silently treated as an empty answer. Parsed malformed step elements also count as
predicted items and cannot match valid reference steps. Missing expected steps remain FN.
Grammar errors are reported separately: a numbering-only error can retain perfect step
F1 while failing contract, sequence, and exact-case checks.

If both expected and predicted step collections are empty, precision/recall/F1 are 1.
No predictions against a nonempty reference gives precision/recall/F1 of 0. An empty
reference with extra predictions has recall 1, precision 0, and F1 0. Case-level metrics
still penalize missing NOT_APPLICABLE cases, even though their reference has zero steps.

### Field-level accuracy

Within a unique expected case, align steps by `(phase, system_id, resource_id)`. For
repeated anchors, pair in occurrence order. Compare all seven fields including `step_no`
with strict type equality. This alignment avoids an evidence or operation error making
every field incorrect, and does not use an optimizer to select favorable matches.

Each paired step occupies one slot; each unmatched predicted or expected step also
occupies a slot with seven incorrect fields. Duplicate-case rows are all unmatched;
their expected steps also remain unmatched. Unexpected cases and opaque malformed rows
add unmatched slots. A changed anchor produces an unmatched expected and predicted slot.

`overall field accuracy = correct field values / (7 * slots)`; each field's accuracy is
its correct values / slots. No slots gives 1. Status is reported by its own case metric.

## Commands and exit codes

From the repository root:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py run --split sample --report artifacts/sample_pipeline.json
python code/main.py run --split full --report artifacts/full_pipeline.json
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/main.py validate --split full --predictions output.csv --report artifacts/full_validation.json
python code/main.py self-test --report artifacts/evaluator_self_test.json
```

The sample-prediction and full-prediction paths above must be supplied by a future solver;
`run` intentionally does not create them. For a quick **reference self-comparison only**:

```text
python code/main.py evaluate --split sample --predictions dataset/sample_output.csv --report artifacts/reference_self_comparison.json
```

This command and the controlled self-test measure evaluator consistency, not solver skill.
Exit code 0 means contract-valid/success, 1 means invalid predictions with diagnostics,
and 2 means an input/configuration error. Accuracy alone is not an exit-code threshold.
Use `validate --split full` rather than `evaluate --split full`, which is rejected.

## Remaining work

Evidence normalization (including machine-readable observation timestamps) and identity
history are now implemented in separate modules. The audit engine still needs PNG extraction,
typed PDF business interpretation, authorization classification, scoped temporal state
reconstruction, policy application, dependency analysis, grounded citations, and prediction serialization.
No full-run prediction accuracy or model token/cost performance is claimed here. Preserve
the raw harness trace in its existing location; final trace packaging follows
`agent_trace_instructions.md` after the session is closed, rather than copying an active
or unrelated session into the repo.

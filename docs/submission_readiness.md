# Submission readiness and uncertainty investigation

Measured 25 October 2026. **The goal of a fully compliant 518-case submission is still
blocked by evidence gaps.** This iteration implements source-backed improvements rather
than changing the validator, accepting future evidence, or manufacturing output labels.

## Actual results

| Metric | Actual sample predictions |
| --- | ---: |
| case_status_accuracy | 75.000000% |
| exact_case_accuracy | 28.125000% |
| step_precision | 99.315068% |
| step_recall | 75.129534% |
| step_f1 | 85.545723% |
| field_accuracy | 72.606775% |
| sequence_accuracy | 28.125000% |

Sample: **24/32** contract-valid, **8** unresolved; all 32 diagnostic rows written.
Status correct 24/32, exact cases and sequences 9/32, step matches 145/146 predicted versus
193 reference steps. These metrics are unchanged from the previous iteration.

Full: **413/518** contract-valid, improved from **408/518**; **105** unresolved verdicts,
down from **110**. Full ground-truth accuracy is unavailable. Status distribution:
`{'INCOMPLETE': 348, 'UNRESOLVED': 105, 'COMPLETE': 55, 'NOT_APPLICABLE': 10}`. All 518 diagnostic rows are written. There are **126** cases with
some incomplete proof/plan scope: 105 unresolved verdicts plus 21 decided cases whose
known violations support INCOMPLETE but whose entire plan scope remains uncertain.
Contract validity is a schema property; it does not certify semantic completeness.

**185 tests pass**, preserving all prior 152 tests and adding 33 regressions. The original
five-scenario evaluator controlled self-test passes separately. All **103 dataset file
SHA-256 hashes** match the turn-start inventory (`artifacts/iteration_dataset_integrity.json`).
No original dataset file, organizer truth, API key or model API is used for predictions.

## Reproduce

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/evaluation/diagnose_solver.py --predictions artifacts/sample_predictions.csv --solver-report artifacts/sample_solver_report.json --output artifacts/sample_mismatches.json --extractions artifacts/ocr_cache
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json --extractions artifacts/ocr_cache --submission-output output.csv
python code/main.py validate --split full --predictions artifacts/full_predictions.csv --report artifacts/full_validation.json
python code/evaluation/abstentions.py --before artifacts/iteration_baseline/full_solver_report.json --after artifacts/full_solver_report.json --output artifacts/full_abstention_review.json
python code/evaluation/abstentions.py --before artifacts/iteration_baseline/sample_solver_report.json --after artifacts/sample_solver_report.json --output artifacts/sample_abstention_review.json
python code/main.py self-test --report artifacts/evaluator_self_test.json
```

Native extraction uses Windows PowerShell 5.1 and the installed Windows.Media.Ocr English
recognizer. It writes outside dataset/, caches per manifest file ID and byte hash, and reports
unavailability explicitly on other platforms or missing recognizers. Core Python components
work without it or API keys. Previously generated valid caches can be consumed on other
platforms. The `--extractions` argument is explicit; caches are not silently discovered.
The snapshot of previous reports in `artifacts/iteration_baseline/` is diagnostic history,
never prediction input. For a future comparison, preserve the existing reports there before
running the new implementation.

`solve`, `validate` and `evaluate` still exit **1** for these unresolved outputs; artifacts
are written for inspection. Fatal input/cache/configuration errors return **2**. OCR returns
1 for unavailable extraction and preserves explicit missing records. Root `output.csv` was
**not published**: the publication guard requires full split, complete verdict/proof scope,
strict contract validity and dataset integrity. It preserves any previous submission file
when blocked, and publishes atomically only when eligible. Diagnostic paths and submission,
report and cache paths are protected against overwriting dataset or extraction inputs.

## What changed

1. Added native OCR caching and eight narrowly typed screenshot readbacks. These cover
   literal account, selected search document, active connector, attributable analytics,
   downloadable export, shared support conversation, security journal and marketing profile
   facts. Matching never repairs ambiguous OCR letters/digits or derives resource IDs from
   user/case IDs. The selected details panel is used for multi-row export/connector/search
   screens; unrelated rows do not establish ownership. Raw text and word boxes remain in
   provenance. Cache schema, original file ID/path/capture time and SHA-256 are validated.
2. Three screenshots remain **text/context only**: backup, deleted-reference registry and
   object storage. Archive existence does not establish restore permission; a displayed stable
   reference does not prove every direct identifier was removed; an object listing does not
   prove ownership or attachment contents. All eleven raw PNG pending records remain for
   inventory compatibility, with the overlay outcomes explicitly listed in `screen_extractions`.
3. Added a signed-journal PDF adapter requiring explicit resource, subject reference and
   retention deadline. It proves a retained security record exists; an account-closure event
   in that record remains a claim about profile deletion. No account absence is inferred.
4. The five resolved previous full-run abstentions are **case_35, case_39, case_50, case_52, case_53**. Each now has a
   direct source-backed violation and ordered remediation/checks. Remaining issues are retained.
5. Added exact OCR subject corroboration before treatment. The marketing screenshot's OCR
   subject does not match the catalog-linked subject. It is withheld with
   `OCR_SUBJECT_LINK_UNCORROBORATED`, not assigned through fuzzy names, repaired email text,
   or a trusted catalog result. No deletion finding is manufactured for that subject.
6. Explicit copy identities such as `eu_west` and `ap_south` remain separate even when their
   labels do not contain the word `replica`. A clean copy cannot clear a dirty independent copy.
7. Introduced `AuditDecision.status: str | None` through `decide_case`. **Unresolved is now
   null internally**, with separate resolution/cause/action diagnostics. Diagnostic CSV rows
   have a blank status and fail validation openly. The legacy `audit()` tuple is retained for
   compatibility with existing callers/tests, but its old INCOMPLETE placeholder is never
   serialized as a submission verdict. No UNKNOWN label, invented finding or empty COMPLETE
   proof is added to the contract.

## All abstentions examined

The baseline full-run 110 abstentions had disjoint issue patterns:

| Original issue pattern | Cases |
| --- | ---: |
| Primary profile verification ungrounded only | 96 |
| Primary proof ungrounded plus no direct resource state | 11 |
| Primary proof ungrounded plus required kept record missing | 2 |
| No direct resource state only | 1 |

All eight sample abstentions were inspected: `case_01`, `case_02`, and `case_04` have no
admissible exact resource ownership link. `case_21` and `case_25` through `case_28` have
retained/downstream records but lack grounded primary verification; potentially useful links
in later captures cannot be backfilled across audit_at. These are authorized deletion requests,
not NOT_APPLICABLE. Ten full requests are classified non-deletion from their supplied text,
including the nine previously empty-link cases; workflow classifications are not treated as
consent or state proof.

Current full unresolved cases, once per cause (causes overlap):

| Cause or investigation lead | Cases |
| --- | ---: |
| absent_verification_evidence | 105 |
| temporal_admissibility_gap | 40 |
| inadequate_scoped_negative_evidence | 2 |
| policy_ambiguity | 2 |
| unsupported_source_parsing | 1 |
| missing_ownership | 1 |

The 40 temporal leads mean potentially useful subject links occur in excluded later sources;
they do **not** mean 40 invalid joins were admitted. Negative-scope/policy labels are hypotheses
requiring inspection, not assertions that the underlying negative is false. A genuinely missing
required retained record also lacks a supported restoration operation in the submission table;
the engine records this rather than inventing an operation.

Machine-readable reports:

- `artifacts/full_abstention_review.json`: every original 110 abstentions, original issue
  pattern, current outcome, proposed next actions, and all 518 current per-case diagnostics.
- `artifacts/sample_abstention_review.json`: every original eight abstentions and all 32 cases.
- `artifacts/sample_mismatches.json`: expected/predicted statuses, every missing/extra step,
  admissible/excluded source IDs and mismatch classifications, in the evaluation-only path.
- Both solver reports preserve resource states, copy scopes, original observation/source IDs,
  uncertainty causes, proposed next actions, cutoff, verdict resolution and plan completeness.

## Read-only investigator interface

`code/deletion_audit/investigator.py` exposes `AuditTools` and an `Investigator` protocol:

| Tool | Behavior |
| --- | --- |
| `search_evidence` | Exact user/email/hash/phone/resource/file-ID search; only observations available at the pinned cutoff |
| `trace_identity` | Known identity versions and exact resource ownership bases at that cutoff |
| `inspect_timeline` | Admissible, ordered resource observations, provenance, and direct state versus claim distinction |
| `explain_policy` | Exact supplied CSV rule or explicit contract flow rule; no invented policy fallback |

Tool schemas are closed JSON schemas; a fixed dispatcher rejects arbitrary methods, arguments,
execution/file-writing tools and cutoff overrides. Result limits are 1..100. Returned results
are detached copies, so a client cannot mutate identity, evidence or policy through them.
There is no LLM client, framework, provider dependency or automatic proposal acceptance.
File-ID search lets an investigator read untyped OCR/PDF context without arbitrary disk access.

Exact remaining integration work:

1. Add an optional provider adapter and bounded tool loop using the exported schemas, with
   a read-only case context and no CSV/decision write tool. Core CLI must remain keyless.
2. Define a structured investigation proposal containing observation IDs, explicit subject
   links, temporal/copy scope and policy-condition evidence. A proposal cannot itself choose
   an accepted verdict or add a new operation.
3. Implement deterministic proposal validation: admissible source IDs, literal identifiers,
   original-source provenance, exact subject/resource bindings and supported conditional policy.
   Reject future sources, fuzzy/repaired OCR IDs, injected instructions and unsupported claims.
4. Cache by source hashes, extraction/tool versions, identity knowledge and audit_at. Record
   provider/model, calls, input/output tokens, elapsed time, failures and estimated cost; enforce
   call/token/cost caps and preserve unresolved results on unavailable keys/provider failures.
5. Rerun deterministic reconstruction, planning, strict validation and sample evaluation after
   accepted grounded additions. Integrate only changes that improve evidence-backed coverage.
   If no admissible public link exists, an AI model cannot legitimately supply it: supporting
   participant evidence or clarification of the unresolved-case contract is needed.

## Runtime, usage and changed files

Latest local runtimes: sample 11.112s, full 16.627s (vary by
machine/load). Application model calls, input/output tokens, total/average token usage and
model cost are all **zero**. Native OCR is a local recognizer, not an application LLM call.
Development-agent usage is separate and retained in the original structured harness trace.
Logs remain append-only. No archive is created while the active trace is being written.

Added: `code/deletion_audit/extractions.py`, `ocr_cache.py`, `sufficiency.py`, `investigator.py`,
`code/tools/extract_png.ps1`, `code/evaluation/abstentions.py`,
`tests/test_extractions.py`, `tests/test_investigator.py`, and this document.
Updated: `code/deletion_audit/solver.py`, `state.py`, `cli.py`,
`code/evaluation/diagnose_solver.py`, `tests/test_solver.py`, `tests/test_investigator.py`,
`README.md`, `docs/audit_solver.md`, `code/evaluation/evaluation_report.md`,
`code/evaluation/usage_report.md`, and append-only `log.txt`.
Ignored generated outputs remain under `artifacts/`. Existing unrelated working changes are
preserved. No commit, external submission, model integration, frontend or framework was added.

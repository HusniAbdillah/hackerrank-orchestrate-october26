> Current: [proof_quality_submission.md](proof_quality_submission.md). All three files exist; output.csv is best-effort, format-valid but 516/518 strict-valid. 337 tests pass. NO-GO for claiming full correctness; GO only for disclosed experimental upload. Historical sections follow.

> Latest: [active_agent_submission.md](active_agent_submission.md). Real full run: 9 DeepSeek calls, 3 accepted recommendations, zero prediction delta. 320 tests pass; strict 510/518, experimental 516/518. Historical reports follow.

> **Latest final sprint:** [final_submission_sprint.md](final_submission_sprint.md). 305 tests pass. Experimental candidate: 518 rows, 516 contract-valid, eight assumed verdicts; not evidence-validated. Strict coverage stays 510/518. Results below are historical.

> Final recovery: **235 tests**, opt-in candidate preflight blocked without unsupported claims. Current upload checklist and official schedule verification: [submission_recovery.md](submission_recovery.md). Previous iteration reports below are historical.

# Submission readiness — final forensic review, 25 October 2026

**Not submission-ready.** All 518 diagnostic rows are generated; 510 are contract-valid,
eight verdicts remain unresolved, and one additional decided case has incomplete plan scope.
Root output.csv was not published. All 103 dataset hashes remain unchanged. **232 tests pass**,
including the previous 224 and eight agent-boundary regressions; the controlled evaluator self-test passes.
The final source/contract review is in docs/final_forensic_review.md. Lack of COMPLETE
proof does not itself supply an allowed INCOMPLETE finding. The final iteration corrects
case_34's overbroad retention diagnosis but does not change CSV predictions or accuracy.

## Measured before and after

| Measurement | Iteration baseline | Final deterministic |
| --- | ---: | ---: |
| Sample status accuracy | 90.625% | 90.625% |
| Exact-case / sequence accuracy | 28.125% | 28.125% |
| Step precision | 97.546% | 97.546% |
| Step recall | 82.383% | 82.383% |
| Step F1 | 89.326% | 89.326% |
| Field accuracy | 77.447% | 77.447% |
| Sample contract-valid | 29/32 | 29/32 |
| Full contract-valid | 510/518 | 510/518 |
| Full unresolved | 8 | 8 |
| Decided incomplete plans | 1 | 1 |

The preceding debugging iteration improved full coverage but regressed public step accuracy. The literal object listing
and explicit sole-owner catalog link support three extra object_19 steps omitted by the
sample reference. They are retained rather than suppressed using sample labels. No sample
accuracy improvement or hidden full accuracy is claimed. All intermediate measurements
are preserved in artifacts/submission_debug/. See docs/submission_debugging.md for all 13
original abstentions, every candidate acceptance/exclusion, all 21 obligation ledgers and
all 23 sample exact-case discrepancies. The detailed matrix includes original request text,
audit_at, identity validity intervals, ownership source IDs, policy and raw fields.

Support message_text contact details are now recognized as direct exposed PII. This fixes
20 incomplete plans and three unresolved verdicts. Literal catalog/document/listing joins
resolve two more verdicts. Conjoined source availability includes the catalog link time;
an old image/document cannot backdate that knowledge. Mixed SQL tables without declared
origin-service coverage no longer create negative observations for unrelated resources.
Planner ordering, allowed operations/states, citations and numbering remain unchanged.

## Every remaining unresolved verdict

| Case | Audit cutoff UTC | Exact blocker and evidence |
| --- | --- | --- |
| case_46 | 2026-03-11 08:00 | activity_4011 links tombstone_17; evidence_42 registry view shows stable references but does not expose all identifier fields. Cannot prove redaction. evidence_67's account lookup does not prove tombstone state. |
| case_55 | 2026-04-30 11:00 | activity_4006 and evidence_32 ground backup_9287's archive context; restore permission/block is not displayed. Later restore/log activity is unavailable at cutoff. |
| case_63 | 2026-09-17 09:20 | activity_4008 links marketing_001 to the request subject, but evidence_60 visibly exposes another email. Cached Gemini extraction did not corroborate the subject; no fuzzy merge is permitted. |
| case_506 | 2026-02-08 07:00 | evidence_47 proves retained audit_record_1361, but has no grounded subject-specific account readback or declared exhaustive account inventory. |
| case_512 | 2026-02-08 07:00 | evidence_47 proves retained audit_record_4219; primary account identity/state remains ungrounded. |
| case_524 | 2026-01-29 12:00 | evidence_62 proves retained audit_record_5429; partial service readbacks do not identify this subject's absent primary account. |
| case_530 | 2026-01-29 12:00 | evidence_62 proves retained audit_record_2152; no admissible grounded primary final-state proof. |
| case_532 | 2026-01-29 12:00 | evidence_62 proves retained audit_record_4828, redacted support_7724, blocked backup_6344 and disabled data_flow_6987; these do not establish primary account deletion. |

Unresolved issue groups are disjoint: five primary-proof gaps, two unsupported direct
readback semantics, one screenshot identity conflict. Additional cutoff leads can overlap.
Missing evidence cannot justify either COMPLETE or an invented noncompliance finding.
Three sample requests still have no admissible resource link. Nine full empty-link cases
are justified non-deletion requests; full NOT_APPLICABLE count remains ten.

The remaining decided plan gap is **case_34**, now correctly RETENTION_CONDITION_UNPROVEN.
Earlier evidence_01 proves audit_record_3753 was available; later evidence_93 omits it from
the captured security table. Neither supplies that resource's retention period. Rule_12 is
conditional, so a required-retention breach is not established; dates belonging to other
records cannot be borrowed. The old REQUIRED_RETAINED_RECORD_MISSING claim was overbroad.
Other direct account/attachment violations still establish INCOMPLETE, but the policy gap
remains explicit and blocks publication. A proven retention breach would also require
clarification because no restore/recover-record operation is allowed. No invented operation
or PRESENT verification is emitted. The earlier 20 decided plan gaps remain cleared.

## AI, reproducibility and packaging

The current bounded correction pilot made seven successful live calls (DeepSeek six,
Gemini vision one), with 76,950 input / 3,056 output tokens and estimated USD 0.02904615.
case_17 explicitly retrieved its thirteenth observation through the new cursor. Four accepted
proposals are duplicates; no unique new facts, accepted enrichments or changed predictions.
Paid experimentation stopped after this pilot. The older zero-budget cache replay was a
previous iteration. Full details and historical accounting remain in code/evaluation/usage_report.md.

A fresh virtual environment installed requirements-dev.txt, extracted the runnable source ZIP,
and regenerated all 11 PNG extractions using Windows.Media.Ocr with the English recognizer.
Both 32-row sample and 518-row full CSVs were byte-identical to the working results, without
copying old caches or credentials. The source uses repository-relative paths and --dataset;
no user's Windows directory is hardcoded. This verifies Windows reproduction. Native OCR
on Linux/macOS is unavailable unless a separately validated extraction backend/cache is
provided; deterministic ingestion without images remains runnable with explicit gaps.

## Exact run and validation commands

From the repository root, with Python 3.11+ and Windows English OCR installed:

```text
python -m pip install -r requirements-dev.txt
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python -m pytest -q
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/evaluation/diagnose_solver.py --predictions artifacts/sample_predictions.csv --solver-report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache --output artifacts/sample_mismatches.json
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json --extractions artifacts/ocr_cache --submission-output output.csv
python code/main.py validate --split full --predictions artifacts/full_predictions.csv --report artifacts/full_validation.json
python code/main.py self-test --report artifacts/evaluator_self_test.json
python code/package_submission.py
```

solve/evaluate/validate intentionally return 1 for these unresolved diagnostic outputs;
artifacts are still written. Fatal input/configuration errors return 2. The unchanged
publication guard requires full validity, complete proof/plan scope and integrity.
code.zip is a source review archive, not evidence of submission eligibility. It includes
source, dependency/config instructions, tests, docs and both required evaluation report
locations; excludes dataset, credentials, predictions, intermediate caches, traces and nested
archives. Root log.txt remains append-only. Native traces are preserved; export only after
finishing/quitting the session per agent_trace_instructions.md.

## Next most valuable work

1. Locate admissible explicit primary-resource ownership; do not infer IDs from sample labels.
2. Obtain complete tombstone fields and backup restore-policy evidence at the required cutoff.
3. Resolve the screenshot/catalog subject conflict through independent exact identifiers.
4. Clarify retained-record absence/remediation semantics within the fixed operation table.
5. Reconcile the grounded object-listing scope with the public reference discrepancy before
   claiming further sample precision gains. Larger model budgets cannot supply absent evidence.

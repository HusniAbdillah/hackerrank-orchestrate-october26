# Final submission recovery and upload checklist

## Decision

The strict solver and validator are unchanged. The opt-in `code/prepare_submission.py` workflow reruns the full strict solver, independently checks CSV/JSON shape and the existing contract, records each unresolved/conditional decision, and publishes a separate candidate only when proof/plan gates pass. It never reads sample answers, trusts a stale report, invents steps, or fills a missing verdict. An existing candidate is preserved on failure.

Actual result: **BLOCKED_WITHOUT_UNSUPPORTED_CLAIMS**. All 518 diagnostic rows are present and CSV/JSON is well formed, but only 510 are contract-valid. Eight unresolved verdicts and one additional conditional plan gap (case_34) remain. There are 509 cases passing both strict verdict and complete proof/plan checks. Candidate schema validity is **not applicable: no candidate was generated**. Zero forced-format judgments, zero low-confidence rows published; eight verdicts would require unsupported assumptions. Root output.csv remains absent.

This is the requested infeasibility branch. A schema-only fallback cannot rescue case_55: COMPLETE would require unsupported restore-block proof, INCOMPLETE would require an unsupported active restore-risk finding, and NOT_APPLICABLE would misclassify an authorized deletion. A documented assumption cannot create a truthful cited step. Missing tombstone fields, conflicting screenshot identity and missing primary-account proof present the same boundary. Strict uncertainty is preserved.

`artifacts/submission_recovery/candidate_report.json` records each cutoff, authorization, strict issue and rejected status assumption. The strict CSV is `artifacts/submission_recovery/strict_predictions.csv`; the requested separate `submission_candidate.csv` is absent. Do not upload the diagnostic CSV as a valid output.csv.

## Sample exact-match analysis

All 32 samples were re-evaluated: status 90.625%; exact-case/sequence 28.125%; step precision 97.546012%, recall 82.383420%, F1 89.325843%; field 77.447426%; 29/32 contract-valid. Predictions and metrics are unchanged.

There are 23 non-exact samples, 34 missing verification steps, four extra steps and 45 aligned step-number shifts. No other aligned operation/state/system/resource/evidence field mismatch was found. Missing-step causes: 17 without grounded subject links, eight with links only after audit_at, seven anonymized records without historical ownership, two retained records without admissible subject links. No verified omitted planner obligation or policy-general solver correction follows from those counts. Three of the four extra steps are the grounded object_19 plan, retained rather than suppressed to fit reference labels. Per-case diagnostics are in `artifacts/submission_recovery/sample_mismatches.json`.

A participant independently reports missing sample-reference records and ambiguous account association in [official repository issue #19](https://github.com/interviewstreet/hackerrank-orchestrate-october26/issues/19). This is an unconfirmed participant report, not an organizer ruling or permission to use reference answers. No maintainer resolution was visible. Dataset files and labels remain unchanged.

## Organizer question — drafted, not sent

> When participant-visible evidence available by audit_at proves neither COMPLETE nor a permitted violation finding, how should we serialize the mandatory three-status row? Eight cases lack required tombstone/restore/primary-account proof or have screenshot identity conflicting with the catalog (case_63). Is corrected evidence available, or an official uncertainty rule specifying valid evidence-backed steps? Please confirm the final dataset revision and treatment of case_34's unsupplied retention condition.

Verified clarification routes: [repository issues](https://github.com/interviewstreet/hackerrank-orchestrate-october26/issues) and the [Orchestrate Discord invite](https://discord.gg/hackerrank-orchestrate) linked by the official event page. The invite itself was inaccessible through browsing. No message or issue was posted.

## Official requirements and time check

Sources checked on 25 October 2026:

- [Official statement](https://github.com/interviewstreet/hackerrank-orchestrate-october26/blob/main/problem_statement.md): exactly 518 sorted rows, three statuses, ordered permitted steps, source ZIP, output CSV, chat transcript and AI interview. Both evaluation/evaluation_report.md and evaluation/usage_report.md are required.
- [Official trace instructions](https://github.com/interviewstreet/hackerrank-orchestrate-october26/blob/main/agent_trace_instructions.md): complete structured traces in agent-trace.zip, staged after finishing/quitting the harness and reviewed/redacted before upload. Root conversation summaries do not replace native traces.
- [Official event page](https://www.hackerrank.com/hackerrank-orchestrate-october26): start 24 October 2026, 18:00 IST; advertised duration 24 hours. Arithmetic inference gives a nominal end of 25 October, 18:00 IST = 12:30 UTC = 19:30 Asia/Bangkok. **The authenticated submission closing timestamp was not verified.** This inference is not a confirmed deadline or extension. At 06:54 UTC, the nominal remaining window was 5h36m. Confirm the actual timer after signing in; the problem link redirected to login.
- Repository AGENTS.md still contains no configured October end timestamp. No September deadline is reused.

Required repository-prescribed submission URL:
https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

## Reproduction

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/prepare_submission.py --strict-output artifacts/submission_recovery/strict_predictions.csv --output artifacts/submission_recovery/submission_candidate.csv --report artifacts/submission_recovery/candidate_report.json --extractions artifacts/ocr_cache
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/submission_recovery/sample_evaluation.json
python code/main.py validate --split full --predictions artifacts/submission_recovery/strict_predictions.csv --report artifacts/submission_recovery/strict_validation.json
python code/package_submission.py --output artifacts/code.zip
```

Candidate preflight and validation intentionally exit 1 when blocked; exit 2 denotes path/input errors. `make prepare-candidate` runs the same workflow and propagates failure. The ordinary solve CLI and publication guard retain their previous behavior. No model calls or credentials are needed.

## Upload checklist and exact local names

| Item | Local filename | State / action |
| --- | --- | --- |
| Runnable source | artifacts/code.zip | Regenerated; excludes dataset, caches, environments, secrets and transcripts. Required reports are in evaluation/. |
| Mandatory prediction output | output.csv at repository root | **Absent; blocked.** Do not rename the invalid strict CSV to imply compliance. |
| Separate candidate | artifacts/submission_recovery/submission_candidate.csv | **Absent; no truthful 518-row candidate passed the gates.** |
| Candidate diagnostics | artifacts/submission_recovery/candidate_report.json | Ready for review/clarification; not the prediction upload. |
| Chat transcript | log.txt at repository root | Append-only; latest turn appended before response completion. Review before upload. |
| Native traces | artifacts/agent-trace.zip | Pending shutdown and reviewed export of every challenge session, per trace instructions. Current active session is not completely exported. |
| Evaluation report | code/evaluation/evaluation_report.md | Included as evaluation/evaluation_report.md; actual metrics and three independent business cases retained. |
| Usage report | code/evaluation/usage_report.md | Included as evaluation/usage_report.md; recovery run has zero model usage and no eligible output.csv. Historical usage retained. |
| AI interview | Online after submission | Pending; explain the bounded tool loop, strict grounding, zero incremental pilot gain and evidence gaps. |

Next: request organizer clarification/corrected evidence, confirm the authenticated timer, rerun preflight after a legitimate resolution, then upload an independently valid output.csv with source and transcripts. Mandatory output and complete trace export are still blockers. Verification results are in `artifacts/submission_recovery/verification.json`.

Final verification: 235 tests passed in the working checkout (30.91 seconds) and extracted source checkout (36.27 seconds). The latter used the previously isolated, declared-dependency environment and explicitly supplied native OCR cache regenerated in the preceding clean run; no credentials or caches were bundled in the archive. Its full candidate preflight produced the same refusal and byte-identical strict CSV. All 103 dataset SHA-256 values match the original inventory. The source archive contains 71 files, including the new workflow, tests, checklist and required reports; CRC, source identity and exclusions were checked. No source-policy change or sample accuracy gain is claimed. Agent trace export remains pending shutdown; the live root log is appended for this turn.

# Final proof quality and submission record

25 October 2026. Current source/results supersede older iteration narratives. Working suite: **337 tests passed**. Prior source, code.zip, predictions and reports are frozen and hashed under artifacts/proof_quality/before.

## Shipped artifacts and recommendation

All three upload files now exist: root **output.csv**, artifacts/**code.zip**, and authentic root **log.txt**. Output is EXPLICITLY EXPERIMENTAL BEST-EFFORT: 518 sorted rows, correct CSV/JSON format, **516/518 strict contract-valid**, eight assumption-based COMPLETE verdicts. It is not evidence-validated. Two failures remain: case_55/case_63 have no admissible verification. Root output_diagnostics.json preserves assumptions and strict failures; no verification, citation, resource or operation was invented.

**GO for an explicitly risky best-effort upload; NO-GO for claiming a fully contract-valid or fully proven result.** File availability and format do not establish correctness. Strict solver/validator and publication gate remain unchanged. Only the new explicit --publish-best-effort branch copies the candidate after independent format/citation checks; it tolerates only the disclosed empty-COMPLETE proof requirement, not other schema/citation/ordering errors. Its exit code stays 1 to signal strict failure.

Output SHA256: 4263f02a16d30b525c0cc9ff4fb9ee62657ebcb26d8aec65475cef8287b88aab. It is byte-identical to the prior best candidate: publication improved deliverable readiness, not predictions. Strict verdict coverage remains 510/518; 509 pass both internal verdict and complete proof/plan checks. Eight verdicts remain unresolved, plus case_34's conditional-retention plan gap.

## Implemented and verified changes

- AuditRecommendation now requires an eight-category Proof Ledger: authorization, identity, ownership, state, treatment, recreation, retention and plan. Entries name required proof, actual inspected observations, accepted source references, coverage, recommendation and admissible leads. Independent results and case-level prediction effects are added by code, not trusted from the model.
- Ledger checks reject invented/non-inspected references, inadmissible leads, dirty-state compliance claims, unsupported retention conditions and falsely complete plans. Accepted duplicate proof is never counted as a novel fact. Global scope without evidence stays unresolved.
- Routing inventories all 32/518 requests and prioritizes actionable original fields or shared-support policy context. Partial lead lists do not imply absence. Missing proof, late-only scope and contradictory identity are excluded. Full inventory: 92 conditional-context candidates, 407 unambiguous, ten non-deletion, eight without actionable proof, one identity conflict.
- An inherited sufficient-case gate initially suppressed conditional-policy routes without untyped leads. This was corrected and tested with a mocked provider. The new gate was not subsequently live-benchmarked: paid experiments stopped after the pilot showed no gain.
- Multilingual conjunction scope was corrected for Indonesian, Spanish, French, Portuguese and English, including a French account-negation conflict. Original omitted/null PII guards remain. All actual sample/full decisions remain unchanged.

## Actual model execution and metrics

The new pilot investigated sample case_29 through four real DeepSeek/deepseek-flash calls: 52098 input, 8079 output, USD 0.0253242 estimate at USD 0.30/input-million and 1.20/output-million. All usage was reported, no provider errors/retries/cache hits. Provider latency total 30.296 seconds; whole sample run 48.349 seconds.

The model selected policy tools, then source inspections, then returned and corrected an audit recommendation. Final ledger: nine ACCEPTED, four UNRESOLVED. Complete recommendation rejected because one finding was missing. Novel facts, resolved obligations, changed predictions, improved cases and regressed cases: zero. No further paid calls were made. Current selected output-producing run: 30.341 seconds, zero live model calls/tokens/cache hits/USD, explicitly capped after the pilot. Older nine-call full investigations remain historical and are not attributed to this run.

| Sample metric | Before | After |
| --- | ---: | ---: |
| Status | 90.625% | 90.625% |
| Exact / sequence | 28.125% | 28.125% |
| Step precision | 97.546012% | 97.546012% |
| Step recall | 82.383420% | 82.383420% |
| Step F1 | 89.325843% | 89.325843% |
| Field | 77.447426% | 77.447426% |
| Sample strict-valid | 29/32 | 29/32 |
| Full strict-valid | 510/518 | 510/518 |
| Best-effort strict-valid | 516/518 | 516/518 |

34 missing sample verification steps persist: 17 without grounded ownership, eight with only late links, seven anonymized records lacking historical ownership and two retained-record links without admissible proof. No new exact join was justified. Grounded object-storage steps are retained. Detailed new diagnostics: artifacts/proof_quality/sample_mismatches.json.

## Exact reproduction and upload

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/main.py solve --split sample --output artifacts/proof_quality/agent_sample.csv --report artifacts/proof_quality/agent_sample_run.json --extractions artifacts/ocr_cache --ai auto --ai-cache artifacts/proof_quality/pilot_cache --max-ai-cases 2 --max-model-calls 8 --max-cost-usd 0.35 --ai-max-rounds 4 --ai-case-seconds 120
python code/main.py evaluate --split sample --predictions artifacts/proof_quality/agent_sample.csv --report artifacts/proof_quality/sample_evaluation.json
python code/prepare_submission.py --strict-output artifacts/proof_quality/selected_full.csv --output artifacts/proof_quality/selected_candidate.csv --report artifacts/proof_quality/selected_run.json --extractions artifacts/ocr_cache --candidate-policy observed-scope --ai auto --ai-cache artifacts/proof_quality/full_cache --max-ai-cases 0 --max-model-calls 0 --max-cost-usd 0 --publish-best-effort output.csv
python code/main.py validate --split full --predictions output.csv --report artifacts/proof_quality/output_validation.json
python code/package_submission.py --output artifacts/code.zip
```

The measured pilot preceded the sufficient-gate correction and selected one case, not all five now eligible samples. A new live run with current routing can select different cases and incur cost; it is not a replay of the recorded pilot. Offline reconstruction uses --ai none and regenerated native OCR, not undeclared model caches. Real calls set process settings LLM_MAX_RETRIES=0, LLM_TIMEOUT_SECONDS=45, LLM_MAX_TOKENS=4096; credentials remain environment/ignored .env only.

Upload artifacts/code.zip, root output.csv, and root log.txt separately. Official packaging retains README.md and code/, with reports and human-readable traces under code/evaluation/. Additional copies at evaluation/ satisfy repository instructions. ZIP excludes dataset, caches, environments, secrets and nested archives. Actual fresh tests/OCR/full reproduction, source correspondence, ZIP CRC and all 103 dataset hashes are recorded in artifacts/proof_quality/verification.json. Native agent-trace.zip still requires session shutdown and reviewed export; do not copy active native traces.

Interview pitch and case study: code/evaluation/interview_brief.md. Actual trace/ledger tables: code/evaluation/agent_execution_report.md. Submission page: https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists . No authenticated closing timestamp is asserted.

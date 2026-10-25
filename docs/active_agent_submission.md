# Active runtime audit agent — measured execution

25 October 2026. Previous source, archive, predictions and reports are frozen under artifacts/active_agent/before. The existing agent was extended; no multi-agent framework or solver rewrite was introduced.

## Actual role and validation

--ai auto/deepseek/gemini now enables AuditRecommendation: intent/target/quote, proof goals, resources, source references, unresolved obligations, recommended verdict, justification, findings, remediation, verification, alternatives and confidence rationale. Internal UNRESOLVED never becomes a CSV status. --ai none is the baseline. Legacy facts-only Python clients still work.

The same five read-only tools remain. The model can perform two retrieval rounds and follow a concrete lead; on the penultimate turn it may instead submit a draft and receive one correction. Measured runs cap four turns and six successful tools per case. Invalid calls are recorded; no arbitrary filesystem, shell, web or destructive action exists.

recommendations.py independently checks literal request quote/authorization, ownership, source identity, event/capture cutoff, policy, operation/state and complete canonical obligations/citations. Projected negatives are recomputed by existing scope logic, not trusted from model text. Existing fact/link/field guards are unchanged. Newly validated facts can trigger case-local replanning; otherwise the baseline survives. Intent, verdict and complete-plan components are reported separately. ACCEPTED means agreement within independently grounded scope, not proof about hypothetical unobserved copies. Unresolved questions remain visible.

## Live runs

| Run | Calls | Input tokens | Output tokens | Estimate USD |
| --- | ---: | ---: | ---: | ---: |
| Initial three-sample pilot | 9 | 102492 | 6460 | 0.0384996 |
| Corrected three-sample investigation; all 32 predictions evaluated | 11 | 135048 | 10919 | 0.0536172 |
| 518-row agent-enabled full run | 9 | 96938 | 7079 | 0.0375762 |
| Candidate materialization, revalidated cache | 0 new | 0 new | 0 new | 0 new |
| Iteration total | 29 | 334478 | 24458 | 0.1296930 |

Provider and returned model: DeepSeek/deepseek-flash. Gemini is available but was not called in this iteration; no further vision request was justified. All 29 calls succeeded with reported usage and no retries/provider errors. Configured estimates: USD 0.30/input-million and 1.20/output-million, not invoices. Older experiments are separate historical usage.

The live full run has 104017 tokens, 200.805019 tokens/request, USD 0.0000725409/request; average investigated-case cost is USD 0.0125254. Cost per newly resolved obligation is undefined because zero new obligations were resolved.

Actual model-selected tools, arguments, rounds, verdict justifications, proposed steps/citations and validation are in code/evaluation/agent_execution_report.md, generated from real application reports. It contains concise decision summaries, not hidden chain-of-thought.

- Sample case_07: source/policy inspection followed by a literal filename search and another document view; INCOMPLETE, delete two attachments and verify absence. Complete plan accepted; two fact proposals duplicate existing observations.
- Sample case_06: source/timelines/policy followed by identifier searches; INCOMPLETE for a remaining search entry. Verdict/known plan accepted with primary-state uncertainty retained.
- Sample case_17: backup/tombstone source/policy investigation followed by more readbacks; INCOMPLETE for restore risk. Required retained/account checks included after feedback; missing tombstone state remains.
- Full case_113: original sources, profile/retention policy, then additional source and subject search; COMPLETE with account absence and retained-audit verification, accepted within grounded scope.
- Full case_114: source/policy then source/search follow-up; INCOMPLETE, delete search record, redact support PII, verify both. Accepted; shared-context/global questions remain documented.
- Full case_115: sources/policies then timelines; INCOMPLETE for remaining account/search records, delete and verify, accepted.

Initial plans failed future-citation, omitted-verification and source-reference checks. One targeted correction tightened remediation citation schema, clarified verification obligations and exposed independently projected negative proof to validation. Corrected sample outcomes: one ACCEPTED and two ACCEPTED_WITH_UNRESOLVED_OBLIGATIONS. Full outcomes: three ACCEPTED. No further paid experiments followed.

## Measured comparison and coverage

Full: 518 requests, three live-investigated, 356 skipped as deterministically sufficient, ten non-deletion, 149 eligible but skipped because the three-case cap was exhausted. Do not describe all 518 as model-investigated. Candidate materialization revalidated those three cached recommendations: zero new calls; original nine-call generation usage is preserved separately.

| Sample metric | Baseline | Agent |
| --- | ---: | ---: |
| Status | 90.625% | 90.625% |
| Exact / sequence | 28.125% | 28.125% |
| Step precision | 97.546012% | 97.546012% |
| Step recall | 82.383420% | 82.383420% |
| Step F1 | 89.325843% | 89.325843% |
| Field | 77.447426% | 77.447426% |
| Sample valid | 29/32 | 29/32 |
| Full strict valid | 510/518 | 510/518 |

New facts/enrichments, changed predictions, improved cases and regressed cases: zero. Baseline 305 tests passed; final working suite 320 passed. Existing multilingual/field-coverage fixes and grounded object-storage steps remain. Source ZIP/fresh checks are in artifacts/active_agent/verification.json.

Eight strict unresolved verdicts: case_46, case_55, case_63, case_506, case_512, case_524, case_530, case_532. case_34 has an additional retention-condition plan gap. 509 cases pass internal verdict plus complete proof/plan checks, not a hidden-label correctness guarantee.

Actual candidate: artifacts/active_agent/submission_candidate.csv. Exactly 518 sorted rows, CSV/JSON valid, 516 contract-valid, eight explicitly assumed COMPLETE verdicts. case_55/case_63 lack verification and fail STATUS_SHAPE. Nine proof/plan risks remain in candidate_report.json. No evidence/resource/operation was invented. Root output.csv remains absent.

## Exact reproduction

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/main.py solve --split sample --output artifacts/active_agent/baseline_sample.csv --report artifacts/active_agent/baseline_sample_run.json --extractions artifacts/ocr_cache --ai none
python code/main.py solve --split sample --output artifacts/active_agent/agent_sample.csv --report artifacts/active_agent/agent_sample_run.json --extractions artifacts/ocr_cache --ai deepseek --ai-case-id case_06 --ai-case-id case_07 --ai-case-id case_17 --ai-cache artifacts/active_agent/final_cache --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.35 --ai-max-rounds 4 --ai-case-seconds 120
python code/main.py evaluate --split sample --predictions artifacts/active_agent/agent_sample.csv --report artifacts/active_agent/agent_evaluation.json
python code/main.py solve --split full --output artifacts/active_agent/agent_full.csv --report artifacts/active_agent/agent_full_run.json --extractions artifacts/ocr_cache --ai auto --ai-cache artifacts/active_agent/final_full_cache --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.45 --ai-max-rounds 4 --ai-case-seconds 120 --submission-output output.csv
python code/prepare_submission.py --strict-output artifacts/active_agent/chosen_full.csv --output artifacts/active_agent/submission_candidate.csv --report artifacts/active_agent/candidate_report.json --extractions artifacts/ocr_cache --candidate-policy observed-scope --ai auto --ai-cache artifacts/active_agent/final_full_cache --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.45 --ai-max-rounds 4
python code/evaluation/report_agent_audit.py --run artifacts/active_agent/agent_sample_run.json --run artifacts/active_agent/agent_full_run.json --output code/evaluation/agent_execution_report.md
python code/package_submission.py --output artifacts/code.zip
```

Measured calls set process variables LLM_MAX_RETRIES=0, LLM_TIMEOUT_SECONDS=45, LLM_MAX_TOKENS=4096. Keys come only from environment/ignored .env. Missing credentials are explicit skips, not live runs. A fresh cache can incur calls. For offline clean reproduction, --ai none plus regenerated Windows OCR reproduces these unchanged canonical predictions. Model cache/credentials are not packaged; tests use mocked transports.

The official README packages README.md and code/. Our archive preserves code/, README/config and required reports at code/evaluation/ and evaluation/. Upload code.zip, predictions CSV if accepted with disclosed risks, and authentic root log.txt separately. No fully valid output.csv exists. Native trace ZIP requires session completion/shutdown and secret review. Interview briefing: demonstrate real follow-up tool use, independent rejections, accepted audit recommendations, original cache usage, and honestly state zero accuracy gain.

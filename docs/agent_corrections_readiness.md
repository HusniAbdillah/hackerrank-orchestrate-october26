# Agent boundary corrections and measured readiness

25 October 2026. This iteration changes agent context, schemas, grounding feedback and the case-local handoff. It does not redesign deletion policy or use reference answers in prediction.

## Implemented and independently checked

- `compact()` preserves all observation arrays and original strings. Only OCR word boxes and local cache paths are omitted, with an explicit omission marker. Tools return at most 12 observations per page, newest first, with `total_count`, `shown_count`, `offset`, `truncated`, `next_cursor`, fixed cutoff and ordering. Cursors bind the complete admissible result contents/cutoff and reject stale or unrelated results. Contradictory observations remain separately retrievable. Oversized provider inputs fail explicitly rather than silently discarding evidence.
- Resource searches have a conditional JSON schema requiring nonempty `system_id`. Invalid argument/schema calls do not spend successful-tool budget; model-turn and API caps remain unchanged. Budget-denied requests still appear in traces.
- Proposal categories are the 15 supplied policy categories plus the contract's DATA_FLOW. LINK_ASSET requires SUPPORT_ATTACHMENT/PRESENT and literal catalog/listing proof. Exact errors distinguish unsupported category, missing admissible catalog, unsupported sole ownership, missing literal filename and unsupported quote.
- At most one schema/grounding correction is allowed, only if a model turn remains. Rejected proposal contents and precise errors are retained and returned to the model. A final-turn rejection cannot purchase another turn. Unit transports demonstrate correction and persistent rejection; the live pilot reached final proposals on turn three, leaving no grounding correction turn.
- Validated vision metadata updates retain the original observation_id, immutable fields, source provenance, image hash and cutoff. A per-case EvidenceStore replaces that observation and rebuilds indexes. The shared store remains unchanged. An actual solve() regression spies on both decisions and proves delivery of the same-ID update. No new state, identity edge or relaxed completeness check follows from a corroboration flag.
- Every live model turn records round ID, generated call ID, context hash, start timestamp, tool-call batch and concise host decision summary. Tool entries link model/tool call IDs, arguments, full bounded results/counts/cursor, budget consumption and validation. Usage journals share call IDs. Proposal reasoning summaries are short explicit outputs; hidden chain-of-thought, Gemini thought parts and credentials are not persisted. Cache entries retain their original round traces and are marked CACHE_HIT on reuse. Context hashes identify inputs but are not a complete replay transcript.
- Novelty compares system/resource/category/source/time/state assertions, not derived ID spelling. An equivalent asset assertion with a new ID is recorded as a duplicate.

## One preplanned live pilot, then stop

Deterministic baseline and all 32 DeepSeek-mode sample rows were generated/evaluated independently. Only case_07/case_17 were selected for paid text investigation; all other sample rows remain deterministic. Explicit diagnostic selection can investigate an otherwise sufficient case, but still requires a grounded resource. Gemini vision investigated case_63 in a full 518-row run. This is not a Gemini sample evaluation or a fully paid full-dataset batch.

| Metric | Deterministic baseline | DeepSeek selected-case run | Gemini case_63 full run |
| --- | ---: | ---: | ---: |
| Sample status accuracy | 90.625% | 90.625% | Not evaluated on samples |
| Sample exact-case / sequence | 28.125% | 28.125% | Not evaluated on samples |
| Step precision | 97.546012% | 97.546012% | Not evaluated on samples |
| Step recall | 82.383420% | 82.383420% | Not evaluated on samples |
| Step F1 | 89.325843% | 89.325843% | Not evaluated on samples |
| Field accuracy | 77.447426% | 77.447426% | Not evaluated on samples |
| Sample contract-valid | 29/32 | 29/32 | N/A |
| Full contract-valid | 510/518 | N/A | 510/518 |
| Prediction changes against matching split | — | 0 | 0 |

Both provider integrations succeeded live, with zero API errors and no cache hits. DeepSeek deepseek-flash: six calls, 73,796 input / 2,713 output tokens, estimated USD 0.02539440 (configured USD 0.30/1.20 per million). Gemini gemini-3.5-flash-lite: one call, 3,154 input / 343 output tokens, estimated USD 0.00365175 (local configured USD 0.75/3.75 per million, overriding code defaults). Overall: seven calls, 76,950 input / 3,056 output, USD 0.02904615. These are configured tariff estimates, not provider invoices. No retry, model turn, tool or token budget was increased. Experiment caps were six calls/USD 0.12 text and one call/USD 0.03 vision, 3072 output tokens/call, 90 seconds/case, zero retries.

Actual unique new grounded facts: **0**. Accepted metadata enrichments: **0**. Accepted duplicate proposals: **4**. Sample and full pilot CSVs are byte-identical to their deterministic split baselines. No incremental accuracy gain is claimed. Paid experimentation stopped after this pilot.

### Concrete live trace checks

- case_17 DeepSeek round 1 searches email: total_count=13, shown_count=12, truncated=true with next_cursor. Round 2 autonomously uses that exact cursor and receives the thirteenth observation (shown_count=1, offset=12, truncated=false). No resource query omits system_id. Three accepted readbacks (evidence_01:line:21, evidence_67:line:3, evidence_01:line:53) are all duplicates. Activity-as-state and resource-association proposals remain rejected.
- case_07 returns contract-valid SUPPORT_ATTACHMENT LINK_ASSET after retrieving the listing/catalog. It cites an already deterministically linked listing and is correctly counted as a semantic duplicate, despite its different derived observation ID. Two other claims/unsupported interpretations are rejected. Two excess tool requests receive TOOL_BUDGET_EXHAUSTED; they do not execute or enlarge the budget.
- case_63 Gemini again extracts sj.park@naver.com from evidence_60 while the request is for user_09. VISIBLE_IDENTIFIER_NOT_EXACTLY_CORROBORATED remains a rejection. No metadata update bypasses this exact-identity boundary.

Machine reports: artifacts/agent_fixes/{summary.json,baseline_sample.json,baseline_full.json,baseline_evaluation.json,deepseek_sample.json,deepseek_evaluation.json,gemini_full.json,gemini_validation.json}. Each pilot JSON contains actual ordered rounds and proposals. Durable usage journals are in text_cache/usage and vision_cache/usage under the same directory. Raw pilot artifacts stay outside the source archive.

## Remaining forensic blockers, rechecked after fixes

The new forensic_matrix.json independently re-runs all nine problematic decisions with full relevant file context. Nothing in pagination, schema correction or valid vision corroboration supplies absent source fields or ownership. The exact original contract quotes and full per-case explanations remain in docs/final_forensic_review.md.

| Case | Audit_at UTC | Remaining blocker / smallest admissible next input |
| --- | --- | --- |
| case_46 | 2026-03-11 08:00 | evidence_42 registry lacks complete tombstone PII fields; account absence in evidence_67 is not tombstone redaction. Need complete tombstone readback. |
| case_55 | 2026-04-30 11:00 | evidence_32/archive catalog does not display backup_9287 restore permission/block. Later logs remain excluded. Need dated permission readback. |
| case_63 | 2026-09-17 09:20 | evidence_60 visible identity conflicts with activity_4008 subject link. Live vision confirms the same conflict. Need independently corroborated exact link/state. |
| case_506 | 2026-02-08 07:00 | evidence_47 retained audit_record_1361 supplies no exact primary account link/state or exhaustive primary scope. |
| case_512 | 2026-02-08 07:00 | evidence_47 retained audit_record_4219 has the same primary-proof gap. |
| case_524 | 2026-01-29 12:00 | evidence_62 retained audit_record_5429 does not identify the primary account; evidence_49 is captured later. |
| case_530 | 2026-01-29 12:00 | evidence_62 retained audit_record_2152 has the same primary-proof gap. |
| case_532 | 2026-01-29 12:00 | evidence_62 compliant audit/support/backup/flow observations do not prove deletion of an unidentified primary account. |
| case_34 (decided INCOMPLETE) | 2026-09-27 13:00 | audit_record_3753's resource-specific retention period is unsupplied. RETENTION_CONDITION_UNPROVEN remains a conditional plan gap; dirty account/support independently justify the verdict. No restoration operation or unrelated deadline is invented. |

Disjoint unresolved groups: five primary-account proof/ownership gaps, two missing direct compliance fields, one contradictory identity. One additional decided plan has an unproved retention condition. Lack of COMPLETE proof is still not a supported INCOMPLETE finding. No further admissible generalizable solver fix was identified, and no uncertainty was coerced into a valid status.

## Reproduce and interpret exit codes

```powershell
python -m pytest -q
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json --extractions artifacts/ocr_cache --submission-output output.csv
python code/main.py validate --split full --predictions artifacts/full_predictions.csv --report artifacts/full_validation.json
python code/package_submission.py --output artifacts/code.zip
```

Solve/validate return exit 1 for these unresolved diagnostic predictions. The publication guard must refuse root output.csv. The source archive is runnable, not evidence of a valid submission. A deterministic run needs no credentials; fresh Windows OCR can regenerate all eleven image caches using `python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json`.

Exact paid pilot commands (do not repeat by default; original caches avoid repeated billing):

```powershell
$env:LLM_MAX_TOKENS='3072'; $env:LLM_MAX_RETRIES='0'; $env:LLM_TIMEOUT_SECONDS='60'
$env:DEEPSEEK_MODEL='deepseek-flash'
python code/main.py solve --split sample --output artifacts/agent_fixes/deepseek_sample.csv --report artifacts/agent_fixes/deepseek_sample.json --extractions artifacts/ocr_cache --ai deepseek --ai-case-id case_07 --ai-case-id case_17 --ai-cache artifacts/agent_fixes/text_cache --max-ai-cases 2 --max-model-calls 6 --max-cost-usd 0.12 --ai-case-seconds 90
$env:GEMINI_MODEL='gemini-3.5-flash-lite'
python code/main.py solve --split full --output artifacts/agent_fixes/gemini_full.csv --report artifacts/agent_fixes/gemini_full.json --extractions artifacts/ocr_cache --ai gemini --vision --ai-case-id case_63 --ai-cache artifacts/agent_fixes/vision_cache --max-ai-cases 1 --max-model-calls 1 --max-cost-usd 0.03 --ai-case-seconds 90
```

Use GEMINI_API_KEY / DEEPSEEK_API_KEY in the environment or an ignored .env. Optional *_INPUT_USD_PER_MILLION and *_OUTPUT_USD_PER_MILLION determine cost assumptions. Actual configured rates are persisted in each usage record. Native coding trace export must wait until this session is closed, per agent_trace_instructions.md; the append-only root conversation log remains separate.

## Final verification and changed files

All **232 tests pass** (working checkout 29.22 seconds; fresh declared-dependency environment 30.92 seconds). The controlled evaluator self-test passes separately. Fresh archive source, a new virtual environment, and all eleven newly generated Windows.Media.Ocr caches reproduce byte-identical 32-sample and 518-full CSVs. Only the externally supplied dataset is linked into that checkout; no .env, old OCR/model cache or credentials are copied. Windows reproduction is verified; Linux/macOS native OCR is not claimed.

All 103 original dataset SHA-256 values still match artifacts/ai_iteration/before/dataset_hashes.json. ZIP CRC, required root evaluation reports, source identity and exclusion of dataset, environments, private artifacts and actual API credentials are checked in artifacts/agent_fixes/verification.json. Root output.csv remains absent. Native coding-session trace export is deliberately deferred until session shutdown as required by agent_trace_instructions.md.

Files changed for this iteration:
- code/deletion_audit/ai_auditor.py: truthful context, bounded correction, semantic novelty, enrichment delivery, versioned caches and per-round traces.
- code/deletion_audit/investigator.py: cutoff-bound newest-first cursor pages and conditional resource schema.
- code/deletion_audit/proposals.py: exact category vocabulary, precise grounding errors, immutable metadata checks and case-local replacement.
- code/deletion_audit/providers.py: correlation IDs/context hashes in durable usage entries.
- code/deletion_audit/solver.py: apply validated same-ID updates through the indexed case-local store.
- tests/test_agent_corrections.py and tests/test_ai_foundation.py: eight new regressions and corrected existing vision-delivery assertion.
- docs/agent_corrections_readiness.md, docs/agent_implementation_audit.md, docs/ai_investigator.md, docs/submission_readiness.md: current findings and explicit historical audit labeling.
- code/evaluation/evaluation_report.md and usage_report.md: measured results, per-model usage and historical accounting.
- README.md, COMMANDS.md and Makefile: diagnostic selection semantics, commands and current pilot warning.
- log.txt: mandatory append-only conversation record. artifacts/code.zip is regenerated; prediction, pilot and verification reports remain under ignored artifacts/.

Preexisting conditional-retention, forensic-report and packaging edits are preserved. No additional policy or deterministic planner change was justified in this iteration. The next useful input is admissible source evidence or an official rule clarification for the eight proof gaps and case_34 retention condition, rather than another unchanged paid pilot.

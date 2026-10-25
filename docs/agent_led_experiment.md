# Blind-first agent-led experiment: NO-GO for promotion

Stable artifacts were frozen before implementation under artifacts/agent_led/frozen/.
The hard experimental cutoff was 2026-10-25T11:39:11Z. Paid experimentation stopped after
one unsuccessful four-call pilot; no further live calls were made to test later corrections.
Original output.csv and artifacts/code.zip are intentionally retained, not overwritten.

## Couplings and implementation

Frozen source couplings: ai_auditor.py:207-213 included baseline diagnostics in the first
model context; recommendations.py:90 called decide_case and lines 131-145 required verdict
and complete-plan agreement; solver.py:278-282 replanned only for grounded observations.
The source snapshot in frozen/code/ preserves those original locations.

Existing modes retain their checks. New --ai agent-led uses:

- agent_led.blind_context: request, cutoff, actual identity history, policy definitions,
  bounded admissible source index and neutral proof goals. No baseline verdict, plan,
  resource-state conclusions or diagnostic issue labels enter the first model context.
- Existing multi-step providers/tools and unchanged maximum calls, time, cost and retries.
  Policy is preloaded. Redundant explain_policy calls after the first are rejected without
  consuming additional successful tool slots. No new framework or unrestricted tool exists.
- Seven certificate types: RESOURCE_OWNERSHIP, LITERAL_FIELDS, EXPLICIT_STATE,
  RETENTION_OPERANDS, DATA_FLOW, RESTORE_PERMISSION and NEGATIVE_SCOPE. Existing exact
  source-derived extraction verifies each. Certificate subject, original capture time,
  observation time, literal source span and structured pointers must match. Omitted fields
  remain unknown and original negative scope is preserved. New historical identity
  interpretations and unsupported natural-language policy claims remain hypotheses;
  current admissible historical identity lookup is still available through trace_identity.
- agent_led.verify independently enumerates known resources from the temporal identity
  graph and admissible observations, reconstructs replica state, applies supplied policy
  per resource, checks each proposed step and enumerates missing obligations. It does NOT
  call decide_case or compare the plan with a baseline step array. It reuses source/state,
  scoped-negative and policy primitives rather than replacing these safety mechanisms.
- Source grounding, policy-valid steps and whole-scope completion have separate results.
  Correct steps survive partial-plan rejection. Unknown resources, contradictory state,
  ambiguous ownership, unsupported screenshot identity and missing primary proof block
  completeness. The model's free-text ledger is diagnostic; it is not certified evidence.
- Baseline agreement is recorded only after recommendation validation, diagnostic-only.
  This is a host comparison stage; no extra paid model critique was added.
- Fully verified plans can reach a separate experimental CSV without a new observation.
  No partial plan can do so. Root output.csv and --submission-output publication are blocked
  in this experimental mode. prepare_submission also rejects --publish-best-effort with it.

The independent verifier intentionally remains conservative about unknown primary resources
and alternative citations. It is not a complete new natural-language policy interpreter.
Removing baseline equality is confined to this tested opt-in path; old checks remain intact.

## Actual paired sample results

All modes processed the same 32 requests with the same dataset and OCR/cutoff context.
Only case_29 was selected for this bounded agent comparison. End-to-end fallback results
are not standalone accuracy measurements of unexecuted model decisions.

| Metric | A deterministic | B informed agent | C blind-first |
| --- | ---: | ---: | ---: |
| Status accuracy | 90.625% | 90.625% | 90.625% |
| Exact case / sequence | 28.125% | 28.125% | 28.125% |
| Step precision | 97.546012% | 97.546012% | 97.546012% |
| Step recall | 82.383420% | 82.383420% | 82.383420% |
| Step F1 | 89.325843% | 89.325843% | 89.325843% |
| Field accuracy | 77.447426% | 77.447426% | 77.447426% |
| Strict-valid sample rows | 29/32 | 29/32 | 29/32 |
| New live calls | 0 | 0 | 4 |
| Cached recommendations | 0 | 1 | 0 |
| Canonical changes / improved / regressed cases | 0 | 0 | 0 |

B revalidated the historical case_29 cache: its original four-call cost USD 0.0253242
is not charged to this experiment again. C used DeepSeek/deepseek-flash, 45,023 input and
4,740 output tokens, total 49,763, estimated USD 0.0191949 at USD 0.30/1.20 per million.
Reported provider latency sums to 20.890 seconds; whole C sample run 38.628 seconds.
No retries, provider errors or missing usage records. Estimates are not invoices.

## Actual agent behavior and failure

Round 1 autonomously selected inspect_source for the analytics profile, connector, search
readback and support record in evidence_92. All four succeeded. In the informed cached
pilot only two source inspections succeeded after four policy calls. This is a measured
retrieval allocation improvement, not a prediction accuracy improvement.

Round 2 attempted four activity observations as manifest file IDs; inspect_source correctly
rejected them. Round 3 searched both current and historical email identifiers. These result-
dependent follow-up calls and their errors are preserved in agent_led_execution_report.md.

Round 4 produced 4,096 output tokens but ended mid-JSON string. Parsing rejected it as
INVALID_FINAL_JSON. The partial text contains an INCOMPLETE recommendation and a draft
plan, including an incorrect exposed-PII finding for a DELETE search record. It is not a
schema-valid recommendation and was not repaired or accepted. No live semantic certificate,
new fact, corrected obligation or canonical change was accepted. Mocked certificate successes
must not be described as live agent contributions.

After the pilot, version 2 truthfully marks manifest-vs-activity sources in the index,
instructs compact final JSON and reserves the penultimate turn for a draft plus one existing
correction turn. These changes passed local regressions but were NOT retested live. Calls
were stopped on no gain rather than spending until a favorable result appeared.

## Release and remaining blockers

NO-GO for promoting the experimental path: no successful schema-valid live recommendation,
no incremental correctness gain, only one live-investigated sample, and v2 is mock-tested
rather than live-qualified. No agent-led full paid batch was run. A fresh deterministic
518-case run retains 510 strict-valid cases and the eight existing unresolved verdicts.

The retained best-effort output has 518 format-valid rows, 516 strict contract-valid rows,
eight assumption-based verdicts and the same case_55/case_63 failures. case_34 retains a
plan-proof gap. This experiment does not resolve those missing-source problems.

Stable uploads remain output.csv, artifacts/code.zip and authentic root log.txt. The new
source is packaged separately as artifacts/agent_led/code_agent_led.zip and is NOT promoted.
It has README.md, code/, required code/evaluation/ reports and root evaluation duplicates.

## Reproduction

```powershell
python -m pytest -q
python code/main.py solve --split sample --output artifacts/agent_led/baseline_sample.csv --report artifacts/agent_led/baseline_run.json --extractions artifacts/ocr_cache --ai none
python code/main.py solve --split sample --output artifacts/agent_led/blind_sample.csv --report artifacts/agent_led/blind_run.json --extractions artifacts/ocr_cache --ai agent-led --ai-case-id case_29 --ai-cache artifacts/agent_led/blind_cache --max-ai-cases 1 --max-model-calls 4 --max-cost-usd 0.35 --ai-max-rounds 4 --ai-max-tools 6 --ai-case-seconds 120
python code/main.py evaluate --split sample --predictions artifacts/agent_led/blind_sample.csv --report artifacts/agent_led/blind_evaluation.json
python code/main.py solve --split full --output artifacts/agent_led/stable_full.csv --report artifacts/agent_led/stable_full_run.json --extractions artifacts/ocr_cache --ai none
python code/package_submission.py --output artifacts/agent_led/code_agent_led.zip
```

Measured pilot used LLM_MAX_TOKENS=4096, LLM_TIMEOUT_SECONDS=45 and LLM_MAX_RETRIES=0.
A fresh live v2 invocation can incur new costs and is not a reproduction of v1 model text.
Use --max-ai-cases 0 --max-model-calls 0 --max-cost-usd 0 for offline fallback execution.
Detailed machine reports are under artifacts/agent_led/; Markdown execution history is
code/evaluation/agent_led_execution_report.md. No golden labels enter prediction logic.


## Artifact drift detected during verification

The stable code.zip SHA-256 remained equal to the frozen snapshot. Root output.csv did
not: case_55 and case_63 changed from INCOMPLETE to COMPLETE during the iteration, while
the experimental publisher was blocked and never invoked on root. The cause has not been
established. Both versions are retained in frozen/output.csv and observed_root_output.csv.
The observed root hash is 4263f02a16d30b525c0cc9ff4fb9ee62657ebcb26d8aec65475cef8287b88aab.
Its independent validation still finds exactly two missing COMPLETE-verification failures,
516/518 strict-valid rows. No claim is made that root remained byte-identical to this
iteration's initial snapshot. All 103 original dataset hashes remain unchanged.

Current working suite: 352 passed. Certificate, blind-context, no-baseline-authority,
partial-plan, false-COMPLETE, source-time, source-span, negative-scope and publication-block
regressions are included. Final fresh-package results are recorded in artifacts/agent_led/verification.json.


Final artifact check also detected a later change to artifacts/code.zip after the earlier
matching-hash check. Attribution is not established; our packaging commands targeted only
artifacts/agent_led/code_agent_led.zip. The original frozen/artifacts/code.zip and latest
observed_code.zip are both preserved. Treat verification.json as the final drift record;
do not describe the live archive as byte-identical to the initial snapshot. Both observed
archives pass CRC and contain the required README/code/evaluation paths.

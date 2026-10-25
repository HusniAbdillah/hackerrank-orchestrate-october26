# Optional AI investigation — measured 25 October 2026

Current submission-debugging result: 510/518 contract-valid, eight unresolved and one
decided incomplete plan; 222 tests pass. The existing Gemini vision cache was revalidated
with a zero-call/zero-cost budget. No new live calls were justified; no AI accuracy gain
is claimed. Source-grounded catalog aliases now have a deterministic adapter. It improves
full coverage but introduces three sample steps outside the reference, reducing sample
F1 to 89.326%. See docs/submission_debugging.md and the refreshed readiness report.
The scope-correction and live-model experiment descriptions below are historical results
from the preceding iteration, retained for usage and experiment provenance.

The agent is implemented and has made live Gemini and DeepSeek calls. It is a bounded
evidence investigator, not a verdict generator. No incremental AI sample accuracy gain
was observed. The deterministic fixes improved status accuracy from 75% to 90.625%,
step F1 from 85.546% to 90.085%, and full contract-valid rows from 413 to 505.

Files changed in this iteration:
- code/deletion_audit/solver.py, investigator.py and cli.py: scoped proof, literal asset
  search, optional investigator routing and diagnostic serialization.
- code/deletion_audit/ai_config.py, providers.py, proposals.py and ai_auditor.py: optional
  credentials/config, documented HTTP adapters, grounded proposal validation and one agent.
- tests/test_ai_foundation.py: 29 new regressions; all 214 repository tests pass.
- code/evaluation/aggregate_usage.py and code/package_submission.py: usage aggregation
  and source-only ZIP creation.
- .gitignore, .env.example, README.md, docs/ai_investigator.md,
  docs/submission_readiness.md, code/evaluation/evaluation_report.md and
  code/evaluation/usage_report.md: configuration, measured results and reproduction.
- log.txt: append-only conversation record. Diagnostic outputs and caches are under
  ignored artifacts/; the original dataset and active native trace remain unchanged.

## Evidence sufficiency correction

The former solver demanded a subject-specific primary profile readback even when an
admissible SQL snapshot explicitly declared account-service coverage and its complete
customer_profiles table was empty. It now records a scoped absence certificate without
inventing a profile resource ID. This first correction, measured before paid inference,
yielded 29/32 sample-valid and 492/518 full-valid rows. A second general correction admits
a declared profile inventory when every captured row uniquely resolves to another subject;
anonymous, conflicting or matching rows block the certificate. Full validity becomes 505/518.

**Scope assumption:** the snapshot's declared primary-service inventory is authoritative
within that captured scope and time. It is not proof about every possible unobserved replica.
Known independent copies, flows, conflicts and retention obligations still participate.
SQL file capture availability and embedded snapshot observation time both must be <= audit_at.
Future identity changes remain excluded. Regression fixtures exercise unavailable snapshots,
wrong service scope and anonymous rows. No sample answer is used by this logic.

COMPLETE requires existing compliant state evidence, supplemented only by these explicit
scope certificates. INCOMPLETE requires an observed policy violation; missing evidence
alone is not a noncompliance finding. Its remediation and future verification citations
are empty, including grounded retained/anonymized/replica final-state scope where known.
All unresolved verdicts remain null internally and blank in diagnostic CSVs. Strict
validation and the publication guard remain unchanged.

## Agent and grounding boundary

`ai_auditor.py` gives the agent the request, cutoff, baseline issues, exact resource links
and identity trace. It exposes only search_evidence, trace_identity, inspect_timeline and
explain_policy. Asset-reference search uses literal filenames, not fuzzy ownership joins.
Tool replies are bounded; business text is explicitly untrusted input. Models return
closed-schema facts, hypotheses, unresolved questions and a concise summary.

`proposals.py` independently validates every response and proposed fact. It checks the
original observation/file/activity ID, exact timestamp, capture availability, unique
identity/resource ownership, category/state and literal quote. Activity success cannot
become a direct readback. REUSE_DIRECT adds no new observation. The narrow LINK_ASSET
adapter requires an explicit sole-owner attachment-catalog link plus the exact filename
in an admissible original listing; it cannot infer object ownership from a filename alone.
Every rejected fact and malformed final response is kept with its reason. Accepted new
facts are applied only to a per-case store clone; deterministic policy/planning then reruns.
The model cannot choose deletion_status, operations, ordering or serialization.

The investigator currently cannot solve genuinely missing evidence, ambiguous ownership,
or required retention without an allowed restoration operation. Reusing an already parsed
fact is recorded as accepted but is not claimed as new evidence or an accuracy improvement.

## OCR and optional vision

Windows.Media.Ocr remains the first extraction path. All 11 PNGs have hash-bound cached
text/word boxes; eight have narrow typed overlays and three remain context-only. The raw
ingestion report retains explicit pending-image records, so inventory accounting is intact.
Four formerly uncategorized readbacks remain visible with their correlated typed adapters.

`--vision` sends only a flagged ambiguous original PNG to Gemini, with file ID and SHA-256
provenance. Its cache key includes image hash, model, schema/prompt versions, request/cutoff,
policy and source hashes. Existing adequate OCR is not automatically sent. Vision output
still requires exact identity and structured-state corroboration; it cannot repair an OCR
letter/digit or infer hidden redaction/restore permission. The live flagged marketing-image
proposal was rejected because the visible identifier did not corroborate the catalog-linked
subject. This preserves the uncertainty instead of claiming that vision resolved it.
`ocr_disagreements` contains model-reported hypotheses, not independently established errors.
This initial vision implementation is conservative corroboration; it does not yet accept
novel states unsupported by existing structured extraction.

## Providers, limits and configuration

Official documented HTTP endpoints are used with stdlib urllib; no SDK/framework is needed:
[Gemini generateContent](https://ai.google.dev/api/generate-content),
[Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling),
[DeepSeek chat completions](https://api-docs.deepseek.com/api/create-chat-completion/).
Authenticated model discovery succeeded for both credentials. Default models are
`deepseek-flash` and `gemini-3.5-flash-lite`; Gemini 3.8 Flash was also available but suffered
timeouts in this pilot. [Gemini model documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite)
and [DeepSeek pricing/model list](https://api-docs.deepseek.com/quick_start/pricing/)
were checked before selection.

DeepSeek uses native tools and JSON-object mode. Gemini preserves original function-call
thought signatures and uses native responseSchema with responseMimeType application/json.
An initial responseJsonSchema request was rejected; a minimal live schema probe and later
full investigator/vision calls confirmed the corrected responseSchema format. Local schema
validation remains stricter than the provider's OpenAPI subset.

Environment variables: GEMINI_API_KEY, DEEPSEEK_API_KEY, GEMINI_MODEL, DEEPSEEK_MODEL,
LLM_ENABLED, LLM_TEXT_PROVIDER, LLM_VISION_PROVIDER, LLM_MAX_TOKENS, LLM_MAX_TOOL_CALLS,
LLM_MAX_RETRIES, LLM_TIMEOUT_SECONDS, GEMINI_INPUT_USD_PER_MILLION,
GEMINI_OUTPUT_USD_PER_MILLION, DEEPSEEK_INPUT_USD_PER_MILLION,
DEEPSEEK_OUTPUT_USD_PER_MILLION. Existing environment wins over `.env`. Keys are excluded
from config repr, cache keys, traces and HTTP errors. `.env` stays ignored; `.env.example`
contains no credentials. CLI `--ai` selects routing; the old LLM_ROUTING variable is unused.

Defaults: three model rounds, six tools (environment can lower/raise within 1–30), 90 seconds
per case, max 32 investigated cases, 96 generation attempts and USD 1 run budget. Use explicit
smaller CLI caps for pilots. Retries count toward call/cost limits, use bounded backoff, and
share the case deadline. Full reports contain token usage, returned model, errors and latency.
Failed/unreported usage retains a conservative reservation rather than claiming zero cost.
Per-call journals under artifacts/ai_cache/usage append before/after requests so interruptions
remain visible. Cached results are source-revalidated; cache hits make no provider calls.

## Reproduction and paid-run decision

Run OCR on Windows once, or supply a valid existing cache on another platform:

```text
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/main.py solve --split sample --output artifacts/deepseek_predictions.csv --report artifacts/deepseek_run.json --extractions artifacts/ocr_cache --ai deepseek --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.20 --ai-case-seconds 180
python code/main.py evaluate --split sample --predictions artifacts/deepseek_predictions.csv --report artifacts/deepseek_evaluation.json
python code/main.py solve --split sample --output artifacts/gemini_predictions.csv --report artifacts/gemini_run.json --extractions artifacts/ocr_cache --ai gemini --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.20 --ai-case-seconds 180
python code/main.py evaluate --split sample --predictions artifacts/gemini_predictions.csv --report artifacts/gemini_evaluation.json
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json --extractions artifacts/ocr_cache --submission-output output.csv
python code/main.py validate --split full --predictions artifacts/full_predictions.csv --report artifacts/full_validation.json
python -m pytest -q
python code/package_submission.py
```

To compare the historical experiment precisely, set LLM_MAX_TOKENS=3072,
LLM_MAX_RETRIES=0, LLM_TIMEOUT_SECONDS=60 and the model/rates above; Gemini's successful
32-row comparison used one cached case from an interrupted pilot and six fresh calls.
Sample labels are loaded only by the separate evaluate command. Paid investigation was
not scaled to all 518 cases because sample investigations produced no new validated facts.
The full deterministic run and one specifically flagged full-run vision pilot were measured.
See code/evaluation/usage_report.md for all calls, failed experiments and missing accounting.

Next priorities: recover admissible ownership for missing reference scope; strengthen
generic literal catalog/listing joins with source-qualified fields; examine retained-record
negative scope; resolve screenshot identity conflicts with independent identifiers; extend
the investigator's validated extraction vocabulary only with independently specified tests.

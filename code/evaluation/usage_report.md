# Application model usage — 25 October 2026

The latest 518-row deterministic run used **zero model calls, zero input/output tokens,
USD 0 model cost**, averaging zero tokens/cost per request. It took 40.71 seconds and yielded
510 contract-valid rows and eight unresolved rows. No eligible final submission output.csv was
produced; this is the latest diagnostic full run, not an accepted submission run.

Submission-debugging iteration: no new paid calls, zero new input/output tokens and zero
new model cost. A targeted Gemini screenshot investigation used one existing cache entry,
revalidated every proposal against current sources, and rejected the same uncorroborated
subject. Its configured budget was zero calls and USD 0. No complete agent-assisted batch
was justified by the earlier lack of measured AI gains. Fresh-environment runs also used
zero calls; Windows native OCR is local extraction. Final source ZIP excludes model/OCR
caches and credentials. All prior paid-experiment accounting below is retained unchanged.

## Recorded development/pilot usage

| Provider/model | Generation attempts | API errors | Reported input tokens | Reported output tokens | Cost estimate + missing-usage reservation USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| DeepSeek/deepseek-flash | 12 | 0 | 115122 | 5453 | 0.0410802 |
| Gemini/gemini-3.8-flash | 6 | 5 | 5149 | 73 | 0.1464255 |
| Gemini/gemini-3.5-flash-lite | 18 | 4 | 137939 | 4385 | 0.1200049 |
| Recorded overall | 36 | 9 | 258210 | 9911 | 0.3075106 |

Reported overall tokens: 268121. Nine failed attempts have **unknown usage**, not zero actual
usage. Token-priced cost for reported usage is USD 0.0975599; conservative reservations for
missing usage total USD 0.2099507. These are application estimates, not an invoice. Two
successful authenticated model-discovery GET requests are additional API requests, with no
generation/token usage attributed. Schema-format probe usage is included above.

**Accounting limitation:** one interrupted Gemini sample pilot occurred before durable usage
journaling was added. It completed at least one investigation later used from cache, but its
per-call usage ledger was lost before the run report was written. Its configured upper bounds
were 12 generation attempts and USD 0.50. Thus 36 generation attempts are recorded, additional
interrupted-run calls/tokens are unmeasured (at most 12 attempts), and recorded estimates plus
the interrupted reservation are at most USD 0.8075106 under configured tariff assumptions.
Do not interpret 36 or USD 0.3075106 as an exact all-session total. New runs append durable
per-call reservation/completion records under artifacts/ai_cache/usage before sending requests.

## Evaluated mode costs

| Physical run | Fresh attempts | Input | Output | Estimate/reservation USD | Result |
| --- | ---: | ---: | ---: | ---: | --- |
| DeepSeek pilot | 3 | 22878 | 1544 | 0.0087162 | Live structured final; facts rejected |
| Gemini 3.8 pilot | 2 | 5149 | 73 | 0.0300420 | Tool call worked; final timeout |
| DeepSeek 32-row comparison | 9 | 92244 | 3909 | 0.0323640 | Two valid finals; one malformed final |
| Gemini 3.8 32-row comparison | 3 | unknown | unknown | 0.0898635 | Timeouts/503; deterministic fallback |
| Gemini 3.8 vision pilot | 1 | unknown | unknown | 0.0265200 | HTTP 400 |
| Gemini Lite first comparison | 9 | 60662 | 1794 | 0.0792243 | Tools worked; structured-final 400s |
| Gemini Lite first vision | 1 | unknown | unknown | 0.0111200 | HTTP 400 |
| Gemini Lite schema probe | 1 | 15 | 5 | 0.0000170 | Live native structured response worked |
| Gemini Lite corrected 32-row comparison | 6 | 74186 | 2257 | 0.0278983 | Two fresh completed investigations + one cache hit |
| Gemini Lite corrected full-run vision pilot | 1 | 3076 | 329 | 0.0017453 | Live extraction; identity proposal rejected |

DeepSeek comparison averages per 32 requests: 2882.625 input, 122.15625 output,
3004.78125 total tokens and USD 0.001011375. Corrected Gemini comparison averages:
2318.3125 input, 70.53125 output, 2388.84375 total tokens and USD 0.000871821875 in
**fresh** usage; its cached case's original unmeasured cost is excluded and disclosed above.
The one-image full-run pilot averages 6.57336 reported tokens and USD 0.0000033693 per
518 requests; only one request was investigated. No full paid text-agent rollout was run
because the pilots yielded no newly accepted facts or incremental sample accuracy gain.

## Tariff assumptions and observability

USD per million input/output tokens: DeepSeek Flash 0.30/1.20 (conservative peak/cache-miss),
Gemini 3.8 Flash 0.75/3.75 for these historical pilots, Gemini 3.5 Flash Lite 0.30/2.50.
Pricing sources checked before calls: [DeepSeek](https://api-docs.deepseek.com/quick_start/pricing/)
and [Gemini](https://ai.google.dev/gemini-api/docs/pricing). Rates are configurable via
{GEMINI,DEEPSEEK}_{INPUT,OUTPUT}_USD_PER_MILLION. Set them when changing models/tariffs.
Thought output tokens are included where reported. Unknown usage is reserved using the
request's conservative input bound and configured output cap; retries each consume a slot.
Local OCR/CPU/storage and development-assistant tokens are not application provider usage.

Machine totals: artifacts/ai_iteration/usage_totals.json. Its explicit run list excludes
duplicate stdout copies and includes every completed experiment, successful or failed.
Reproduce aggregation with code/evaluation/aggregate_usage.py --run <report> (repeat per
non-overlapping physical run) --output artifacts/usage_totals.json. Per-run reports retain
configured limits, returned models, errors, latency, tool traces, proposals/rejections and
token/cost records. Cache hits are explicit. No credential values are recorded or packaged.

# Foundation usage report

Run date: 24 October 2026. This is an evaluation-foundation milestone, **not the final
full-dataset prediction run required for submission**. No `output.csv` was generated.
The full-input readiness run loaded all 518 cases and left them unresolved.

| Application provider/model | Calls | Input tokens | Output tokens | Total tokens | Estimated cost |
| --- | ---: | ---: | ---: | ---: | ---: |
| None (standard-library ingestion, validation, scoring) | 0 | 0 | 0 | 0 | USD 0.00 |
| **Overall** | **0** | **0** | **0** | **0** | **USD 0.00** |

For the 518-request readiness run: average input/output/total model tokens per request
are all 0, and estimated model cost per request is USD 0.00. The 32-case sample readiness
and all evaluator self-tests also used zero application model calls. No API credentials
are read and no provider price assumptions are needed. Local CPU, storage, development
time, and the coding assistant's own session usage are outside application model accounting;
the harness trace records the development session separately.

Before final submission, replace this milestone account with actual measurements from
the full-dataset run that produces the final predictions: provider/model names, calls,
input/output and total tokens, per-request averages, per-model/overall totals, pricing
assumptions, and total/per-request costs. Do not describe the current readiness run as
an audit solver run.

## Evidence/identity iteration

The `ingest` command now normalizes all 94 manifest files (eleven images explicitly pending)
and computes identity coverage for 32 sample and 518 evaluation requests using one shared
parsed store. This run and all 112 tests used **zero application model calls**, zero input
or output model tokens, and USD 0.00 in model costs. Total and per-request token/cost
figures above therefore remain zero. Runtime dependencies are local Python and pypdf;
there is no provider/model integration, OCR service, or multimodal API invocation.

There is still no final audit prediction run or generated submission CSV. These zero-cost
diagnostics must not be represented as a completed challenge submission.

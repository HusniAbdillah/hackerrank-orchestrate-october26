# Current application usage

25 October 2026. Latest full run: 518 diagnostic rows in 16.627s, with
413 contract-valid and 105 unresolved rows. `artifacts/full_predictions.csv` is not a final
submission. `output.csv` publication was blocked; an existing file would be preserved.

| Provider/model | Calls | Input tokens | Output tokens | Total tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: |
| None (deterministic Python plus optional local Windows OCR) | 0 | 0 | 0 | 0 | 0.00 |
| Overall | 0 | 0 | 0 | 0 | 0.00 |

Average input/output/total tokens per full request: 0/0/0. Average model cost: USD 0.00.
Sample run: 32 rows in 11.112s, also zero model usage. Native OCR is cached
for all eleven images, with eight typed overlays and three context-only results. OCR is
not an LLM call and no API credentials are required. Cache hits and extraction failures
are explicit in artifacts/ocr_run.json; source hashes and engines remain in each cache.
Local CPU/storage and development-assistant usage are separate from application model costs.
All 103 dataset hashes remain unchanged. Replace this report with final accepted submission
run measurements when evidence sufficiency and contract validity are complete.

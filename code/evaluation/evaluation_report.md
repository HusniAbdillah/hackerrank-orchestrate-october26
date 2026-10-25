# Actual solver evaluation

25 October 2026. Actual predictions, not evaluator self-test results.

| Metric | Sample value |
| --- | ---: |
| case_status_accuracy | 75.000000% |
| exact_case_accuracy | 28.125000% |
| step_precision | 99.315068% |
| step_recall | 75.129534% |
| step_f1 | 85.545723% |
| field_accuracy | 72.606775% |
| sequence_accuracy | 28.125000% |

Sample status 24/32, exact-case and sequence 9/32; step matches 145/146 predicted versus
193 reference steps. These sample metrics are unchanged. Schema-valid rows: **24/32**.
All rows generated, with eight unresolved null internal verdicts / blank diagnostic statuses.
Full contract-valid rows improved **408/518 -> 413/518**; 105 unresolved verdicts remain.
126 full cases have some incomplete proof/plan scope. Fully compliant submission is blocked.

**185 tests passed** (all prior 152 plus 33 new). The controlled evaluator self-test also passes.
Three independently specified business cases retained in tests/test_solver.py cover:
1. Clean primary versus dirty replica, active connector and retained audit data: disable before
   deletion, preserve retained evidence and verify the complete known scope.
2. Tombstone with stable reference versus exposed identifiers and a future-captured dirty
   document: use only admissible state, redact identifiers, preserve the stable reference.
3. Access-only request versus a deletion worker success claim: access is NOT_APPLICABLE;
   worker success alone cannot establish deletion and remains unresolved.

Additional regressions cover stale/invalid OCR caches, missing native recognizers, exact
resource text, OCR subject mismatch, optional CLI routing, signed PDF retention, arbitrary
replica labels, blank unresolved output, protected submission publication, and read-only tools
that cannot admit future observations, mutate results or override the cutoff.

Improvements: five full cases now have grounded screenshot facts; all eleven PNGs are accounted
for with eight typed overlays and three context-only extractions. No sample case mapping or
expected steps are embedded in prediction logic. The marketing OCR identity discrepancy is
withheld rather than repaired/fuzzily merged. Unknown decisions are no longer coerced into
INCOMPLETE. Strict validation remains unchanged.

See ../../docs/submission_readiness.md for exact commands, every baseline abstention group,
current causes, changed files, and remaining AI integration work. Machine reports reside under
artifacts/ (repository root): sample_evaluation.json, sample_mismatches.json,
sample_abstention_review.json, full_abstention_review.json, and both solver reports.

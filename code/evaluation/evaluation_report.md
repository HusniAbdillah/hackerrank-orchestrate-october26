# Current submission-oriented debugging evaluation

25 October 2026. All metrics are actual public-sample predictions, not self-test values.

| Metric | Iteration baseline | Support-body fix | Final source-grounded joins |
| --- | ---: | ---: | ---: |
| Status accuracy | 90.625% | 90.625% | 90.625% |
| Exact-case accuracy | 28.125% | 28.125% | 28.125% |
| Step precision | 99.375% | 99.375% | 97.546% |
| Step recall | 82.383% | 82.383% | 82.383% |
| Step F1 | 90.085% | 90.085% | 89.326% |
| Field accuracy | 78.792% | 78.792% | 77.447% |
| Sequence accuracy | 28.125% | 28.125% | 28.125% |
| Sample contract-valid | 29/32 | 29/32 | 29/32 |
| Full contract-valid | 505/518 | 508/518 | 510/518 |
| Unresolved full verdicts | 13 | 10 | 8 |
| Decided incomplete plans | 21 | 1 | 1 |

**222 tests passed in 45.32 seconds**; all 214 previous tests remain passing. The separate
controlled evaluator self-test passed. All 103 dataset SHA-256 values remain unchanged.
The same 222 tests also passed in the freshly installed dependency environment (34.81s).
Fresh virtual environment installation, source ZIP extraction, and regeneration of all
11 OCR extractions produced byte-identical sample and full CSVs. This was verified on
Windows with the installed English Windows.Media.Ocr recognizer; equivalent extraction
on Linux/macOS has not been verified. No undeclared caches or credentials were copied.

Full status distribution: 353 INCOMPLETE, 147 COMPLETE, ten NOT_APPLICABLE and eight
unresolved blank diagnostic statuses. Full hidden-label accuracy remains unmeasurable.
The publication guard refused output.csv: eight invalid rows plus case_34's policy gap.

Source-backed corrections:
- Support contact identifiers embedded in message_text are now direct PII observations,
  including when separate email/phone columns are null. Twenty incomplete plans are fixed;
  three previously unresolved full verdicts become grounded INCOMPLETE.
- Literal catalog/document aliases and sole-owned attachment listings retain original
  file IDs and both source timestamps/provenances. Two more full verdicts are resolved.
  A later catalog link cannot become admissible at the document's earlier observation time.
- Heterogeneous SQL rows without declared origin-service scope no longer certify absence
  of other resources. Declared typed inventories still apply; no blanket completeness claim.

**Sample regression is retained transparently:** the evidence-grounded object_19 adds
three steps outside the public case_07 reference. It has literal sole ownership in
activity_4007 and visible positive file metadata in evidence_46; no later deletion readback
was found. Suppressing it from that sample would be label-dependent. Thus 159/163 predicted
steps match 193 reference steps: 34 missing and four extra. Exact/sequence remain nine of 32.
The three status errors remain requests without admissible resource ownership.

All 23 exact-case discrepancies are listed in docs/submission_debugging.md, with status,
missing/extra steps and anchored field differences. Missing-step causes: 17 ungrounded
subject links, eight future-only links, seven anonymized records without historic links,
two retained-record links. Among matching phase/system/resource anchors, 45 step_no
differences arise from scope omissions/additions; no other aligned field mismatch was found.
These explain scoring differences, not permission to use later evidence or infer resource IDs.

Every original 13 abstentions and 21 decided plan gaps has a source matrix and obligation
ledger in artifacts/submission_debug/case_matrix.json and docs/submission_debugging.md.
Eight unresolved: case_46, case_55, case_63, case_506, case_512, case_524, case_530, case_532.
case_34 remains INCOMPLETE with an unplannable required-retention gap; no allowed operation
can restore a missing retained record. Independent original business cases below remain
in tests; eight added regressions cover the actual fixes, cutoff joins and negative scope.

No new API calls were made. The existing Gemini image proposal was source-revalidated
through its cache under max-model-calls=0 and max-cost-usd=0: still rejected for identity
corroboration. Prior live proposals were reviewed; no new paid pilot was justified by the
remaining absent/unshown state. Historical live comparisons and their failures follow.

## Historical preceding-iteration solver and live investigator evaluation

25 October 2026. Public sample metrics below come from actual 32-row predictions;
they are not controlled evaluator self-test metrics. Labels are used only in evaluation.

| Metric | Previous deterministic | Corrected deterministic | + DeepSeek | + Gemini Flash Lite |
| --- | ---: | ---: | ---: | ---: |
| Status accuracy | 75.000% | 90.625% | 90.625% | 90.625% |
| Exact-case accuracy | 28.125% | 28.125% | 28.125% | 28.125% |
| Step precision | 99.315% | 99.375% | 99.375% | 99.375% |
| Step recall | 75.130% | 82.383% | 82.383% | 82.383% |
| Step F1 | 85.546% | 90.085% | 90.085% | 90.085% |
| Field accuracy | 72.607% | 78.792% | 78.792% | 78.792% |
| Sequence accuracy | 28.125% | 28.125% | 28.125% | 28.125% |
| Contract-valid rows | 24/32 | 29/32 | 29/32 | 29/32 |

Corrected counts: 29 correct statuses, nine exact cases/sequences, 159 matching steps of
160 predicted and 193 reference steps; 34 missing and one extra verification. All three
remaining status errors are explicit unresolved rows, not mislabeled non-deletion requests.
Full deterministic run: 518 rows, 505 contract-valid, 13 unresolved; another 21 decided
cases have incomplete plan scope. Full accuracy cannot be measured without hidden labels.
Publication of output.csv was refused by the unchanged contract/proof/integrity guard.

## Experiment sequence and live results

1. Baseline snapshot: 413/518 valid, 105 unresolved.
2. Before any paid inference, declared empty primary-profile scope corrected an unnecessarily
   strict subject-specific readback requirement: 492/518 valid, 29/32 sample-valid.
3. Generic exact-subject filtering of declared profile inventories: 505/518 valid. Every
   captured row must uniquely belong to someone else; anonymous/ambiguous rows block proof.
   Known replicas/flows/retention still apply. This is a scoped inventory interpretation,
   not a universal claim about unobserved systems. Sample metrics unchanged from step 2.
4. Live DeepSeek pilot and complete 32-row sample run: tool calls succeeded; one malformed
   final response, unsupported quotes/categories, activity claims and incorrect timestamps
   were rejected. Accepted proposals reused existing facts. No new fact or accuracy gain.
5. Initial Gemini 3.8 runs suffered timeouts/503. Gemini Flash Lite tools succeeded but the
   first structured-final request shape returned 400. These failed modes also fell back to
   the same deterministic metrics; they are not successful agent evaluations.
6. Corrected Gemini native responseSchema passed a live format probe and live investigations.
   The complete 32-row comparison used six fresh calls and one cached investigation from an
   interrupted pilot. No newly grounded fact and no incremental accuracy gain.
7. Original-image Gemini vision succeeded on the full run's flagged screenshot. Its visible
   identifier failed exact subject corroboration; the proposal was rejected. Full validity
   remained 505/518. No paid bulk full-split investigator run was justified by these results.

DeepSeek sample runtime was 42.20 seconds; the corrected Gemini sample run was 32.92 seconds,
including local solving and one cache hit. Final deterministic full runtime was 24.94 seconds.
These are single local measurements, not stable performance benchmarks.

## Matching definitions

Status is correct unique-case status / 32. Exact-case also requires identical ordered
seven-field steps and a contract-valid case/file. Step precision/recall/F1 use micro multiset
matches within each case on all fields except step_no, including evidence_id. Field accuracy
aligns steps by case/phase/system/resource and compares all seven strict-type fields;
missing/extra steps add unmatched slots. Sequence accuracy requires identical ordered arrays
including step_no, independently of status. JSON key order/whitespace do not matter.
Strict validation is unchanged; it does not itself prove semantic evidence sufficiency.

## Failures and root causes

All original 105 abstentions are in artifacts/full_abstention_review.json with before/after
issues and proposed next actions; 92 are now resolved. Disjoint original issue groups:
97 primary-proof only, four primary-proof + no direct state, two primary-proof + required
kept record missing, one no-direct-state only, one primary-proof + OCR subject conflict.

Remaining 13 cases, grouped by unresolved issue (groups overlap at case_508):
six primary-profile proofs, five no-direct-state readbacks, two required-kept-record absences,
one OCR subject conflict. Cause classification: absent verification 10, temporal availability
gap seven, inadequate negative scope two, policy ambiguity two, unsupported source parsing
one, missing ownership one. Those temporal leads are excluded evidence, not admitted joins.

Sample missing-step diagnosis counts: no grounded subject link 17; link only after cutoff
eight; anonymized resource without historical link seven; retained resource without link
two. There is one additional grounded verification outside reference scope and three
abstentions. These are evaluation discrepancies, not permission to bypass evidence rules.

Three sample requests have no admissible resource link and remain unresolved. Nine full
requests without links are justified non-deletion requests; a tenth non-deletion request
has links. All eleven PNG OCR caches remain accounted for (eight typed, three context-only).
Four raw uncategorized readbacks have explicit correlated adapters. No dataset is edited.

## Independent cases and regressions

The three independent business cases in tests/test_solver.py cover:
1. A clean primary, dirty regional replica, active connector and retained audit record:
   stop the connector, remove the prohibited copy, preserve required records and verify scope.
2. A stable-reference tombstone, exposed identifiers and a dirty future-captured document:
   redact the admissible tombstone, preserve its stable reference and exclude future evidence.
3. Access-only authorization versus a deletion worker success claim: access is NOT_APPLICABLE;
   a success claim alone leaves an authorized deletion unresolved.

**214 tests passed in 28.78 seconds**, preserving all previous 185 and adding 29 regressions.
The controlled evaluator self-test also passed, independently of solver accuracy.
The suite additionally exercises scoped inventory proof, anonymous rows, provider normalization,
Gemini thought signatures/native schema/image payloads, cached proposal revalidation,
future capture exclusion, fabricated IDs/states/quotes, sole-owner asset links, missing keys,
malformed proposals, HTTP secret redaction, retries, missing-usage reservations and durable
usage journals. Existing evaluation, ingestion, identity, OCR and planner tests are retained.
Run `python -m pytest -q`; see artifacts/ai_iteration/final_tests.txt for the measured result.

## Artifacts and reproduction

Baseline: artifacts/ai_iteration/before/. Current deterministic: artifacts/sample_predictions.csv,
sample_evaluation.json, sample_mismatches.json, full_predictions.csv, full_solver_report.json,
full_validation.json and both abstention reviews. AI comparisons: artifacts/ai_iteration/
deepseek_sample.json, deepseek_evaluation.json, gemini_fixed_sample.json,
gemini_fixed_evaluation.json and vision_fixed_full.json. Failed experiments are retained.
All 103 dataset SHA-256 values match the turn-start inventory.

See docs/ai_investigator.md and README.md for setup and bounded reproduction commands.
See usage_report.md for complete recorded application usage and the interrupted-run caveat.
The initial malformed DeepSeek final retained its error but not raw response text; later
malformed finals preserve bounded response text plus validation reasons.

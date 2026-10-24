# Evaluation foundation report

Run date: 24 October 2026. Scope: evaluator and ingestion pipeline only. The audit solver
has not been implemented, and no submission predictions were produced. The results below
are controlled evaluator checks, not measured deletion-audit prediction accuracy.

## Commands and results

```text
python -m pytest -q
python code/main.py self-test --report artifacts/evaluator_self_test.json
python code/main.py evaluate --split sample --predictions dataset/sample_output.csv --report artifacts/reference_self_comparison.json
python code/main.py run --split sample --report artifacts/sample_pipeline.json
python code/main.py run --split full --report artifacts/full_pipeline.json
```

Pytest: **62 passed**. Controlled self-test: **all five scenarios passed**.
Public reference self-comparison: 32 cases, 193 steps, contract-valid, every metric 1.0.
Sample readiness: 32 cases loaded, 32 unresolved, zero predictions.
Full readiness: 518 cases loaded, 518 unresolved, zero predictions.
Both splits loaded a metadata catalog of 94 file IDs, 4,011 activity IDs, and 306 audit IDs.

| Controlled input | Contract valid | Status accuracy | Exact-case accuracy | Step precision | Step recall | Step F1 | Field accuracy | Sequence accuracy |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Reference with reordered JSON object keys/whitespace | Yes | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| One step array reversed and renumbered | No | 1.000000 | 0.968750 | 1.000000 | 1.000000 | 1.000000 | 0.998520 | 0.968750 |
| One case removed | No | 0.968750 | 0.968750 | 1.000000 | 0.974093 | 0.986877 | 0.974093 | 0.968750 |
| One case duplicated | No | 0.968750 | 0.968750 | 0.989691 | 0.994819 | 0.992248 | 0.984615 | 0.968750 |
| One cited ID replaced with nonexistent evidence | No | 1.000000 | 0.968750 | 0.994819 | 0.994819 | 0.994819 | 0.999260 | 0.968750 |

The reversed-array scenario retains all 193 step payloads but fails canonical ordering.
The missing scenario has 188 matched/reference-retrieved steps of 193. The duplicate
scenario has 192 true-positive steps out of 194 predicted and 193 reference steps; both
rows for the duplicate case are quarantined. The bad-citation scenario has 192/193 matched
steps. Status credit is intentionally independent of step-contract validity.

## Matching definitions

- Case denominator: every expected case, including missing cases. Duplicate cases receive
  no case credit. Unexpected cases add false-positive steps and unmatched field slots.
- Status accuracy: correct status on a unique expected-case row / expected cases.
- Exact-case accuracy: correct status and identical ordered seven-field JSON array on a
  unique, contract-valid case / expected cases. Any file-level schema or row-order issue
  removes all exact-case credit. Unknown extra cases remain visible through contract
  failure and step/field penalties rather than changing the expected-case denominator.
- Step precision/recall/F1: micro multiset matching by case on every field except
  `step_no`, including evidence ID and any extra keys. Array order is ignored only for
  this metric. Repeated steps retain multiplicity. Unparseable JSON adds an opaque
  false-positive step. Duplicate/unknown case rows cannot generate true positives.
- Field accuracy: align by case, phase, system, and resource, pairing repeated anchors
  by occurrence order. Compare all seven fields with strict types. Each unmatched step
  occupies a seven-field slot with no correct fields. Overall is correct fields / (7 ×
  slots); per-field accuracy is correct values / slots.
- Sequence accuracy: unique rows with identical ordered arrays including all step numbers
  / expected cases, independently of case status. JSON key order and whitespace are ignored.
- Empty conventions: precision/recall/F1 and field accuracy equal 1 when both step
  collections are empty. No predictions against nonempty reference gives step metrics 0.

These are documented local evaluation definitions; the hidden grader's exact formulas
are not available. Full diagnostic definitions also appear in each JSON scoring report.

## Participant-created evaluation cases

The pytest suite builds an independent fictional three-case dataset, without copying
real challenge case IDs or case-specific answers into prediction logic:

1. **Synthetic account absence with retained journal.** A COMPLETE answer verifies an
   absent profile and present retained record. A file/activity exactly at audit time
   is admissible; a citation one second later is rejected. Wrong-but-existing evidence
   loses one step and one evidence-field match without claiming semantic entailment.
2. **Synthetic search copy plus active connector.** An INCOMPLETE answer contains two
   findings, disables the connector before deletion, and verifies both final states.
   Removing a finding, its remediation, or its verification fails structural plan coverage.
3. **Synthetic non-applicable request.** The reference has NOT_APPLICABLE with an empty
   array. Empty-step metrics are well-defined; adding steps fails status-shape validation.
   This tests output semantics, not a nonexistent intent classifier.

Additional variants cover array order, phase/operation/state mismatches, consecutive integer
numbering (including boolean/float rejection), duplicate JSON keys, malformed JSON,
nonfinite numbers, CSV headers/width, missing/duplicate/unexpected cases, illegal extra
fields, duplicate steps, system/resource tie-breaks, future file/activity/audit evidence,
invalid statuses, and pipeline isolation from sample ground truth. Entry points are also
tested from a different working directory.

## Failures found and improvements made

- Initial chronology tests moved catalog timestamps that were also used by the reference.
  The evaluator correctly refused that now-corrupt reference. The tests were corrected
  to exercise the validator directly with the altered catalog, preserving the explicit
  reference-validation guard instead of weakening it.
- Strict JSON loading rejects duplicate keys and nonfinite values, including overflow
  such as `1e999`, so they cannot crash canonical scoring or masquerade as legal values.
- Missing-case denominators, duplicate-case quarantine, multiset step matching, opaque
  malformed-row penalties, and unmatched-field slots prevent easy score inflation.
- Readiness reports leave cases unresolved rather than emitting unsupported statuses.
  Report path guards prevent overwriting dataset inputs or supplied prediction files.

## Limits and next work

The foundation validates metadata chronology, not embedded business observation times,
identity/resource ownership, policy correctness, evidence support, or dependency semantics.
It cannot determine whether an existing citation actually proves a claim. The later audit
engine must implement those features before generating predictions. No accuracy against
hidden answers, no full-dataset solver run, and no production submission readiness are
claimed. Original dataset bytes were verified unchanged after this work.

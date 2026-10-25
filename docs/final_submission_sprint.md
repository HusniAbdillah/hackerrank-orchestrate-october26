# Final submission sprint — 25 October 2026

## Actual deliverables

**305 tests pass.** Strict sample/full predictions are unchanged. There were zero new application model calls. Source, field-coverage and intent corrections improve independently demonstrated correctness, not measured corpus accuracy.

An actual experimental **artifacts/final_sprint/submission_candidate.csv** contains 518 unique lexicographically sorted cases and valid CSV/JSON. Eight verdicts use explicitly uncertain observed-scope COMPLETE assumptions. **Only 516/518 pass strict contract validation.** case_55 and case_63 have no admissible verification to include; their arrays remain empty and visibly fail STATUS_SHAPE. No evidence ID, resource, state observation or operation was invented. Root output.csv remains absent. Renaming the candidate does not fix its errors or prove the eight assumed verdicts.

| Measurement | Before | After |
| --- | ---: | ---: |
| Sample status accuracy | 90.625% | 90.625% |
| Exact-case / sequence | 28.125% | 28.125% |
| Step precision | 97.546012% | 97.546012% |
| Step recall | 82.383420% | 82.383420% |
| Step F1 | 89.325843% | 89.325843% |
| Field accuracy | 77.447426% | 77.447426% |
| Sample contract-valid | 29/32 | 29/32 |
| Full strict contract-valid | 510/518 | 510/518 |
| Unresolved verdicts / additional conditional plans | 8 / 1 | 8 / 1 |
| Sample reference false-COMPLETE | 0 | 0 |

Full hidden-label accuracy/false-COMPLETE count is unknown. Contract validation is not semantic correctness certification. The experimental candidate has eight explicitly recorded false-COMPLETE risks; its additional six format-valid rows are not six evidence-grounded resolutions.

## Implemented fixes

- authorization.py binds explicit deletion/negation to account clauses across supported languages. Protecting invoices no longer vetoes unrelated account deletion; conflicting account instructions return unknown. Regression cases include Indonesian, Spanish, French, Portuguese, Japanese, Korean, Chinese, English, correction, access and opt-out.
- state.py requires category-specific identifier coverage or direct-state certificates before declaring redaction/anonymization. Omitted fields differ from explicit null. Literal PII and stable links override clean certificates/counters. Workflow claims remain excluded. The independent tombstone fixture now includes explicit phone/hash nulls; its former partial row was insufficient.
- solver.py retains grounded partial checks in diagnostics before abstention; strict verdicts, CSV steps and publication guard are unchanged.
- prepare_submission.py adds opt-in --candidate-policy observed-scope. It uses only existing grounded partial verification, records assumptions separately and independently validates the output. Empty proof stays empty. Experimental candidates cannot be named output.csv. Default strict behavior is preserved; exit 1 still indicates no fully contract-valid candidate.

## Missing-step audit and remaining cases

34 missing sample verification steps remain: 17 without grounded subject links, eight with links available only after cutoff, seven anonymized records without historical ownership, two retained-record links without admissible proof. No general source-backed join was found to repair these. Forty-five aligned step-number shifts are consequences of missing/extra steps. No new wrong-field/citation mismatch appears on aligned matched steps. The grounded three-step object_19 plan remains; reference labels never enter prediction logic.

| Case | Strict blocker | Experimental interpretation |
| --- | --- | --- |
| case_46 | Complete tombstone identifier readback missing | Unknown treatment assumed compliant; known account-absence check retained |
| case_55 | Archive restore permission missing | Unknown restore state assumed safe; no verification, contract-invalid |
| case_63 | Screenshot/catalog subject conflict | Unresolved association assumed non-blocking; no verification, contract-invalid |
| case_506, case_512 | Retained record does not prove primary state | Missing primary obligation assumed compliant |
| case_524, case_530 | Partial export lacks admissible primary link/readback | Missing primary obligation assumed compliant |
| case_532 | Compliant downstream state does not prove primary state | Missing primary obligation assumed compliant |

case_34 is independently INCOMPLETE but audit_record_3753's retention condition remains unproved. No restoration operation is invented. Candidate diagnostics retain this ninth plan/proof risk separately from eight forced verdicts. Per-case assumptions, issues and validation errors are in candidate_report.json; actual observations/cutoffs remain in full_run.json.

## Reproduce from source root

Provide original dataset/ externally. Windows native OCR must be regenerated for these measured results; caches and credentials are not bundled. No API key is needed. See agent_trace_instructions.md for native trace export after session shutdown.

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ocr --output artifacts/ocr_cache --report artifacts/ocr_run.json
python code/main.py solve --split sample --output artifacts/final_sprint/sample.csv --report artifacts/final_sprint/sample_run.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/final_sprint/sample.csv --report artifacts/final_sprint/sample_evaluation.json
python code/evaluation/diagnose_solver.py --predictions artifacts/final_sprint/sample.csv --solver-report artifacts/final_sprint/sample_run.json --output artifacts/final_sprint/sample_mismatches.json --extractions artifacts/ocr_cache
python code/prepare_submission.py --strict-output artifacts/final_sprint/full.csv --output artifacts/final_sprint/submission_candidate.csv --report artifacts/final_sprint/candidate_report.json --extractions artifacts/ocr_cache --candidate-policy observed-scope
python code/main.py validate --split full --predictions artifacts/final_sprint/full.csv --report artifacts/final_sprint/full_validation.json
python code/main.py validate --split full --predictions artifacts/final_sprint/submission_candidate.csv --report artifacts/final_sprint/candidate_validation.json
python code/package_submission.py --output artifacts/code.zip
```

Solve/evaluate/validate/preflight exit 1 for documented unresolved/invalid results while writing artifacts; exit 2 means input/configuration errors. A strict solve --split full ... --submission-output output.csv attempt refuses publication with current evidence. Windows reproduction is tested; native OCR portability to Linux/macOS is not claimed.

## Upload checklist and blockers

| Artifact | Exact filename | Status |
| --- | --- | --- |
| Runnable source | artifacts/code.zip | Regenerated, required evaluation/ reports, README and configuration; no dataset/secrets/caches |
| Strict diagnostics | artifacts/final_sprint/full.csv | 518 rows, 510 contract-valid; not official prediction upload |
| Experimental candidate | artifacts/final_sprint/submission_candidate.csv | 518 rows, CSV/JSON valid, 516 contract-valid, eight assumed verdicts |
| Assumptions / evaluation | artifacts/final_sprint/candidate_report.json and sample_evaluation.json | Actual results, not self-test metrics |
| Selected official prediction | output.csv | Absent; no fully contract-valid evidence-supported result |
| Chat transcript | log.txt | Real append-only record, final turn appended before response |
| Native traces | agent-trace.zip | Pending session completion, shutdown, staging and secret review |
| Required reports | code/evaluation/evaluation_report.md and usage_report.md | Packaged at evaluation/ as well as source location |

Usage reports identify the exact experimental candidate run and SHA256, with no providers/models, zero calls/tokens/model-cache hits and USD 0 total/per-request cost. Local native OCR reuse is not model usage. Historical pilots and unknown older usage are separate. No report falsely claims a run produced an eligible output.csv.

Final working/fresh checks, source ZIP integrity, source correspondence, credential exclusion and all 103 original dataset hashes are recorded in artifacts/final_sprint/verification.json. Native traces must not be copied while active: quit Codex, stage relevant session JSONL under agent-trace/codex/, review/redact, then Compress-Archive -Path .\agent-trace -DestinationPath .\agent-trace.zip. Include other harness sessions as required; do not copy auth/config stores.

Submission page prescribed by the repository: https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists . No authenticated closing timestamp is asserted. If the platform accepts an experimental candidate upload, it remains a disclosed risky attempt, not a fully verified submission.

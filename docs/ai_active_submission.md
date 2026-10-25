# AI-active final submission: actual execution summary

This is the stable informed agent with real runtime API calls, not LLM-only and not experimental blind-first agent-led. The agent sees a baseline, chooses read-only tools, receives results, follows leads, and recommends intent/verdict/complete plans. Independent source/cutoff/identity/policy validators retain final authority.

**Selected full run:** 518 requests, 16 actually live-investigated, 64 DeepSeek/deepseek-flash generations; nine audit recommendations ACCEPTED, seven REJECTED. 782,324 input + 98,778 output = 881,102 tokens; configured estimated USD 0.3532308. No provider errors, retries, cache hits or unknown usage. Runtime 490.285956 seconds.

No unique new grounded facts or canonical prediction changes. Nine accepted recommendations demonstrate source-grounded audit reasoning, not incremental prediction gain. All 518 selected predictions match the prior offline candidate. The current production artifact is generated from the live run, not the zero-cost replay.

| Case | Model verdict | Independent recommendation outcome | Remaining validation codes |
| --- | --- | --- | --- |
| case_100 | INCOMPLETE | ACCEPTED |  |
| case_102 | INCOMPLETE | ACCEPTED |  |
| case_104 | INCOMPLETE | REJECTED | LEDGER_SELECTED_STATE_PROOF_MISSING, LEDGER_STATE_PROOF_NOT_INSPECTED |
| case_124 | INCOMPLETE | REJECTED | PLAN_OBLIGATION_OR_CITATION_MISMATCH, UNKNOWN_OR_MISMATCHED_EVIDENCE |
| case_130 | INCOMPLETE | REJECTED | PLAN_OBLIGATION_OR_CITATION_MISMATCH |
| case_131 | INCOMPLETE | ACCEPTED |  |
| case_143 | INCOMPLETE | ACCEPTED |  |
| case_148 | INCOMPLETE | ACCEPTED |  |
| case_151 | COMPLETE | ACCEPTED |  |
| case_160 | INCOMPLETE | REJECTED | LEDGER_SELECTED_STATE_PROOF_MISSING, PLAN_OBLIGATION_OR_CITATION_MISMATCH |
| case_174 | INCOMPLETE | ACCEPTED |  |
| case_175 | COMPLETE | REJECTED | LEDGER_COVERAGE_NOT_INDEPENDENTLY_ESTABLISHED |
| case_179 | INCOMPLETE | REJECTED | PLAN_OBLIGATION_OR_CITATION_MISMATCH |
| case_180 | INCOMPLETE | REJECTED | LEDGER_COVERAGE_NOT_INDEPENDENTLY_ESTABLISHED, PLAN_OBLIGATION_OR_CITATION_MISMATCH |
| case_182 | INCOMPLETE | ACCEPTED |  |
| case_184 | INCOMPLETE | ACCEPTED |  |

## Representative accepted tool-using audit: case_100

Round 1: model chose explain_policy twice and inspect_source twice. Round 2: it chose three follow-up identifier/resource searches. Subsequent model turns produced and corrected a structured audit plan. The accepted INCOMPLETE recommendation reports search_018 present and support_1630 identifying PII, citing evidence_89; it proposes deletion/redaction and the respective future verification checks. Full original arguments, citations, plans, proof ledger and independent rejections are in agent_execution_report.md. Tool-budget denials are preserved; attempts are not counted as successful inspections.

## Reproducibility and safety

A verification replay revalidated the same 16 cached recommendations with zero new model calls and reproduced output.csv byte-for-byte. Cache generation provenance is the selected 64-call live run above. Caches are retained as local evidence, excluded from the ZIP. Fresh API output text is nondeterministic; repeated live execution may differ. Offline --ai none also reproduces this unchanged CSV, as a separate ablation rather than a new live run.

All 61 runtime Python/PowerShell files are byte-identical to the repaired stable package previously tested with 337 passing tests. All 103 dataset file hashes remain unchanged. Existing Windows native OCR and independent verification are preserved. No experimental runtime or hardcoded case branches were added.

Format 518/518, strict contract 516/518, strict-decided verdicts 510/518 and complete internal proof/plan 509/518. Eight assumption-based candidate verdicts remain. case_55 lacks direct restore-state proof; case_63 has a conflicting subject link; case_34 retains its conditional-plan gap. These are not cured by model repetition.

Only 16 cases were investigated live. 76 more eligible cases were skipped at the explicit budget, 407 were unambiguous, ten non-deletion, eight lacked actionable proof and one had contradictory identity. We do not claim all 518 received an LLM call.

Sample pilot is separate: four live calls on one case, one accepted audit recommendation; USD 0.0248181. The full 32-case end-to-end evaluation remains status 90.625%, exact/sequence 28.125%, step F1 89.325843%, field 77.447426%; no improved or regressed cases. Total this request: 68 new calls, estimated USD 0.3780489.

**Readiness: GO WITH DISCLOSED RISK**, not 518/518 evidence-proven. Use the new FINAL_UPLOAD_AI trio together; preserve the earlier FINAL_UPLOAD as the offline backup.

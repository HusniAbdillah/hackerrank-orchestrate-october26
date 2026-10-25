# Gemini live runtime comparison — not promoted

The prior full run called DeepSeek for 16 requests and used deterministic processing
without model calls for 502 others: 407 unambiguous, 76 eligible but budget-skipped,
ten non-deletion, eight without actionable proof, one identity conflict. The agent is
the existing AuditInvestigator._loop: model-selected tool calls, observed results,
follow-up retrieval, structured verdict/plan recommendations and validation feedback.
It is an informed agent receiving a baseline, not an LLM-only or blind-first solver.

Gemini model availability was verified with the authenticated model-list endpoint.
Model: gemini-3.5-flash-lite. First pilot: four generation attempts, three successful
tool-using calls and one HTTP 400 final-schema rejection. The API disallowed enum:[""]
in the native response schema. Fixed only the Gemini wire schema to omit that enum;
the original local schema still strictly requires empty remediation citations. Direct
regression verified nonempty citations are rejected, and the 337 stable tests passed.

Corrected pilot: three successful calls, 44,245 input and 3,785 output tokens; estimated
USD 0.0473775. It returned valid JSON, but the audit recommendation was rejected for
unsupported/missing proof-ledger claims. No prediction changed.

Full Gemini run: 518 processed, 14 live-investigated, 51 real generation calls, 692,464
input and 56,718 output tokens. All API calls succeeded, zero retries/cache hits/missing
usage. Configured rates USD 0.75/input-million and USD 3.75/output-million; estimated
USD 0.7320405, not a billing invoice. Runtime 269.767213 seconds. Case cap was raised
to 518, call cap 1000, cost cap USD 20, output room 8192 tokens/call. Investigation
was time-bounded to 180 seconds, with the existing final in-flight case deadline.
It stopped because of the submission-time window, not the old 16-case limit.

This still preserves existing evidence-based routing: at most 92 cases are eligible.
The remaining 504 requests in this run had no model call: 407 unambiguous, 78 eligible
but time-skipped, ten non-deletion, eight lacking leads and one identity conflict.
There is NO claim all 518 received AI review. Token allowance alone does not change routing.

All 14 complete recommendations were REJECTED. Intent components: 14 accepted; complete
plan components: one accepted, 13 rejected/unresolved. Errors: 13 plan/citation mismatches,
20 claimed tool inspections not actually returned, 11 missing ledger categories, ten
unproven ledger-coverage claims, two missing selected-state proofs and one uninspected
state proof. Counts overlap by case. On the same 14 requests, DeepSeek had 7
accepted complete recommendations versus Gemini zero. This is a proposal-validation
comparison, not a claim about universal provider quality or hidden-label accuracy.

No new grounded facts or canonical prediction changes. Gemini CSV is byte-identical
to the prior candidate: format 518/518, strict contract 516/518, strict-decided 510/518,
eight assumed verdicts and case_55/case_63 verification failures remain. Sample pilot
status 90.625%, exact/sequence 28.125%, F1 89.325843%, field 77.447426% are unchanged.

Total this Gemini request: 58 generation attempts. Known successful-usage estimate
is USD 0.81052875. The failed first-pilot HTTP 400 has no reported usage; its ledger
retained a conservative USD 0.07267725 reservation, not known actual billing. Thus the
raw ledger sum USD 0.883206 must not be reported as an exact invoiced cost.

**NO-GO for replacing the selected DeepSeek submission with Gemini.** Keep the existing
DeepSeek AI-active output and report its actual 64-call usage. Gemini remains an honest
comparison experiment. Raw traces are preserved locally; gemini_execution_report.md
contains actual model-selected tools, proposals and rejection details visible to a judge.

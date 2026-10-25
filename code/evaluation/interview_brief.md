# Interview briefing and actual agent case study

## 90-second architecture pitch

We built a deletion-audit system that separates investigation from evidence authority. It reads the participant CSVs, reconstructs current and historical identity, normalizes local media, and evaluates each request at its audit cutoff. Our single LLM agent chooses bounded read-only tools and proposes intent, verdict, remediation and verification. It now also produces an Audit Proof Ledger covering authorization, identity, ownership, state, treatment, recreation risk, retention and plan coverage.

Every proposal is checked independently against original sources, exact ownership, event and capture times, policy conditions and canonical obligations. Model commentary never becomes evidence. Missing fields do not prove redaction, workflow success does not prove deletion, and a clean primary does not clear a dirty replica.

Our latest real pilot inspected shared-support policy and source records, producing thirteen proof goals: nine accepted and four unresolved. Its complete plan was rejected because a finding was omitted. It did not improve accuracy, so we stopped paid experiments. Earlier full-run investigations also produced accepted recommendations without changing canonical predictions.

The shipped CSV is explicitly best-effort: all 518 rows have valid format, but two fail strict contract checks and eight verdicts depend on disclosed assumptions. We report that limitation rather than invent verification.

## Real case study: sample case_29

This is actual DeepSeek/deepseek-flash execution, not a staged dialogue. Four generation calls reported 52098 input and 8079 output tokens; estimated USD 0.0253242 using configured rates. Sum of provider latencies: 30.296 seconds; whole sample run: 48.349 seconds.

1. Round 1: model selects explain_policy for ANALYTICS_PROFILE, DATA_FLOW, SEARCH_INDEX_ENTRY and SUPPORT_MESSAGE.
2. Round 2: model requests inspect_source for the analytics profile and connector in evidence_92, then search/support records. The first two inspections succeed; the last two exceed the six-successful-tool budget and remain visible as errors. They are not falsely counted as inspected.
3. Round 3: model recommends INCOMPLETE with a plan and proof ledger. Independent validation rejects timestamp mismatches, a wrong support finding, missing TREATMENT ledger coverage and an unsupported PLAN proof claim.
4. Round 4: bounded correction fixes the ledger/source claims. The final ledger has nine ACCEPTED and four UNRESOLVED entries. The complete plan still omits the search_1993 remaining-record finding and is rejected. The independent canonical result survives.

No novel fact, resolved obligation, improved sample case or changed canonical prediction resulted. Full tool arguments, proposed operations, source IDs and ledger outcomes are in agent_execution_report.md. Accepted existing facts are duplicates, not new evidence. An accepted ledger claim is not an isolated causal contribution to prediction accuracy.

## Technical answers

- **Is this a real agent?** Yes: model-selected tool batches, tool responses appended to history, follow-up retrieval, structured recommendations and bounded validation feedback. Final formatting and evidence acceptance remain deterministic.
- **Where did AI help?** It performed policy/source investigation and explicit proof accounting. Earlier full investigations accepted COMPLETE/INCOMPLETE recommendations; latest ledger makes rejected and unresolved claims observable. No measured accuracy gain is claimed.
- **Why not call every case?** Routing found 92 full cases with original support-policy context; 407 were unambiguous, ten non-deletion, eight lacked actionable proof and one had conflicting identity. A failed legacy routing gate was fixed and regression-tested. After the zero-gain pilot, no further paid full batch was run.
- **Why did the latest full run use no models?** The selected materialization explicitly sets generation/case budgets to zero after the zero-gain stopping decision. It is not presented as a new live LLM run. Earlier nine-call full usage is historical, not charged again.
- **Why no perfect CSV?** case_55 lacks archive restore-permission proof; case_63 has screenshot/catalog identity conflict. Root output.csv exists only as an assumption-based best-effort candidate, with strict failures preserved in output_diagnostics.json.
- **How do you prevent leakage?** Prediction modules never read sample_output.csv; it is evaluation-only. No hidden labels, suffix ownership, future links, or model-created evidence are accepted.
- **How reproducible?** Declared dependencies, regenerated Windows native OCR, source ZIP checks and dataset hashes. Offline --ai none reproduces the unchanged canonical predictions. Live output can vary and is independently checked.
- **What would improve accuracy next?** Admissible historical ownership and state proof for missing verification obligations. More model calls cannot supply facts absent from the corpus.

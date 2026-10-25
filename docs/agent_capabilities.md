# Agent proof discovery and bounded investigation

## Implemented

The existing single investigator now has five read-only tools. New `inspect_source(file_id, observation_id, pointer_path, offset, limit)` returns bounded original observation text or an RFC 6901 JSON location, not arbitrary files or SQL. It reports the source hash/locator, event and capture times, kind/direct state, character counts and continuation offset. It refuses mismatched files and future sources. Undated available content is inspectable as a lead, never automatically state proof. Existing paginated tools remain unchanged.

Two new proposal interpretations extend capabilities without relaxing old interpretations:

- `LINK_IDENTITY`: the same structured entity must explicitly contain system, resource, policy category, and either a unique stable subject reference or a complete source_system_id/source_resource_id foreign key to an already uniquely owned parent. Known ownership conflicts and contradictory direct identifiers are rejected. Names, substring matches, row positions and timestamps cannot establish ownership. A validated relation is stored as relationship metadata with UNKNOWN state, never as presence/deletion proof.
- `EXTRACT_FIELDS`: relative canonical field pointers select literal values from the identified entity. They cannot rename another boolean, cross a resource/subject boundary, select a proposed configuration, or bypass conflicting values. Untyped JSON requires an explicit direct_readback/snapshot_row marker. Scalar derived fields are isolated from raw decoded/profile wrappers. Original nested values remain in provenance. The state engine independently computes the proposed state. Partial null fields cannot prove tombstone redaction/anonymization.

For vision, EXTRACT_FIELDS accepts only explicit unambiguous enabled/restore_allowed/deletion_block true/false lines in the original OCR text, with matching original PNG hash, exact corroborated subject email and a single resource scope. A button, absent label, OCR repair, conflicting flag or multi-resource screen is rejected. Unlike the older metadata-only corroboration, a validated derived field can reach the existing state engine and change its computed state. This is deliberately narrower than arbitrary visual reasoning.

Derived observations preserve original source/file IDs, raw data, image/file hash, pointer bindings and parent proof sources. Derived IDs are stable hashes of their extraction bindings; they are internal observation IDs, not invented evidence IDs. Source capture time remains in derivation provenance; composite availability includes ownership-join knowledge. Entity event time remains separate from file availability. Original observations are immutable and all changes are case-local. Literal replica scope is preserved; an unscoped clean context cannot clear a known copy, and a clean replica cannot clear a dirty primary. Ownership memoization is isolated between disposable proof stores.

Every derived relation/field observation is explicitly row-only. It cannot become an exhaustive table inventory or project absence onto other resources, even if its source carried table metadata. Scope metadata is retained for provenance/copy reconstruction, not promoted into a new global negative proof. Pointer paths also reject conflicting canonical values across current-state wrappers and proposed/desired scopes. These restrictions apply to the new proof paths; previously grounded deterministic observations retain their existing behavior.

## Selection and model budgets

Context now contains concrete unresolved proof goals, grounded resource/policy obligations, preloaded identity and exact-identifier or owned-parent source leads. Lead counts/truncation are explicit. A case with no preexisting resource may be investigated when such a lead exists; no-source cases and non-deletion requests still skip. Otherwise sufficient cases can be explored for an untyped-source lead, within the existing case/call/cost limits. Leads are not proof and may be duplicates.

When retrieval has no pending page/error, the penultimate turn requests a structured draft. At most one schema/grounding correction uses the remaining turn. An explicitly incomplete page or failed tool can instead use that turn for adaptive retrieval; then no extra correction turn is promised. Default three model turns, six successful tools, token/deadline/cost caps and provider routes are unchanged. The new source tool shares the same tool budget. No model framework, provider API change or budget increase was introduced. Prompt version is audit-investigator-4 and schema version 3, invalidating older proposal caches.

Relations are validated before dependent field facts in the same proposal. Failed relations cannot supply ownership; each remaining fact must independently pass grounding. Every attempt is retained. Proof deltas distinguish new relationship, field proof, state fact, metadata enrichment and duplicate. The solver reports actual status/step changes, resolved/introduced issue codes and new resource links; new facts do not automatically imply accuracy improvement. Final policy, remediation, ordering and serialization remain deterministic.

## Verification and measured limitations

Independent fixtures exercise source traversal/cutoffs, identity and foreign-key discovery, dependent fact validation, conflicting subjects/fields, scoped replicas, visible fields, complete-identifier requirements and bounded draft correction. One mock tool-using investigation reads a new structured source, returns a relationship plus field proof, and uses two model turns. Another independently specified business case changes from COMPLETE to INCOMPLETE when an explicit active backup readback is grounded. These are tests of capability, **not a measured live-model or public-sample improvement**.

Offline replay of the actual prior DeepSeek case_07/case_17 and Gemini vision case_63 proposals yields four duplicates and five rejected facts, zero new facts, zero status/step changes. Original model proposals are replayed; the new prompt/tool choices have not been live-evaluated. No new paid calls were made because replay revealed no additional admissible facts in those previously exhausted cases. Prior historical seven-call usage is not charged again.

Current deterministic sample metrics remain: status 90.625%, exact/sequence 28.125%, precision 97.546012%, recall 82.383420%, F1 89.325843%, field 77.447426%, validity 29/32. Full output still has 510/518 contract-valid rows, eight unresolved verdicts and one additional decided plan gap. The new capabilities do not invent the absent tombstone fields, restore permission, missing primary links or resolution of conflicting screenshot identity. Root output.csv remains withheld. Sample labels never enter investigation or prediction.

## Commands and artifacts

```powershell
python -m pytest -q
python -m pytest -q tests/test_agent_proof_paths.py
make agent-replay
python code/main.py solve --split sample --output artifacts/agent_capabilities/sample.csv --report artifacts/agent_capabilities/sample_run.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/agent_capabilities/sample.csv --report artifacts/agent_capabilities/sample_evaluation.json
python code/main.py solve --split full --output artifacts/agent_capabilities/full.csv --report artifacts/agent_capabilities/full_run.json --extractions artifacts/ocr_cache --submission-output output.csv
python code/package_submission.py --output artifacts/code.zip
```

`make agent-replay` needs the historical pilot reports under artifacts/agent_fixes; these are intentionally excluded from the source archive. For other reports use `python code/evaluation/replay_agent.py --run <report> --extractions <ocr-cache> --output <replay-report>`. Offline replay has no provider imports or API calls. Fresh-source regression tests and ordinary deterministic commands do not require historical model reports or credentials. Model-assisted CLI flags remain compatible; the new proof paths are exercised only for explicitly enabled AI runs.

Machine verification, full regression output and actual replay results are under artifacts/agent_capabilities. Clean archive execution uses the externally supplied dataset and declared dependencies. Existing original dataset hashes and append-only conversation logs are preserved. Native session trace export still waits for shutdown under agent_trace_instructions.md.

Working regression result: **273 tests passed** (235 preceding tests plus 38 proof-path regressions). All prior strict solver/evaluator/ingestion tests remain passing. The sample and full CSVs are byte-identical to their preceding strict outputs. The final archive/checkouts are verified in artifacts/agent_capabilities/verification.json; any fresh-run result there is separate from the mocked agent demonstrations and historical proposal replay.

Extracted-source verification also passed all 273 tests (37.78 seconds; working run 33.01 seconds). It used the existing isolated declared-dependency environment and explicitly supplied native OCR cache from the preceding clean extraction; no credentials or model caches were copied into the source checkout. The fresh full preflight reproduces the exact strict CSV and refuses publication. The source ZIP has 77 files; required reports, CRC, source correspondence, actual credential exclusion and all 103 original dataset hashes are verified. This verifies Windows reproduction, not native OCR availability on other operating systems.

# Evidence normalization and temporal identity resolution

This iteration adds evidence ingestion and exact identity/resource lookup. It does not
produce deletion statuses, infer final resource state, implement remediation planning,
or call model APIs. Existing evaluation, validation, readiness, and self-test commands remain
available. The readiness `run` command remains a metadata-only milestone; use `ingest` for
the new normalization and identity diagnostics.

## Reproduce

From the repository root with Python 3.11+:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
python code/main.py ingest --report artifacts/ingestion_coverage.json --identity-report artifacts/identity_coverage.json --normalized artifacts/normalized_evidence.jsonl
python code/main.py self-test --report artifacts/evaluator_self_test.json
```

`pypdf==6.14.2` is the only ingestion runtime dependency beyond Python's standard library.
`--dataset` and `--inventory-doc` can override the repository-relative defaults. All three
output paths are optional and must be distinct, outside the dataset, and different from the
inventory input. The coverage report is printed to stdout regardless of `--report`.

Exit 0 means supported adapters completed and the inventory/integrity checks passed. PNG
pending extraction is explicitly permitted at this milestone and reported as incomplete
extraction. Exit 1 means parser failure, partial parsing, unmanifested evidence, or an
inventory/integrity mismatch. Exit 2 means a fatal input/configuration problem, such as a
missing manifest file or invalid identity input. An invalid document with no readable PDF
text is an ingestion failure, not an empty clean record.

## Modules and data contract

- `observations.py`: typed observation records, bounded exact identifier extraction, and
  shared resource/identifier indexes.
- `parsers.py`: observed JSON shapes, in-memory SQLite snapshots, six log wrappers,
  trace correlation, handover text, and PDF page text.
- `ingestion.py`: authoritative manifest traversal, PNG pending records, activity claims,
  inventory accounting, file hashes, and coverage reporting.
- `identity.py`: current/historical identifier intervals, knowledge-time filtering,
  exact resolution, and resource ownership with evidence provenance.
- `diagnostics.py`: one shared parsed store for both request splits, identity coverage,
  documented CSV/evidence count checks, and before/after dataset integrity.

An observation preserves `observation_id`, `source_id`, `file_id`, `system_id`, `resource_id`,
collection/category, observation timestamp, capture timestamp, evidence kind, original fields,
scope, exact identifier tokens, explicit resource links, and raw-source provenance. Provenance
contains a source path, SHA-256, and JSON pointer, SQL table/row locator, log/text line number,
or PDF page number. JSON and SQL original text is retained once in the in-memory store;
SQL records retain both the original `record_json` cell and its decoded object. SQL row
locators identify the inspected result row, not an invented source-code line number.
The optional JSONL exports the normalized records; the unchanged dataset remains the raw source.

Manifest origins are not case membership. The manifest determines which evidence files
are read; additional physical evidence outside it is a visible error. Parsing is once per
file per ingest process. The resulting store is reused for all cases, with resource keys
`(system_id, resource_id)` and identifier-token indexes. No external or persistent database
is required. Each new CLI invocation rereads the files; there is no unversioned disk cache.

## Evidence distinctions and temporal scope

| Kind | Meaning in this iteration |
| --- | --- |
| `direct` | Structured snapshot/readback content; still not an adjudicated deletion verdict |
| `reported_claim` | A row from global `system_activity.csv`; SUCCESS/FAILED/PARTIAL remains a reported outcome |
| `scoped_negative` | Explicit empty captured collection, scoped empty SQL table, or negative lookup for the stated resource |
| `missing_data` | Empty lookup-export array without exhaustive scope, out-of-scope empty SQL table, or failed attachment preview |
| `context` | Lookup starts, debug/control lines, handover prose, or extracted PDF page text |
| `metadata` | Explicit SQL snapshot-scope rows |
| `pending_multimodal` | PNG source with dimensions and hash, requiring structured visual extraction |

The machine-readable coverage report counts these separately. A negative collection has
no invented subject/resource ID and does not prove absence in another system. A cache miss,
thumbnail failure, workflow success, or exporter completion never becomes record absence.
For typed SQL, only systems actually listed in `snapshot_scope` are covered; even an empty
scope table does not grant global negative evidence. Primary and each replica remain separate
observations, including when they share a resource key.

`Observation.admissible(at)` requires both capture/availability time and observation time
to be known and no later than the cutoff. Querying a resource applies this filter before
returning observations; there is no latest-state collapse. Snapshot times, explicit
`observed_at`/`recorded_at`, SQL snapshot headers, and per-system scope timestamps determine
observation times. `updated_at`, creation, expiry, and retention deadlines remain original
fields and are not substituted for snapshot observation time.

Logs normalize plain/quoted key-values, bracketed traces, pipe records, syslog, timestamped
JSON, and cloud runtime messages with escaped payloads. A completion may obtain identity
context only from an earlier, non-future lookup start in the same file, service, and trace.
The original reporting service is preserved; the observed `support_replica` store is mapped
to support_platform while retaining the replica reporting context. Unknown events fail
visibly instead of being counted as understood noise. Trace reuse/out-of-order streams
without a preceding eligible start may retain an unlinked completion for later investigation.

PDFs retain the full extracted text of every page. Their capture time describes when the
document text was available, not the date of every embedded transaction. They remain context
records, not structured assertions about every order or privacy treatment. A page with several
subjects/resources is not split into guessed ownership pairs. Pending PNGs have no observation
time and cannot establish absence or prove identity/resource state.

## Identity graph and resource ownership

The graph loads all current identity rows and audit changes. Each identifier version has
user ID, type, normalized value, `valid_from`, `valid_to`, `known_at`, and source ID. Old and
new email, hash, and phone values are indexed. User ID is the stable subject key; names are
retained in the source dataset but never used to merge or match identities.

Email casing and phone formatting are normalized. Dot/plus-tag removal, provider-specific
email rewriting, phone suffix matching, fuzzy names, and substring joins are prohibited.
Text token extraction respects complete email/user/hash boundaries; integrity seals are
not treated as customer email hashes. Historical hashes come from actual supplied values,
not inferred links to arbitrary digests.

Validity and knowledge time are different. An audit row's old value becomes admissible
knowledge when the change was recorded, unless an earlier source already established it.
Future changes cannot reveal their old/new values or even a future `valid_to` on an already
known value. A current snapshot cannot reveal a value before its update time; a matching
audited future transition also prevents a stale snapshot timestamp from exposing that future
value early. Stable user-reference provenance cites the earliest eligible snapshot/audit
source. Gaps or disagreements in the complete supplied history are diagnostic issues.

Resource ownership is a provenance-bearing candidate association, not a deletion-state
decision. Exact identifier matches seed links only from admissible observations. Both the
identity knowledge time and observation availability are recorded. A reported catalog link
keeps `reported_claim` in its basis; it is not promoted to direct state proof. Conflicting
exact subjects remain multiple candidates on the resource, with no identity union/merge.

Historical resource links are retained after a later observation removes all PII. Explicit
search `source_resource_id` links may propagate association between the search document and
its account; arbitrary co-occurring resource strings cannot. Each propagated link retains
its own source and availability time. Resource-owner results are cached per store/cutoff;
the same parsed evidence is reused across cases. Queries return all admissible observations,
including conflicting replicas and earlier states, for a future state-reconstruction stage.

## Measured coverage

Results from the actual participant dataset, without parsing reference answers:

| Evidence format | Files | Raw units accounted | Result |
| --- | ---: | ---: | --- |
| JSON | 28 | 890 domain records | Parsed |
| SQL | 24 | 969 rows, including scope metadata and replica copies | Parsed |
| Logs | 26 | 2,211 physical lines, including control/debug lines | Parsed |
| Handover text | 1 | 46 physical lines | Parsed |
| PDF | 4 | 7 complete text pages | Parsed as page context |
| PNG | 11 | 11 images | Explicitly pending multimodal extraction |
| **Total** | **94** | Units remain separate by type | **83 parsed; 11 pending** |

All 94 per-file counts match the appendix in `dataset_analysis.md`. Eight non-reference
CSV row counts also match its inventory. `sample_output.csv` is not parsed by this path;
it is included only in the all-file integrity hash check. The output template is checked
as a zero-row CSV, not used as answers.

The normalized store has **8,163 observations**, **4,837 resource keys**, and **1,481 identifier
keys**. Observation kinds: 2,648 direct, 253 scoped-negative, 4,011 reported claims, 1,151
context, 78 metadata, 11 missing-data, and 11 pending-multimodal. These are accounting units,
not counts of unique customers or deletion violations.

The identity graph has **850 subjects**, **306 audit changes**, and **4,008 identifier versions**;
the supplied history produced no gap/conflict diagnostics.

| Request split | Unique identity resolution | Current email | Historical email only | With at least one resource candidate |
| --- | ---: | ---: | ---: | ---: |
| Public sample | 32/32 | 29 | 3 | 29/32 |
| Evaluation inputs | 518/518 | 418 | 100 | 509/518 |

These are identity/linkage coverage metrics, not prediction accuracy, and do not imply that
all relevant resources were found. Original SHA-256 hashes of all **103 dataset files** remain
unchanged. The coverage report includes a stable aggregate fingerprint and every evidence
file's hash. Normalized data, capture times, counts, and report ordering are reproducible
for the pinned runtime and unchanged inputs.

## Unresolved evidence and actual limitations

- Eleven PNGs remain pending: evidence_04 (account administration), evidence_09 (search),
  evidence_14 (connector management), evidence_19 (analytics), evidence_23 (exports),
  evidence_28 (support), evidence_32 (backups), evidence_37 (security), evidence_42 (deleted
  reference), evidence_46 (object storage), and evidence_60 (marketing).
- Four direct readback observations in evidence_61, lines 3, 5, 6, and 8, have preserved
  event collections but no adjudicated policy category. They describe legacy/contact and
  deletion-marker reads; the parser does not guess a treatment from their resource prefix.
- Sample case_01, case_02, and case_04 resolve to identities but currently lack grounded
  resource links. Evaluation cases case_534 through case_542 likewise have no resource
  candidate at their cutoffs. These are measured diagnostics, not hardcoded program rules;
  missing links cannot justify COMPLETE or NOT_APPLICABLE.
- PDF page extraction is complete, but typed business record splitting, embedded human-date
  interpretation, retention semantics, and multi-subject resource pairing remain to be built.
- Ambiguous identity/resource candidates are preserved rather than resolved heuristically.
  This dataset run had no ambiguous request identity or multi-subject resource for the
  resolved cases; synthetic tests exercise those paths.
- Normalization does not adjudicate stale evidence, retries, conflicting direct readbacks,
  policy conditions, deletion authorization, active-flow risk, or legal retention. It
  supplies the inputs for that work. There is no final prediction CSV or measured audit accuracy.

Recommended next step: extract the pending visual/business facts and close missing ownership
links, then implement a scope-aware state timeline and policy-decision layer at `audit_at`.
Only after that should the ordered remediation planner and end-to-end prediction evaluation
be added.

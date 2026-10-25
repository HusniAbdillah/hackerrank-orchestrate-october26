# HackerRank Orchestrate - October 2026

Current final artifacts/results: [docs/proof_quality_submission.md](docs/proof_quality_submission.md).
337 tests pass. Root output.csv now exists as explicit best-effort: 518 format-valid rows,
516 strict contract-valid, eight assumed verdicts, NOT evidence-validated. Strict mode
remains 510/518. Read output_diagnostics.json and the current report before uploading.
The latest real proof-ledger pilot made four DeepSeek calls with zero prediction gain;
paid runs stopped. Final materialization explicitly uses zero model budget. Actual
tool/ledger evidence and interview pitch are in code/evaluation/ Markdown reports.
All earlier iteration descriptions below are historical.

Latest active-agent run: [docs/active_agent_submission.md](docs/active_agent_submission.md).
The LLM now recommends intent, verdict and full audit plans through five read-only tools;
independent grounding/policy/planning retains authority. The full run made nine live
DeepSeek calls on three cases; all three recommendations were accepted with no prediction
or accuracy change. Readable actual traces: code/evaluation/agent_execution_report.md.
320 tests pass. Strict validity remains 510/518; the experimental candidate remains
516/518 contract-valid. Root output.csv is withheld. Older sections are historical.

Latest final commands/results: [docs/final_submission_sprint.md](docs/final_submission_sprint.md).
305 tests pass; strict coverage remains 510/518. The opt-in observed-scope candidate
contains 518 rows but only 516 pass contract validation; eight verdicts are assumed,
not evidence-proven. Root output.csv remains withheld. Regenerate native OCR on
Windows for measured results; local caches and credentials are not bundled.

The single optional investigator now supports five read-only tools, including bounded `inspect_source`, exact identity/foreign-key proposals and source-validated JSON/visible field extraction. Default model/tool budgets are unchanged. See [docs/agent_capabilities.md](docs/agent_capabilities.md) for proof constraints, tests and the distinction between offline capability and measured sample accuracy. No live accuracy gain is claimed.

Final recovery: `make prepare-candidate` checks whether a separate submission candidate can be published. It preserves strict uncertainty and never fills unknown statuses. Current result is blocked on eight verdicts and one conditional plan gap. See [docs/submission_recovery.md](docs/submission_recovery.md) for exact commands, upload filenames and official schedule verification.

## Ghost Data Still Exists

Build an AI agent that audits whether a user's personal data was actually deleted.

A deletion workflow may report **Complete** while data still exists in databases, logs, support attachments, exports, search indexes, archives, or backups. Sync and restore processes may also bring deleted data back.

For each request, the agent must first determine whether deletion was actually requested. It then returns `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`, reports any remaining data or recreation risk, and produces the ordered remediation and verification steps required to finish an authorized deletion safely.

Read [`problem_statement.md`](./problem_statement.md) for the complete challenge contract.

## Quick Command Automation (`Makefile`)

All Python pipeline commands, tests, preprocessing steps, evaluations, and packaging routines are fully automated via `Makefile`. For the complete reference of all commands, options, and maintenance policies, see [`COMMANDS.md`](./COMMANDS.md).

```bash
make help               # Display formatted list of all available commands
make test               # Run the full unit and regression suite
make workflow-sample    # Run complete sample loop: ocr -> solve -> eval -> diagnose
make workflow-full      # Run production loop: ocr -> solve -> validate -> package
```

## Runnable deterministic audit baseline

The CLI now generates cutoff-aware predictions using exact identity/resource links,
direct readbacks, all 15 policy categories, and canonical remediation/verification steps.
It requires no model API key. `run` remains the earlier metadata readiness command;
use `solve` to generate predictions.

```text
python code/main.py solve --split sample --output artifacts/sample_predictions.csv --report artifacts/sample_solver_report.json --extractions artifacts/ocr_cache
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
python code/evaluation/diagnose_solver.py --predictions artifacts/sample_predictions.csv --solver-report artifacts/sample_solver_report.json --output artifacts/sample_mismatches.json
python code/main.py solve --split full --output artifacts/full_predictions.csv --report artifacts/full_solver_report.json --extractions artifacts/ocr_cache --submission-output output.csv
```

The sample run writes all 32 rows, with 90.625% measured status accuracy and 89.326%
step F1. Three cases lack an admissible grounded resource link. They are explicitly
unresolved with a null internal verdict and blank diagnostic CSV status;
these three rows deliberately fail validation. `solve` and `evaluate` therefore return
exit code 1 while still writing their artifacts. Exit 2 means fatal input/configuration
failure. The current outputs are diagnostic predictions, **not submission-ready**.
Full processing writes 518 rows; evidence gaps still block fully valid submission output.
Full-run contract-valid coverage is now 510/518 after optional local OCR (8 unresolved).
One decided case has incomplete proof/plan scope, so publication remains blocked.
The latest grounded catalog/listing join adds three sample steps omitted by the public
reference, lowering step precision/F1 despite improved full coverage. See
[docs/submission_debugging.md](docs/submission_debugging.md) for the measured tradeoff,
all original 13 abstentions and 21 plan ledgers. No sample-specific suppression is used.
Use `python code/main.py ocr --output artifacts/ocr_cache` on Windows, then add
`--extractions artifacts/ocr_cache` to solve commands. `--submission-output output.csv`
publishes only when all verdicts, proof scopes, validation and integrity checks pass.

See [docs/submission_readiness.md](docs/submission_readiness.md) for current results, exact limitations,
per-case discrepancies, and the next accuracy priorities. No dataset file is modified.

## Optional live Audit Investigator

Gemini and DeepSeek integrations use their documented HTTPS APIs, with no agent framework.
The agent can call five read-only tools; deterministic checks retain control of identity,
evidence admissibility, policy, verdicts and CSV ordering. Live text/tool investigations
succeeded with both providers, and Gemini image extraction succeeded. **No incremental
sample accuracy gain from AI was measured** in this iteration; unsupported proposals were rejected.

Configure an ignored `.env` using `.env.example` (preserve existing credentials), set
`LLM_ENABLED=true`, and select `DEEPSEEK_MODEL=deepseek-flash` or
`GEMINI_MODEL=gemini-3.5-flash-lite`. Never put keys on command lines or in reports.

```text
python code/main.py solve --split sample --output artifacts/deepseek_predictions.csv --report artifacts/deepseek_run.json --extractions artifacts/ocr_cache --ai deepseek --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.20 --ai-case-seconds 180
python code/main.py evaluate --split sample --predictions artifacts/deepseek_predictions.csv --report artifacts/deepseek_evaluation.json
python code/main.py solve --split sample --output artifacts/gemini_predictions.csv --report artifacts/gemini_run.json --extractions artifacts/ocr_cache --ai gemini --max-ai-cases 3 --max-model-calls 12 --max-cost-usd 0.20 --ai-case-seconds 180
python code/main.py evaluate --split sample --predictions artifacts/gemini_predictions.csv --report artifacts/gemini_evaluation.json
```

`--ai auto` routes text to DeepSeek and flagged OCR ambiguity to Gemini; `--vision`
permits original-image extraction for those flags. Sufficient deterministic cases and cases
without grounded resource candidates are skipped. No bulk paid full-run investigation was
justified by the sample experiment. See [docs/ai_investigator.md](docs/ai_investigator.md)
for limits, cache validity, costs, failure accounting, and exact reproduction commands.
Without configured credentials the optional agent reports unavailability and falls back.
`--ai none` (the default) neither loads `.env` nor makes network calls.

Build a source-only review package with `python code/package_submission.py`.
It writes `artifacts/code.zip`, excludes dataset, credentials, runtime caches and traces,
and includes required reports in both supported archive locations. This package does not
make the unresolved predictions submission-ready. Export agent traces separately after
ending the session, following `agent_trace_instructions.md`.

Use Python 3.11+. Evaluation/readiness uses the standard library; PDF ingestion additionally
requires the pinned `pypdf` dependency in `requirements.txt`. To install dependencies and run tests:

```text
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Normalize all manifest evidence once, check every evidence file's record/line/page count
against the reconnaissance inventory, and measure both identity-resolution splits:

```text
python code/main.py ingest --report artifacts/ingestion_coverage.json --identity-report artifacts/identity_coverage.json --normalized artifacts/normalized_evidence.jsonl
```

This parses JSON, SQL, logs, handover text, and PDF text. PNGs produce explicit pending
multimodal records. Reports include unsupported/partial parser failures, original-dataset
SHA-256 integrity, and identity coverage at each request's cutoff. No reference answers are
parsed and no deletion verdicts are generated. Unsupported/partial files or inventory
mismatches return exit code 1; expected PNG pending records are listed prominently and
make `complete_extraction=false`, while allowing diagnostics to finish successfully.

See [`docs/ingestion_identity.md`](./docs/ingestion_identity.md) for architecture, measured
coverage, unresolved evidence, and temporal knowledge limitations.

From the repository root, load each input split independently:

```text
python code/main.py run --split sample --report artifacts/sample_pipeline.json
python code/main.py run --split full --report artifacts/full_pipeline.json
```

Evaluate **your own sample prediction file** with the public reference:

```text
python code/main.py evaluate --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_evaluation.json
```

Validate full predictions without ground-truth access:

```text
python code/main.py validate --split full --predictions output.csv --report artifacts/full_validation.json
```

Run a controlled evaluator demonstration:

```text
python code/main.py self-test --report artifacts/evaluator_self_test.json
```

The self-test derives temporary test inputs from the public sample answers, changes
object-key order, reverses a step array, removes/duplicates cases, and corrupts a citation.
It is an evaluator test, **not solver performance**; its temporary CSVs are removed.
The `run` path never reads `sample_output.csv`. The CLI deliberately rejects reference
evaluation for the full split, for which no participant ground truth is available.

`--dataset` can override the default repository-relative dataset location on each command.
Every command prints JSON; `--report` additionally saves it outside `dataset/`. Exit codes:
`0` for a valid artifact/successful readiness or self-test run, `1` for invalid predictions
(diagnostic metrics are still reported), and `2` for input/configuration errors. Low accuracy
alone does not change the exit code. `python code/evaluation/main.py` accepts the same
subcommands as a compatibility entry point.

See [`docs/evaluation_foundation.md`](./docs/evaluation_foundation.md) for exact matching
definitions, validation limits, and architecture. Foundation results and usage are in
[`code/evaluation/evaluation_report.md`](./code/evaluation/evaluation_report.md) and
[`code/evaluation/usage_report.md`](./code/evaluation/usage_report.md).

---

## Quick Start

Clone the repository and move into the project directory:

```bash
git clone https://github.com/interviewstreet/hackerrank-orchestrate-october26.git
cd hackerrank-orchestrate-october26
```

Start your AI coding tool from the **repository root** so it automatically reads [`AGENTS.md`](./AGENTS.md) and logs your session turns to `log.txt` in the root directory.

Build your solution in `code/main.py`, or use another language and document its setup and run command clearly in your README.

Your solution must:

- Read the input files from `dataset/`
- Generate one prediction row for every request in `dataset/deletion_requests.csv`
- Write the final predictions to `output.csv` in the repository root

Inspect the implemented entry point with:

```bash
python code/main.py --help
```

The blank template at `dataset/output.csv` is provided as a reference. Your final generated file for submission must be the root-level `output.csv`.


## Dataset

All participant-facing files are in `dataset/`:

| File | Contents |
| --- | --- |
| `deletion_requests.csv` | 518 requests |
| `sample_deletion_requests.csv` | 32 sample requests |
| `sample_output.csv` | Correct sample answers |
| `user_identities.csv` | Current user identities |
| `user_audit_log.csv` | Historical identity changes |
| `system_activity.csv` | Activity across services and data processes |
| `deletion_rules.csv` | Required treatment for each data category |
| `evidence_files.csv` | Manifest of supplied evidence files |
| `output.csv` | Blank output template |

Evidence is stored under `dataset/evidence/` and may include PDFs, images, logs, JSON, plain text, or SQL snapshot exports. SQL captures may contain a primary database, regional replicas, a reporting replica, or a failover replica so replication drift can be investigated directly. The `.sql` files are readable as text and executable with SQLite.

Only `deletion_requests.csv` requires answers. The other files provide evidence and context.

---

## Output

Create `output.csv` with these columns in this exact order:

```text
case_id,deletion_status,steps_json
```

Produce exactly one row per request. `deletion_status` is `COMPLETE`, `INCOMPLETE`, or `NOT_APPLICABLE`. `steps_json` is an ordered JSON array containing findings, remediation actions, and verification checks. Use an empty array (`[]`) for `NOT_APPLICABLE`. Evidence references may be a `file_id`, `activity_id`, or `audit_id`. Determine the resource state at `audit_at` from the available evidence; reported workflow statuses and operation results are claims. Use `dataset/sample_output.csv` as the format reference.

The final file must contain 518 data rows sorted by `case_id` (plus the header row). The grader parses `steps_json` as JSON, so object-key order and whitespace do not matter; array order does. Order findings, remediation, and verification in that phase order. Within a phase, follow the operation order in the problem statement, then sort by `system_id` and `resource_id`.

---

## Evaluation

`output.csv` will be compared with hidden canonical answers. Scoring considers:

- deletion assessment accuracy;
- current and historical identity resolution;
- discovery of remaining data and recreation risks;
- correct policy application and evidence references; and
- completeness and ordering of remediation and verification steps.

Your `code.zip` must include:

```text
code/evaluation/evaluation_report.md
code/evaluation/usage_report.md
```

- `evaluation_report.md` must cover case, row, field, and sequence accuracy, at least three additional evaluation cases created by you, failures found, and improvements made.
- `usage_report.md` must cover the final full-dataset run, including model providers and names, model calls, input and output tokens, total and average tokens per request, and estimated total and per-request cost. Include per-model and overall totals when using multiple models.

**Important:** Place `evaluation_report.md` and `usage_report.md` inside `code/evaluation/` (matching `code/evaluation/main.py` in this starter layout), write your complete evaluation metrics, custom evaluation test cases, and token/cost breakdowns directly inside those Markdown files, and keep prompts in source code or Markdown files. Automated code evaluation ignores raw data files (`.csv`, `.tsv`, `.json`, `.jsonl`, `.sql`, `.log`), so content stored only in those formats will not be visible to the code judge or AI interviewer.

---

## Chat Transcript

This repository includes [`AGENTS.md`](./AGENTS.md), which instructs compatible AI coding tools to append conversation summaries to `log.txt` in the repository root:

| Platform | Path |
| --- | --- |
| macOS / Linux | `<repo root>/log.txt` |
| Windows | `<repo root>\log.txt` |

- Always launch your AI coding agent from the repository root (or explicitly ask it to read `./AGENTS.md` first) so every turn is logged to `log.txt` with the required `User Prompt`, `Agent Response Summary`, `Actions`, and `Context` sections.
- Upload `log.txt` directly as your `chat_transcript` submission on HackerRank.
- Do not include API keys, tokens, credentials, or secrets in prompts, code, configuration, or `log.txt`.

---

## Packaging `code.zip` and Submission

| Item | Description |
| --- | --- |
| `code.zip` | Runnable solution, prompts, configuration, `README.md`, and `evaluation/` reports |
| `output.csv` | One answer row for each of the 518 requests in `dataset/deletion_requests.csv` |
| `chat_transcript` | The root `log.txt` file generated by your coding agent |
| AI interview | Live explanation of your architecture, approach, and evaluation |

You may use any programming language, model, framework, or retrieval approach. Include clear setup and execution instructions in `README.md` inside `code.zip`.

To package `code.zip` from the repository root without bundling the dataset:

**macOS / Linux:**

```bash
zip -r code.zip README.md code -x "*/__pycache__/*" "*/.venv/*" "*/venv/*" "*/node_modules/*" "*/.git/*" "*/.DS_Store"
```

**Windows (PowerShell):**

```powershell
Compress-Archive -Path README.md, code -DestinationPath code.zip -Force
```

When packaging `code.zip`:

- Keep your evaluation reports in `code/evaluation/` so they are bundled automatically with `code` (or add `evaluation` to the archive command above if you placed them in a top-level `evaluation/` directory).
- Do **not** include `dataset/`, virtual environments (`.venv`, `venv`, `node_modules`), or build caches (`__pycache__`). On Windows, keep `.venv` at the repository root (outside `code/`) and remove any `code/__pycache__` folders before running `Compress-Archive`.
- Do **not** include nested archives (`.zip`, `.tar`, `.gz`, `.tgz`, `.7z`, `.rar`) inside `code.zip` — submissions containing nested archive files will be rejected.

Before submitting, confirm that:

- `output.csv` has the exact header `case_id,deletion_status,steps_json` and contains all 518 data rows sorted by `case_id`;
- every `steps_json` value is a valid JSON array with consecutive step numbers starting at `1`;
- findings cite valid evidence IDs, and `COMPLETE` verification steps cite evidence proving the current state;
- proposed remediation and future verification steps use an empty `evidence_id` (`""`);
- `code.zip` includes your runnable code, `README.md`, `code/evaluation/evaluation_report.md`, and `code/evaluation/usage_report.md`;
- `log.txt` follows the `AGENTS.md` turn format and is uploaded to the `chat_transcript` slot; and
- no API keys, credentials, real personal data, or sensitive configuration values are included.

### Latest bounded agent correction pilot

See [docs/agent_corrections_readiness.md](docs/agent_corrections_readiness.md) for exact commands, real traces and cost. Pagination and one bounded grounding correction are implemented; same-ID vision enrichments reach a case-local solver copy. `--ai-case-id` explicitly investigates selected cases even if the deterministic decision is sufficient; it still requires grounded resource candidates and does not change evidence validation. Seven successful live calls yielded zero new facts or accuracy gain, so further paid experimentation was stopped. Full validity remains 510/518; `output.csv` is not published.

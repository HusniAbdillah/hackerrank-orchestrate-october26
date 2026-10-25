# Project Commands & Automation Reference (`Makefile`)

## Offline agent proof replay

`make agent-replay` revalidates the existing DeepSeek/Gemini pilot reports without API calls. It runs `python code/evaluation/replay_agent.py --dataset dataset --run artifacts/agent_fixes/deepseek_sample.json --run artifacts/agent_fixes/gemini_full.json --extractions artifacts/ocr_cache --output artifacts/agent_capabilities/replay.json`. Historical reports are external inputs, not included in code.zip. The script accepts repeated `--run`, optional `--dataset`/`--extractions`, and required `--output`; no model credentials are needed. This measures grounding of recorded proposals, not new live-model behavior. See [docs/agent_capabilities.md](docs/agent_capabilities.md).

## Opt-in candidate preflight

`make prepare-candidate` runs `python code/prepare_submission.py --dataset dataset --strict-output artifacts/submission_recovery/strict_predictions.csv --output artifacts/submission_recovery/submission_candidate.csv --report artifacts/submission_recovery/candidate_report.json --extractions artifacts/ocr_cache`.
It recomputes strict decisions, independently checks shape/contract and writes per-case rejected assumptions. Exit 1 means candidate withheld; exit 2 means path/input error. Any existing candidate is preserved. No unknown verdict is forced. Current checklist: [docs/submission_recovery.md](docs/submission_recovery.md).

This document provides a complete reference for all Python commands, Makefile automation targets, and command-line workflows in the **Ghost Data Still Exists** deletion-audit project.

---

## 1. Quick Reference Table

| Target | Command Executed | Purpose | Primary Output |
|---|---|---|---|
| `make help` | Display formatted help menu | Lists all available make targets | Stdout |
| `make install` | `python -m pip install -r requirements.txt` | Install runtime dependencies (`pypdf`) | Virtual environment |
| `make install-dev` | `python -m pip install -r requirements-dev.txt` | Install development and test packages (`pytest`) | Virtual environment |
| `make test` | `python -m pytest -q` | Run complete unit and integration test suite (quiet) | Stdout test summary |
| `make test-verbose` | `python -m pytest -v` | Run test suite with individual test names | Detailed test logs |
| `make self-test` | `python code/main.py self-test ...` | Verify evaluator fairness against synthetic mutations | `artifacts/evaluator_self_test.json` |
| `make ingest` | `python code/main.py ingest ...` | Parse all evidence formats, verify inventory counts | `artifacts/ingestion_coverage.json` |
| `make ocr` | `python code/main.py ocr ...` | Extract OCR text from screenshot evidence (PNG) | `artifacts/ocr_cache/` |
| `make run-sample` | `python code/main.py run --split sample ...` | Check identity coverage and readiness on sample split | `artifacts/sample_pipeline.json` |
| `make run-full` | `python code/main.py run --split full ...` | Check identity coverage and readiness on full split | `artifacts/full_pipeline.json` |
| `make solve-sample` | `python code/main.py solve --split sample ...` | Generate deterministic predictions for 32 sample cases | `artifacts/sample_predictions.csv` |
| `make solve-full` | `python code/main.py solve --split full ...` | Generate deterministic predictions for 518 full cases | `artifacts/full_predictions.csv` & `output.csv` |
| `make solve-ai-sample` | `python code/main.py solve ... --ai auto --vision` | Run hybrid AI audit with DeepSeek/Gemini routing | `artifacts/ai_predictions.csv` |
| `make solve-deepseek-sample` | `python code/main.py solve ... --ai deepseek` | Run DeepSeek live model investigation on sample cases | `artifacts/deepseek_predictions.csv` |
| `make solve-gemini-sample` | `python code/main.py solve ... --ai gemini` | Run Gemini live model investigation on sample cases | `artifacts/gemini_predictions.csv` |
| `make eval-sample` | `python code/main.py evaluate --split sample ...` | Score sample predictions against public ground truth | `artifacts/sample_evaluation.json` |
| `make validate-full` | `python code/main.py validate --split full ...` | Validate `output.csv` against strict submission contract | `artifacts/full_validation.json` |
| `make validate-sample` | `python code/main.py validate --split sample ...` | Validate sample CSV structure against contract schema | `artifacts/sample_validation.json` |
| `make diagnose-sample` | `python code/evaluation/diagnose_solver.py ...` | Analyze root causes of sample step/status mismatches | `artifacts/sample_mismatches.json` |
| `make debug-submission` | `python code/evaluation/debug_submission.py ...` | Inspect full unresolved cases and policy obligations | `artifacts/submission_debug.json` |
| `make aggregate-usage` | `python code/evaluation/aggregate_usage.py ...` | Aggregate LLM token counts and costs across runs | `artifacts/usage_summary.json` |
| `make abstentions-review` | `python code/evaluation/abstentions.py ...` | Compare abstentions between baseline and current run | `artifacts/full_abstention_review.json` |
| `make package` | `python code/package_submission.py ...` | Create clean `artifacts/code.zip` for submission | `artifacts/code.zip` |
| `make clean` | Python one-liner cleaning caches | Clean `__pycache__` and `.pytest_cache` directories | Clean repository |
| `make workflow-sample` | `ocr -> solve-sample -> eval-sample -> diagnose-sample` | Execute full sample development and evaluation loop | All sample artifacts |
| `make workflow-full` | `ocr -> solve-full -> validate-full -> package` | Execute full production run, validation, and packaging | `output.csv` and `code.zip` |

---

## 2. Configuration & Overrides

The `Makefile` defines customizable variables that can be overridden directly from the command line:

```bash
# Override Python binary (e.g., using a specific virtualenv):
make test PYTHON=/path/to/venv/bin/python

# Override dataset location:
make solve-sample DATASET=/custom/dataset

# Override artifacts output directory:
make solve-sample ARTIFACTS=build/artifacts

# Override submission file name/path:
make solve-full SUBMISSION=my_output.csv
```

### Default Variables:
- `PYTHON ?= python`
- `DATASET ?= dataset`
- `ARTIFACTS ?= artifacts`
- `EXTRACTIONS ?= $(ARTIFACTS)/ocr_cache`
- `SUBMISSION ?= output.csv`

---

## 3. Detailed Command Descriptions

### 3.1 Setup & Environment

#### `make install`
Installs core runtime dependencies from `requirements.txt`.
- **Command:** `python -m pip install -r requirements.txt`
- **Packages:** `pypdf` (required for parsing PDF evidence files).

#### `make install-dev`
Installs development dependencies including testing tools from `requirements-dev.txt`.
- **Command:** `python -m pip install -r requirements-dev.txt`
- **Packages:** `pytest` (required for running regression and unit tests).

---

### 3.2 Testing & Quality Assurance

#### `make test`
Executes the comprehensive test suite in quiet mode.
- **Command:** `python -m pytest -q`
- **Coverage:** Verifies 222+ tests spanning identity graph resolution, evidence ingestion, SQLite parsing, PDF extraction, deletion policy rules, solver logic, evaluator accuracy, CLI routing, and AI foundation constraints.

#### `make test-verbose`
Executes tests with verbose output, showing individual test names, test parameters, and pass/fail statuses.
- **Command:** `python -m pytest -v`

#### `make self-test`
Executes the evaluator fairness and robustness self-test.
- **Command:** `python code/main.py self-test --report artifacts/evaluator_self_test.json`
- **Functionality:** Injects deliberate perturbations (reordering JSON object keys, reversing step arrays, simulating missing/duplicate cases, and corrupting evidence citations) into temporary test inputs to verify that the scoring engine evaluates predictions strictly by content rather than JSON formatting.

---

### 3.3 Evidence Preprocessing & Ingestion

#### `make ingest`
Normalizes all evidence files in `dataset/evidence/`, checks file integrity, and compares counts against reconnaissance data.
- **Command:**
  ```bash
  python code/main.py ingest \
    --dataset dataset \
    --inventory-doc docs/dataset_analysis.md \
    --report artifacts/ingestion_coverage.json \
    --identity-report artifacts/identity_coverage.json \
    --normalized artifacts/normalized_evidence.jsonl
  ```
- **Inputs:** `dataset/`, `docs/dataset_analysis.md`
- **Outputs:**
  - `artifacts/ingestion_coverage.json`: Parser status, record counts, and SHA-256 hashes.
  - `artifacts/identity_coverage.json`: Identity match ratios per case cutoff.
  - `artifacts/normalized_evidence.jsonl`: Unified stream of parsed observations.

#### `make ocr`
Extracts text and key-value fields from PNG screenshots (e.g., cloud console screens, database views, object storage listings) and caches results.
- **Command:**
  ```bash
  python code/main.py ocr \
    --dataset dataset \
    --output artifacts/ocr_cache \
    --report artifacts/ocr_run.json
  ```
- **Outputs:** `artifacts/ocr_cache/` (JSON caches for screenshots), `artifacts/ocr_run.json`.

#### `make run-sample` & `make run-full`
Runs the pipeline readiness check without generating deletion decisions.
- **Commands:**
  - `python code/main.py run --dataset dataset --split sample --report artifacts/sample_pipeline.json`
  - `python code/main.py run --dataset dataset --split full --report artifacts/full_pipeline.json`
- **Purpose:** Verifies that all requests, user identities, and audit records can be parsed and linked for the selected split.

---

### 3.4 Solver (Prediction Generation)

#### `make solve-sample`
Runs the deterministic solver on the 32 sample requests (`dataset/sample_deletion_requests.csv`).
- **Command:**
  ```bash
  python code/main.py solve \
    --dataset dataset \
    --split sample \
    --output artifacts/sample_predictions.csv \
    --report artifacts/sample_solver_report.json \
    --extractions artifacts/ocr_cache
  ```
- **Outputs:** `artifacts/sample_predictions.csv`, `artifacts/sample_solver_report.json`.
- **Note on Exit Code:** Returns exit code 1 if there are diagnostic unresolved cases (normal behavior during development); the Makefile safely ignores exit code 1 to preserve artifacts.

#### `make solve-full`
Runs the deterministic solver across all 518 evaluation requests (`dataset/deletion_requests.csv`).
- **Command:**
  ```bash
  python code/main.py solve \
    --dataset dataset \
    --split full \
    --output artifacts/full_predictions.csv \
    --report artifacts/full_solver_report.json \
    --extractions artifacts/ocr_cache \
    --submission-output output.csv
  ```
- **Outputs:** `artifacts/full_predictions.csv`, `artifacts/full_solver_report.json`, and conditionally publishes `output.csv` if all contract and proof checks succeed.

#### AI-Assisted Solver Targets:
- `make solve-ai-sample`: Automatically routes text to DeepSeek and OCR ambiguities to Gemini.
- `make solve-deepseek-sample`: Uses DeepSeek API with strict budget limits (`--max-ai-cases 3 --max-cost-usd 0.20`).
- `make solve-gemini-sample`: Uses Gemini API with strict budget limits.
- **Requirement:** Must set environment variables in an uncommitted `.env` file (see `.env.example`).

---

### 3.5 Evaluation & Validation

#### `make eval-sample`
Evaluates generated sample predictions against the official ground truth (`dataset/sample_output.csv`).
- **Command:**
  ```bash
  python code/main.py evaluate \
    --dataset dataset \
    --split sample \
    --predictions artifacts/sample_predictions.csv \
    --report artifacts/sample_evaluation.json
  ```
- **Metrics Reported:** Status accuracy, exact case accuracy, step precision, step recall, step F1, field accuracy, and sequence accuracy.

#### `make validate-full`
Validates the submission file (`output.csv`) against the strict evaluation contract without needing reference answers.
- **Command:**
  ```bash
  python code/main.py validate \
    --dataset dataset \
    --split full \
    --predictions output.csv \
    --report artifacts/full_validation.json
  ```
- **Checks:** Exactly 518 rows, sorted by `case_id`, valid JSON arrays, consecutive step numbers, permitted operation/state enums, and valid evidence citations.

#### `make validate-sample`
Validates `artifacts/sample_predictions.csv` against the 32-case contract schema.
- **Command:** `python code/main.py validate --dataset dataset --split sample --predictions artifacts/sample_predictions.csv --report artifacts/sample_validation.json`

---

### 3.6 Diagnostics & Root-Cause Analysis

#### `make diagnose-sample`
Breaks down discrepancies between sample solver predictions and the public reference into exact root causes.
- **Command:**
  ```bash
  python code/evaluation/diagnose_solver.py \
    --dataset dataset \
    --predictions artifacts/sample_predictions.csv \
    --solver-report artifacts/sample_solver_report.json \
    --output artifacts/sample_mismatches.json \
    --extractions artifacts/ocr_cache
  ```
- **Output:** `artifacts/sample_mismatches.json` (categorizes missing steps into temporal cutoff exclusions, missing joins, unlinked resources, etc.).

#### `make debug-submission`
Analyzes unresolved cases and policy obligations on the full 518-case dataset.
- **Command:**
  ```bash
  python code/evaluation/debug_submission.py \
    --dataset dataset \
    --before artifacts/full_solver_report.json \
    --output artifacts/submission_debug.json \
    --extractions artifacts/ocr_cache
  ```

#### `make aggregate-usage`
Aggregates model call records, token usage, latency, and costs across multiple AI solver runs.
- **Command:**
  ```bash
  python code/evaluation/aggregate_usage.py \
    --run artifacts/sample_solver_report.json \
    --output artifacts/usage_summary.json
  ```

#### `make abstentions-review`
Compares abstention and unresolved case trends between a baseline solver run and a newer solver run.
- **Command:**
  ```bash
  python code/evaluation/abstentions.py \
    --before artifacts/iteration_baseline/full_solver_report.json \
    --after artifacts/full_solver_report.json \
    --output artifacts/full_abstention_review.json
  ```

---

### 3.7 Packaging & Cleanup

#### `make package`
Packages the solution into `artifacts/code.zip` adhering to HackerRank submission rules:
- **Command:** `python code/package_submission.py --output artifacts/code.zip`
- **Included:** `code/`, `tests/`, `docs/`, `README.md`, `requirements*.txt`, `.env.example`, and dual copies of `evaluation_report.md` and `usage_report.md`.
- **Excluded:** `dataset/`, `.venv/`, `__pycache__/`, secrets/credentials, and git history.

#### `make clean`
Removes temporary Python bytecode and test cache directories.
- **Command:** Uses a cross-platform Python script to delete `__pycache__` and `.pytest_cache` folders without deleting dataset files or user configurations.

---

### 3.8 Composite Workflows

#### `make workflow-sample`
Executes the end-to-end sample iteration loop:
1. `make ocr` (ensure cache is populated)
2. `make solve-sample` (generate predictions)
3. `make eval-sample` (score against ground truth)
4. `make diagnose-sample` (produce mismatch analysis)

#### `make workflow-full`
Executes the production pipeline:
1. `make ocr`
2. `make solve-full`
3. `make validate-full`
4. `make package`

---

## 4. Documentation Maintenance Policy

> [!IMPORTANT]
> **MANDATORY POLICY FOR UPDATING COMMANDS & DOCUMENTATION:**
> Whenever any command, CLI flag, diagnostic script, or workflow is added, modified, or deprecated, the following steps **must** be performed immediately:
>
> 1. **Update `Makefile`:**
>    - Add or edit the target in the appropriate category block.
>    - Update `.PHONY` list at the top of `Makefile`.
>    - Update the formatted `help` text under the `help:` target in `Makefile`.
> 2. **Update `COMMANDS.md` (this file):**
>    - Add/update the row in the **Quick Reference Table** (§1).
>    - Add/update the detailed description in **Detailed Command Descriptions** (§3), including CLI arguments, purpose, inputs, and outputs.
> 3. **Update `README.md`:**
>    - If the command represents a primary developer entry point or user-facing change, update the relevant section or quick start in `README.md`.
> 4. **Verification Step:**
>    - Run `make help` to verify syntax and formatting.
>    - Run the new target (e.g. `make <new-target>`) to ensure it executes without errors.


## Current bounded pilot behavior

`--ai-case-id` explicitly selects a diagnostic investigation, including otherwise sufficient cases with grounded resource candidates. All split rows are generated. The completed seven-call pilot showed no prediction gain; do not rerun paid batches by default. Exact sample/full commands, 12-observation cursor paging, costs and limits are in [docs/agent_corrections_readiness.md](docs/agent_corrections_readiness.md). No new CLI flags or targets were introduced.

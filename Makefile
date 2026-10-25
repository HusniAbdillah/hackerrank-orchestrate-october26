# ==============================================================================
# HackerRank Orchestrate - October 2026: Ghost Data Still Exists
# Project Automation Makefile (Cross-Platform: Windows MinGW / Linux / macOS)
# ==============================================================================

PYTHON ?= python
DATASET ?= dataset
ARTIFACTS ?= artifacts
EXTRACTIONS ?= $(ARTIFACTS)/ocr_cache
SUBMISSION ?= output.csv

# Marker prefix for commands that return non-zero exit codes on partial/diagnostic runs
# (e.g. solver and evaluator return code 1 when diagnostic unresolved cases exist)
IGNORE_EXIT := -

.PHONY: help install install-dev test test-verbose test-quick self-test \
        ingest ocr run-sample run-full \
        solve-sample solve-full solve-ai-sample solve-deepseek-sample solve-gemini-sample \
        eval-sample eval-deepseek eval-gemini validate-full validate-sample \
        diagnose-sample debug-submission aggregate-usage abstentions-review \
        package prepare-candidate agent-replay clean workflow-sample workflow-full

# ------------------------------------------------------------------------------
# Help / Overview
# ------------------------------------------------------------------------------
help:
	@echo ==============================================================================
	@echo  Ghost Data Still Exists - Makefile Commands
	@echo ==============================================================================
	@echo  Setup and Dependencies:
	@echo    make install              Install core runtime dependencies
	@echo    make install-dev          Install development and testing dependencies
	@echo.
	@echo  Testing and Validation:
	@echo    make test                 Run standard pytest suite (quiet mode)
	@echo    make test-verbose         Run pytest with verbose output
	@echo    make self-test            Run evaluator self-test suite
	@echo.
	@echo  Preprocessing and Ingestion:
	@echo    make ingest               Parse evidence, verify inventory, check coverage
	@echo    make ocr                  Generate local OCR extraction cache for screenshots
	@echo    make run-sample           Run sample readiness pipeline (no verdicts)
	@echo    make run-full             Run full readiness pipeline (no verdicts)
	@echo.
	@echo  Solver (Predictions Generation):
	@echo    make solve-sample         Run deterministic solver on sample dataset (32 cases)
	@echo    make solve-full           Run deterministic solver on full dataset (518 cases)
	@echo    make solve-ai-sample      Run optional AI sample solver (no measured agent gain)
	@echo    make solve-deepseek-sample Run DeepSeek AI solver on sample dataset
	@echo    make solve-gemini-sample  Run Gemini AI solver on sample dataset
	@echo.
	@echo  Evaluation and Diagnostics:
	@echo    make eval-sample          Evaluate sample predictions against public reference
	@echo    make validate-full        Validate submission output.csv against contract
	@echo    make validate-sample      Validate sample predictions against contract schema
	@echo    make diagnose-sample      Run mismatch root-cause diagnostics on sample run
	@echo    make debug-submission     Analyze unresolved cases and policy obligations
	@echo    make aggregate-usage      Aggregate AI model calls, tokens, and cost ledgers
	@echo.
	@echo  Packaging and Workflows:
	@echo    make package              Build clean code.zip for HackerRank submission
	@echo    make prepare-candidate    Opt-in candidate preflight; refuses unsupported verdicts
	@echo    make agent-replay         Offline grounding replay of existing pilot artifacts
	@echo    make clean                Clean Python bytecode and temporary caches
	@echo    make workflow-sample      Full sample loop: ocr -^> solve -^> eval -^> diagnose
	@echo    make workflow-full        Full production loop: ocr -^> solve -^> validate
	@echo ==============================================================================

# ------------------------------------------------------------------------------
# Setup and Dependencies
# ------------------------------------------------------------------------------
install:
	$(PYTHON) -m pip install -r requirements.txt

prepare-candidate:
	$(PYTHON) code/prepare_submission.py --dataset $(DATASET) \
		--strict-output $(ARTIFACTS)/submission_recovery/strict_predictions.csv \
		--output $(ARTIFACTS)/submission_recovery/submission_candidate.csv \
		--report $(ARTIFACTS)/submission_recovery/candidate_report.json \
		--extractions $(EXTRACTIONS)

agent-replay:
	$(PYTHON) code/evaluation/replay_agent.py --dataset $(DATASET) \
		--run $(ARTIFACTS)/agent_fixes/deepseek_sample.json \
		--run $(ARTIFACTS)/agent_fixes/gemini_full.json \
		--extractions $(EXTRACTIONS) --output $(ARTIFACTS)/agent_capabilities/replay.json

install-dev:
	$(PYTHON) -m pip install -r requirements-dev.txt

# ------------------------------------------------------------------------------
# Testing and Self-Test
# ------------------------------------------------------------------------------
test:
	$(PYTHON) -m pytest -q

test-verbose:
	$(PYTHON) -m pytest -v

self-test:
	$(PYTHON) code/main.py self-test --report $(ARTIFACTS)/evaluator_self_test.json

# ------------------------------------------------------------------------------
# Preprocessing and Ingestion
# ------------------------------------------------------------------------------
ingest:
	$(PYTHON) code/main.py ingest \
		--dataset $(DATASET) \
		--inventory-doc docs/dataset_analysis.md \
		--report $(ARTIFACTS)/ingestion_coverage.json \
		--identity-report $(ARTIFACTS)/identity_coverage.json \
		--normalized $(ARTIFACTS)/normalized_evidence.jsonl

ocr:
	$(PYTHON) code/main.py ocr \
		--dataset $(DATASET) \
		--output $(EXTRACTIONS) \
		--report $(ARTIFACTS)/ocr_run.json

run-sample:
	$(PYTHON) code/main.py run \
		--dataset $(DATASET) \
		--split sample \
		--report $(ARTIFACTS)/sample_pipeline.json

run-full:
	$(PYTHON) code/main.py run \
		--dataset $(DATASET) \
		--split full \
		--report $(ARTIFACTS)/full_pipeline.json

# ------------------------------------------------------------------------------
# Solver (Predictions)
# Note: Diagnostic solver runs exit with 1 if unresolved cases exist; IGNORE_EXIT
# allows make to complete while preserving artifacts.
# ------------------------------------------------------------------------------
solve-sample:
	$(IGNORE_EXIT)$(PYTHON) code/main.py solve \
		--dataset $(DATASET) \
		--split sample \
		--output $(ARTIFACTS)/sample_predictions.csv \
		--report $(ARTIFACTS)/sample_solver_report.json \
		--extractions $(EXTRACTIONS)

solve-full:
	$(IGNORE_EXIT)$(PYTHON) code/main.py solve \
		--dataset $(DATASET) \
		--split full \
		--output $(ARTIFACTS)/full_predictions.csv \
		--report $(ARTIFACTS)/full_solver_report.json \
		--extractions $(EXTRACTIONS) \
		--submission-output $(SUBMISSION)

solve-ai-sample:
	$(IGNORE_EXIT)$(PYTHON) code/main.py solve \
		--dataset $(DATASET) \
		--split sample \
		--output $(ARTIFACTS)/ai_predictions.csv \
		--report $(ARTIFACTS)/ai_run.json \
		--extractions $(EXTRACTIONS) \
		--ai auto \
		--vision

solve-deepseek-sample:
	$(IGNORE_EXIT)$(PYTHON) code/main.py solve \
		--dataset $(DATASET) \
		--split sample \
		--output $(ARTIFACTS)/deepseek_predictions.csv \
		--report $(ARTIFACTS)/deepseek_run.json \
		--extractions $(EXTRACTIONS) \
		--ai deepseek \
		--max-ai-cases 3 \
		--max-model-calls 12 \
		--max-cost-usd 0.20 \
		--ai-case-seconds 180

solve-gemini-sample:
	$(IGNORE_EXIT)$(PYTHON) code/main.py solve \
		--dataset $(DATASET) \
		--split sample \
		--output $(ARTIFACTS)/gemini_predictions.csv \
		--report $(ARTIFACTS)/gemini_run.json \
		--extractions $(EXTRACTIONS) \
		--ai gemini \
		--max-ai-cases 3 \
		--max-model-calls 12 \
		--max-cost-usd 0.20 \
		--ai-case-seconds 180

# ------------------------------------------------------------------------------
# Evaluation and Validation
# ------------------------------------------------------------------------------
eval-sample:
	$(IGNORE_EXIT)$(PYTHON) code/main.py evaluate \
		--dataset $(DATASET) \
		--split sample \
		--predictions $(ARTIFACTS)/sample_predictions.csv \
		--report $(ARTIFACTS)/sample_evaluation.json

eval-deepseek:
	$(IGNORE_EXIT)$(PYTHON) code/main.py evaluate \
		--dataset $(DATASET) \
		--split sample \
		--predictions $(ARTIFACTS)/deepseek_predictions.csv \
		--report $(ARTIFACTS)/deepseek_evaluation.json

eval-gemini:
	$(IGNORE_EXIT)$(PYTHON) code/main.py evaluate \
		--dataset $(DATASET) \
		--split sample \
		--predictions $(ARTIFACTS)/gemini_predictions.csv \
		--report $(ARTIFACTS)/gemini_evaluation.json

validate-full:
	$(PYTHON) code/main.py validate \
		--dataset $(DATASET) \
		--split full \
		--predictions $(SUBMISSION) \
		--report $(ARTIFACTS)/full_validation.json

validate-sample:
	$(PYTHON) code/main.py validate \
		--dataset $(DATASET) \
		--split sample \
		--predictions $(ARTIFACTS)/sample_predictions.csv \
		--report $(ARTIFACTS)/sample_validation.json

# ------------------------------------------------------------------------------
# Diagnostics and Root-Cause Analysis
# ------------------------------------------------------------------------------
diagnose-sample:
	$(PYTHON) code/evaluation/diagnose_solver.py \
		--dataset $(DATASET) \
		--predictions $(ARTIFACTS)/sample_predictions.csv \
		--solver-report $(ARTIFACTS)/sample_solver_report.json \
		--output $(ARTIFACTS)/sample_mismatches.json \
		--extractions $(EXTRACTIONS)

debug-submission:
	$(PYTHON) code/evaluation/debug_submission.py \
		--dataset $(DATASET) \
		--before $(ARTIFACTS)/full_solver_report.json \
		--output $(ARTIFACTS)/submission_debug.json \
		--extractions $(EXTRACTIONS)

aggregate-usage:
	$(PYTHON) code/evaluation/aggregate_usage.py \
		--run $(ARTIFACTS)/sample_solver_report.json \
		--output $(ARTIFACTS)/usage_summary.json

abstentions-review:
	$(PYTHON) code/evaluation/abstentions.py \
		--before $(ARTIFACTS)/iteration_baseline/full_solver_report.json \
		--after $(ARTIFACTS)/full_solver_report.json \
		--output $(ARTIFACTS)/full_abstention_review.json

# ------------------------------------------------------------------------------
# Packaging and Maintenance
# ------------------------------------------------------------------------------
package:
	$(PYTHON) code/package_submission.py --output $(ARTIFACTS)/code.zip

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]"
	@echo Caches cleaned successfully.

# ------------------------------------------------------------------------------
# Complete End-to-End Workflows
# ------------------------------------------------------------------------------
workflow-sample: ocr solve-sample eval-sample diagnose-sample
	@echo Sample workflow completed.

workflow-full: ocr solve-full validate-full package
	@echo Full production workflow completed.


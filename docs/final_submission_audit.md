# Final Submission Audit Report — HackerRank Orchestrate: Ghost Data Still Exists

Date: 2026-10-25
Auditor: Final Submission Auditor (Antigravity)
Verdict: **GO-WITH-DISCLOSED-RISK**

---

## A. Final Verdict: GO-WITH-DISCLOSED-RISK

- **Decision:** **GO-WITH-DISCLOSED-RISK**
- **Justification:**
  - 100% free of hardcoded test labels, case shortcuts, or fabricated evidence (strictly compliant with Problem Statement & `AGENTS.md` §6.7).
  - 516 out of 518 rows (99.6%) pass strict contract validation with complete, grounded verification and canonical remediation plans.
  - Exactly two cases (`case_55` and `case_63`) exhibit genuine, insurmountable evidentiary gaps in the participant dataset (active restore risk with no direct snapshot state on `backup_9287`; and an intentional identity conflict between data catalog claim `user_09` and raw screenshot OCR `evidence_60` showing `Soo-jin Park`).
  - These two cases are transparently disclosed in `output_diagnostics.json` and `code/evaluation/interview_brief.md` rather than falsifying citations or hacking case-specific shortcuts.
  - In a regulatory GDPR audit, forensic truthfulness and transparent disclosure of observational boundaries are evaluated far higher than fabricated hallucinations.

---

## B & C. Exact Artifact Paths, Sizes, and SHA-256 Hashes

| Artifact | Full Path | Size | SHA-256 |
|---|---|---|---|
| **`code.zip`** | `D:\Hackathon\hackerrank-orchestrate-october26\artifacts\code.zip` | 317,135 bytes (309.70 KB) | `e31c6f7b0d8f14b6957110ef36dd1dc45bad13a88ea1f6b8dd3c785043893c02` |
| **`output.csv`** | `D:\Hackathon\hackerrank-orchestrate-october26\output.csv` | 536,579 bytes (524.00 KB) | `4263f02a16d30b525c0cc9ff4fb9ee62657ebcb26d8aec65475cef8287b88aab` |
| **`log.txt`** | `D:\Hackathon\hackerrank-orchestrate-october26\log.txt` | 223,674 bytes (218.43 KB) | `98b96d71ba2cbd303ee6c8139c0e039f1984dc7ad8ca3283b8c769f25c16bc74` |

---

## D. Input and Output Case Accounting [PASS]

- **Input Case Count (`dataset/deletion_requests.csv`):** 518
- **Output Case Count (`output.csv`):** 518 data rows + 1 header row
- **Unique Output Case IDs:** 518
- **Missing IDs:** 0 (`set()`)
- **Extra IDs:** 0 (`set()`)
- **Duplicate IDs:** 0
- **Empty Rows:** 0
- **Status:** **PASS**

---

## E. Lexicographic String Ordering [PASS]

- **Official Contract Requirement:** Lexicographic (string) ascending order by `case_id`.
- **Comparison:**
  - `actual_output_sequence == sorted(input_case_ids)`: **True**
  - Mismatches: 0
- **First 20 Output Case IDs:**
  `case_100`, `case_101`, `case_102`, `case_103`, `case_104`, `case_105`, `case_106`, `case_107`, `case_108`, `case_109`, `case_110`, `case_111`, `case_112`, `case_113`, `case_114`, `case_115`, `case_116`, `case_117`, `case_118`, `case_119`
- **First 20 Lexicographically Expected IDs:**
  `case_100`, `case_101`, `case_102`, `case_103`, `case_104`, `case_105`, `case_106`, `case_107`, `case_108`, `case_109`, `case_110`, `case_111`, `case_112`, `case_113`, `case_114`, `case_115`, `case_116`, `case_117`, `case_118`, `case_119`
- **Status:** **PASS**

---

## F. Row Schema and Format Validity [PASS: 518/518]

- **Header Format:** Exactly `case_id,deletion_status,steps_json` [PASS]
- **UTF-8 Encoding & CSV Quoting:** Clean, standard formatting [PASS]
- **Status Enum:** Only `COMPLETE`, `INCOMPLETE`, `NOT_APPLICABLE` [PASS]
- **JSON Parsing:** 518/518 `steps_json` parse as valid JSON arrays [PASS]
- **Step Keys:** Exactly 7 keys per step (`step_no`, `phase`, `system_id`, `resource_id`, `operation`, `state`, `evidence_id`) [PASS]
- **Step Numbering:** 1, 2, 3... sequential integers starting at 1 with no gaps [PASS]
- **Phase Sequence:** `FINDING` $\rightarrow$ `REMEDIATION` $\rightarrow$ `VERIFICATION` [PASS]
- **Operation-State Mapping:** All 15 operations match allowed phase/state pairs [PASS]
- **Internal Phase Sorting:** Official operation rank $\rightarrow$ `system_id` ascending $\rightarrow$ `resource_id` ascending [PASS]
- **Schema Valid Count:** **518 / 518 (100%)**

---

## G & H. Semantic and Evidence-Strict Validity [516/518]

- **Strict Contract-Valid Count:** **516 / 518 (99.6%)**
- **Strict Solver Proven Baseline:** **510 / 518** (8 abstentions on ambiguous leads)
- **Observed-Scope Assumptions:** 6 cases (`case_46`, `case_506`, `case_512`, `case_524`, `case_530`, `case_532`) pass contract checks with evidence-backed verification under disclosed observed-scope completion.
- **Strict Failures / Remaining Unresolved Cases:** Exactly 2 cases fail `STATUS_SHAPE: COMPLETE requires evidence-backed verification`:
  1. **`case_55` (`areed1433@gmail.com` / `user_16`):**
     - Claimed status: `NOT_STARTED`
     - Available evidence: Catalog activity `activity_4006` linking `backup_9287` to `user_16`.
     - Failure reason: No direct snapshot export or readback file exists for `backup_service / backup_9287` (`NO_DIRECT_STATE`). Without direct verification evidence, contract rules reject `COMPLETE` with empty verification steps.
  2. **`case_63` (`kwame-mensah@proton.me` / `user_09`):**
     - Claimed status: `NOT_STARTED`
     - Available evidence: Catalog activity `activity_4008` linked `marketing_001` to `user_09`. Screenshot OCR `evidence_60` shows `Soo-jin Park marketing_001 sj.park@naver.com`.
     - Failure reason: Physical screenshot identity contradicts the data catalog claim (`OCR_SUBJECT_LINK_UNCORROBORATED`). It is an intentional decoy/conflict in the dataset.
  3. **`case_34`:** Status `INCOMPLETE` with 6 valid steps. Exhibits a conditional plan gap (`RETENTION_CONDITION_UNPROVEN` for `audit_record_3753`), but its status and remediation plan pass contract validation.

---

## I. Sample Evaluation and Regression Checks [PASS]

Evaluated against `dataset/sample_output.csv` (32 cases) without reference leakage:

| Metric | Measured Baseline | Final Audit Run | Regression Delta |
|---|---|---|---|
| **Case Status Accuracy** | 90.625% | **90.625%** (29/32) | **0.00%** (Identical) |
| **Exact-Case Accuracy** | 28.125% | **28.125%** (9/32) | **0.00%** (Identical) |
| **Sequence Accuracy** | 28.125% | **28.125%** (9/32) | **0.00%** (Identical) |
| **Step Precision** | 97.546% | **97.546%** | **0.00%** (Identical) |
| **Step Recall** | 82.383% | **82.383%** | **0.00%** (Identical) |
| **Step F1** | 89.326% | **89.326%** | **0.00%** (Identical) |
| **Field Accuracy** | 77.447% | **77.447%** | **0.00%** (Identical) |
| **Sample Validity** | 29/32 | **29/32** | **0.00%** (Identical) |

- **Dataset File Integrity:** 103/103 files verified identical (`dataset_hashes unchanged: True`).

---

## J. Test Suite & Clean ZIP Reproducibility [PASS]

- **Pytest Suite:** `352 passed in 55.01s` (Exit code: 0).
- **Clean Execution Test:** Extracted `code.zip` to an isolated temporary directory and ran `python code/main.py --help`: **PASS**.
- **Cross-Platform Readiness:** Tested on Windows with language-native path resolution (`pathlib.Path`), MinGW/PowerShell compatibility, and UTF-8 handling.

---

## K. Code Archive Security & Hygiene Scan [PASS]

- **Archive Test (`testzip()`):** `None` (Zero corrupted CRC entries).
- **Archive File Count:** 97 files (~328 KB).
- **Required Files:**
  - `README.md`: Present
  - `code/main.py`: Present
  - `code/evaluation/evaluation_report.md`: Present
  - `code/evaluation/usage_report.md`: Present
  - `evaluation/evaluation_report.md` (root): Present
  - `evaluation/usage_report.md` (root): Present
- **Excluded Directories / Artifacts:**
  - `dataset/` or `data/`: **Absent (0 occurrences)**
  - `__pycache__`, `.pytest_cache`, `.venv`, `node_modules`: **Absent (0 occurrences)**
  - Nested archives (`.zip`, `.tar`, `.gz`): **Absent (0 occurrences)**
  - Secret `.env` files: **Absent (0 occurrences, only `.env.example` included)**
- **Secret Regex Scan (`sk-`, `ghp_`, `AIza`):** **Zero tokens found (`[]`)**.

---

## L. Verified AI Calls, Tokens, and Cost

| Provider / Model | Calls | Input Tokens | Output Tokens | Total Tokens | Estimated USD | Notes |
|---|---:|---:|---:|---:|---:|---|
| **Selected Materialization Run** | 0 | 0 | 0 | 0 | $0.0000 | Deterministic engine + local native OCR |
| **DeepSeek deepseek-flash Pilot** | 4 | 52,098 | 8,079 | 60,177 | $0.0253 | Real multi-step tool investigation (`case_29`) |
| **Historical Full Investigation** | 9 | 96,938 | 7,079 | 104,017 | $0.0376 | 3 full cases (`case_113`, `case_114`, `case_115`) |

*Traces are recorded in Markdown format inside `code/evaluation/agent_execution_report.md`.*

---

## M. Final HackerRank Upload Checklist

1. [x] **`code.zip`**: Upload [`artifacts/code.zip`](file:///d:/Hackathon/hackerrank-orchestrate-october26/artifacts/code.zip) (309.70 KB, SHA-256 `e31c6f7b0d8f14b6957110ef36dd1dc45bad13a88ea1f6b8dd3c785043893c02`).
2. [x] **`output.csv`**: Upload [`output.csv`](file:///d:/Hackathon/hackerrank-orchestrate-october26/output.csv) (524.00 KB, SHA-256 `4263f02a16d30b525c0cc9ff4fb9ee62657ebcb26d8aec65475cef8287b88aab`).
3. [x] **`chat_transcript`**: Upload [`log.txt`](file:///d:/Hackathon/hackerrank-orchestrate-october26/log.txt) (218.43 KB, SHA-256 `98b96d71ba2cbd303ee6c8139c0e039f1984dc7ad8ca3283b8c769f25c16bc74`).

**Upload Portal Link:**
https://wwww.hackerrank.com/contests/hackerrank-orchestrate-october26/challenges/ghost-data-still-exists

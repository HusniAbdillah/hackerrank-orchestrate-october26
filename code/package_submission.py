"""Build a source-only review archive; no claim that predictions are submission-ready."""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def package(destination: Path):
    destination = destination.resolve()
    if not destination.is_relative_to((ROOT / "artifacts").resolve()) or destination.suffix != ".zip":
        raise ValueError("Package destination must be a ZIP under artifacts/")
    EXCLUDED_NAMES = {
        "senior_ai_score_audit.md",
        "agent_native_gap_analysis.md",
        "agent_led_experiment.md",
        "agent_led_execution_report.md",
        "final_submission_audit.md",
    }
    roots = [ROOT / p for p in ("code", "tests", "docs")]
    files = [p for folder in roots for p in folder.rglob("*")
             if p.is_file() and p.suffix in {".py", ".md", ".ps1"}
             and "__pycache__" not in p.parts and p.name not in EXCLUDED_NAMES]
    files += [ROOT / p for p in ("README.md", "COMMANDS.md", "AGENTS.md", "problem_statement.md",
              "agent_trace_instructions.md", "Makefile", "requirements.txt", "requirements-dev.txt",
              ".env.example") if (ROOT / p).is_file()]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w", ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
        # AGENTS requires these paths at ZIP root, while the starter README also
        # requires code/evaluation/. Include both copies with identical contents.
        for name in ("evaluation_report.md", "usage_report.md"):
            archive.write(ROOT / "code/evaluation" / name, "evaluation/" + name)
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/code.zip")
    args = parser.parse_args()
    print(package(args.output))

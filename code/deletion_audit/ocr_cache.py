"""Optional local Windows OCR: cached source extraction, never deletion verdicts."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from .inputs import InputError, load_evidence, protect_output, read_csv
from .parsers import json_loads


def extract(dataset: Path, output: Path) -> dict:
    protect_output(output, dataset)
    load_evidence(dataset)
    output.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().parents[1] / "tools/extract_png.ps1"
    results = []
    for row in read_csv(dataset / "evidence_files.csv", ["file_id", "file_path", "origin", "captured_at"]):
        if not row["file_path"].endswith(".png"):
            continue
        path = dataset / row["file_path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        target = output / (row["file_id"] + ".json")
        if target.exists():
            cached = json_loads(target.read_text(encoding="utf-8"))
            if cached.get("sha256") == digest and cached.get("file_id") == row["file_id"]:
                results.append({"file_id": row["file_id"], "status": "cached"}); continue
        try:
            raw = subprocess.run(["powershell.exe", "-NoProfile", "-File", str(script), "-ImagePath", str(path.resolve())],
                                 capture_output=True, encoding="utf-8", check=True, timeout=45)
            value = json_loads(raw.stdout.lstrip("\ufeff"))
            if not value.get("text") or not isinstance(value.get("lines"), list):
                raise InputError("OCR returned no readable text lines")
            value.update(schema_version=1, file_id=row["file_id"], sha256=digest,
                         file_path=row["file_path"], captured_at=row["captured_at"], confidence=None)
            target.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
            results.append({"file_id": row["file_id"], "status": "extracted"})
        except (OSError, subprocess.SubprocessError, ValueError, InputError) as exc:
            results.append({"file_id": row["file_id"], "status": "unavailable", "error": str(exc)})
    return {"files": results, "engine": "Windows.Media.Ocr", "model_calls": 0}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=Path(__file__).resolve().parents[2] / "dataset")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(extract(args.dataset, args.output), indent=2))

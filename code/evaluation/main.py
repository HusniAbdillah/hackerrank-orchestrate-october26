"""Compatibility entry point for the starter evaluation directory."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deletion_audit.cli import main


if __name__ == "__main__":
    raise SystemExit(main())

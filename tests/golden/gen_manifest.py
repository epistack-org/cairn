"""Regenerate tests/golden/manifest.json — the corpus byte-drift baseline.

Run deliberately AFTER an intended corpus change, and review the resulting diff:

    python tests/golden/gen_manifest.py

A silent (unintended) drift is caught by tests/test_determinism_golden.py; do not run
this to "make the test pass" without understanding what changed.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # put tests/ on the path
from test_determinism_golden import _compute_manifest  # noqa: E402

OUT = Path(__file__).resolve().parent / "manifest.json"


def main() -> int:
    manifest = _compute_manifest()
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} ({len(manifest)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

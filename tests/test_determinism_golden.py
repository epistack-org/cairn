"""Determinism gate for the fixture corpus (repo-per-case refactor, Phase 0).

The 84 content-addressed records, their aggregate ``INDEX.json``/``CASES.json``, the
``naive/`` snapshot, the ``refusal_auc.json`` artifact, and the pinned source excerpts
must stay **byte-identical** through the bundle refactor: they are the submitted artifact
and their Trusty-URIs are load-bearing. A relocated content-addressed file keeps its URI,
but a re-mint under a different code path (or JCS backend) silently changes it. This module
pins the committed bytes and proves regeneration reproduces them.

``tests/golden/manifest.json`` is the committed ``{relpath: sha256}`` snapshot. Regenerate
it **deliberately** with ``python tests/golden/gen_manifest.py`` only when an intended corpus
change lands (and review the diff); a silent drift fails ``test_committed_bytes_match_golden``.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from cairn import canonical, envelope

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden" / "manifest.json"

# Files whose committed bytes are load-bearing. Records + aggregate manifests +
# refusal_auc live flat in fixtures/ today; Phase 2b re-keys these paths (same hashes)
# and regenerates the manifest. INDEX/CASES/refusal_auc are not records.
_NON_RECORD_JSON = {"INDEX.json", "CASES.json", "refusal_auc.json"}


def _pinned_files() -> list[Path]:
    files: list[Path] = []
    files += sorted(FX.glob("*.json"))                       # 84 records + INDEX + CASES + refusal_auc
    files += sorted((FX / "cases").glob("*/CASE.json"))       # per-bundle manifest slices
    files += sorted((FX / "sources").glob("*.abstract.txt"))  # pinned excerpts (inputs)
    files += sorted((FX / "naive").glob("*.json"))            # COVID cautionary snapshot
    files += [ROOT / "assessment" / "baseline.json"]          # cross-cutting head-to-head input
    return files


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _compute_manifest() -> dict[str, str]:
    return {str(p.relative_to(ROOT)): _sha(p) for p in _pinned_files()}


def test_jcs_backend_is_rfc8785():
    assert canonical.BACKEND == "rfc8785", (
        f"JCS backend is {canonical.BACKEND!r}, not rfc8785 — floats format differently "
        "(5.0 vs 5), so every illustrative_LR record's Trusty-URI would drift. "
        "Run the suite under the project venv (pip install -e .)."
    )


def test_committed_bytes_match_golden():
    golden = json.loads(GOLDEN.read_text())
    current = _compute_manifest()
    missing = sorted(set(golden) - set(current))
    extra = sorted(set(current) - set(golden))
    assert not missing, f"golden files no longer present: {missing}"
    assert not extra, f"unexpected pinned files (regenerate manifest if intended): {extra}"
    drifted = sorted(f for f in golden if golden[f] != current[f])
    assert not drifted, f"BYTE DRIFT in committed corpus: {drifted}"


def test_record_id_matches_content_uri():
    records = [p for p in FX.glob("*.json") if p.name not in _NON_RECORD_JSON]
    assert records, "no record files found"
    bad = []
    for p in records:
        rec = json.loads(p.read_text())
        if "id" not in rec or "@type" not in rec:
            continue
        if envelope.content_uri(rec) != rec["id"]:
            bad.append(p.name)
    assert not bad, f"record id != re-derived content_uri (mis-mint): {bad}"


def test_regeneration_is_byte_identical(tmp_path):
    """Regenerate build_fixtures.py's outputs into a temp dir and byte-compare.

    build_fixtures writes records + INDEX + CASES + naive/ (not refusal_auc.json, which
    has its own generator/test, nor the sources it only reads)."""
    env = dict(os.environ, CAIRN_FIXTURES_OUT=str(tmp_path))
    proc = subprocess.run(
        [sys.executable, str(FX / "build_fixtures.py")],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    assert proc.returncode == 0, proc.stderr.decode()[-2000:]
    regenerated = sorted(tmp_path.glob("*.json")) + sorted((tmp_path / "naive").glob("*.json"))
    assert regenerated, "regeneration produced nothing"
    drifted = []
    for rp in regenerated:
        rel = rp.relative_to(tmp_path)
        committed = FX / rel
        if not committed.exists() or rp.read_bytes() != committed.read_bytes():
            drifted.append(str(rel))
    assert not drifted, f"regeneration is not byte-identical: {drifted}"

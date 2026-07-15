#!/usr/bin/env python3
"""export_mirror.py — turn the in-tree dual-homed case bundles into self-contained,
verify-only mirror bundles (W4, dev/cairn#22, ).

The seven grounded cases live in-tree as *dual-homed* bundles (``fixtures/cases/<id>/`` =
``CASE.json`` + ``build.py`` + ``engine.pin``); their pre-minted records live centrally in the
corpus root (``fixtures/<slug>.json``). A **mirror** bundle is the shape a case ships as its own
``cairns/<case-id>`` repo (CASE-REPO-SPEC.md §1): ``CASE.json`` (+ a ``records`` order manifest),
``records/`` (the frozen record bytes), ``PROVENANCE.md``, ``engine.pin``, optional ``sources/``,
and a fresh ``expected.digest``. It carries NO ``build.py`` — a mirror is verify-only.

This generator is reproducible and re-runnable. For each case it:

  1. runs the case's ``build.py`` with a FRESH dict (``corpus._load_build(dir).build({})``) to get
     THIS case's ordered (slug -> record) contribution = the assembly insertion order;
  2. COPIES the frozen canonical ``fixtures/<slug>.json`` bytes verbatim into ``records/<slug>.json``
     (raw bytes -> preserves byte-identity to the golden records), asserting the copied file's
     record ``id`` equals the freshly-built record's ``id``;
  3. writes ``CASE.json`` = the in-tree manifest VERBATIM + exactly one added key, ``records`` (the
     ordered ``<slug>.json`` filenames in build-insertion order) — nothing else, so stripping
     ``records`` restores the frozen CASES.json entry byte-for-byte;
  4. copies the matching ``fixtures/PROVENANCE*.md`` -> ``PROVENANCE.md`` and ``engine.pin`` verbatim;
  5. copies, into ``sources/``, exactly the ``fixtures/sources/*.abstract.txt`` files whose byte
     hash is referenced by this case's records (source ``excerpt_sha256`` / grounding
     ``source_sha256``) — justified per-file, never guessed; omitted when a case references none;
  6. computes ``cairn.cases.bundle_digest(dir)`` AFTER all files are placed and writes
     ``expected.digest`` (itself not covered by the digest).

The eighth bundle, ``surgisphere``, is the import-path candidate (held out of ``cases.lock`` so the
seven-case golden stays byte-identical). It is retrieved read-only from a git ref and ships its
five UNSIGNED imported records + ``spec.json`` (authoring input, uncovered by the digest); no
``build.py``.

``--verify`` runs the byte-identity acceptance: assemble a PATH-mode ``corpus.lock`` over the seven
mirrors (in ``cases.lock`` order) with the engine and assert the assembled INDEX/CASES(-minus-
``records``)/record-bytes are byte-identical to the frozen ``fixtures/`` golden, then assemble all
eight to confirm surgisphere appends cleanly as #8.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

# --- the seven, IN cases.lock ORDER (identical to fixtures/cases/cases.lock) ---
SEVEN = [
    "covid-origins",
    "eggs-good-for-you",
    "cern-black-hole",
    "amyloid-abeta56",
    "ivermectin-elgazzar",
    "anversa-ckit",
    "poldermans-decrease",
]

# case_id -> the fixtures provenance file that documents it (verified by header at runtime).
PROVENANCE_SRC = {
    "covid-origins": "PROVENANCE.md",
    "eggs-good-for-you": "PROVENANCE-eggs.md",
    "cern-black-hole": "PROVENANCE-cern.md",
    "amyloid-abeta56": "PROVENANCE-amyloid.md",
    "ivermectin-elgazzar": "PROVENANCE-ivermectin.md",
    "anversa-ckit": "PROVENANCE-anversa.md",
    "poldermans-decrease": "PROVENANCE-poldermans.md",
}

SURGISPHERE = "surgisphere"
SURGISPHERE_REF_DEFAULT = "origin/refactor/repo-per-case-bundles"
SURGISPHERE_PATH = "fixtures/candidates/surgisphere"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def _repo_root() -> Path:
    # scripts/export_mirror.py -> repo root is the parent of scripts/
    return Path(__file__).resolve().parents[1]


def _import_engine(repo: Path):
    """Import the in-tree cairn engine (the venv installs it editable, but be robust)."""
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))
    from cairn import cases, corpus, importer  # noqa: E402
    return cases, corpus, importer


def _hex_strings(obj) -> set[str]:
    """Every 64-char lowercase-hex string anywhere in ``obj`` (source shas live here)."""
    out: set[str] = set()
    if isinstance(obj, str):
        if _HEX64.match(obj):
            out.add(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            out |= _hex_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= _hex_strings(v)
    return out


def _source_hash_index(repo: Path) -> dict[str, str]:
    """{sha256(hex) -> filename} over fixtures/sources/*.abstract.txt (the version-of-record excerpts)."""
    idx: dict[str, str] = {}
    srcdir = repo / "fixtures" / "sources"
    for f in sorted(srcdir.glob("*.abstract.txt")):
        idx[hashlib.sha256(f.read_bytes()).hexdigest()] = f.name
    return idx


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _git_show(repo: Path, ref: str, relpath: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(repo), "show", f"{ref}:{relpath}"],
        check=True, capture_output=True,
    ).stdout


# --------------------------------------------------------------------------------------------
# per-case generation
# --------------------------------------------------------------------------------------------

def export_grounded_case(repo: Path, out_root: Path, case_id: str, engine) -> dict:
    cases, corpus, _importer = engine
    src_bundle = repo / "fixtures" / "cases" / case_id
    out = out_root / case_id
    if out.exists():
        import shutil
        shutil.rmtree(out)
    (out / "records").mkdir(parents=True)

    # 1. fresh-dict build -> this case's ordered (slug -> record) contribution.
    built: dict = {}
    corpus._load_build(src_bundle).build(built)
    order = list(built.keys())

    # 2. copy the frozen canonical record bytes; assert id-parity with the fresh build.
    referenced_hex: set[str] = set()
    record_ids: list[str] = []
    for slug in order:
        frozen = repo / "fixtures" / f"{slug}.json"
        raw = frozen.read_bytes()
        on_disk = json.loads(raw)
        if on_disk["id"] != built[slug]["id"]:
            raise SystemExit(
                f"{case_id}/{slug}: frozen id {on_disk['id']} != freshly-built id {built[slug]['id']}")
        _write(out / "records" / f"{slug}.json", raw)
        referenced_hex |= _hex_strings(on_disk)
        record_ids.append(on_disk["id"])

    # 3. CASE.json = in-tree manifest VERBATIM + exactly one added key: `records`.
    manifest = json.loads((src_bundle / "CASE.json").read_text())
    manifest["records"] = [f"{slug}.json" for slug in order]
    (out / "CASE.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # 4. PROVENANCE.md + engine.pin (verbatim copies).
    prov_name = PROVENANCE_SRC[case_id]
    prov_bytes = (repo / "fixtures" / prov_name).read_bytes()
    _write(out / "PROVENANCE.md", prov_bytes)
    _write(out / "engine.pin", (src_bundle / "engine.pin").read_bytes())

    # 5. sources/ — exactly the excerpt files this case's records reference (by byte hash).
    src_index = _source_hash_index(repo)
    matched = sorted({src_index[h] for h in referenced_hex if h in src_index})
    for name in matched:
        _write(out / "sources" / name, (repo / "fixtures" / "sources" / name).read_bytes())

    # README (optional, uncovered by the digest).
    _write(out / "README.md", _readme(case_id, manifest, order, matched).encode("utf-8"))

    # 6. expected.digest — AFTER everything else is placed (not self-covered).
    digest = cases.bundle_digest(out)
    (out / "expected.digest").write_text(digest + "\n")

    return {
        "digest": digest,
        "records": manifest["records"],
        "record_ids": record_ids,
        "sources": matched or None,
        "provenance_src": prov_name,
    }


def export_surgisphere(repo: Path, out_root: Path, ref: str, engine) -> dict:
    cases, _corpus, importer = engine
    out = out_root / SURGISPHERE
    if out.exists():
        import shutil
        shutil.rmtree(out)
    (out / "records").mkdir(parents=True)

    # candidate authoring inputs, read-only from the git ref.
    case_json = _git_show(repo, ref, f"{SURGISPHERE_PATH}/CASE.json")
    prov = _git_show(repo, ref, f"{SURGISPHERE_PATH}/PROVENANCE.md")
    spec_bytes = _git_show(repo, ref, f"{SURGISPHERE_PATH}/spec.json")
    spec = json.loads(spec_bytes)

    # order: candidate CASE.json declares none -> derive from the import build insertion order.
    manifest = json.loads(case_json)
    if manifest.get("records"):
        order = [Path(n).stem for n in manifest["records"]]
    else:
        order = [rec["assertion"]["label"] for rec in importer.import_corpus(spec)]
    built = {rec["assertion"]["label"]: rec for rec in importer.import_corpus(spec)}

    # copy the 5 candidate record bytes; assert id-parity with a fresh import.
    record_ids: list[str] = []
    for slug in order:
        raw = _git_show(repo, ref, f"{SURGISPHERE_PATH}/records/{slug}.json")
        on_disk = json.loads(raw)
        if on_disk["id"] != built[slug]["id"]:
            raise SystemExit(
                f"surgisphere/{slug}: candidate id {on_disk['id']} != freshly-imported {built[slug]['id']}")
        _write(out / "records" / f"{slug}.json", raw)
        record_ids.append(on_disk["id"])

    # CASE.json = candidate + `records` manifest (keep its import_note et al.).
    manifest["records"] = [f"{slug}.json" for slug in order]
    (out / "CASE.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    # PROVENANCE.md (candidate's) + engine.pin (from a seven-case: cairn.v0/JCS/cairn-case/1.0).
    _write(out / "PROVENANCE.md", prov)
    _write(out / "engine.pin", (repo / "fixtures" / "cases" / "covid-origins" / "engine.pin").read_bytes())

    # spec.json — SHIP it (authoring input; deliberately uncovered by the digest). NO build.py.
    _write(out / "spec.json", spec_bytes)
    _write(out / "README.md", _readme(SURGISPHERE, manifest, order, []).encode("utf-8"))

    digest = cases.bundle_digest(out)
    (out / "expected.digest").write_text(digest + "\n")

    return {
        "digest": digest,
        "records": manifest["records"],
        "record_ids": record_ids,
        "sources": None,
        "provenance_src": f"{SURGISPHERE_PATH}/PROVENANCE.md@{ref}",
    }


def _readme(case_id: str, manifest: dict, order: list[str], sources: list[str]) -> str:
    title = manifest.get("title", case_id)
    nsrc = f" and {len(sources)} version-of-record source excerpt(s) under `sources/`" if sources else ""
    return (
        f"# {case_id}\n\n"
        f"**{title}**\n\n"
        f"Self-contained, verify-only mirror of the `{case_id}` case bundle (CASE-REPO-SPEC.md). "
        f"It ships {len(order)} pre-minted `records/` in the pinned assembly order (`CASE.json` "
        f"`records`), a `PROVENANCE.md` vetting record, an `engine.pin`{nsrc}, and an "
        f"`expected.digest`. Verify standalone with `cairn cases verify .` and recompute the "
        f"digest against `expected.digest`; no `build.py`, no signing seed, no minting required.\n")


# --------------------------------------------------------------------------------------------
# verification (the byte-identity acceptance — step 2)
# --------------------------------------------------------------------------------------------

def _path_lock(out_root: Path, case_ids: list[str], engine) -> dict:
    cases, _corpus, _imp = engine
    return {
        "corpus_lock_version": "1.0",
        "corpus": {"name": "w4-mirror-acceptance", "record_schema": "cairn.v0",
                   "canonicalization": "JCS/RFC-8785"},
        "cases": [
            {"case_id": cid, "path": str((out_root / cid).resolve()),
             "digest": cases.bundle_digest(out_root / cid), "engine": "cairn.v0"}
            for cid in case_ids
        ],
    }


def verify(repo: Path, out_root: Path, engine) -> int:
    cases, corpus, _imp = engine
    fx = repo / "fixtures"
    ok = True

    # (a) per-bundle: expected.digest == recomputed digest.
    print("== per-bundle digest self-consistency ==")
    for cid in SEVEN + [SURGISPHERE]:
        d = out_root / cid
        want = (d / "expected.digest").read_text().strip()
        got = cases.bundle_digest(d)
        good = want == got
        ok = ok and good
        print(f"  {'OK ' if good else 'BAD'} {cid}: {got}")

    # (b) 7-case byte-identity acceptance (base_dir='/' since paths are absolute).
    print("\n== 7-case byte-identity acceptance ==")
    lock7 = _path_lock(out_root, SEVEN, engine)
    assembled = corpus.assemble(lock7, base_dir="/")

    got_index = json.dumps(assembled["index"], indent=2) + "\n"
    want_index = (fx / "INDEX.json").read_text()
    index_ok = got_index == want_index
    ok = ok and index_ok
    print(f"  INDEX byte-identical: {'YES' if index_ok else 'NO'}")

    stripped = {cid: {k: v for k, v in man.items() if k != "records"}
                for cid, man in assembled["cases"].items()}
    got_cases = json.dumps(stripped, indent=2, ensure_ascii=False) + "\n"
    want_cases = (fx / "CASES.json").read_text()
    cases_ok = got_cases == want_cases
    ok = ok and cases_ok
    print(f"  CASES(minus `records`) byte-identical: {'YES' if cases_ok else 'NO'}")

    drift = []
    for slug, rec in assembled["records"].items():
        got = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        committed = fx / f"{slug}.json"
        if not committed.is_file() or committed.read_text() != got:
            drift.append(slug)
    records_ok = not drift
    ok = ok and records_ok
    print(f"  records byte-identical to frozen fixtures: {'YES' if records_ok else 'NO'}"
          + (f" (drift: {drift})" if drift else ""))

    # (c) 8-case assembly: surgisphere appends cleanly as #8; the 8-case INDEX extends the 7-case.
    print("\n== 8-case assembly (surgisphere appended as #8) ==")
    lock8 = _path_lock(out_root, SEVEN + [SURGISPHERE], engine)
    a8 = corpus.assemble(lock8, base_dir="/")
    seven_keys = list(assembled["index"].keys())
    eight_keys = list(a8["index"].keys())
    extends = eight_keys[: len(seven_keys)] == seven_keys
    appended = len(eight_keys) - len(seven_keys)
    good8 = extends and list(a8["cases"].keys()) == SEVEN + [SURGISPHERE]
    ok = ok and good8
    print(f"  8-case assembly succeeded: cases={list(a8['cases'].keys())}")
    print(f"  8-case INDEX extends the 7-case prefix: {'YES' if extends else 'NO'} "
          f"(+{appended} surgisphere records, {len(eight_keys)} total)")

    print(f"\nRESULT: {'ALL GREEN' if ok else 'FAILURES ABOVE'}")
    return 0 if ok else 1


# --------------------------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=str(_repo_root()), help="dev/cairn worktree root (has fixtures/, cairn/)")
    ap.add_argument("--out", default="/home/ubuntu/work/w4-mirrors", help="output root for the mirror bundles")
    ap.add_argument("--surgisphere-ref", default=SURGISPHERE_REF_DEFAULT,
                    help="git ref carrying fixtures/candidates/surgisphere/")
    ap.add_argument("--verify", action="store_true",
                    help="run the byte-identity acceptance over already-generated mirrors (no regen)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    out_root = Path(args.out).resolve()
    engine = _import_engine(repo)

    if args.verify:
        return verify(repo, out_root, engine)

    out_root.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, dict] = {}
    for cid in SEVEN:
        manifest[cid] = export_grounded_case(repo, out_root, cid, engine)
        print(f"exported {cid}: {manifest[cid]['digest']}  "
              f"({len(manifest[cid]['records'])} records, "
              f"{len(manifest[cid]['sources'] or [])} sources)")
    manifest[SURGISPHERE] = export_surgisphere(repo, out_root, args.surgisphere_ref, engine)
    print(f"exported {SURGISPHERE}: {manifest[SURGISPHERE]['digest']}  "
          f"({len(manifest[SURGISPHERE]['records'])} records, unsigned import-path)")

    (out_root / "EXPORT-MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(f"\nwrote {out_root / 'EXPORT-MANIFEST.json'}")
    print("run `python scripts/export_mirror.py --verify` for the byte-identity acceptance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

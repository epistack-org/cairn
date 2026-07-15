"""cairn corpus assemble — assemble a byte-identical corpus from a ``corpus.lock``.

This is the engine going *corpus-agnostic*: the hardcoded
``fixtures/build_fixtures.py`` path (``CASE_ORDER = fixtures/cases/cases.lock``) becomes a
generic assembler driven by a ``corpus.lock`` that lives OUTSIDE the engine (CORPUS-SPEC.md).
Nothing here knows *which* cases exist — the lock does.

For each entry, in lock order:

  1. resolve the bundle — a local ``path``, or (W4) clone ``repo`` at an immutable ``ref`` (a git
     tag or a full 40-hex commit SHA; a branch name is not reproducible and is rejected).
     ``domain`` stays reserved (it lands with subdomain-delegation infra),
  2. verify its content **digest** (``cairn.cases.bundle_digest``) against the pin,
  3. verify its declared **structure** (``cairn.cases.verify_bundle``),
  4. verify **engine compatibility** (its ``engine.pin`` vs what this engine implements),
  5. collect its records — from a self-contained bundle's ``records/`` (in the CASE.json
     ``records`` order), or, for an in-tree dual-homed bundle (the seven today: CASE.json +
     build.py, no records/), by running its authoring ``build.py`` (the monolith->trifurcation
     bridge; re-mints deterministically — CORPUS-SPEC.md §2/§3).

Then it emits ``INDEX.json``/``CASES.json`` in lock order, byte-identical to what the reference
builder emits (INDEX: ``json.dumps(index, indent=2)``; CASES: ``ensure_ascii=False``).
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import cases, canonical

# --- what THIS engine implements: the axes an engine.pin gates on (CASE-REPO-SPEC.md §4) ---
ENGINE_RECORD_SCHEMA = "cairn.v0"                 # envelope.CONTEXT is .../cairn.v0.jsonld
ENGINE_CANONICALIZATION = "JCS/RFC-8785" if canonical.BACKEND == "rfc8785" else canonical.BACKEND
ENGINE_CASE_SPECS = frozenset({"cairn-case/1.0"})


class AssemblyError(RuntimeError):
    """A corpus.lock entry failed a gate (digest / structure / engine-compat / resolution)."""


def engine_satisfies_pin(pin: dict) -> tuple[bool, str]:
    """Does the running engine satisfy a case's engine.pin? (record_schema + canonicalization +
    case_spec — never the engine point release; CASE-REPO-SPEC.md §4)."""
    if pin.get("record_schema") != ENGINE_RECORD_SCHEMA:
        return False, f"record_schema {pin.get('record_schema')!r} != engine {ENGINE_RECORD_SCHEMA!r}"
    if pin.get("canonicalization") != ENGINE_CANONICALIZATION:
        return False, f"canonicalization {pin.get('canonicalization')!r} != engine {ENGINE_CANONICALIZATION!r}"
    if pin.get("case_spec") not in ENGINE_CASE_SPECS:
        return False, f"case_spec {pin.get('case_spec')!r} not in engine-supported {sorted(ENGINE_CASE_SPECS)}"
    return True, "ok"


# --- repo-mode resolution (W4) -------------------------------------------------------------

# `ref` is immutable iff it is a full 40-hex commit SHA or a git tag; a branch name is rejected.
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")


def _forge_base() -> str:
    """The forge to clone a bare ``repo`` slug from (overridable for other forges / offline)."""
    return os.environ.get("CAIRN_FORGE_BASE", "https://forge.example.org").rstrip("/")


def _clone_url(repo: str) -> str:
    """A ``repo`` that already carries a scheme (``://``) is a full clone URL, used verbatim;
    otherwise it is a forge slug resolved against ``CAIRN_FORGE_BASE``."""
    return repo if "://" in repo else f"{_forge_base()}/{repo}.git"


def _git(argv: list[str], case_id: str, what: str) -> None:
    r = subprocess.run(["git", *argv], capture_output=True, text=True)
    if r.returncode != 0:
        raise AssemblyError(f"{case_id}: git {what} failed — {(r.stderr or r.stdout).strip()}")


def _resolve_repo(entry: dict, clones: dict | None, tmpdirs: list | None) -> Path:
    """Clone ``repo`` at the immutable ``ref`` and return the clone ROOT (a case repo carries
    CASE.json at its root — the cairns/_case-template layout).

    ``ref`` is accepted iff it is a full 40-hex commit SHA **or** a tag in the clone; a
    branch-only ref is not reproducible and is rejected (CORPUS-SPEC §1). Clones are cached by
    ``(url, ref)`` so a repeated entry clones once, and each tempdir root is recorded in
    ``tmpdirs`` for the caller (``assemble``) to clean up. The clone is trusted only for
    reachability — the digest gate in ``assemble`` re-verifies the bytes (CORPUS-SPEC §8)."""
    cid = entry["case_id"]
    repo = entry["repo"]
    ref = entry.get("ref")
    if not ref:
        raise AssemblyError(f"{cid}: repo mode requires `ref` (a tag or a full 40-hex commit SHA)")
    url = _clone_url(repo)
    key = (url, ref)
    if clones is not None and key in clones:
        return clones[key]

    root = Path(tempfile.mkdtemp(prefix="cairn-corpus-clone-"))
    if tmpdirs is not None:
        tmpdirs.append(root)
    dest = root / "bundle"
    _git(["clone", "--filter=blob:none", "--quiet", url, str(dest)], cid, f"clone {repo!r}")

    if not _FULL_SHA.match(ref):
        is_tag = subprocess.run(
            ["git", "-C", str(dest), "show-ref", "--verify", "--quiet", f"refs/tags/{ref}"]
        ).returncode == 0
        if not is_tag:
            raise AssemblyError(
                f"{cid}: ref {ref!r} is not an immutable ref — repo mode requires a git TAG or a "
                f"full 40-hex commit SHA (a branch name is not reproducible; CORPUS-SPEC §1)")
    _git(["-C", str(dest), "checkout", "--quiet", ref], cid, f"checkout {ref!r}")

    if clones is not None:
        clones[key] = dest
    return dest


def resolve_entry(entry: dict, base_dir, *, clones: dict | None = None,
                  tmpdirs: list | None = None) -> Path:
    """Resolve a lock entry to a bundle directory.

    - **local** (``path``) — a working-tree-relative directory (unchanged).
    - **repo** (``repo`` + ``ref``, W4) — clone the case repo at the immutable ``ref`` and return
      the clone ROOT. ``clones``/``tmpdirs`` are the caller's clone cache + cleanup registry
      (``assemble`` supplies them and removes the tempdirs in a ``finally``).
    - **domain** — reserved (CORPUS-SPEC §8); no resolver yet."""
    if "path" in entry:
        return Path(base_dir) / entry["path"]
    if "repo" in entry:
        return _resolve_repo(entry, clones, tmpdirs)
    if "domain" in entry:
        raise AssemblyError(
            f"{entry['case_id']}: domain-mode is reserved (CORPUS-SPEC §8) — no resolver yet.")
    raise AssemblyError(f"{entry['case_id']}: no resolution mode (need path | repo+ref | domain)")


def _load_build(bundle_dir: Path):
    """Load a bundle's authoring build.py by path (case-ids contain hyphens)."""
    path = bundle_dir / "build.py"
    modname = "cairn_corpus_build_" + bundle_dir.name.replace("-", "_")
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _collect_records(bundle_dir: Path, manifest: dict, recs: dict) -> None:
    """Add a bundle's records to ``recs`` (keyed by slug), preserving insertion order.

    Self-contained bundle -> read records/ in the CASE.json ``records`` order (which MUST be
    declared and MUST match records/ on disk — a sort would break byte-identity, CORPUS-SPEC §2).
    In-tree dual-homed bundle -> run its build.py (the monolith->trifurcation bridge).
    """
    records_dir = bundle_dir / "records"
    if records_dir.is_dir():
        order = manifest.get("records")
        if not order:
            # A self-contained bundle MUST pin its record order (CORPUS-SPEC §2 "Record order"):
            # a bare sorted() would reorder INDEX.json and silently break byte-identity.
            raise AssemblyError(
                f"{bundle_dir.name}: records/ present but CASE.json declares no `records` order — "
                "assembly order is not pinned (a filesystem sort would break byte-identity; CORPUS-SPEC §2)")
        on_disk = {p.name for p in records_dir.glob("*.json")}
        if set(order) != on_disk:
            raise AssemblyError(
                f"{bundle_dir.name}: `records` manifest {sorted(order)} != records/ on disk {sorted(on_disk)}")
        for name in order:
            f = records_dir / name
            rec = json.loads(f.read_text())
            _insert(recs, f.stem, rec, bundle_dir.name)
    elif (bundle_dir / "build.py").is_file():
        _load_build(bundle_dir).build(recs)      # bridge: deterministic re-mint (seed via lib.mint)
    else:
        raise AssemblyError(f"{bundle_dir.name}: neither records/ nor build.py — cannot collect records")


def _insert(recs: dict, slug: str, rec: dict, case_id: str) -> None:
    prev = recs.get(slug)
    if prev is not None and prev.get("id") != rec.get("id"):
        raise AssemblyError(f"slug collision across bundles: {slug!r} (at {case_id}) resolves to two records")
    recs[slug] = rec


def load_lock(path) -> dict:
    return json.loads(Path(path).read_text())


def assemble(lock: dict, base_dir=".") -> dict:
    """Assemble a corpus from a parsed ``corpus.lock``. Returns
    ``{index, cases, records}``; raises AssemblyError on the first failing gate (named entry)."""
    entries = lock["cases"]
    corpus_schema = lock["corpus"]["record_schema"]

    seen: set[str] = set()
    for e in entries:
        if e["case_id"] in seen:
            raise AssemblyError(f"duplicate case_id in corpus.lock: {e['case_id']!r}")
        seen.add(e["case_id"])

    # Repo-mode clones live in tempdirs; cache by (url, ref) so a repeated entry clones once, and
    # remove them all after assembly (shared-host filesystem hygiene). Every read below — digest,
    # engine.pin, manifest, records — happens BEFORE the finally, so cleanup is safe.
    clones: dict = {}
    tmpdirs: list = []
    try:
        recs: dict[str, dict] = {}
        manifests: dict[str, dict] = {}
        for e in entries:
            bundle = resolve_entry(e, base_dir, clones=clones, tmpdirs=tmpdirs)
            if not (bundle / cases.MANIFEST).is_file():
                raise AssemblyError(f"{e['case_id']}: no {cases.MANIFEST} at {bundle}")

            # (2) digest gate — the bytes must be exactly what the lock pins
            got = cases.bundle_digest(bundle)
            if got != e["digest"]:
                raise AssemblyError(f"{e['case_id']}: digest drift\n  pinned:  {e['digest']}\n  on disk: {got}")

            # (4) engine-compat gate — engine.pin vs this engine, and the schema keys must agree.
            # engine.pin is REQUIRED (CASE-REPO-SPEC §4) and is the SOLE compat guard here — assembly
            # never re-derives Trusty-URIs — so its absence is a loud failure, never a skipped gate.
            pin_path = bundle / "engine.pin"
            if not pin_path.is_file():
                raise AssemblyError(
                    f"{e['case_id']}: no engine.pin — cannot verify engine compatibility (CASE-REPO-SPEC §4)")
            pin = json.loads(pin_path.read_text())
            ok, why = engine_satisfies_pin(pin)
            if not ok:
                raise AssemblyError(f"{e['case_id']}: engine does not satisfy engine.pin — {why}")
            entry_engine = e.get("engine", corpus_schema)
            if not (pin["record_schema"] == entry_engine == corpus_schema):
                raise AssemblyError(
                    f"{e['case_id']}: record_schema disagreement — pin={pin['record_schema']!r} "
                    f"entry.engine={entry_engine!r} corpus.record_schema={corpus_schema!r}")

            manifest = cases.load_manifest(bundle)
            _collect_records(bundle, manifest, recs)
            # CASES.json carries only a case's SEMANTIC declaration. The `records` order manifest is
            # assembly-only metadata (CORPUS-SPEC §2): once _collect_records has consumed it, drop
            # it (shallow copy, this key only) so CASES.json is byte-identical whether a case is
            # in-tree (no `records`) or a self-contained mirror (records/-shipping). verify_bundle
            # does not read `records`, so the structure gate is unaffected.
            manifests[e["case_id"]] = {k: v for k, v in manifest.items() if k != "records"}

        # (3) structure gate — every case's declared structure must hold over the assembled store
        store = {r["id"]: r for r in recs.values()}
        alias = {slug: r["id"] for slug, r in recs.items()}
        for cid, manifest in manifests.items():
            result = cases.verify_bundle(manifest, store, lambda s: alias.get(s, s))
            if not result["ok"]:
                bad = [c for c in result["checks"] if not c["ok"]]
                raise AssemblyError(f"{cid}: declared structure does not hold — {bad}")

        index = {slug: rec["id"] for slug, rec in recs.items()}
        return {"index": index, "cases": manifests, "records": recs}
    finally:
        for d in tmpdirs:
            shutil.rmtree(d, ignore_errors=True)


def write_assembled(assembled: dict, out_dir, *, write_records: bool = False) -> Path:
    """Write INDEX.json/CASES.json (and optionally records) in the reference byte-form."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    # INDEX.json: json.dumps(index, indent=2) — ensure_ascii default (slugs/URIs are ASCII)
    (out / "INDEX.json").write_text(json.dumps(assembled["index"], indent=2) + "\n")
    # CASES.json: ensure_ascii=False — case prose carries non-ASCII
    (out / "CASES.json").write_text(json.dumps(assembled["cases"], indent=2, ensure_ascii=False) + "\n")
    if write_records:
        for slug, rec in assembled["records"].items():
            (out / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
    return out

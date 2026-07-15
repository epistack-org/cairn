"""cairn corpus assemble — assemble a byte-identical corpus from a ``corpus.lock``.

This is the engine going *corpus-agnostic*: the hardcoded
``fixtures/build_fixtures.py`` path (``CASE_ORDER = fixtures/cases/cases.lock``) becomes a
generic assembler driven by a ``corpus.lock`` that lives OUTSIDE the engine (CORPUS-SPEC.md).
Nothing here knows *which* cases exist — the lock does.

For each entry, in lock order:

  1. resolve the bundle (local ``path`` today; ``repo``/``domain`` are declared in the schema
     and raise a clear not-yet-wired error until W4/federation land),
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


def resolve_entry(entry: dict, base_dir) -> Path:
    """Resolve a lock entry to a bundle directory. Local (``path``) mode is wired; ``repo`` and
    ``domain`` are accepted by the schema but not yet fetchable (W4 / federation infra)."""
    if "path" in entry:
        return Path(base_dir) / entry["path"]
    if "repo" in entry:
        raise AssemblyError(
            f"{entry['case_id']}: repo-mode resolution is not wired yet (W4). "
            "Assemble a local (path-mode) corpus.lock, or vendor the case repo first.")
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

    recs: dict[str, dict] = {}
    manifests: dict[str, dict] = {}
    for e in entries:
        bundle = resolve_entry(e, base_dir)
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

        manifests[e["case_id"]] = cases.load_manifest(bundle)
        _collect_records(bundle, manifests[e["case_id"]], recs)

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

"""Per-case bundle discovery + verification — the repo-per-case seam.

A *bundle* is a directory with a ``CASE.json`` manifest (``crux``, ``laundered_set``,
``shared_upstream``, ``contrast_pair``/``contrast_expected``, ``battery``, ``punchline``).
``verify_bundle`` runs the same structural assertions the corpus' ``tests/test_cases.py``
makes — the laundered set must REFUSE, the declared shared upstream must be the one the
DAG walk collectively finds, and the contrast pair must land on its declared verdict —
against ANY bundle plus a record store. So a new case, or an external case repo, is
checked exactly the way the built-in seven are.

``discover`` + ``cases.lock`` keep "N worked examples is a checked property" true without
a hardcoded count: the lock pins the ordered case set and a per-bundle content digest, so
adding/removing a case is an intentional, reviewed lock edit and any silent byte drift in a
bundle flips its digest.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import provenance

MANIFEST = "CASE.json"
LOCK = "cases.lock"


def load_manifest(bundle_dir) -> dict:
    return json.loads((Path(bundle_dir) / MANIFEST).read_text())


def discover(cases_dir) -> list[str]:
    """Case-ids of every bundle (a subdir with a CASE.json) under ``cases_dir``, sorted."""
    return sorted(p.parent.name for p in Path(cases_dir).glob("*/" + MANIFEST))


def _digest_relpaths(bundle_dir: Path) -> list[str]:
    """The bundle's committed source files, in a stable order, that the digest covers."""
    rels = [n for n in (MANIFEST, "build.py", "PROVENANCE.md", "engine.pin")
            if (bundle_dir / n).is_file()]
    for sub in ("records", "sources"):
        d = bundle_dir / sub
        if d.is_dir():
            rels += sorted(f"{sub}/{f.name}" for f in d.iterdir() if f.is_file())
    return rels


def bundle_digest(bundle_dir) -> str:
    """Content digest over the bundle's committed source files. Flips on any byte drift."""
    d = Path(bundle_dir)
    h = hashlib.sha256()
    for rel in _digest_relpaths(d):
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update((d / rel).read_bytes())
        h.update(b"\0")
    return "sha256:" + h.hexdigest()


def load_lock(cases_dir) -> dict:
    return json.loads((Path(cases_dir) / LOCK).read_text())


def build_lock(cases_dir, order: list[str]) -> dict:
    """Assemble the lock object for the given pinned order (order must cover all bundles)."""
    d = Path(cases_dir)
    found = set(discover(d))
    assert set(order) == found, ("cases.lock order != bundles on disk", sorted(order), sorted(found))
    return {
        "order": list(order),
        "bundles": {cid: {"digest": bundle_digest(d / cid)} for cid in order},
    }


def verify_bundle(manifest: dict, store: dict, resolve) -> dict:
    """Run the structural assertions the case declares. ``resolve(slug) -> id``.

    Returns ``{ok, case, checks:[{check, ok, detail}]}`` — the caller decides fatality.
    """
    checks: list[dict] = []

    def add(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    laundered = [resolve(s) for s in manifest["laundered_set"]]
    v = provenance.combine_verdict(laundered, store)
    add("laundered_set REFUSES", v["verdict"] == "REFUSE-TO-COMBINE", v["verdict"])

    collective = provenance.shared_upstreams(laundered, store)["collective_shared"]
    add("declared shared_upstream is shared by ALL lines",
        resolve(manifest["shared_upstream"]) in collective, manifest["shared_upstream"])

    if manifest.get("contrast_pair"):
        pair = [resolve(s) for s in manifest["contrast_pair"]]
        cv = provenance.combine_verdict(pair, store)
        want = manifest.get("contrast_expected", "COMBINABLE")
        add(f"contrast_pair == {want}", cv["verdict"] == want, cv["verdict"])

    return {"ok": all(c["ok"] for c in checks), "case": manifest.get("title", ""), "checks": checks}

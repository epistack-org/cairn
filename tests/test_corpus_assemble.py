"""`cairn corpus assemble` — the corpus-agnostic assembler.

Two halves of the golden, bifurcated:

- **Content byte-identity** (``test_assemble_reproduces_golden_byte_identical``): assembling a
  local (path-mode) ``corpus.lock`` over the in-tree bundles reproduces today's frozen
  ``INDEX.json``/``CASES.json`` byte-for-byte. This is the W1 acceptance. The *content* golden
  itself (the exact bytes) is handed to the corpus repo in W3; this test asserts the assembler
  reproduces it while it still lives here.
- **Mechanism determinism** (``test_mechanism_is_deterministic_on_a_synthetic_corpus``): the
  engine assembles a small SYNTHETIC corpus reproducibly, referencing **no real case content** —
  so it survives the content golden moving out. This is the determinism test dev/cairn keeps.

Plus the gates: a drifted digest, an incompatible engine.pin, a duplicate case_id, and an
unresolvable/reserved mode must each fail loudly.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from cairn import cases, corpus, importer

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
LOCAL_LOCK = FX / "corpus.local.lock"
CORPUS_SCHEMA = json.loads((ROOT / "schemas" / "corpus.schema.json").read_text())


def test_local_lock_is_schema_valid():
    lock = json.loads(LOCAL_LOCK.read_text())
    errors = list(Draft202012Validator(CORPUS_SCHEMA).iter_errors(lock))
    assert not errors, [e.message for e in errors]


def test_local_lock_digests_match_disk():
    """The pinned digests are the live bundle digests — a stale lock fails assembly, not silently."""
    lock = json.loads(LOCAL_LOCK.read_text())
    for entry in lock["cases"]:
        assert entry["digest"] == cases.bundle_digest(ROOT / entry["path"]), entry["case_id"]


def test_assemble_reproduces_golden_byte_identical():
    """THE W1 acceptance: assemble over the local corpus.lock == today's INDEX/CASES, byte-for-byte."""
    lock = json.loads(LOCAL_LOCK.read_text())
    assembled = corpus.assemble(lock, base_dir=ROOT)
    want_index = (FX / "INDEX.json").read_text()
    want_cases = (FX / "CASES.json").read_text()
    got_index = json.dumps(assembled["index"], indent=2) + "\n"
    got_cases = json.dumps(assembled["cases"], indent=2, ensure_ascii=False) + "\n"
    assert got_index == want_index, "assembled INDEX.json is not byte-identical to the golden"
    assert got_cases == want_cases, "assembled CASES.json is not byte-identical to the golden"


def test_assembled_records_are_byte_identical_too():
    """The records the assembler collects are the frozen record bytes (extra strength beyond acceptance)."""
    lock = json.loads(LOCAL_LOCK.read_text())
    assembled = corpus.assemble(lock, base_dir=ROOT)
    drift = []
    for slug, rec in assembled["records"].items():
        got = json.dumps(rec, indent=2, ensure_ascii=False) + "\n"
        committed = FX / f"{slug}.json"
        if not committed.is_file() or committed.read_text() != got:
            drift.append(slug)
    assert not drift, f"assembled records not byte-identical: {drift}"


# --- gates ---------------------------------------------------------------------------------

def _local_lock() -> dict:
    return json.loads(LOCAL_LOCK.read_text())


def test_gate_digest_drift():
    lock = _local_lock()
    lock["cases"][0]["digest"] = "sha256:" + "0" * 64
    with pytest.raises(corpus.AssemblyError, match="digest drift"):
        corpus.assemble(lock, base_dir=ROOT)


def test_gate_duplicate_case_id():
    lock = _local_lock()
    lock["cases"].append(dict(lock["cases"][0]))
    with pytest.raises(corpus.AssemblyError, match="duplicate case_id"):
        corpus.assemble(lock, base_dir=ROOT)


def test_gate_domain_mode_reserved():
    lock = _local_lock()
    e = lock["cases"][0]
    e.pop("path")
    e["domain"] = "covid-origins.a.epistack.dev"
    lock["cases"] = [e]
    with pytest.raises(corpus.AssemblyError, match="domain-mode is reserved"):
        corpus.assemble(lock, base_dir=ROOT)


def test_engine_satisfies_pin_axes():
    good = {"record_schema": "cairn.v0", "canonicalization": "JCS/RFC-8785", "case_spec": "cairn-case/1.0"}
    assert corpus.engine_satisfies_pin(good)[0]
    for bad_key, bad_val in (("record_schema", "cairn.v1"),
                             ("canonicalization", "RDFC-1.0"),
                             ("case_spec", "cairn-case/2.0")):
        pin = dict(good, **{bad_key: bad_val})
        ok, why = corpus.engine_satisfies_pin(pin)
        assert not ok and bad_key in why, (bad_key, why)


# --- mechanism determinism (synthetic, content-free) ---------------------------------------

# Deliberately NON-alphabetical insertion order so INDEX order != sorted(records/): this is what
# makes the determinism test able to catch a regression from manifest-order to a filesystem sort.
_SYNTH_ORDER = ["z-shared", "m-shared", "a-shared", "x-trial", "y-trial"]


def _synthetic_bundle(dir_: Path) -> None:
    """A tiny self-contained (records/-shipping) bundle: three claims sharing one urn upstream
    (must REFUSE) + a disjoint contrast pair (must COMBINE). No real corpus content. The record
    order is deliberately non-alphabetical (_SYNTH_ORDER)."""
    shared = {"z-shared", "m-shared", "a-shared"}
    spec = {
        "minted_by": "import:test-synthetic",
        "at": "2026-01-01T00:00:00Z",
        "claims": [
            {"slug": s,
             "text": f"Claim {s} from the shared registry." if s in shared else f"Claim {s} from an independent trial.",
             "derivedFrom": ["urn:test:shared-db"] if s in shared else [f"urn:test:{s}"]}
            for s in _SYNTH_ORDER
        ],
    }
    recs = importer.import_corpus(spec)
    records_dir = dir_ / "records"
    records_dir.mkdir(parents=True)
    order = []
    for rec in recs:
        slug = rec["assertion"]["label"]
        (records_dir / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        order.append(f"{slug}.json")
    manifest = {
        "case_spec_version": "1.0",
        "title": "Synthetic — three masks, one registry",
        "crux": "Do three lines rest on independent evidence or one shared registry?",
        "shared_upstream": "urn:test:shared-db",
        "laundered_set": ["z-shared", "m-shared", "a-shared"],
        "contrast_pair": ["x-trial", "y-trial"],
        "contrast_expected": "COMBINABLE",
        "records": order,
        "punchline": "Three claims that cite one urn are one line, not three.",
    }
    (dir_ / "CASE.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    (dir_ / "engine.pin").write_text(json.dumps({
        "pin_schema": "cairn-engine-pin/1.0", "record_schema": "cairn.v0",
        "canonicalization": "JCS/RFC-8785", "case_spec": "cairn-case/1.0",
    }) + "\n")


def _synthetic_lock(case_id: str, digest: str) -> dict:
    return {
        "corpus_lock_version": "1.0",
        "corpus": {"name": "synthetic", "record_schema": "cairn.v0", "canonicalization": "JCS/RFC-8785"},
        "cases": [{"case_id": case_id, "path": case_id, "digest": digest, "engine": "cairn.v0"}],
    }


def test_synthetic_bundle_is_schema_valid_and_verifies(tmp_path):
    _synthetic_bundle(tmp_path / "synthetic")
    manifest = json.loads((tmp_path / "synthetic" / "CASE.json").read_text())
    case_schema = json.loads((ROOT / "schemas" / "case.schema.json").read_text())
    assert not list(Draft202012Validator(case_schema).iter_errors(manifest))


def test_mechanism_is_deterministic_on_a_synthetic_corpus(tmp_path):
    """The assembler reproduces byte-identical INDEX/CASES on a synthetic corpus across two runs —
    determinism of the mechanism, referencing no real case content (survives W3's golden move)."""
    root = tmp_path
    _synthetic_bundle(root / "synthetic")
    lock = _synthetic_lock("synthetic", cases.bundle_digest(root / "synthetic"))

    a = corpus.assemble(lock, base_dir=root)
    b = corpus.assemble(lock, base_dir=root)
    a_index, a_cases = json.dumps(a["index"], indent=2), json.dumps(a["cases"], indent=2, ensure_ascii=False)
    b_index, b_cases = json.dumps(b["index"], indent=2), json.dumps(b["cases"], indent=2, ensure_ascii=False)
    assert a_index == b_index and a_cases == b_cases, "assembly is not deterministic"
    # and the mechanism actually assembled the declared structure (REFUSE trio + COMBINE pair held)
    assert list(a["cases"]) == ["synthetic"]
    assert len(a["records"]) == 5
    # INDEX order follows the records manifest order, NOT a filesystem sort. This only tests what it
    # claims because _SYNTH_ORDER is deliberately non-alphabetical:
    assert _SYNTH_ORDER != sorted(_SYNTH_ORDER), "test would be blind to a sorted() regression"
    assert list(a["index"]) == _SYNTH_ORDER


def test_gate_missing_engine_pin_is_rejected(tmp_path):
    """engine.pin is required (CASE-REPO-SPEC §4) and the sole compat guard — its absence must fail loudly."""
    b = tmp_path / "synthetic"
    _synthetic_bundle(b)
    (b / "engine.pin").unlink()
    lock = _synthetic_lock("synthetic", cases.bundle_digest(b))  # re-pin so the digest gate passes first
    with pytest.raises(corpus.AssemblyError, match="no engine.pin"):
        corpus.assemble(lock, base_dir=tmp_path)


def test_gate_records_without_order_manifest_is_rejected(tmp_path):
    """A self-contained bundle with records/ but no `records` order manifest must fail, not silently sort."""
    b = tmp_path / "synthetic"
    _synthetic_bundle(b)
    manifest = json.loads((b / "CASE.json").read_text())
    manifest.pop("records")
    (b / "CASE.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    lock = _synthetic_lock("synthetic", cases.bundle_digest(b))  # re-pin so the digest gate passes first
    with pytest.raises(corpus.AssemblyError, match="no .records. order"):
        corpus.assemble(lock, base_dir=tmp_path)

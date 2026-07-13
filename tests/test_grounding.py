import hashlib
import json
from pathlib import Path

from cairn import envelope, grounding

AT = "2026-06-28T00:00:00Z"
FX = Path(__file__).resolve().parents[1] / "fixtures"
EX = "Early cases centered on the market; two lineages A and B were reported."


def _src(excerpt=EX, title="Src"):
    return envelope.mint(envelope.new_record(
        "epi:Source", {"title": title, "excerpt": excerpt, "verification": "L1"},
        minted_by="team:test", method="ingest", at=AT))


def _claim(source_id, span, quote, *, label="SUPPORTS", rung="L4",
           derived=None, extra_grounding=None):
    g = {"source": source_id, "char_span": list(span), "quote": quote,
         "extractor": "tool:test", "entailment_label": label}
    if extra_grounding:
        g.update(extra_grounding)
    return envelope.mint(envelope.new_record(
        "epi:Claim", {"text": "c", "verification": rung, "grounding": g},
        minted_by="team:test", method="extract",
        derived_from=[source_id] if derived is None else derived, at=AT))


def _store(*recs):
    return {r["id"]: r for r in recs}


def _span(quote, text=EX):
    i = text.index(quote)
    return [i, i + len(quote)]


def test_grounding_resolves_and_passes():
    s = _src()
    q = "centered on the market"
    c = _claim(s["id"], _span(q), q)
    r = grounding.check_claim(c, _store(s, c))
    assert r["ok"] and r["resolves"] and r["errors"] == []


def test_span_that_does_not_match_quote_fails():
    s = _src()
    c = _claim(s["id"], [0, 5], "centered on the market")  # [0:5] == "Early"
    r = grounding.check_claim(c, _store(s, c))
    assert not r["ok"] and any("does not resolve to quote" in e for e in r["errors"])


def test_source_must_be_in_derivedfrom():
    s = _src()
    q = "Early"
    c = _claim(s["id"], _span(q), q, derived=[])  # grounded on s but not derivedFrom it
    r = grounding.check_claim(c, _store(s, c))
    assert not r["ok"] and any("derivedFrom" in e for e in r["errors"])


def test_out_of_range_span_fails():
    s = _src()
    c = _claim(s["id"], [0, 9999], "whatever")
    r = grounding.check_claim(c, _store(s, c))
    assert not r["ok"] and any("does not resolve" in e for e in r["errors"])


def test_L4_requires_positive_entailment_label():
    s = _src()
    q = "Early"
    c = _claim(s["id"], _span(q), q, label="NEI")
    r = grounding.check_claim(c, _store(s, c))
    assert not r["ok"] and any("positive entailment" in e for e in r["errors"])


def test_source_sha256_bind_is_checked():
    s = _src()
    q = "Early"
    c = _claim(s["id"], _span(q), q, extra_grounding={"source_sha256": "0" * 64})
    r = grounding.check_claim(c, _store(s, c))
    assert not r["ok"] and any("source_sha256" in e for e in r["errors"])
    # the true digest passes
    good = hashlib.sha256(EX.encode()).hexdigest()
    c2 = _claim(s["id"], _span(q), q, extra_grounding={"source_sha256": good})
    assert grounding.check_claim(c2, _store(s, c2))["ok"]


def test_L4_claim_without_grounding_fails_schema_and_check():
    r = envelope.mint(envelope.new_record(
        "epi:Claim", {"text": "x", "verification": "L4"},
        minted_by="t", method="extract", at=AT))
    assert envelope.validate(r)                       # schema requires grounding at L4/L5
    assert not grounding.check_claim(r, {r["id"]: r})["ok"]


def test_lower_rung_claim_without_grounding_stays_valid():
    # engine generality: a bare / L3 claim needn't be span-grounded
    r = envelope.mint(envelope.new_record(
        "epi:Claim", {"text": "x", "verification": "L3"},
        minted_by="t", method="assert", at=AT))
    assert envelope.validate(r) == []
    assert grounding.check_claim(r, {r["id"]: r})["ok"]


def test_legacy_unverified_fixture_value_is_rejected():
    r = envelope.mint(envelope.new_record(
        "epi:Source", {"title": "x", "verification": "unverified-fixture"},
        minted_by="t", method="ingest", at=AT))
    assert envelope.validate(r)  # enum no longer admits the legacy value


def test_fixtures_corpus_is_fully_grounded_and_valid():
    idx = json.loads((FX / "INDEX.json").read_text())
    store = {}
    for slug in idx:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
        assert envelope.validate(rec) == [], (slug, envelope.validate(rec))
    report = grounding.check_store(store)
    assert report["ok"], report["failed"]
    # every claim in the corpus is span-grounded — across all three worked examples
    n_claims = sum(1 for r in store.values() if r["@type"] == "epi:Claim")
    assert report["grounded"] == report["checked"] == n_claims
    assert n_claims >= 16, "the 3-case corpus should carry at least 16 grounded claims"

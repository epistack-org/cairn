"""Shared minting library for the fixture bundles.

Extracted verbatim from build_fixtures.py (repo-per-case refactor, Phase 1). Every
per-case bundle builder imports these primitives, so no bundle forks the signing seed,
the timestamp, the JCS canonicalizer, or the pinned-abstract SHA table — the invariants
that keep the corpus' Trusty-URIs byte-stable. Do NOT change AT, KEY, SOURCES, or the
assertion-key order in mk_claim without regenerating the corpus and reviewing the golden
diff (tests/test_determinism_golden.py).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from cairn import envelope
from cairn.keys import SigningKey

# Excerpts live in fixtures/sources/ (this module is fixtures/lib/mint.py).
SRC = Path(__file__).resolve().parents[1] / "sources"


AT = "2026-06-28T00:00:00Z"
# throwaway deterministic demo identity (NOT a real keystone key)
KEY = SigningKey.from_seed_hex("c0" * 32, label="keystone:epistack-corpus")
# who performed the span extraction (the faithfulness tuple's `extractor`)
EXTRACTOR = "agent:claude-opus-4-8[1m]/A1-source-vetting"
# the floor-#3 cases (eggs / cern) were vetted in a later pass, by a different model;
# the extractor is part of the faithfulness tuple, so it is recorded honestly per claim.
EXTRACTOR_F3 = "agent:claude-fable-5/floor3-source-vetting"
# the amyloid case (4th worked example) was vetted in a decoupling spike on 2026-07-15.
EXTRACTOR_AMYLOID = "agent:claude-fable-5/amyloid-spike-source-vetting"
# the 5th/6th/7th worked examples (ivermectin, Anversa, Poldermans) were imported in the
# 2026-07-15 backtest-scaling pass (dev/cairn#15), from a ranked research sweep of known-answer
# fraud/non-independence cases. Same first-party vetting standard.
EXTRACTOR_BACKTEST = "agent:claude-fable-5/backtest-scaling-source-vetting"


# Pinned abstracts (version of record). The build fails loudly if a byte drifts.
SOURCES = {
    "worobey": {
        "file": "worobey-2022.abstract.txt",
        "sha256": "93f3dc1858bf1dba8891cc8413568244915ca66c4908d690066ad3e12f1caba4",
    },
    "pekar": {
        "file": "pekar-2022.abstract.txt",
        "sha256": "c046d96297900e9d067e47ab0e17d2dedf317037c19d09d9593689c17f5adbfe",
    },
    # --- cern (LHC-safety) case. arXiv Atom <summary>, whitespace-normalized:
    #     " ".join(text.split()) — arXiv hard-wraps abstracts and pads the leading line.
    #     That normalization is the ONLY transform; see fixtures/PROVENANCE-cern.md.
    "ellis": {
        "file": "ellis-2008.abstract.txt",
        "sha256": "030c49f7802c2564f5ae9115af3e65c3da314533c520b67c6ab9b3fd24c68e90",
    },
    "giddings-mangano": {
        "file": "giddings-mangano-2008.abstract.txt",
        "sha256": "36ed1846d1d8fccac5a8bcd37f6a0516c0ac96f0801650d45438ab2da95d2a33",
    },
    "jaffe": {
        "file": "jaffe-2000.abstract.txt",
        "sha256": "4f1bf34242c2eb1c83cfbe6e756fb6e16f7b92042dc6e3393b7059ee1f14ae9c",
    },
    # --- eggs (egg consumption / CVD) case. PubMed structured abstracts, serialized as
    #     "LABEL: text" one section per line. The two meta-analyses additionally carry
    #     their COMPLETE Table 1 (included studies) from the Europe PMC OA JATS XML —
    #     the inclusion edges exist nowhere else. See fixtures/PROVENANCE-eggs.md.
    "hu-1999": {
        "file": "hu-1999.abstract.txt",
        "sha256": "ce74e4ba732856e977c96ddd3cba2480a85ce33eba8e16e0720ada87c1162769",
    },
    "drouin-chartier-2020": {
        "file": "drouin-chartier-2020.abstract.txt",
        "sha256": "69e0dd0797c9dd95bf70517efcaf6ad105d0c93d252e6a15df90b173cd34f786",
    },
    "djousse-2008": {
        "file": "djousse-2008.abstract.txt",
        "sha256": "4b21e2cb029cd3779142f162fa16f6fec91c0c3e4439681182ac58569706f8ca",
    },
    "rong-2013": {
        "file": "rong-2013.abstract.txt",
        "sha256": "c0b06aab867e54989aaabc8852bbd18814cc2f1c3bbdf59e87b9a31615f3729c",
    },
    "godos-2021": {
        "file": "godos-2021.abstract.txt",
        "sha256": "0cd54915d2077111969e052717153e89314a5ce3226f1849b6f4e333313a1faf",
    },
    # --- amyloid (Alzheimer's Aβ*56) case. PubMed abstracts (version of record), extracted
    #     from NCBI E-utilities XML with AbstractText itertext() (structured sections serialized
    #     "LABEL: text" one per line; these four are unstructured, so the text is verbatim).
    #     ENCODING FOOTGUN, recorded not hidden (see fixtures/PROVENANCE-amyloid.md): the SAME
    #     concept is spelled "Abeta*56" (ASCII) in the 2006 + 2008 records but "Aβ*56" (U+03B2
    #     GREEK SMALL LETTER BETA) in the 2011 + 2013 records — PubMed changed its Greek-letter
    #     serialization between deposits. A quote copied across records would silently fail the
    #     span check. Each quote below is pinned to the exact bytes of ITS OWN source.
    "lesne-2006": {
        "file": "lesne-2006.abstract.txt",
        "sha256": "d34840d0a0b49e317ade116e888ff5fc8a309e2fa3a79bde7a40d13682c54b86",
    },
    "lesne-2013": {
        "file": "lesne-2013.abstract.txt",
        "sha256": "f795a135a8297c2036875c19f1ac7815cdf2d3e8a9e8d0194e64c79429c6b8af",
    },
    "sherman-2011": {
        "file": "sherman-2011.abstract.txt",
        "sha256": "2365ef5e7845e0a2a676b16fb974f930cd71e0cc7e24647bb409fb29670833c5",
    },
    "shankar-2008": {
        "file": "shankar-2008.abstract.txt",
        "sha256": "c2991a214c140703fb140e06e3187747beaaaecf94d74df9cfaea2b226f64417",
    },
    # --- ivermectin (Elgazzar-fraud) case (dev/cairn#15). The three positive syntheses each
    #     ship their ABSTRACT (PubMed, version of record) PLUS their COMPLETE included-study
    #     characteristics table (Europe PMC OA JATS, whitespace-normalized pipe-rows — the same
    #     transform the eggs meta-analyses use for Table 1). The Elgazzar-naming row is the
    #     byte-grounded proof that each pooled the withdrawn preprint. ENCODING FOOTGUN, recorded
    #     not hidden (see fixtures/PROVENANCE-ivermectin.md): the Zein 2021 abstract uses U+00A0
    #     NO-BREAK SPACE inside its statistics ("p = 0.004"), so a quote hand-typed with
    #     ASCII spaces would silently fail the span check — the eggs/amyloid footgun class again.
    "bryant-2021": {
        "file": "bryant-2021.abstract.txt",
        "sha256": "715af76955736e2628255ad57a640ec89bd82bd3e2398d8f06f32fb014083bac",
    },
    "zein-2021": {
        "file": "zein-2021.abstract.txt",
        "sha256": "a2e9e5fc5c421d8fbba3d5aaf50a089abe679eb691ea29fa661a68aba3641d60",
    },
    "kory-2021": {
        "file": "kory-2021.abstract.txt",
        "sha256": "bd06c3d4a16e11ce3fc472514583e42a83d9779ea8493d1ca5c5cc93f6aa2f28",
    },
    "reis-2022": {  # TOGETHER — the upstream-disjoint contrast RCT
        "file": "reis-2022.abstract.txt",
        "sha256": "6908794567add22f5329b21fb4382008ab52104c7877b22fd3d1bcb597b1ea3a",
    },
    "hill-2021": {  # the published counterfactual: same meta, RETRACTED, null once Elgazzar's weight is pulled
        "file": "hill-2021.abstract.txt",
        "sha256": "f66ca4aea476e3dc2dd2d7d72123f2346261083557bdadcb8db0cdc04f98a02b",
    },
    # --- anversa (c-kit+ cardiac stem cell) case (dev/cairn#15). PubMed abstracts, version of record. ---
    "beltrami-2003": {
        "file": "beltrami-2003.abstract.txt",
        "sha256": "52559bb7c0eeecb5e731b30e24b72944f16a270c8bed0e24bfa349d0bd8e0729",
    },
    "bearzi-2007": {
        "file": "bearzi-2007.abstract.txt",
        "sha256": "c63b7ac1e19c8dcccd4ad1b784e50ab01eae19fd8e3a1954f6df9a33a6ebac63",
    },
    "bolli-2011": {  # SCIPIO — RETRACTED (Lancet 2019); the literal shared-cell-prep clinical line
        "file": "bolli-2011.abstract.txt",
        "sha256": "33bab0ee2cd8b5cbe3bad66cee4206c660d53b4b2ed6ba2154d5fffe9cd635fa",
    },
    "makkar-2012": {  # CADUCEUS — the upstream-disjoint contrast (cardiosphere-derived cells, Marbán lab)
        "file": "makkar-2012.abstract.txt",
        "sha256": "b6de36d79cb6846b0aa05b1b46fe544d295da422570b1c41b2019fafe433e549",
    },
    # --- poldermans (DECREASE / perioperative beta-blockade) case (dev/cairn#15). PubMed abstracts. ---
    "poldermans-1999": {  # DECREASE-I
        "file": "poldermans-1999.abstract.txt",
        "sha256": "078de8baccf8bd05765227d6a94f921b7c8ea7d84c7d3c288b2786e990435450",
    },
    "boersma-2001": {  # the DECREASE screening-cohort JAMA paper
        "file": "boersma-2001.abstract.txt",
        "sha256": "c8c8e0db90698dc587017e296b8be5a8f470fdfb4837fd3ee7b877aaa84996a2",
    },
    "dunkelgrun-2009": {  # DECREASE-IV
        "file": "dunkelgrun-2009.abstract.txt",
        "sha256": "d2c47de80ed89f0832d0e702e40b2ead222176f33fe211f01ab5e5f009f419b4",
    },
    "devereaux-2008": {  # POISE — the upstream-disjoint contrast RCT
        "file": "devereaux-2008.abstract.txt",
        "sha256": "47b8b5836b57355623771bf7f0b02bc72bb46592af1683072790bcc2a1e62d1a",
    },
    "bouri-2014": {  # the DECREASE-excluded "secure trials" meta — the published sign-flip
        "file": "bouri-2014.abstract.txt",
        "sha256": "8a502e70f5980eee457e6c6a8fa875bfbcb4f3edf1154822813a0fa46ace66ba",
    },
}


# src-<record slug> -> key into SOURCES (used to bind grounding.source_sha256)
_SHA_KEYS = {
    "src-ellis-2008": "ellis",
    "src-giddings-mangano-2008": "giddings-mangano",
    "src-jaffe-2000": "jaffe",
    "src-hu-1999": "hu-1999",
    "src-drouin-chartier-2020": "drouin-chartier-2020",
    "src-djousse-2008": "djousse-2008",
    "src-rong-2013": "rong-2013",
    "src-godos-2021": "godos-2021",
    "src-lesne-2006": "lesne-2006",
    "src-lesne-2013": "lesne-2013",
    "src-sherman-2011": "sherman-2011",
    "src-shankar-2008": "shankar-2008",
    # ivermectin / Anversa / Poldermans backtest cases (dev/cairn#15)
    "src-bryant-2021": "bryant-2021",
    "src-zein-2021": "zein-2021",
    "src-kory-2021": "kory-2021",
    "src-reis-2022": "reis-2022",
    "src-hill-2021": "hill-2021",
    "src-beltrami-2003": "beltrami-2003",
    "src-bearzi-2007": "bearzi-2007",
    "src-bolli-2011": "bolli-2011",
    "src-makkar-2012": "makkar-2012",
    "src-poldermans-1999": "poldermans-1999",
    "src-boersma-2001": "boersma-2001",
    "src-dunkelgrun-2009": "dunkelgrun-2009",
    "src-devereaux-2008": "devereaux-2008",
    "src-bouri-2014": "bouri-2014",
}


def load_excerpt(slug: str) -> str:
    text = (SRC / SOURCES[slug]["file"]).read_text(encoding="utf-8")
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert got == SOURCES[slug]["sha256"], f"{slug} excerpt sha mismatch: {got}"
    return text


def mk(slug, type_, assertion, derived_from=None, method="assert"):
    rec = envelope.new_record(
        type_, assertion, minted_by=KEY.label, method=method,
        derived_from=derived_from or [], at=AT,
    )
    envelope.sign(rec, KEY)
    errs = envelope.validate(rec)
    assert not errs, (slug, errs)
    return rec


def span_of(excerpt: str, quote: str) -> list[int]:
    i = excerpt.find(quote)
    assert i >= 0, f"quote is not a literal substring of the source excerpt: {quote[:60]!r}..."
    return [i, i + len(quote)]


def mk_claim(recs, slug, *, text, subject, source_slug, excerpt, quote, label, rung, lr=None,
             extractor=EXTRACTOR_F3, also_derived_from=(), polarity=None):
    """Mint a span-grounded claim (the generic helper the floor-#3 cases use).

    ``also_derived_from`` carries *extra* non-independence edges beyond the source
    the claim is grounded in — e.g. a shared load-bearing premise. It is what the
    layer-(a) detector intersects over.

    ``lr=None`` mints a claim with NO ``illustrative_LR``. That is deliberate for
    *structural* claims — the ones whose job is to evidence a derivedFrom edge with
    bytes (e.g. "this meta-analysis lists the NHS/HPFS cohorts in its Table 1").
    They are evidence ABOUT the DAG, not evidential lines to be combined, and
    `cairn frechet` selects only claims carrying an ``illustrative_LR``, so they are
    correctly excluded from any combination.
    """
    assertion = {
        "text": text,
        "subject": recs[subject]["id"],
        "grounding": {
            "source": recs[source_slug]["id"],
            "char_span": span_of(excerpt, quote),
            "quote": quote,
            "extractor": extractor,
            "entailment_label": label,
            "source_sha256": SOURCES[_SHA_KEYS[source_slug]]["sha256"],
        },
        "verification": rung,
    }
    if lr is not None:
        # demo-only naive-baseline input (not a vetted quantity)
        assertion["illustrative_LR"] = lr
    if polarity:
        assertion["polarity"] = polarity
    derived = [recs[source_slug]["id"]] + [recs[s]["id"] for s in also_derived_from]
    recs[slug] = mk(slug, "epi:Claim", assertion, derived_from=derived, method="extract")
    return recs[slug]

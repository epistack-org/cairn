"""Mint the vetted COVID-HSM mini-corpus as signed, span-grounded Cairn records.

VETTED corpus (roadmap A1). Unlike the earlier illustrative fixtures, every claim
is **span-grounded to a real, retrieved source** and carries the faithfulness
tuple ``(source_doc, char_span, extractor, entailment_label)`` (internal research notes
toolchest/02; internal notes:122). No record sits at ``unverified-fixture``.

Sources: the byte-exact **abstracts** (version of record) of Worobey 2022 and
Pekar 2022 ship as raw artifacts under ``fixtures/sources/*.abstract.txt`` and are
pinned by SHA-256 below. They were retrieved first-party and confirmed
byte-identical across two independent services (NCBI E-utilities efetch + Europe
PMC REST); see ``fixtures/PROVENANCE.md`` for the full retrieval record, the
Trust-Ladder rung rationale, and two honest vetting decisions (an ungrounded
"ascertainment centroid" line was retired; the two-lineages claim was reworded to
what the abstract entails).

Structural point (REPORT section 7): the proximity trio all derive from ONE
paper (Worobey) -> not three independent votes -> REFUSE-TO-COMBINE; the molecular
two-lineages line (Pekar) is a genuinely different upstream -> COMBINABLE.

Deterministic: fixed signing seed + fixed timestamps => stable Trusty URIs.
Self-verifying: asserts grounding resolves + trio refuses + contrast combines.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from cairn import envelope, grounding, provenance
from cairn.keys import SigningKey

OUT = Path(__file__).resolve().parent
SRC = OUT / "sources"
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
}


def load_excerpt(slug: str) -> str:
    text = (SRC / SOURCES[slug]["file"]).read_text(encoding="utf-8")
    got = hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert got == SOURCES[slug]["sha256"], f"{slug} excerpt sha mismatch: {got}"
    return text


# --- The worked examples (floor deliverable #3) -------------------------------------
#
# Each case DECLARES its structure here, and `main()` mechanically verifies the
# declaration against what the provenance detector actually finds before writing a
# single file. A case whose `laundered_set` fails to REFUSE, or whose shared upstream
# is not the one the detector names, fails the build. The README's "3 worked examples"
# is therefore a checked property of the corpus, not a sentence in a markdown file.
#
# `n_eff_corpus_scale` records what the Phase-2 corpus run measured for the same crux
# at 2,261-paper scale. It is a REPORTED number for the writeup,
# not an input to anything here — the fixtures stay substrate-free by construction.
CASES = {
    "covid-origins": {
        "title": "COVID origins — the Huanan-market proximity trio",
        "crux": "Did SARS-CoV-2 emerge via zoonotic spillover associated with the Huanan "
                "Seafood Wholesale Market, as opposed to a non-market or non-zoonotic "
                "introduction?",
        "battery": "assessment/probes.json",
        "shared_upstream": "src-worobey-2022",
        "shared_upstream_kind": "one paper / one author collective; at the data layer two of the "
                                "three (geographic clustering, environmental sampling) descend from "
                                "the same market-anchored PRC early-case investigation, and the third "
                                "(live-mammal sales, Xiao 2021) does not",
        "laundered_set": [
            "claim-geographic-clustering",
            "claim-environmental-sampling",
            "claim-live-mammal-sales",
        ],
        # Worobey 2022 x Pekar 2022 was the entry's false COMBINABLE. On the honest DAG the
        # pair REFUSES: Pekar cites Worobey (ref [39], first-person) and calibrates its clock
        # on Worobey 2021, and both rest on the PRC early-case investigation. The naive
        # document-level DAG (fixtures/naive/) still COMBINES them — that contrast IS the demo.
        "contrast_pair": ["claim-geographic-clustering", "claim-two-lineages"],
        "contrast_expected": "REFUSE-TO-COMBINE",
        "punchline": "Three apparently independent lines of proximity evidence come from ONE paper "
                     "by ONE author collective (Worobey 2022); at the data layer two of the three "
                     "descend from the same market-anchored PRC early-case investigation, and the "
                     "third (Xiao 2021) does not. The naive transcript multiplies 5x5x5 = 125:1; the "
                     "provenance intersection collapses to a single upstream, so the product is undefined.",
    },
    "eggs-good-for-you": {
        "title": "Are eggs good for you — the egg/CVD meta-analyses",
        "crux": "Do the several apparently independent meta-analyses finding no association "
                "between egg consumption and cardiovascular disease constitute independent "
                "confirmations of that null result?",
        "battery": "assessment/probes-eggs.json",
        "shared_upstream": "ent-nhs-hpfs-cohorts",
        "shared_upstream_kind": "cohort (one shared participant backbone, TWO HOPS UP)",
        "laundered_set": [
            "claim-eggs-rong-no-association",     # BMJ 2013 meta-analysis
            "claim-eggs-godos-no-association",    # Eur J Nutr 2021 meta-analysis (39 studies)
            "claim-eggs-drouin-no-association",   # BMJ 2020 cohorts + updated meta-analysis
        ],
        "contrast_pair": ["claim-eggs-hu-no-association", "claim-eggs-djousse-no-association"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Three apparently independent reassuring findings — a 2013 BMJ "
                     "dose-response meta-analysis, a 2021 meta-analysis of 39 studies and "
                     "'nearly 2 million individuals', and a 2020 BMJ three-cohort study plus "
                     "updated meta-analysis — all re-pool the SAME nurses and health "
                     "professionals (NHS/HPFS). Each review de-duplicates internally and is "
                     "locally correct; the laundering happens BETWEEN them, at the aggregation "
                     "layer. 'Nearly 2 million individuals' is not 2 million independent people. "
                     "The shared upstream is invisible at the claim level — it is two hops up, "
                     "found only by walking the DAG.",
        "exercises": "the TRANSITIVE shared-ancestor detector — the first real corpus to do so "
                     "(previously proven only against a synthetic fixture in tests)",
    },
    "cern-black-hole": {
        "title": "CERN black hole — the LHC/RHIC safety assurances",
        # The crux is deliberately CONDITIONAL, and that precision is load-bearing.
        # The safety literature runs two distinct argument families:
        #   (A) theoretical — microscopic black holes evaporate (Hawking radiation);
        #   (B) empirical  — the cosmic-ray / astronomical-survival argument.
        # Family (A) is a genuinely separate line (the 2003 LHC Safety Study Group rests
        # its black-hole conclusion on it), so "every assurance shares one premise" would
        # be an OVERCLAIM and we do not make it. But the public concern — and the reason
        # the 2008 reviews were commissioned — is precisely "what if the black hole does
        # NOT decay?". Conditional on (A) failing, everything left standing is (B), and
        # (B) is one argument. That is the crux this case scores.
        "crux": "IF microscopic black holes produced at the LHC do not decay (i.e. conditional "
                "on the Hawking-radiation argument failing), do the collider-safety reviews "
                "constitute multiple INDEPENDENT lines of evidence that they are still harmless?",
        "battery": "assessment/probes-cern.json",
        "shared_upstream": "ent-cosmic-ray-argument",
        "shared_upstream_kind": "premise (one load-bearing empirical argument)",
        "laundered_set": [
            "claim-cern-astro-stability",     # Ellis et al. 2008 (LSAG) — LHC
            "claim-cern-wd-ns-bound",         # Giddings & Mangano 2008 — LHC
            "claim-cern-moon-strangelet",     # Jaffe et al. 2000 — RHIC
        ],
        # The genuine COMBINABLE (#6): the Hawking-radiation evaporation line (QFT premise) and
        # the white-dwarf/neutron-star survival bound (Giddings & Mangano, premised on stable
        # black holes — i.e. on Hawking FAILING) are upstream-disjoint by construction. A hostile
        # reader cannot break it: the papers themselves build the WD/NS argument to survive the
        # failure of the Hawking premise.
        "contrast_pair": ["claim-cern-hawking-evaporation", "claim-cern-wd-ns-bound"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Three safety assurances that look maximally independent — three papers, "
                     "two accelerators, three author teams, eight years apart, three different "
                     "hypothetical catastrophes — all reach 'safe' through ONE premise: cosmic "
                     "rays have hit astronomical bodies harder for billions of years and they "
                     "are still here. Each paper says so in its own abstract. This is the case "
                     "with the STRONGEST expert consensus, and cairn prices it honestly "
                     "(effective independence ~1) rather than rewarding it. It does NOT say the "
                     "LHC is unsafe — it says three assurances sharing a premise are not three votes.",
    },
    "amyloid-abeta56": {
        "title": "Alzheimer's amyloid — the Aβ*56 corroboration cascade",
        # The crux is deliberately NARROW. It is NOT "is the amyloid hypothesis true" and NOT
        # "do soluble Aβ oligomers impair memory" (the contrast line answers YES to a version of
        # that). It is about ONE specific claimed molecular species and whether its repeated
        # "confirmations" are independent.
        "crux": "Do the multiple reports of Aβ*56 — a specific 56-kDa soluble amyloid-β "
                "assembly — as a discrete, memory-impairing species constitute independent "
                "confirmations that this species exists and is pathogenic?",
        "battery": "assessment/probes-amyloid.json",
        "shared_upstream": "ent-abeta56",
        "shared_upstream_kind": "a lab-defined molecular species + its detection assay whose sole "
                                "originating characterization is one paper — Lesné et al. 2006 "
                                "(Nature), RETRACTED in 2024 — carried forward by the same lab "
                                "(Ashe/Lesné, U Minnesota). A shared foundational-result AND "
                                "shared-reagent upstream at once.",
        "laundered_set": [
            "claim-abeta56-impairs-memory",     # Lesné 2006 (Nature, RETRACTED) — the origin, in mice
            "claim-abeta56-human-brain",        # Lesné 2013 (Brain) — Aβ*56 measured in human brain
            "claim-abeta56-detection-method",   # Sherman & Lesné 2011 — the Aβ*56 detection assay itself
        ],
        # The genuine COMBINABLE: Shankar et al. 2008 (Nat Med, Selkoe lab) isolated soluble Aβ
        # DIMERS directly from human Alzheimer's brain — a different species, a different lab, a
        # different preparation, upstream-disjoint from the Aβ*56 lineage. Pairing an Aβ*56 line
        # with it COMBINES: the general "soluble Aβ oligomers are synaptotoxic" claim has support
        # that does NOT route through Lesné 2006. That is the whole point of shipping the contrast
        # — the refusal is about corroboration-COUNTING for one species, not about the hypothesis.
        "contrast_pair": ["claim-abeta56-impairs-memory", "claim-shankar-dimers"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Aβ*56 became one of the most-cited soluble-oligomer results in the field. But "
                     "the species was defined in exactly one paper (Lesné 2006), by one lab, using "
                     "one detection assay; the human-brain measurement (Lesné 2013) and the "
                     "methods paper (Sherman 2011) are the SAME lab operationalizing the SAME "
                     "originating characterization — not two more independent confirmations. In "
                     "2024 Nature RETRACTED the 2006 paper over image-integrity concerns; the "
                     "corroboration cascade did not un-happen when it did. cairn refuses to count "
                     "three reports of Aβ*56 as three independent votes and names the shared "
                     "upstream. It does NOT say Aβ oligomers are harmless — the Shankar 2008 "
                     "human-brain dimer line is upstream-disjoint and COMBINES.",
        "exercises": "a shared upstream that is simultaneously a foundational RESULT and a "
                     "shared REAGENT/ASSAY, with the originating source formally RETRACTED after "
                     "the fact — the sharpest real-world 'the anchor moved and the citations "
                     "didn't' exhibit in the corpus",
    },
}


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


def build_cern(recs: dict[str, dict]) -> None:
    """Worked example #3 — "will the LHC create a black hole that destroys the Earth".

    The laundered-corroboration structure (VERIFIED against the real literature, not
    assumed — see fixtures/PROVENANCE-cern.md):

    Three safety assurances that look maximally independent — **three different
    papers, two different accelerators (RHIC 2000, LHC 2008), three different author
    teams, eight years apart, three different hypothetical catastrophes (strangelets,
    black holes, vacuum decay)** — all reach their reassuring conclusion through **one**
    load-bearing empirical premise: *cosmic rays have bombarded astronomical bodies at
    higher energies for billions of years, and those bodies are still here.*

    Each paper says so **in its own abstract**, so the shared-premise edge is
    span-grounded, not asserted by us (`cairn ground` re-checks the exact bytes):

      * Ellis et al. 2008 (the LSAG report): "The stability of astronomical bodies
        indicates that such collisions cannot be dangerous."
      * Giddings & Mangano 2008: black holes from cosmic rays hitting "much denser white
        dwarfs and neutron stars would then catalyze their decay on timescales
        incompatible with their known lifetimes".
      * Jaffe et al. 2000 (RHIC): "the continued existence of the Moon ... despite
        billions of years of cosmic ray exposure, provides powerful empirical evidence".

    -> `cairn intersect` REFUSES the trio, naming `ent-cosmic-ray-argument`.

    This is the sharpest test of the thesis: it is the case with the *strongest* expert
    consensus, and cairn prices that consensus honestly (effective independence ~1)
    instead of rewarding it. **It does not say the LHC is unsafe** — it says you may not
    multiply three assurances that share a premise as though they were three votes.

    The contrast (COMBINABLE): Jaffe's *theoretical* black-hole production estimate
    ("absurdly small") does NOT route through cosmic rays — it is a particle-physics
    rate calculation. Disjoint upstream -> combining IS licensed.
    """
    ellis = load_excerpt("ellis")
    gm = load_excerpt("giddings-mangano")
    jaffe = load_excerpt("jaffe")

    # --- the shared load-bearing premise (the noun the three assurances all lean on) ---
    recs["ent-cosmic-ray-argument"] = mk(
        "ent-cosmic-ray-argument", "epi:Entity",
        {
            "name": "The cosmic-ray / astronomical-stability safety argument",
            "aliases": ["the cosmic-ray argument", "the astrophysical survival bound"],
            "kind": "Premise",
            "statement": "Cosmic rays have bombarded the Earth, Sun, Moon, white dwarfs "
                         "and neutron stars at centre-of-mass energies at or above those "
                         "of collider experiments for billions of years; those bodies "
                         "still exist; therefore such collisions are not catastrophic.",
            "note": "This is the load-bearing empirical premise shared by the LHC and RHIC "
                    "safety assurances. Each citing paper invokes it in its own abstract, "
                    "so every derivedFrom edge into this node is span-grounded (see the "
                    "claims' grounding.quote). It is a PREMISE, not a dataset — the "
                    "generalization of layer-(a): a shared upstream need not be a shared "
                    "corpus, it can be a shared argument.",
            "verification": "L1",
        },
    )

    # --- Sources (L1 observed artifacts: retrieved from arXiv, sha-pinned) ---
    recs["src-ellis-2008"] = mk(
        "src-ellis-2008", "epi:Source",
        {
            "title": "Review of the Safety of LHC Collisions",
            "authors": "Ellis J, Giudice G, Mangano ML, Tkachev I, Wiedemann U "
                       "(the CERN LHC Safety Assessment Group, LSAG)",
            "venue": "Journal of Physics G: Nuclear and Particle Physics",
            "year": 2008, "volume": "35", "issue": "11", "pages": "115004",
            "doi": "10.1088/0954-3899/35/11/115004",
            "arxiv": "0806.3414",
            "url": "https://arxiv.org/abs/0806.3414",
            "excerpt_kind": "abstract (arXiv v1, whitespace-normalized)",
            "excerpt": ellis,
            "excerpt_sha256": SOURCES["ellis"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "arXiv Atom API (export.arxiv.org/api/query?id_list=0806.3414); "
                          "whitespace-normalized (' '.join(text.split())); bibliographic "
                          "record independently confirmed via Crossref (DOI/title/journal/pages)",
                "cross_verified": "bibliographic only — see note",
                "cross_verification_note": "INSPIRE-HEP serves a byte-identical abstract but "
                                           "declares its source as 'arXiv', so it MIRRORS the "
                                           "same upstream and is NOT an independent witness to "
                                           "the text. We record that rather than claim two "
                                           "agreeing services: it is the very error this engine "
                                           "exists to catch. Crossref confirms the bibliographic "
                                           "record but deposits no abstract text (IOP).",
                "sources": [
                    "https://export.arxiv.org/api/query?id_list=0806.3414",
                    "https://api.crossref.org/works/10.1088/0954-3899/35/11/115004",
                ],
            },
            "verification": "L1",
            "role": "the LSAG safety assurance — note it is ONE document, though popular "
                    "accounts sometimes cite 'the LSAG report' and 'Ellis et al. (2008)' as "
                    "two independent reviews; they are the same paper by the same five authors",
            "declares_derivation_from": {
                "what": "the 2003 LHC Safety Study Group report",
                "quote": "we review their 2003 analysis in light of additional experimental "
                         "results and theoretical understanding, which enable us to confirm, "
                         "update and extend the conclusions of the LHC Safety Study Group",
                "note": "the source itself states it is an UPDATE of the 2003 report, not an "
                        "independent re-derivation — a second, self-declared non-independence edge",
            },
        },
        method="ingest",
    )
    recs["src-giddings-mangano-2008"] = mk(
        "src-giddings-mangano-2008", "epi:Source",
        {
            "title": "Astrophysical implications of hypothetical stable TeV-scale black holes",
            "authors": "Giddings SB, Mangano MM",
            "venue": "Physical Review D",
            "year": 2008, "volume": "78", "pages": "035009",
            "doi": "10.1103/PhysRevD.78.035009",
            "arxiv": "0806.3381",
            "url": "https://arxiv.org/abs/0806.3381",
            "excerpt_kind": "abstract (arXiv v1, whitespace-normalized)",
            "excerpt": gm,
            "excerpt_sha256": SOURCES["giddings-mangano"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "arXiv Atom API (id_list=0806.3381); whitespace-normalized; "
                          "bibliographic record confirmed via Crossref",
                "cross_verified": "bibliographic only — INSPIRE mirrors arXiv (see src-ellis-2008)",
                "sources": [
                    "https://export.arxiv.org/api/query?id_list=0806.3381",
                    "https://api.crossref.org/works/10.1103/PhysRevD.78.035009",
                ],
            },
            "verification": "L1",
            "role": "the paper that PATCHES the hole in the cosmic-ray argument (LHC black "
                    "holes would be slow-moving, unlike cosmic-ray ones that pass through "
                    "Earth) by extending it to white dwarfs and neutron stars",
            "author_overlap_note": "M. L. Mangano is an author of BOTH this paper and "
                                   "src-ellis-2008 (the LSAG review that leans on it). That is "
                                   "an independent, author-level non-independence signal on top "
                                   "of the shared premise.",
        },
        method="ingest",
    )
    recs["src-jaffe-2000"] = mk(
        "src-jaffe-2000", "epi:Source",
        {
            "title": 'Review of speculative "disaster scenarios" at RHIC',
            "authors": "Jaffe RL, Busza W, Sandweiss J, Wilczek F",
            "venue": "Reviews of Modern Physics",
            "year": 2000, "volume": "72", "pages": "1125-1140",
            "doi": "10.1103/RevModPhys.72.1125",
            "arxiv": "hep-ph/9910333",
            "url": "https://arxiv.org/abs/hep-ph/9910333",
            "excerpt_kind": "abstract (arXiv, whitespace-normalized)",
            "excerpt": jaffe,
            "excerpt_sha256": SOURCES["jaffe"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "arXiv Atom API (id_list=hep-ph/9910333); whitespace-normalized; "
                          "bibliographic record confirmed via Crossref",
                "cross_verified": "bibliographic only — INSPIRE mirrors arXiv (see src-ellis-2008)",
                "sources": [
                    "https://export.arxiv.org/api/query?id_list=hep-ph/9910333",
                    "https://api.crossref.org/works/10.1103/RevModPhys.72.1125",
                ],
            },
            "verification": "L1",
            "role": "a DIFFERENT accelerator (RHIC), a DIFFERENT author team, eight years "
                    "earlier, a DIFFERENT catastrophe (strangelets) — and the same premise",
        },
        method="ingest",
    )

    cra = "ent-cosmic-ray-argument"

    # --- The OTHER safety argument family: theoretical black-hole evaporation (Hawking
    #     radiation). This is a genuinely SEPARATE premise from the cosmic-ray/astrophysical
    #     survival argument — QFT in curved spacetime, not an astronomical observation. It is
    #     the premise the 2008 reviews were commissioned to interrogate ("what if it does NOT
    #     decay?"), and the WD/NS bound (Giddings & Mangano) is the backstop built to survive
    #     its failure. So {Hawking evaporation} and {WD/NS survival} are upstream-disjoint by
    #     construction — the genuine COMBINABLE (dev/cairn / GATE #6). ---
    recs["ent-hawking-radiation-premise"] = mk(
        "ent-hawking-radiation-premise", "epi:Entity",
        {
            "name": "The Hawking-radiation black-hole-evaporation premise",
            "aliases": ["Hawking radiation", "the black-hole evaporation argument", "the theoretical safety leg"],
            "kind": "Premise",
            "statement": "Any microscopic black hole produced at the LHC evaporates via Hawking "
                         "radiation (trans-horizon particle creation; QFT in curved spacetime) "
                         "before it can accrete, so it poses no danger.",
            "note": "This is the THEORETICAL safety leg (LHC Safety Study Group 2003 rests its "
                    "black-hole conclusion on it). It is upstream-DISJOINT from the "
                    "cosmic-ray/astrophysical-survival premise (ent-cosmic-ray-argument): one is "
                    "quantum field theory, the other is an astronomical observation. Giddings & "
                    "Mangano 2008 deliberately assume THIS premise fails (stable black holes) and "
                    "derive safety anyway from the white-dwarf/neutron-star bound — which is why "
                    "the two legs are genuinely combinable rather than redundant.",
            "verification": "L1",
        },
    )

    # --- The three "independent" safety assurances (each leans on the SAME premise) ---
    mk_claim(
        recs, "claim-cern-astro-stability",
        text="The LHC safety review concludes that the collisions cannot be dangerous "
             "because astronomical bodies subjected to higher-energy cosmic-ray collisions "
             "are still standing.",
        subject=cra, source_slug="src-ellis-2008", excerpt=ellis,
        quote="The stability of astronomical bodies indicates that such collisions cannot be dangerous.",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-lhc-safety",
        also_derived_from=[cra],
    )
    mk_claim(
        recs, "claim-cern-wd-ns-bound",
        text="Stable TeV-scale black holes that could accrete the Earth on sub-solar "
             "timescales are ruled out, because cosmic-ray-produced black holes would "
             "already have destroyed white dwarfs and neutron stars.",
        subject=cra, source_slug="src-giddings-mangano-2008", excerpt=gm,
        quote="black holes produced by cosmic rays impinging on much denser white dwarfs "
              "and neutron stars would then catalyze their decay on timescales incompatible "
              "with their known lifetimes",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-lhc-safety",
        also_derived_from=[cra],
    )
    mk_claim(
        recs, "claim-cern-moon-strangelet",
        text="Dangerous strangelet production is ruled out empirically, because the Moon "
             "has survived billions of years of cosmic-ray exposure.",
        subject=cra, source_slug="src-jaffe-2000", excerpt=jaffe,
        quote="the continued existence of the Moon, in the form we know it, despite billions "
              "of years of cosmic ray exposure, provides powerful empirical evidence against "
              "the possibility of dangerous strangelet production",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-lhc-safety",
        also_derived_from=[cra],
    )

    # --- The genuine COMBINABLE partner (#6): the Hawking-radiation evaporation line.
    #     Grounded byte-for-byte in the LSAG abstract; derives from the Hawking premise, NOT
    #     from the cosmic-ray argument. {this} x {claim-cern-wd-ns-bound} share no upstream. ---
    mk_claim(
        recs, "claim-cern-hawking-evaporation",
        text="Microscopic black holes produced at the LHC are expected to evaporate via Hawking "
             "radiation before they reach the detector walls, so they never accrete.",
        subject="ent-hawking-radiation-premise", source_slug="src-ellis-2008", excerpt=ellis,
        quote="Any microscopic black holes produced at the LHC are expected to decay by Hawking "
              "radiation before they reach the detector walls.",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-lhc-safety",
        also_derived_from=["ent-hawking-radiation-premise"],
    )

    # --- The contrast: a genuinely INDEPENDENT line (theory, not cosmic rays) ---
    mk_claim(
        recs, "claim-cern-bh-production-rate",
        text="The theoretical production rate for black holes in heavy-ion collisions is "
             "negligible ('absurdly small') on particle-physics grounds alone.",
        subject=cra, source_slug="src-jaffe-2000", excerpt=jaffe,
        quote="We estimate the parameters relevant to black hole production; we find that "
              "they are absurdly small.",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-lhc-safety",
        # NOTE: deliberately NO edge to ent-cosmic-ray-argument. This line is a rate
        # calculation; it does not lean on the astrophysical survival bound. Attaching the
        # premise edge at the *paper* level would over-attribute and manufacture a shared
        # upstream that is not there — the precise sin this engine exists to catch.
    )


def build_eggs(recs: dict[str, dict]) -> None:
    """Worked example #2 — "are eggs good for you" (egg consumption and CVD risk).

    The laundered-corroboration structure (VERIFIED against the real literature — and
    the verification CHANGED the hypothesis; see fixtures/PROVENANCE-eggs.md):

    The hypothesis we set out to test was "the meta-analyses sloppily double-count the
    same cohorts inside their own pooled estimates". **That is false, and we do not claim
    it.** The careful reviews state explicit de-duplication rules (Godos: "If more than
    one study was conducted on the same cohort, only the dataset including the larger
    number of individuals ... "), and one 2022 review explicitly *finds and removes*
    participant overlap. No within-review double-count is proven anywhere, and asserting
    one would be a fabrication.

    The real structure is subtler and worse. The laundering is **between** reviews, at the
    aggregation layer:

        ent-nhs-hpfs-cohorts          <-- the shared participant backbone (the root)
              ^                    ^
        src-hu-1999      src-drouin-chartier-2020      (same nurses/professionals,
        (NHS+HPFS, 1999)  (NHS+NHS II+HPFS, 2020)       nested follow-up windows)
              ^                    ^
              |                    |
        src-rong-2013        src-godos-2021             (two "independent" meta-analyses
        (BMJ, 8 articles)    (Eur J Nutr, 39 studies,    that BOTH re-pool that backbone —
                              "nearly 2 million")         each says so in its own Table 1)

    Every actor is *locally* correct. Each review de-duplicates internally. The failure
    emerges only in composition: three apparently independent reassuring findings — a 2013
    BMJ dose-response meta-analysis, a 2021 meta-analysis of 39 studies and "nearly 2
    million individuals", and a 2020 BMJ three-cohort study + updated meta-analysis — all
    rest on the same nurses and health professionals. "Nearly 2 million individuals" is not
    2 million independent people. Reading five agreeing meta-analyses as five confirmations
    counts one cohort backbone five times.

    That makes this the *sophisticated* exhibit, and a harder one than COVID: there is no
    villain, no error to point at in any single paper, and the shared upstream is invisible
    at the claim level — it is **two hops up**, discoverable only by walking the DAG. It is
    the first real corpus to exercise cairn's transitive shared-ancestor detector (which
    until now was proven only against a synthetic fixture in tests/test_provenance.py).

    GROUNDING NOTE (the material limitation, recorded not hidden): the meta-analyses do NOT
    name their constituent cohorts in their abstracts — those edges exist ONLY in Table 1.
    So the source_doc for the two reviews is the abstract **plus the complete, unedited
    included-studies table**, extracted deterministically from the Europe PMC open-access
    JATS XML. A1 explicitly anticipated this extension ("a future L4 version grounded to
    the open-access PMC full text is a clean extension"). The inclusion edges are therefore
    evidenced by bytes (`cairn ground`), not asserted by us.

    The contrast (COMBINABLE): Hu 1999 (NHS+HPFS) and Djoussé 2008 (Physicians' Health
    Study) are two primary analyses of **disjoint participant pools**. Different people,
    different upstream -> combining IS licensed. (Mirrors Worobey-vs-Pekar.)
    """
    hu = load_excerpt("hu-1999")
    drouin = load_excerpt("drouin-chartier-2020")
    djousse = load_excerpt("djousse-2008")
    rong = load_excerpt("rong-2013")
    godos = load_excerpt("godos-2021")

    # --- the two participant pools (the nouns the primary studies analyse) ---
    recs["ent-nhs-hpfs-cohorts"] = mk(
        "ent-nhs-hpfs-cohorts", "epi:Entity",
        {
            "name": "The Nurses' Health Study + Health Professionals Follow-up Study cohorts",
            "aliases": ["NHS", "HPFS", "NHS/HPFS", "the shared cohort backbone"],
            "kind": "Cohort",
            "note": "The shared participant backbone of the egg-CVD literature. Hu 1999, "
                    "Bernstein 2012 and Drouin-Chartier 2020 are analyses of THE SAME PEOPLE "
                    "over nested follow-up windows (Drouin-Chartier's NHS coronary cases "
                    "contain Hu's). Both major meta-analyses re-pool them. This node is what "
                    "the provenance intersection collapses to.",
            "verification": "L1",
        },
    )
    recs["ent-phs-cohort"] = mk(
        "ent-phs-cohort", "epi:Entity",
        {
            "name": "The Physicians' Health Study I cohort",
            "aliases": ["PHS", "PHS I"],
            "kind": "Cohort",
            "note": "A genuinely DISJOINT participant pool (21,327 male physicians) — the "
                    "contrast referent. Independence on the provenance dimension really does "
                    "hold between this and NHS/HPFS.",
            "verification": "L1",
        },
    )

    # --- the primary cohort analyses (each derives from a participant pool) ---
    recs["src-hu-1999"] = mk(
        "src-hu-1999", "epi:Source",
        {
            "title": "A prospective study of egg consumption and risk of cardiovascular "
                     "disease in men and women",
            "authors": "Hu FB, Stampfer MJ, Rimm EB, et al. (12 authors)",
            "venue": "JAMA", "year": 1999, "volume": "281", "issue": "15", "pages": "1387-1394",
            "doi": "10.1001/jama.281.15.1387", "pmid": "10217054",
            "excerpt_kind": "abstract (structured; one labelled section per line)",
            "excerpt": hu, "excerpt_sha256": SOURCES["hu-1999"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "NCBI E-utilities efetch (PMID 10217054); AbstractText sections "
                          "serialized as 'LABEL: text', one per line",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=10217054&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the canonical NHS+HPFS egg-CVD analysis — pooled as an input by BOTH "
                    "downstream meta-analyses",
        },
        derived_from=[recs["ent-nhs-hpfs-cohorts"]["id"]], method="ingest",
    )
    recs["src-drouin-chartier-2020"] = mk(
        "src-drouin-chartier-2020", "epi:Source",
        {
            "title": "Egg consumption and risk of cardiovascular disease: three large "
                     "prospective US cohort studies, systematic review, and updated meta-analysis",
            "authors": "Drouin-Chartier JP, Chen S, Li Y, et al. (10 authors)",
            "venue": "BMJ", "year": 2020, "volume": "368", "pages": "m513",
            "doi": "10.1136/bmj.m513", "pmid": "32132002", "pmcid": "PMC7190072",
            "excerpt_kind": "abstract (structured; one labelled section per line)",
            "excerpt": drouin, "excerpt_sha256": SOURCES["drouin-chartier-2020"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "NCBI E-utilities efetch (PMID 32132002)",
                "encoding_note": "the BMJ abstract uses U+2009 THIN SPACE as the digit-group "
                                 "separator ('83 349' is '83\\u2009349'). The raw bytes are "
                                 "pinned as retrieved; a naive re-typing of these numbers "
                                 "would silently fail the span check.",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=32132002&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "SIMULTANEOUSLY a primary NHS/NHS-II/HPFS analysis AND a meta-analysis "
                    "pooling 33 risk estimates — it is both a node and an aggregator, which "
                    "is exactly how the same participants re-enter the evidence base twice",
        },
        derived_from=[recs["ent-nhs-hpfs-cohorts"]["id"]], method="ingest",
    )
    recs["src-djousse-2008"] = mk(
        "src-djousse-2008", "epi:Source",
        {
            "title": "Egg consumption in relation to cardiovascular disease and mortality: "
                     "the Physicians' Health Study",
            "authors": "Djoussé L, Gaziano JM",
            "venue": "American Journal of Clinical Nutrition", "year": 2008,
            "volume": "87", "issue": "4", "pages": "964-969",
            "doi": "10.1093/ajcn/87.4.964", "pmid": "18400720", "pmcid": "PMC2386667",
            "excerpt_kind": "abstract (structured; one labelled section per line)",
            "excerpt": djousse, "excerpt_sha256": SOURCES["djousse-2008"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "NCBI E-utilities efetch (PMID 18400720)",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=18400720&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "a DISJOINT participant pool (PHS) — the combinable contrast",
        },
        derived_from=[recs["ent-phs-cohort"]["id"]], method="ingest",
    )

    # --- the two "independent" meta-analyses (each re-pools the same backbone) ---
    # derivedFrom is not asserted: each edge is evidenced, byte-for-byte, by a
    # claim grounded in that review's own Table 1 (see the structural claims below).
    recs["src-rong-2013"] = mk(
        "src-rong-2013", "epi:Source",
        {
            "title": "Egg consumption and risk of coronary heart disease and stroke: "
                     "dose-response meta-analysis of prospective cohort studies",
            "authors": "Rong Y, Chen L, Zhu T, et al. (9 authors)",
            "venue": "BMJ", "year": 2013, "volume": "346", "pages": "e8539",
            "doi": "10.1136/bmj.e8539", "pmid": "23295181", "pmcid": "PMC3538567",
            "excerpt_kind": "abstract + Table 1 (included studies), complete and unedited",
            "excerpt": rong, "excerpt_sha256": SOURCES["rong-2013"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "abstract via NCBI E-utilities efetch (PMID 23295181); Table 1 via "
                          "Europe PMC open-access JATS XML (PMC3538567), extracted "
                          "deterministically: cells whitespace-normalized and joined with "
                          "' | ', rows with newlines. The COMPLETE table ships — trimming "
                          "rows to the convenient ones would be cherry-picking.",
                "encoding_note": "Table 1 uses U+2019 RIGHT SINGLE QUOTATION MARK in "
                                 "“Nurses’ Health Study”; the ASCII apostrophe "
                                 "would not match.",
                "sources": [
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=23295181&rettype=abstract&retmode=xml",
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC3538567/fullTextXML",
                ],
            },
            "verification": "L1",
            "role": "meta-analysis #1 — presents as independent evidence; its Table 1 lists "
                    "Hu 1999 (NHS + HPFS) and Djoussé 2008 (PHS) as pooled inputs",
        },
        derived_from=[recs["src-hu-1999"]["id"], recs["src-djousse-2008"]["id"]],
        method="aggregate",
    )
    recs["src-godos-2021"] = mk(
        "src-godos-2021", "epi:Source",
        {
            "title": "Egg consumption and cardiovascular risk: a dose-response meta-analysis "
                     "of prospective cohort studies",
            "authors": "Godos J, Micek A, Brzostek T, et al. (10 authors)",
            "venue": "European Journal of Nutrition", "year": 2021,
            "volume": "60", "issue": "4", "pages": "1833-1862",
            "doi": "10.1007/s00394-020-02345-7", "pmid": "32865658", "pmcid": "PMC8137614",
            "excerpt_kind": "abstract + Table 1 (included studies), complete and unedited",
            "excerpt": godos, "excerpt_sha256": SOURCES["godos-2021"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-13",
                "method": "abstract via NCBI E-utilities efetch (PMID 32865658); Table 1 via "
                          "Europe PMC open-access JATS XML (PMC8137614), same deterministic "
                          "extraction as src-rong-2013",
                "sources": [
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=32865658&rettype=abstract&retmode=xml",
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8137614/fullTextXML",
                ],
            },
            "verification": "L1",
            "role": "meta-analysis #2 — 39 studies, 'nearly 2 million individuals'. Its Table 1 "
                    "lists Hu 1999, Drouin-Chartier 2020 AND Djoussé 2008. The headline scale "
                    "is not a headcount of independent people.",
            "honest_note": "Godos states an explicit de-duplication rule, so we do NOT claim it "
                           "double-counts internally. The non-independence is BETWEEN reviews, "
                           "not inside this one.",
        },
        derived_from=[
            recs["src-hu-1999"]["id"],
            recs["src-drouin-chartier-2020"]["id"],
            recs["src-djousse-2008"]["id"],
        ],
        method="aggregate",
    )

    cohorts = "ent-nhs-hpfs-cohorts"

    # --- The three "independent" reassuring findings (the laundered set) ---
    mk_claim(
        recs, "claim-eggs-rong-no-association",
        text="A dose-response meta-analysis of prospective cohort studies (BMJ 2013) finds "
             "that eating up to one egg per day is not associated with increased risk of "
             "coronary heart disease or stroke.",
        subject=cohorts, source_slug="src-rong-2013", excerpt=rong,
        quote="Higher consumption of eggs (up to one egg per day) is not associated with "
              "increased risk of coronary heart disease or stroke.",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-eggs-benign",
    )
    mk_claim(
        recs, "claim-eggs-godos-no-association",
        text="A dose-response meta-analysis of 39 studies covering nearly 2 million "
             "individuals (Eur J Nutr 2021) finds no conclusive evidence that eggs raise "
             "cardiovascular disease risk.",
        subject=cohorts, source_slug="src-godos-2021", excerpt=godos,
        quote="There is no conclusive evidence on the role of egg in CVD risk",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-eggs-benign",
    )
    mk_claim(
        recs, "claim-eggs-drouin-no-association",
        text="Three large prospective US cohorts plus an updated meta-analysis of 33 risk "
             "estimates (BMJ 2020) find that an extra egg per day is not associated with "
             "cardiovascular disease risk.",
        subject=cohorts, source_slug="src-drouin-chartier-2020", excerpt=drouin,
        quote="an increase of one egg per day was not associated with cardiovascular disease risk",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-eggs-benign",
    )

    # --- The STRUCTURAL claims: they evidence the derivedFrom edges with bytes. ---
    # No illustrative_LR: these are evidence ABOUT the DAG, not lines to be combined.
    mk_claim(
        recs, "claim-eggs-rong-pools-nhs-hpfs",
        text="The BMJ 2013 meta-analysis lists Hu 1999's Nurses' Health Study and Health "
             "Professionals Follow-up Study analyses among its pooled input studies.",
        subject=cohorts, source_slug="src-rong-2013", excerpt=rong,
        quote="Hu et al36 | 1999 | Nurses’ Health Study | USA | Female",
        label="ENTAILS", rung="L5",
    )
    mk_claim(
        recs, "claim-eggs-godos-pools-nhs-hpfs",
        text="The Eur J Nutr 2021 meta-analysis lists Hu 1999 (HPFS + NHS) among its pooled "
             "input studies — the same cohort backbone the BMJ 2013 meta-analysis pools.",
        subject=cohorts, source_slug="src-godos-2021", excerpt=godos,
        quote="Hu [16] | HPFS, 1986 and NHS, 1980 (US)",
        label="ENTAILS", rung="L5",
    )
    mk_claim(
        recs, "claim-eggs-godos-pools-drouin",
        text="The Eur J Nutr 2021 meta-analysis ALSO pools Drouin-Chartier 2020, which "
             "re-analyses the same NHS/HPFS participants over a longer follow-up window — so "
             "the backbone enters this review by two separate paths.",
        subject=cohorts, source_slug="src-godos-2021", excerpt=godos,
        quote="Drouin-Chartier [48] | HPFS, 1986, NHS, 1980, NHS II, 1991 (US)",
        label="ENTAILS", rung="L5",
    )

    # --- The contrast: two primary analyses of DISJOINT participant pools ---
    mk_claim(
        recs, "claim-eggs-hu-no-association",
        text="The 1999 NHS + HPFS analysis found no significant overall association between "
             "egg consumption and coronary heart disease or stroke.",
        subject=cohorts, source_slug="src-hu-1999", excerpt=hu,
        quote="we found no evidence of an overall significant association between egg "
              "consumption and risk of CHD or stroke in either men or women",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-eggs-benign",
    )
    mk_claim(
        recs, "claim-eggs-djousse-no-association",
        text="The Physicians' Health Study I analysis (a disjoint cohort of 21,327 male "
             "physicians) found egg consumption not associated with incident myocardial "
             "infarction or stroke.",
        subject="ent-phs-cohort", source_slug="src-djousse-2008", excerpt=djousse,
        quote="Egg consumption was not associated with incident MI or stroke in a "
              "multivariate Cox regression.",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-eggs-benign",
    )


def build_amyloid(recs: dict[str, dict]) -> None:
    """Worked example #4 — the Alzheimer's Aβ*56 corroboration cascade (the decoupling spike).

    WHY THIS CASE EXISTS. The first three worked examples were co-developed with the
    engine, and we grew worried the engine had quietly been fitted to them. This case
    was added AFTER the fact, from a live scientific controversy nobody on the team had
    modelled, precisely to test whether the refusal generalizes. It does — and the two
    footguns it surfaced are recorded in fixtures/PROVENANCE-amyloid.md, not smoothed over.

    The laundered-corroboration structure (VERIFIED against real, retrieved abstracts):

        src-lesne-2006  (Nature 2006 — "Aβ*56 impairs memory"; RETRACTED 2024)
              |   the sole originating characterization of the species
              v
        ent-abeta56     <-- the shared upstream: a 56-kDa soluble Aβ assembly + its assay
              ^                         ^                          ^
              |                         |                          |
        claim-abeta56-        claim-abeta56-            claim-abeta56-
        impairs-memory        human-brain              detection-method
        (Lesné 2006, mice)    (Lesné 2013, Brain,      (Sherman & Lesné 2011 —
                               human tissue)            the detection assay ITSELF)

    Three "confirmations" that Aβ*56 is a discrete, memory-relevant species — a mouse
    causal experiment, a human-brain correlation, and a biochemical detection paper —
    that all descend from ONE lab (Ashe/Lesné) operationalizing ONE originating result.
    The human-brain paper and the methods paper are not two more independent votes; they
    are the same characterization measured again with the same assay. `cairn intersect`
    REFUSES the trio and names ent-abeta56.

    This is the sharpest real-world version of the entry's thesis — "the anchor moved and
    the citations didn't." In July 2024, Nature RETRACTED Lesné 2006 over image-integrity
    concerns (retraction: Nature 631(8019):240, 10.1038/s41586-024-07691-8). A refusal
    engine walking the provenance DAG prices the cascade at one effective source whether
    or not the retraction has landed; a reader counting agreeing papers does not.

    HONEST SCOPE LIMIT (recorded, not hidden — mirrors the eggs case). This case does NOT
    claim the amyloid hypothesis is false, and it does NOT claim soluble Aβ oligomers are
    harmless. It makes a claim about corroboration-COUNTING for ONE species. The contrast
    proves the point in the other direction: Shankar et al. 2008 (Nat Med, Selkoe lab)
    isolated soluble Aβ DIMERS directly from human Alzheimer's brain — a different species,
    lab, and preparation, upstream-disjoint from Aβ*56 — so an Aβ*56 line and the Shankar
    dimer line COMBINE. The general "soluble Aβ oligomers are synaptotoxic" claim has
    support that does not route through Lesné 2006; the *Aβ*56-specific* corroboration
    count is what is inflated.
    """
    lesne06 = load_excerpt("lesne-2006")
    lesne13 = load_excerpt("lesne-2013")
    sherman = load_excerpt("sherman-2011")
    shankar = load_excerpt("shankar-2008")

    # --- the ROOT: the origin paper. Aβ*56 was isolated and named in exactly one paper, so
    #     src-lesne-2006 is the true derivation root (derivedFrom []). RETRACTED in 2024. Every
    #     other node in the cascade routes back to it. ---
    recs["src-lesne-2006"] = mk(
        "src-lesne-2006", "epi:Source",
        {
            "title": "A specific amyloid-beta protein assembly in the brain impairs memory",
            "authors": "Lesné S, Koh MT, Kotilinek L, Kayed R, Glabe CG, Yang A, Gallagher M, Ashe KH",
            "venue": "Nature", "year": 2006, "volume": "440", "issue": "7082", "pages": "352-357",
            "doi": "10.1038/nature04533", "pmid": "16541076",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": lesne06, "excerpt_sha256": SOURCES["lesne-2006"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 16541076); AbstractText via itertext()",
                "encoding_note": "This 2006 record spells the species 'Abeta*56' (ASCII) — the "
                                 "Greek beta is NOT used here. The 2011/2013 records DO use U+03B2 "
                                 "('Aβ*56'). Quotes are pinned to each record's own bytes.",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=16541076&rettype=abstract&retmode=xml"],
            },
            "retraction": {
                "status": "RETRACTED",
                "notice": "Retraction: Nature 2024 Jul;631(8019):240 (10.1038/s41586-024-07691-8), PMID 38914864",
                "note": "Retracted in 2024 over image-integrity concerns first raised publicly in 2022 "
                        "(Schrag/Piller, Science). Recorded as a fact about the source; the refusal "
                        "does not depend on it — the trio shares this upstream regardless.",
            },
            "verification": "L1",
            "role": "the sole originating characterization of Aβ*56 — the derivation root the "
                    "cascade collapses to",
        },
        derived_from=[], method="ingest",
    )

    # --- the shared upstream node the CASE declares: the species + assay, derived from the origin
    #     paper. Downstream lines derive from THIS node (which routes to src-lesne-2006), so the
    #     collective intersection names BOTH ent-abeta56 and the retracted origin. ---
    recs["ent-abeta56"] = mk(
        "ent-abeta56", "epi:Entity",
        {
            "name": "Aβ*56 — the 56-kDa soluble amyloid-β assembly (as defined by Lesné 2006)",
            "aliases": ["Abeta*56", "Aβ*56", "Aβ star 56", "the 56-kDa Aβ oligomer"],
            "kind": "MolecularSpecies",
            "statement": "A specific 56-kilodalton soluble amyloid-β oligomer, first isolated and "
                         "named 'Aβ*56' by Lesné et al. 2006, and detected thereafter by the same "
                         "laboratory's multistep-fractionation assay. Its originating "
                         "characterization is a single paper, now retracted.",
            "note": "The shared upstream of the Aβ*56 corroboration cascade, and an unusual one: it "
                    "is BOTH a foundational RESULT (the 2006 isolation) and a shared REAGENT/ASSAY "
                    "(the same lab's detection method). Every downstream Aβ*56 measurement "
                    "presupposes this node, so every derivedFrom edge into it is span-grounded by "
                    "the citing abstract naming 'Aβ*56'/'Abeta*56'. It is the generalization of "
                    "the CERN premise node: a shared upstream can be a shared measurement apparatus, "
                    "not only a shared dataset or argument. NOTE the retraction (2024) is a fact "
                    "ABOUT this node's originating source, not an input to the refusal — cairn "
                    "refuses on the shared-provenance topology whether or not the paper is retracted.",
            "verification": "L1",
        },
        derived_from=[recs["src-lesne-2006"]["id"]],
    )

    # --- the disjoint contrast species: human-brain Aβ dimers (Selkoe/Walsh), a different root ---
    recs["ent-human-brain-dimers"] = mk(
        "ent-human-brain-dimers", "epi:Entity",
        {
            "name": "Soluble Aβ dimers isolated directly from human Alzheimer's brain",
            "aliases": ["human-brain Aβ dimers", "the Selkoe/Walsh dimers"],
            "kind": "MolecularSpecies",
            "statement": "Soluble amyloid-β dimers extracted directly from the cerebral cortex of "
                         "human subjects with Alzheimer's disease (Shankar et al. 2008), shown to "
                         "impair synaptic plasticity and memory.",
            "note": "A genuinely DISJOINT upstream from Aβ*56: a different species (dimers, not the "
                    "56-kDa assembly), a different laboratory (Selkoe/Walsh, Harvard/Dublin), a "
                    "different preparation (direct human-brain extraction, not Tg2576 mice), and no "
                    "derivation from the Lesné 2006 characterization. Independence on the provenance "
                    "dimension really does hold between this and ent-abeta56 — which is why the "
                    "contrast COMBINES.",
            "verification": "L1",
        },
        derived_from=[],
    )
    recs["src-lesne-2013"] = mk(
        "src-lesne-2013", "epi:Source",
        {
            "title": "Brain amyloid-β oligomers in ageing and Alzheimer's disease",
            "authors": "Lesné SE, Sherman MA, Grant M, Kuskowski M, Schneider JA, Bennett DA, Ashe KH",
            "venue": "Brain", "year": 2013, "volume": "136", "issue": "Pt 5", "pages": "1383-1398",
            "doi": "10.1093/brain/awt062", "pmid": "23576130",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": lesne13, "excerpt_sha256": SOURCES["lesne-2013"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 23576130); AbstractText via itertext() "
                          "(U+03B2 rendered as the literal Greek beta)",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=23576130&rettype=abstract&retmode=xml"],
            },
            "errata": [
                "Erratum: Brain 2022 Aug 27;145(8):e72-e76 (10.1093/brain/awac143) — image corrections",
            ],
            "verification": "L1",
            "role": "the human-brain Aβ*56 measurement — same senior author (Ashe) and same species "
                    "as Lesné 2006; a re-measurement of the SAME characterization, not an "
                    "independent line",
            "author_overlap_note": "Kathleen H. Ashe (senior) and Sarah/Stéphane Lesné are authors of "
                                   "BOTH this and src-lesne-2006; Michael A. Sherman is shared with "
                                   "src-sherman-2011 — a lab-level non-independence on top of the "
                                   "shared species.",
        },
        derived_from=[recs["ent-abeta56"]["id"]], method="ingest",
    )
    recs["src-sherman-2011"] = mk(
        "src-sherman-2011", "epi:Source",
        {
            "title": "Detecting Aβ*56 oligomers in brain tissues",
            "authors": "Sherman MA, Lesné SE",
            "venue": "Methods in Molecular Biology", "year": 2011, "volume": "670", "pages": "45-56",
            "doi": "10.1007/978-1-60761-744-0_4", "pmid": "20967582",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": sherman, "excerpt_sha256": SOURCES["sherman-2011"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 20967582); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=20967582&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the Aβ*56 detection ASSAY itself — this is the shared reagent. A methods paper "
                    "describing 'our biochemical approach' to isolate Aβ*56 is not an independent "
                    "confirmation that Aβ*56 is real; it is the instrument by which the other two "
                    "lines were measured.",
        },
        derived_from=[recs["ent-abeta56"]["id"]], method="ingest",
    )
    recs["src-shankar-2008"] = mk(
        "src-shankar-2008", "epi:Source",
        {
            "title": "Amyloid-beta protein dimers isolated directly from Alzheimer's brains impair "
                     "synaptic plasticity and memory",
            "authors": "Shankar GM, Li S, Mehta TH, Garcia-Munoz A, Shepardson NE, Smith I, "
                       "Brett FM, Farrell MA, Rowan MJ, Lemere CA, Regan CM, Walsh DM, "
                       "Sabatini BL, Selkoe DJ",
            "venue": "Nature Medicine", "year": 2008, "volume": "14", "issue": "8", "pages": "837-842",
            "doi": "10.1038/nm1782", "pmid": "18568035",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": shankar, "excerpt_sha256": SOURCES["shankar-2008"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 18568035); AbstractText via itertext() "
                          "(this record spells the peptide 'Abeta', ASCII)",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
                            "?db=pubmed&id=18568035&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the genuinely INDEPENDENT line (the combinable contrast) — human-brain Aβ dimers "
                    "from a different lab, species, and preparation; disjoint upstream from Aβ*56",
        },
        derived_from=[recs["ent-human-brain-dimers"]["id"]], method="ingest",
    )

    ab56 = "ent-abeta56"

    # --- The three "independent" Aβ*56 confirmations (the laundered set) ---
    # NOTE the deliberate ASCII 'Abeta*56' in this first quote vs. the Greek 'Aβ*56' below —
    # the bytes differ per source record and the span check is byte-exact.
    mk_claim(
        recs, "claim-abeta56-impairs-memory",
        text="Aβ*56, a 56-kDa soluble amyloid-β assembly purified from the brains of "
             "memory-impaired Tg2576 mice, disrupts memory when administered to young rats.",
        subject=ab56, source_slug="src-lesne-2006", excerpt=lesne06,
        quote="Abeta*56 purified from the brains of impaired Tg2576 mice disrupts memory "
              "when administered to young rats",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-abeta56-pathogenic",
        extractor=EXTRACTOR_AMYLOID, also_derived_from=[ab56],
    )
    mk_claim(
        recs, "claim-abeta56-human-brain",
        text="In cognitively intact human brain tissue, Aβ*56 levels correlate positively "
             "with two pathological forms of soluble tau — a human-tissue corroboration that "
             "Aβ*56 is a pathogenically relevant species.",
        subject=ab56, source_slug="src-lesne-2013", excerpt=lesne13,
        quote="we found strong positive correlations between Aβ*56 and two pathological forms "
              "of soluble tau",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-abeta56-pathogenic",
        extractor=EXTRACTOR_AMYLOID, also_derived_from=[ab56],
    )
    mk_claim(
        recs, "claim-abeta56-detection-method",
        text="A 56-kDa Aβ oligomer, termed Aβ*56, is identified by the laboratory's "
             "multistep-fractionation assay and its abundance correlates with cognitive "
             "impairment — the shared method by which Aβ*56 is measured.",
        subject=ab56, source_slug="src-sherman-2011", excerpt=sherman,
        quote="we identified a 56 kDa oligomer of Aβ, termed Aβ*56, the amount of which "
              "correlates with cognitive impairment",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-abeta56-pathogenic",
        extractor=EXTRACTOR_AMYLOID, also_derived_from=[ab56],
    )

    # --- The contrast: a genuinely INDEPENDENT synaptotoxic-oligomer line (disjoint upstream) ---
    mk_claim(
        recs, "claim-shankar-dimers",
        text="Soluble amyloid-β dimers isolated directly from human Alzheimer's brain potently "
             "impair synapse structure and function — a synaptotoxic species characterized "
             "independently of Aβ*56.",
        subject="ent-human-brain-dimers", source_slug="src-shankar-2008", excerpt=shankar,
        quote="soluble Abeta oligomers extracted from Alzheimer's disease brains potently impair "
              "synapse structure and function and that dimers are the smallest synaptotoxic species",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-oligomer-toxicity",
        extractor=EXTRACTOR_AMYLOID, also_derived_from=["ent-human-brain-dimers"],
    )


def main() -> int:
    worobey_abstract = load_excerpt("worobey")
    pekar_abstract = load_excerpt("pekar")
    recs: dict[str, dict] = {}

    # --- Sources (the upstreams) — L1 Observed artifact: fetched + hashed + cross-verified ---
    recs["src-worobey-2022"] = mk(
        "src-worobey-2022", "epi:Source",
        {
            "title": "The Huanan Seafood Wholesale Market in Wuhan was the early "
                     "epicenter of the COVID-19 pandemic",
            "authors": "Worobey M, et al. (18 authors)",
            "venue": "Science", "year": 2022,
            "volume": "377", "issue": "6609", "pages": "951-959",
            "doi": "10.1126/science.abp8715",
            "pmid": "35881010", "pmcid": "PMC9348750",
            "published": "2022-08-26", "online_first": "2022-07-26",
            "url": "https://www.science.org/doi/10.1126/science.abp8715",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": worobey_abstract,
            "excerpt_sha256": SOURCES["worobey"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-04",
                "method": "NCBI E-utilities efetch (PMID 35881010) + Europe PMC REST; "
                          "byte-identical cross-check; publisher HTML was paywalled (403)",
                "cross_verified": True,
                "sources": [
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=35881010&rettype=abstract&retmode=xml",
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%2210.1126/science.abp8715%22&resultType=core&format=json",
                ],
            },
            "errata": [
                "Erratum: Science 2024 Mar 15;383(6688):eadp1133 (10.1126/science.adp1133) "
                "— does not alter the abstract text used here",
            ],
            "verification": "L1",
            "role": "the early-case dataset shared by the proximity trio",
        },
        method="ingest",
    )
    recs["src-pekar-2022"] = mk(
        "src-pekar-2022", "epi:Source",
        {
            "title": "The molecular epidemiology of multiple zoonotic origins of "
                     "SARS-CoV-2",
            "authors": "Pekar JE, et al. (29 authors)",
            "venue": "Science", "year": 2022,
            "volume": "377", "issue": "6609", "pages": "960-966",
            "doi": "10.1126/science.abp8337",
            "pmid": "35881005", "pmcid": "PMC9348752",
            "published": "2022-08-26", "online_first": "2022-07-26",
            "url": "https://www.science.org/doi/10.1126/science.abp8337",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": pekar_abstract,
            "excerpt_sha256": SOURCES["pekar"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-04",
                "method": "NCBI E-utilities efetch (PMID 35881005) + Europe PMC REST; "
                          "byte-identical cross-check; publisher HTML was paywalled (403)",
                "cross_verified": True,
                "sources": [
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=35881005&rettype=abstract&retmode=xml",
                    "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1126/science.abp8337&resultType=core&format=json",
                ],
            },
            "errata": [
                "Erratum (10.1126/science.adl0585) corrects overestimated Bayes factors "
                "from a coding error; the two-introductions conclusion stands",
            ],
            "verification": "L1",
            "role": "a genuinely distinct (molecular) upstream",
        },
        method="ingest",
    )

    # --- The shared DATASET root: the market-anchored PRC early-case investigation. ---
    # Worobey 2022's spatial line rests on the WHO-China joint report's Dec-2019 line list
    # (174 Hubei cases -> 164 Wuhan -> 155 coordinates re-digitised from maps in the report);
    # its environmental line rests on the China-CDC 22-Jan-2020 market sampling. Both are one
    # non-replicable, single-team investigation. Stansifer certifies its non-replicability in
    # his own decision: "cannot be independently verified or duplicated." (COVID-DOSSIER.md
    # Appendix B / §2.2). It is the data-layer upstream two of the three proximity lines share.
    recs["ent-prc-early-case-investigation"] = mk(
        "ent-prc-early-case-investigation", "epi:Entity",
        {
            "name": "The market-anchored PRC early-case investigation (Dec 2019 - Feb 2021)",
            "aliases": ["WHO-China joint report Dec-2019 line list", "China-CDC Huanan market sampling",
                        "the early-case record"],
            "kind": "Investigation",
            "statement": "The retrospective early-case record assembled by China CDC / Wuhan CDC and "
                         "the WHO-China joint mission: the December-2019 Hubei line list (174 cases -> "
                         "164 Wuhan -> 155 map-extracted coordinates) and the 22-Jan-2020 China-CDC "
                         "Huanan-market environmental sampling campaign.",
            "note": "A single-team, non-replicable investigation and the shared data-layer upstream of "
                    "the geographic-clustering and environmental-sampling lines. NOT an upstream of the "
                    "live-mammal-sales line, which descends from Xiao 2021 (a 2017-2019 pre-outbreak "
                    "animal survey). Judge Stansifer, independently: it 'cannot be independently verified "
                    "or duplicated.'",
            "verification": "L1",
        },
    )
    # --- Worobey 2021: the index-case re-analysis Pekar's molecular clock calibrates on. ---
    recs["src-worobey-2021"] = mk(
        "src-worobey-2021", "epi:Source",
        {
            "title": "Dissecting the early COVID-19 cases in Wuhan",
            "authors": "Worobey M",
            "venue": "Science", "year": 2021, "volume": "374", "issue": "6572", "pages": "1202-1204",
            "doi": "10.1126/science.abm4454", "pmid": "34793199",
            "verification": "L1",
            "role": "the earliest-case re-analysis (the 10-Dec-2019 market-vendor index case) that "
                    "Pekar 2022's molecular-clock calibration rests on — a calibration edge coupling "
                    "Pekar to the Worobey line",
            "note": "Bibliographic record confirmed via NCBI E-utilities (PMID 34793199 -> DOI "
                    "10.1126/science.abm4454). Itself a re-analysis of the same early-case record.",
        },
        derived_from=[recs["ent-prc-early-case-investigation"]["id"]], method="ingest",
    )
    # --- The one AUTHOR node (kept deliberately to one sentence; see AUTHOR-OVERLAP-SPIKE). ---
    recs["ent-author-chris-newman"] = mk(
        "ent-author-chris-newman", "epi:Entity",
        {
            "name": "Chris Newman",
            "kind": "Person",
            "statement": "Chris Newman is a co-author of both Xiao et al. 2021 (the animal-sales survey) "
                         "and Worobey et al. 2022 (author 9 of 18).",
            "note": "The single genuinely author-specific finding in the COVID case: the one proximity "
                    "leg that is data-independent of Worobey 2022 (live-mammal sales, via Xiao 2021) "
                    "still shares a human with it. One sentence, not a case study — a shared author is a "
                    "defeasible prior on shared pipeline, NOT a refusal gate (it would wrongly refuse "
                    "ATLAS/CMS, and we ship a CERN case). Recorded as an identity node, not a "
                    "derivedFrom edge, so provenance is not conflated with attribution.",
            "verification": "L1",
        },
    )
    # --- Xiao 2021: the pre-outbreak animal survey the live-mammal line actually descends from. ---
    recs["src-xiao-2021"] = mk(
        "src-xiao-2021", "epi:Source",
        {
            "title": "Animal sales from Wuhan wet markets immediately prior to the COVID-19 pandemic",
            "authors": "Xiao X, Newman C, Buesching CD, Macdonald DW, Zhou ZM",
            "venue": "Scientific Reports", "year": 2021, "volume": "11", "pages": "11898",
            "doi": "10.1038/s41598-021-91470-2",
            "verification": "L1",
            "role": "the 2017-2019 monthly animal-sales survey (collected to trace SFTS, before the "
                    "outbreak) that Worobey 2022's live-mammal-sales line rests on — the one proximity "
                    "leg that is data-INDEPENDENT of the PRC early-case investigation",
            "author_overlap_note": "Co-author Chris Newman (ent-author-chris-newman) is also author 9 of "
                                   "18 on Worobey et al. 2022: data-independent, not author-independent.",
        },
    )

    # --- Entities (nouns, referenced by claims via Trusty URI; identity records) ---
    recs["ent-hsm-cluster"] = mk(
        "ent-hsm-cluster", "epi:Cluster",
        {
            "name": "Huanan Seafood Market early-case cluster",
            "aliases": ["HSM cluster", "the proximity trio"],
            "kind": "EvidenceCluster", "geo": "Wuhan, Jianghan District",
            "note": "the three proximity lines about this cluster share one upstream",
        },
    )
    recs["ent-fcs"] = mk(
        "ent-fcs", "epi:Entity",
        {
            "name": "SARS-CoV-2 furin cleavage site",
            "aliases": ["FCS", "S1/S2 polybasic cleavage site"],
            "kind": "GenomicFeature",
            "note": "the lab-leak-side crux entity; contrast referent",
        },
    )
    hsm = recs["ent-hsm-cluster"]["id"]
    worobey = recs["src-worobey-2022"]["id"]
    pekar = recs["src-pekar-2022"]["id"]
    worobey_sha = SOURCES["worobey"]["sha256"]
    pekar_sha = SOURCES["pekar"]["sha256"]

    def claim(slug, text, source_id, source_text, source_sha, quote, label, rung, lr,
              extra_derived=(), note=None):
        span = span_of(source_text, quote)
        assertion = {
            "text": text,
            "subject": hsm,
            "polarity": "supports-zoonosis",
            "illustrative_LR": lr,  # demo-only naive-baseline input (not a vetted quantity)
            "grounding": {
                "source": source_id,
                "char_span": span,
                "quote": quote,
                "extractor": EXTRACTOR,
                "entailment_label": label,
                "source_sha256": source_sha,
            },
            "verification": rung,
        }
        if note:
            assertion["provenance_note"] = note
        # grounding.source stays first (the grounding invariant needs it in derivedFrom);
        # extra_derived carries the honest data/citation/calibration edges beyond it.
        recs[slug] = mk(
            slug, "epi:Claim", assertion,
            derived_from=[source_id] + list(extra_derived), method="extract",
        )

    prc = recs["ent-prc-early-case-investigation"]["id"]   # shared data-layer root
    worobey_2021 = recs["src-worobey-2021"]["id"]           # Pekar's clock calibration source
    xiao = recs["src-xiao-2021"]["id"]                      # the data-independent leg's real upstream

    # --- The proximity trio (all extracted from Worobey 2022; two of three ALSO descend, at
    #     the data layer, from the market-anchored PRC early-case investigation). ---
    claim(
        "claim-geographic-clustering",
        "The earliest known December-2019 COVID-19 cases were geographically centered "
        "on the Huanan market, including cases with no reported direct market link.",
        worobey, worobey_abstract, worobey_sha,
        "the earliest known COVID-19 cases from December 2019, including those without "
        "reported direct links, were geographically centered on this market",
        "ENTAILS", "L5", 5.0,
        extra_derived=[prc],
        note="the spatial line rests on the WHO-China Dec-2019 line list (155 map-extracted "
             "coordinates) — the market-anchored PRC early-case investigation.",
    )
    claim(
        "claim-environmental-sampling",
        "Within the Huanan market, SARS-CoV-2-positive environmental samples were "
        "spatially associated with stalls selling live mammals.",
        worobey, worobey_abstract, worobey_sha,
        "within the market, SARS-CoV-2-positive environmental samples were spatially "
        "associated with vendors selling live mammals",
        "SUPPORTS", "L4", 5.0,
        extra_derived=[prc],
        note="the environmental line rests on the China-CDC 22-Jan-2020 Huanan-market sampling "
             "— the same PRC early-case investigation.",
    )
    claim(
        "claim-live-mammal-sales",
        "Live SARS-CoV-2-susceptible mammals were sold at the Huanan market in late 2019.",
        worobey, worobey_abstract, worobey_sha,
        "live SARS-CoV-2-susceptible mammals were sold at the market in late 2019",
        "ENTAILS", "L5", 5.0,
        extra_derived=[xiao],
        note="the honest exception: this line descends from Xiao 2021 (a 2017-2019 pre-outbreak "
             "animal survey), which is data-INDEPENDENT of the PRC early-case investigation. "
             "It is not author-independent, though (ent-author-chris-newman).",
    )

    # --- The molecular line (Pekar 2022) — NOT disjoint from the Worobey line on the honest DAG.
    #     Pekar cites Worobey 2022 (ref [39], first-person: "In a related study, we show...") and
    #     calibrates its molecular clock on Worobey 2021's market-vendor index case. Those are
    #     real citation + calibration edges (COVID-DOSSIER.md §2.4). Modeled on the claim because
    #     the source records are frozen (their Trusty URIs are pinned by the assessment layer). ---
    claim(
        "claim-two-lineages",
        "SARS-CoV-2's early genomic diversity comprised two distinct lineages (A and B) "
        "that resulted from at least two separate zoonotic (cross-species) transmission "
        "events into humans.",
        pekar, pekar_abstract, pekar_sha,
        'We show that SARS-CoV-2 genomic diversity before February 2020 likely comprised '
        'only two distinct viral lineages, denoted "A" and "B." Phylodynamic rooting '
        'methods, coupled with epidemic simulations, reveal that these lineages were the '
        'result of at least two separate cross-species transmission events into humans.',
        "ENTAILS", "L4", 4.0,
        extra_derived=[worobey, worobey_2021],
        note="inherits Pekar 2022's dependence on Worobey 2022 (citation ref [39], the market-link "
             "result imported as a premise) and on Worobey 2021 (the index case the molecular clock "
             "is calibrated on). This is why {geographic-clustering, two-lineages} REFUSES on the "
             "honest DAG though the naive document-level DAG (fixtures/naive/) COMBINES it.",
    )

    # --- the other worked examples (floor deliverable #3, dev/cairn#9) ---
    build_eggs(recs)
    build_cern(recs)
    # --- the 4th worked example: the decoupling spike (Alzheimer's Aβ*56 cascade) ---
    build_amyloid(recs)

    # --- self-verify before writing: every case's declared structure must actually hold ---
    store = {r["id"]: r for r in recs.values()}
    report = grounding.check_store(store)
    assert report["ok"], ("grounding failed", report["failed"])

    for case_id, case in CASES.items():
        laundered = [recs[s]["id"] for s in case["laundered_set"]]
        v = provenance.combine_verdict(laundered, store)
        assert v["verdict"] == "REFUSE-TO-COMBINE", (case_id, "laundered set did not refuse", v)
        # The declared upstream must be shared by EVERY line, not merely by some pair —
        # that is the actual claim each case makes, so check the collective intersection.
        collective = provenance.shared_upstreams(laundered, store)["collective_shared"]
        shared = recs[case["shared_upstream"]]["id"]
        assert shared in collective, (
            case_id, "the declared shared upstream is not shared by ALL lines",
            case["shared_upstream"], [r for r in collective])
        if case.get("contrast_pair"):
            pair = [recs[s]["id"] for s in case["contrast_pair"]]
            cv = provenance.combine_verdict(pair, store)
            want = case.get("contrast_expected", "COMBINABLE")
            assert cv["verdict"] == want, (case_id, f"contrast pair verdict != {want}", cv)

    # --- the GATE assertion, inverted (dev/cairn / flf-contest#5): Worobey 2022 x Pekar 2022
    #     was the entry's false COMBINABLE. On the honest (derived) DAG it MUST refuse, and the
    #     shared upstream it names must include Worobey 2022 (the citation edge) and the PRC
    #     early-case investigation (the shared dataset). This is the heart of the fix. ---
    wxp = provenance.combine_verdict(
        [recs["claim-geographic-clustering"]["id"], recs["claim-two-lineages"]["id"]], store)
    assert wxp["verdict"] == "REFUSE-TO-COMBINE", ("Worobey x Pekar must REFUSE on the honest DAG", wxp)
    for s in ("src-worobey-2022", "ent-prc-early-case-investigation"):
        assert recs[s]["id"] in wxp["shared_upstreams"], (
            "the honest Worobey x Pekar refusal must name the citation + dataset upstreams", s)

    # --- the genuine COMBINABLE (#6): CERN {Hawking evaporation} x {WD/NS survival}. ---
    cern_combine = provenance.combine_verdict(
        [recs["claim-cern-hawking-evaporation"]["id"], recs["claim-cern-wd-ns-bound"]["id"]], store)
    assert cern_combine["verdict"] == "COMBINABLE", ("CERN Hawking x WD/NS must COMBINE", cern_combine)

    # --- the CERN CONCLUSION-UNCHANGED refusal (#7): the trio shares the cosmic-ray premise, but
    #     the WD/NS bound is upstream-disjoint from the Hawking premise and independently sufficient. ---
    cern_trio = [recs[s]["id"] for s in CASES["cern-black-hole"]["laundered_set"]]
    cern_as_indep = provenance.combine_verdict(
        cern_trio, store,
        backstop=recs["claim-cern-wd-ns-bound"]["id"],
        at_risk_upstream=recs["ent-hawking-radiation-premise"]["id"])
    assert cern_as_indep["verdict"] == "REFUSE-TO-COMBINE-AS-INDEPENDENT", cern_as_indep
    assert cern_as_indep["conclusion_unchanged"] is True, cern_as_indep

    # --- write one file per record + an index + the case manifest ---
    index = {}
    for slug, rec in recs.items():
        (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        index[slug] = rec["id"]
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2) + "\n")
    (OUT / "CASES.json").write_text(json.dumps(CASES, indent=2, ensure_ascii=False) + "\n")

    # --- the NAIVE document-level snapshot: the SAME two claims and sources, but with the
    #     dataset/citation/calibration edges REMOVED (each claim derives only from the paper it
    #     was extracted from). This is the cautionary run: on this DAG Worobey x Pekar COMBINES,
    #     exactly as the entry originally (wrongly) shipped. `cairn intersect` on it vs on the
    #     honest corpus above IS the contestability demo (flf-contest#5). Reproducible:
    #        cairn intersect "fixtures/naive/*.json" --claims claim-geographic-clustering claim-two-lineages   # COMBINABLE
    #        cairn intersect "fixtures/*.json"       --claims claim-geographic-clustering claim-two-lineages   # REFUSE
    naive_dir = OUT / "naive"
    naive_dir.mkdir(exist_ok=True)
    naive = {}
    # the two sources, document-level (byte-identical to the honest corpus — sources never carried
    # cross-edges; only the claims did)
    for s in ("src-worobey-2022", "src-pekar-2022"):
        naive[s] = recs[s]
    # the two claims, stripped back to derivedFrom == [grounding.source] (no dataset/citation edge)
    for s in ("claim-geographic-clustering", "claim-two-lineages"):
        a = copy.deepcopy(recs[s]["assertion"])
        a.pop("provenance_note", None)
        naive[s] = mk(s, "epi:Claim", a, derived_from=[a["grounding"]["source"]], method="extract")
    naive_store = {r["id"]: r for r in naive.values()}
    nv = provenance.combine_verdict(
        [naive["claim-geographic-clustering"]["id"], naive["claim-two-lineages"]["id"]], naive_store)
    assert nv["verdict"] == "COMBINABLE", ("naive document-level DAG must still COMBINE Worobey x Pekar", nv)
    naive_index = {}
    for slug, rec in naive.items():
        (naive_dir / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        naive_index[slug] = rec["id"]
    (naive_dir / "INDEX.json").write_text(json.dumps(naive_index, indent=2) + "\n")

    print(f"minted {len(recs)} vetted records across {len(CASES)} worked examples -> {OUT}")
    print(f"  grounding: {report['grounded']}/{report['checked']} claims resolve, ok={report['ok']}")
    for case_id, case in CASES.items():
        print(f"  [{case_id}] shared upstream = {case['shared_upstream']} "
              f"-> REFUSE over {len(case['laundered_set'])} lines"
              + ("" if case.get("contrast_pair") else "  (no combinable contrast — see PROVENANCE)"))
    for slug, rid in index.items():
        print(f"  {slug:32s} {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

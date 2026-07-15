"""Case bundle builder: cern-black-hole.

Extracted from build_fixtures.py (repo-per-case refactor, Phase 2a). Mints this case's
records into the shared ``recs`` store using fixtures/lib/mint.py. Output is byte-identical
to the monolith — do not change record content without regenerating the corpus and
reviewing the golden diff (tests/test_determinism_golden.py).
"""
import sys
from pathlib import Path

_FIX = Path(__file__).resolve().parents[2]  # fixtures/
if str(_FIX) not in sys.path:
    sys.path.insert(0, str(_FIX))
from lib.mint import (  # noqa: E402
    EXTRACTOR, EXTRACTOR_AMYLOID, EXTRACTOR_BACKTEST, EXTRACTOR_F3, SOURCES,
    load_excerpt, mk, mk_claim, span_of,
)


def build(recs):
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



"""Case bundle builder: amyloid-abeta56.

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



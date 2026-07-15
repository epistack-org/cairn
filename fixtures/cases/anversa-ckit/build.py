"""Case bundle builder: anversa-ckit.

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
    """Worked example #6 — the Anversa c-kit+ cardiac stem cell regeneration cascade (dev/cairn#15).

    The amyloid node type (a lab-defined object + its isolation assay, origin source at the root)
    but with the meta-fact carried as an INSTITUTIONAL misconduct finding plus one retracted
    downstream node, rather than a retraction stamp on the origin paper.

        src-beltrami-2003  (Cell 2003 — "adult c-kit+ cardiac stem cells regenerate myocardium")
              |   the originating characterization of the cell type
              v
        ent-anversa-ckit-csc   <-- the shared upstream: the Anversa c-kit+ CSC + its isolation method
              ^                          ^                            ^
              |                          |                            |
        claim-anversa-        claim-anversa-             claim-anversa-
        origin (Beltrami      human (Bearzi 2007,        scipio (Bolli 2011,
        2003, rodent)         human cells)               Lancet, RETRACTED — SCIPIO)

    Three "confirmations" that c-kit+ cells regenerate the heart — a rodent origin, a human-cell
    paper, and a phase-1 clinical trial — that all descend from ONE laboratory's originating
    characterization and its isolation method. SCIPIO used the lab's own cell preps: a literal
    shared-reagent dependency on top of the shared characterization. Harvard and the Brigham found
    falsified/fabricated data across the lab and recommended 31 papers for retraction (2018);
    SCIPIO was retracted (Lancet 2019); a $10M False Claims Act settlement resolved the NIH-grant
    allegations (2017). `cairn intersect` REFUSES the trio and names ent-anversa-ckit-csc.

    HONEST SCOPE LIMIT. The case does NOT say the heart cannot be repaired and does NOT adjudicate
    every cell-therapy approach. The contrast proves the boundary: CADUCEUS (Makkar et al. 2012,
    Lancet) used cardiosphere-derived cells — a different cell type, a different lab (Marbán,
    Cedars-Sinai), a different preparation, upstream-disjoint from the Anversa c-kit+ line — so an
    Anversa line and the CADUCEUS line COMBINE.
    """
    beltrami = load_excerpt("beltrami-2003")
    bearzi = load_excerpt("bearzi-2007")
    bolli = load_excerpt("bolli-2011")
    makkar = load_excerpt("makkar-2012")

    # --- the ROOT: the origin paper (the c-kit+ CSC was characterized here first). NOT itself
    #     retracted — recorded honestly; the meta-fact is institutional + one retracted downstream. ---
    recs["src-beltrami-2003"] = mk(
        "src-beltrami-2003", "epi:Source",
        {
            "title": "Adult cardiac stem cells are multipotent and support myocardial regeneration",
            "authors": "Beltrami AP, Barlucchi L, Torella D, Baker M, Limana F, Chimenti S, "
                       "Kasahara H, Rota M, Musso E, Urbanek K, Leri A, Kajstura J, Nadal-Ginard B, Anversa P",
            "venue": "Cell", "year": 2003, "volume": "114", "issue": "6", "pages": "763-776",
            "doi": "10.1016/S0092-8674(03)00687-1", "pmid": "14505575",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": beltrami, "excerpt_sha256": SOURCES["beltrami-2003"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 14505575); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=14505575&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the originating characterization of the Lin(-)/c-kit(POS) cardiac stem cell — the "
                    "derivation root the cascade collapses to",
            "retraction_status_note": "This origin paper is NOT individually marked retracted on PubMed "
                                      "(as of retrieval). The case's ground truth is INSTITUTIONAL: "
                                      "Harvard Medical School and Brigham and Women's Hospital found "
                                      "falsified/fabricated data across the Anversa lab and recommended "
                                      "31 papers for retraction (2018); a $10M False Claims Act "
                                      "settlement resolved the NIH-grant allegations (2017). The refusal "
                                      "does not depend on any single retraction stamp.",
        },
        derived_from=[], method="ingest",
    )

    recs["ent-anversa-ckit-csc"] = mk(
        "ent-anversa-ckit-csc", "epi:Entity",
        {
            "name": "The Anversa-lab c-kit+ cardiac stem cell (as defined by Beltrami et al. 2003)",
            "aliases": ["c-kit+ cardiac stem cell", "Lin(-) c-kit(POS) CSC", "the Anversa CSC"],
            "kind": "CellType",
            "statement": "A resident Lin(-)/c-kit(POS) adult cardiac cell claimed to be self-renewing, "
                         "clonogenic and multipotent and to regenerate myocardium, first characterized "
                         "and named by the Anversa laboratory (Beltrami et al. 2003) and detected/"
                         "prepared thereafter by the same lab's isolation method.",
            "note": "The shared upstream of the c-kit+ CSC corroboration cascade: BOTH a foundational "
                    "RESULT (the 2003 characterization) and a shared REAGENT/METHOD (the lab's cell "
                    "isolation used downstream, including in the SCIPIO trial's cell preps). Every "
                    "downstream c-kit+ CSC measurement presupposes this node. META-FACT: Harvard/Brigham "
                    "recommended 31 Anversa-lab papers for retraction (2018) for falsified/fabricated "
                    "data; the flagship human trial SCIPIO was retracted (Lancet 2019); a $10M FCA "
                    "settlement (2017) resolved the NIH-grant allegations. The finding is INSTITUTIONAL "
                    "misconduct, not a per-node retraction stamp — cairn refuses on the shared-provenance "
                    "topology whether or not each paper has been individually retracted.",
            "verification": "L1",
        },
        derived_from=[recs["src-beltrami-2003"]["id"]],
    )

    recs["src-bearzi-2007"] = mk(
        "src-bearzi-2007", "epi:Source",
        {
            "title": "Human cardiac stem cells",
            "authors": "Bearzi C, Rota M, Hosoda T, Tillmanns J, Nascimbene A, ... Leri A, Kajstura J, Anversa P",
            "venue": "Proceedings of the National Academy of Sciences", "year": 2007, "volume": "104",
            "issue": "35", "pages": "14068-14073", "doi": "10.1073/pnas.0706760104", "pmid": "17709737",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": bearzi, "excerpt_sha256": SOURCES["bearzi-2007"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 17709737); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=17709737&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the human-cell extension — c-kit+ human CSCs isolated by the same lab's method; a "
                    "re-measurement of the SAME characterization in human tissue, not an independent line",
        },
        derived_from=[recs["ent-anversa-ckit-csc"]["id"]], method="ingest",
    )

    recs["src-bolli-2011"] = mk(
        "src-bolli-2011", "epi:Source",
        {
            "title": "Cardiac stem cells in patients with ischaemic cardiomyopathy (SCIPIO): initial "
                     "results of a randomised phase 1 trial",
            "authors": "Bolli R, Chugh AR, D'Amario D, ... Leri A, Kajstura J, Anversa P",
            "venue": "Lancet", "year": 2011, "volume": "378", "issue": "9806", "pages": "1847-1857",
            "doi": "10.1016/S0140-6736(11)61590-0", "pmid": "22088800",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": bolli, "excerpt_sha256": SOURCES["bolli-2011"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 22088800); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=22088800&rettype=abstract&retmode=xml"],
            },
            "retraction": {
                "status": "RETRACTED",
                "notice": "Retraction: Lancet 2019 Mar 16;393(10176):1084 (10.1016/S0140-6736(19)30542-2), PMID 30894259",
                "expression_of_concern": "Expression of Concern: Lancet 2014 Apr 12;383(9925):1279 (10.1016/S0140-6736(14)60608-5), PMID 24725564",
                "note": "SCIPIO used autologous c-kit+ CSCs prepared per the Anversa-lab method — a literal "
                        "shared-cell-prep dependency on ent-anversa-ckit-csc. Recorded as a fact about the "
                        "source; the refusal does not depend on it — the trial shares this upstream regardless.",
            },
            "verification": "L1",
            "role": "the clinical line — the phase-1 SCIPIO trial (RETRACTED 2019). Its cells were the "
                    "lab's own c-kit+ CSC preps: the literal shared reagent, not an independent confirmation",
        },
        derived_from=[recs["ent-anversa-ckit-csc"]["id"]], method="ingest",
    )

    # --- the disjoint contrast lineage: cardiosphere-derived cells (Marbán), a different root. ---
    recs["ent-cdc-marban"] = mk(
        "ent-cdc-marban", "epi:Entity",
        {
            "name": "Cardiosphere-derived cells (CDCs)",
            "aliases": ["CDCs", "the Marbán cardiosphere cells"],
            "kind": "CellType",
            "statement": "A distinct heart-derived cell population grown from endomyocardial biopsy "
                         "specimens as cardiospheres (Marbán laboratory), tested in the CADUCEUS trial "
                         "for regeneration after myocardial infarction.",
            "note": "A genuinely DISJOINT upstream from the Anversa c-kit+ CSC: a different cell type "
                    "(cardiosphere-derived, not sorted Lin(-)/c-kit(POS)), a different laboratory "
                    "(Marbán, Cedars-Sinai), a different preparation, and no derivation from the Beltrami "
                    "2003 characterization. Independence on the provenance dimension holds — which is why "
                    "the contrast COMBINES.",
            "verification": "L1",
        },
        derived_from=[],
    )
    recs["src-makkar-2012"] = mk(
        "src-makkar-2012", "epi:Source",
        {
            "title": "Intracoronary cardiosphere-derived cells for heart regeneration after myocardial "
                     "infarction (CADUCEUS): a prospective, randomised phase 1 trial",
            "authors": "Makkar RR, Smith RR, Cheng K, Malliaras K, ... Marbán E",
            "venue": "Lancet", "year": 2012, "volume": "379", "issue": "9819", "pages": "895-904",
            "doi": "10.1016/S0140-6736(12)60195-0", "pmid": "22336189",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": makkar, "excerpt_sha256": SOURCES["makkar-2012"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 22336189); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=22336189&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the genuinely INDEPENDENT line (the combinable contrast) — cardiosphere-derived cells "
                    "from a different lab, cell type, and preparation; disjoint upstream from the Anversa CSC",
        },
        derived_from=[recs["ent-cdc-marban"]["id"]], method="ingest",
    )

    csc = "ent-anversa-ckit-csc"
    mk_claim(
        recs, "claim-anversa-origin",
        text="Adult Lin(-)/c-kit+ cardiac stem cells, injected into an ischemic heart, reconstitute "
             "well-differentiated myocardium (Beltrami et al. 2003) — the rodent origin of the claim.",
        subject=csc, source_slug="src-beltrami-2003", excerpt=beltrami,
        quote="these cells or their clonal progeny reconstitute well-differentiated myocardium",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-ckit-regeneration",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=[csc],
    )
    mk_claim(
        recs, "claim-anversa-human",
        text="Human c-kit+ cardiac stem cells, injected into infarcted myocardium, generate a chimeric "
             "heart containing new human myocardium (Bearzi et al. 2007) — a human-tissue corroboration.",
        subject=csc, source_slug="src-bearzi-2007", excerpt=bearzi,
        quote="hCSCs generate a chimeric heart, which contains human myocardium",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-ckit-regeneration",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=[csc],
    )
    mk_claim(
        recs, "claim-anversa-scipio",
        text="In the SCIPIO phase-1 trial, intracoronary infusion of autologous c-kit+ cardiac stem "
             "cells improved left-ventricular systolic function and reduced infarct size in patients "
             "(Bolli et al. 2011) — the clinical corroboration.",
        subject=csc, source_slug="src-bolli-2011", excerpt=bolli,
        quote="intracoronary infusion of autologous CSCs is effective in improving LV systolic function "
              "and reducing infarct size",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-ckit-regeneration",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=[csc],
    )
    mk_claim(
        recs, "claim-anversa-caduceus",
        text="In the CADUCEUS trial, intracoronary infusion of cardiosphere-derived cells increased "
             "viable heart mass after myocardial infarction (Makkar et al. 2012) — a regeneration signal "
             "characterized independently of the Anversa c-kit+ line.",
        subject="ent-cdc-marban", source_slug="src-makkar-2012", excerpt=makkar,
        quote="increases in viable heart mass",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-cardiac-regeneration",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-cdc-marban"],
    )



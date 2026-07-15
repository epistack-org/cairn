"""Case bundle builder: poldermans-decrease.

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
    """Worked example #7 — the Poldermans/DECREASE perioperative beta-blocker cascade (dev/cairn#15).

    The eggs node type (a shared research program / database at the root, found without any single
    origin paper) carrying an institutional-misconduct meta-fact — and the only case in the corpus
    where the honest counterfactual REVERSES the conclusion rather than just deflating the votes.

        ent-decrease-program   (the Poldermans/Erasmus DECREASE trials + vascular-surgery database;
              ^     ^     ^      a 2011-2012 Erasmus MC investigation found FABRICATED/FICTITIOUS data)
              |     |     |
        claim-decrease-1   claim-decrease-boersma   claim-decrease-4
        (DECREASE-I,       (Boersma 2001 JAMA,      (DECREASE-IV,
        Poldermans 1999)   the screening cohort)    Dunkelgrun 2009)

    Three pro-benefit findings for perioperative beta-blockade — a landmark RCT, a large cohort, and
    a second RCT — that look like an evidence base but are ONE research program subsequently found to
    rest on fabricated data. `cairn intersect` REFUSES the trio and names ent-decrease-program.

    HONEST SCOPE LIMIT. The refusal is about corroboration-COUNTING. The contrast is the sharpest in
    the corpus: POISE (Devereaux et al. 2008, Lancet; n=8351) is a large independent RCT,
    upstream-disjoint from DECREASE — so a DECREASE benefit claim and the POISE result COMBINE. And
    once the fabricated lineage is removed, the pooled effect FLIPS SIGN: Bouri et al. 2014's
    DECREASE-excluded "secure trials" meta finds a 27% mortality INCREASE. Removing the fraud does not
    merely weaken the signal — it reverses benefit to harm.
    """
    poldermans = load_excerpt("poldermans-1999")
    boersma = load_excerpt("boersma-2001")
    dunkelgrun = load_excerpt("dunkelgrun-2009")
    devereaux = load_excerpt("devereaux-2008")
    bouri = load_excerpt("bouri-2014")

    # --- the ROOT: the compromised research program (no single origin paper; the shared apparatus). ---
    recs["ent-decrease-program"] = mk(
        "ent-decrease-program", "epi:Entity",
        {
            "name": "The Poldermans/Erasmus DECREASE perioperative beta-blocker research program",
            "aliases": ["DECREASE family of trials", "the DECREASE trials", "Erasmus MC vascular-surgery database"],
            "kind": "ResearchProgram",
            "statement": "The family of DECREASE (Dutch Echocardiographic Cardiac Risk Evaluation Applying "
                         "Stress Echocardiography) trials and the associated Erasmus MC vascular-surgery "
                         "screening database, run by the Poldermans group (1999-2011), which reported "
                         "perioperative beta-blockade sharply reduces cardiac death and myocardial infarction.",
            "note": "The shared upstream of the perioperative beta-blocker evidence base. META-FACT: a "
                    "2011-2012 Erasmus MC investigation found the DECREASE trials contained "
                    "fabricated/fictitious data (scientific misconduct); the corrective literature "
                    "(Bouri et al. 2014) treats 'the DECREASE family of trials, the bedrock of evidence "
                    "for this' as 'no longer secure'. This is an INSTITUTIONAL misconduct finding, not a "
                    "per-node retraction stamp — cairn refuses on the shared-provenance topology "
                    "regardless of which individual papers carry a retraction notice.",
            "verification": "L1",
        },
        derived_from=[],
    )
    prog = recs["ent-decrease-program"]["id"]

    for slug, excerpt, sha_key, title, authors, venue, year, doi, pmid, role in [
        ("src-poldermans-1999", poldermans, "poldermans-1999",
         "The effect of bisoprolol on perioperative mortality and myocardial infarction in high-risk "
         "patients undergoing vascular surgery",
         "Poldermans D, Boersma E, Bax JJ, Thomson IR, van de Ven LL, ... (DECREASE Study Group)",
         "New England Journal of Medicine", 1999, "10.1056/NEJM199912093412402", "10588963",
         "DECREASE-I — the landmark RCT (bisoprolol cut cardiac death/MI from 34% to 3.4%); the origin of "
         "the perioperative beta-blocker recommendation"),
        ("src-boersma-2001", boersma, "boersma-2001",
         "Predictors of cardiac events after major vascular surgery: role of clinical characteristics, "
         "dobutamine echocardiography, and beta-blocker therapy",
         "Boersma E, Poldermans D, Bax JJ, Steyerberg EW, ... (DECREASE screening cohort)",
         "JAMA", 2001, "10.1001/jama.285.14.1865", "11308400",
         "the DECREASE screening-cohort study (beta-blocker recipients had far fewer cardiac events); a "
         "hugely-cited driver of guideline adoption, from the same Erasmus/Poldermans vascular-surgery database"),
        ("src-dunkelgrun-2009", dunkelgrun, "dunkelgrun-2009",
         "Bisoprolol and fluvastatin for the reduction of perioperative cardiac mortality and myocardial "
         "infarction in intermediate-risk patients undergoing noncardiovascular surgery: a randomized "
         "controlled trial (DECREASE-IV)",
         "Dunkelgrun M, Boersma E, Schouten O, ... Poldermans D (DECREASE-IV Study Group)",
         "Annals of Surgery", 2009, "10.1097/SLA.0b013e3181b4c7e8", "19474688",
         "DECREASE-IV — the confirmatory RCT extending the benefit claim to intermediate-risk patients"),
    ]:
        recs[slug] = mk(
            slug, "epi:Source",
            {
                "title": title, "authors": authors, "venue": venue, "year": year, "doi": doi, "pmid": pmid,
                "excerpt_kind": "abstract (version of record)",
                "excerpt": excerpt, "excerpt_sha256": SOURCES[sha_key]["sha256"],
                "retrieval": {
                    "fetched_at": "2026-07-15",
                    "method": f"NCBI E-utilities efetch (PMID {pmid}); AbstractText via itertext()",
                    "sources": [f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=xml"],
                },
                "verification": "L1",
                "role": role,
            },
            derived_from=[prog], method="ingest",
        )

    # --- the disjoint contrast lineage: POISE, a large independent RCT. ---
    recs["ent-poise-trial"] = mk(
        "ent-poise-trial", "epi:Entity",
        {
            "name": "The POISE perioperative beta-blocker trial",
            "aliases": ["POISE", "PeriOperative ISchemic Evaluation"],
            "kind": "Trial",
            "statement": "A large (n=8351), multinational, placebo-controlled RCT of extended-release "
                         "metoprolol in non-cardiac surgery (Devereaux et al. 2008), independent of the "
                         "Poldermans/DECREASE program.",
            "note": "A DISJOINT upstream from the DECREASE program: a different investigator group, a "
                    "different trial, no derivation from the Erasmus database. Independence on the "
                    "provenance dimension holds — which is why the contrast COMBINES. POISE found metoprolol "
                    "cut myocardial infarction but INCREASED total mortality and stroke.",
            "verification": "L1",
        },
        derived_from=[],
    )
    recs["src-devereaux-2008"] = mk(
        "src-devereaux-2008", "epi:Source",
        {
            "title": "Effects of extended-release metoprolol succinate in patients undergoing non-cardiac "
                     "surgery (POISE trial): a randomised controlled trial",
            "authors": "Devereaux PJ, Yang H, Yusuf S, ... (POISE Study Group)",
            "venue": "Lancet", "year": 2008, "volume": "371", "issue": "9627", "pages": "1839-1847",
            "doi": "10.1016/S0140-6736(08)60601-7", "pmid": "18479744",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": devereaux, "excerpt_sha256": SOURCES["devereaux-2008"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 18479744); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=18479744&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the genuinely INDEPENDENT line (the combinable contrast) — a large RCT disjoint from "
                    "the DECREASE program; it points the OTHER way (metoprolol increased mortality)",
        },
        derived_from=[recs["ent-poise-trial"]["id"]], method="ingest",
    )

    # --- the DECREASE-excluded "secure trials" meta: the published SIGN-FLIP. ---
    recs["ent-secure-trials"] = mk(
        "ent-secure-trials", "epi:Entity",
        {
            "name": "The DECREASE-excluded 'secure trials' evidence base",
            "aliases": ["Bouri 2014 secure-trials meta"],
            "kind": "EvidenceSet",
            "statement": "The nine secure (non-DECREASE) randomised trials of perioperative beta-blockade "
                         "meta-analysed by Bouri et al. 2014, after the DECREASE family was deemed insecure.",
            "note": "Disjoint from the DECREASE program by construction (it EXCLUDES it). Its result is the "
                    "counterfactual: with the fabricated lineage removed, initiation of perioperative "
                    "beta-blockade causes a 27% INCREASE in 30-day mortality — the sign flips.",
            "verification": "L1",
        },
        derived_from=[],
    )
    recs["src-bouri-2014"] = mk(
        "src-bouri-2014", "epi:Source",
        {
            "title": "Meta-analysis of secure randomised controlled trials of beta-blockade to prevent "
                     "perioperative death in non-cardiac surgery",
            "authors": "Bouri S, Shun-Shin MJ, Cole GD, Mayet J, Francis DP",
            "venue": "Heart", "year": 2014, "volume": "100", "issue": "6", "pages": "456-464",
            "doi": "10.1136/heartjnl-2013-304262", "pmid": "23904357",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": bouri, "excerpt_sha256": SOURCES["bouri-2014"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 23904357); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=23904357&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the published sign-flip: the DECREASE-excluded 'secure trials' meta finds a 27% "
                    "mortality INCREASE — the honest counterfactual to the DECREASE benefit lineage",
        },
        derived_from=[recs["ent-secure-trials"]["id"]], method="ingest",
    )

    mk_claim(
        recs, "claim-decrease-1",
        text="DECREASE-I (Poldermans et al. 1999) reported that perioperative bisoprolol reduces death "
             "from cardiac causes and nonfatal myocardial infarction in high-risk vascular-surgery patients.",
        subject="ent-decrease-program", source_slug="src-poldermans-1999", excerpt=poldermans,
        quote="Bisoprolol reduces the perioperative incidence of death from cardiac causes and nonfatal "
              "myocardial infarction in high-risk patients",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-perioperative-betablockade",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-decrease-program"],
    )
    mk_claim(
        recs, "claim-decrease-boersma",
        text="In the Erasmus DECREASE screening cohort (Boersma et al. 2001), patients receiving "
             "beta-blockers had a lower risk of perioperative cardiac complications.",
        subject="ent-decrease-program", source_slug="src-boersma-2001", excerpt=boersma,
        quote="patients receiving beta-blockers had a lower risk of cardiac complications",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-perioperative-betablockade",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-decrease-program"],
    )
    mk_claim(
        recs, "claim-decrease-4",
        text="DECREASE-IV (Dunkelgrun et al. 2009) reported that perioperative bisoprolol significantly "
             "reduced 30-day cardiac death and nonfatal myocardial infarction in intermediate-risk patients.",
        subject="ent-decrease-program", source_slug="src-dunkelgrun-2009", excerpt=dunkelgrun,
        quote="Bisoprolol was associated with a significant reduction of 30-day cardiac death and nonfatal MI",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-perioperative-betablockade",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-decrease-program"],
    )
    # the contrast: a genuinely independent RCT (disjoint upstream), pointing the other way
    mk_claim(
        recs, "claim-poise",
        text="The POISE trial (Devereaux et al. 2008) found that perioperative metoprolol led to more "
             "deaths than placebo in patients undergoing non-cardiac surgery.",
        subject="ent-poise-trial", source_slug="src-devereaux-2008", excerpt=devereaux,
        quote="there were more deaths in the metoprolol group than in the placebo group",
        label="ENTAILS", rung="L5", polarity="refutes-perioperative-betablockade",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-poise-trial"],
    )
    # the sign-flip counterfactual (documented; not part of the laundered/contrast verdicts)
    mk_claim(
        recs, "claim-bouri-secure",
        text="Meta-analysing only the secure (non-DECREASE) trials, Bouri et al. 2014 found that "
             "initiating perioperative beta-blockade caused a 27% increase in 30-day all-cause mortality.",
        subject="ent-secure-trials", source_slug="src-bouri-2014", excerpt=bouri,
        quote="caused a 27% risk increase in 30-day all-cause mortality",
        label="ENTAILS", rung="L5", polarity="refutes-perioperative-betablockade",
        extractor=EXTRACTOR_BACKTEST, also_derived_from=["ent-secure-trials"],
    )



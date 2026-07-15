"""Case bundle builder: ivermectin-elgazzar.

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
    """Worked example #5 — the ivermectin / Elgazzar fabricated-meta-analysis cascade (dev/cairn#15).

    The highest-fan-out case in the corpus. The structure (VERIFIED against the real, retrieved
    included-study tables of each meta-analysis, Europe PMC OA):

        src-elgazzar-2020  (Research Square preprint — WITHDRAWN 2021-07-14 for fabricated data)
              |   pooled by every positive synthesis; largest weight, largest effect
        +-----+---------------------+---------------------+
        v                           v                     v
        src-bryant-2021       src-zein-2021         src-kory-2021     (three meta-analyses/reviews)
        (RR 0.38)             (RR 0.39)             (FLCCC review)
        v                           v                     v
        claim-iver-bryant     claim-iver-zein       claim-iver-kory   (the "independent" positives)

    Three syntheses reporting ivermectin roughly halves COVID-19 mortality — which reads as
    independent replication. It is not: all three POOL THE SAME single fabricated trial (Elgazzar),
    which carried the largest weight and the largest effect size in the ivermectin literature. The
    non-independence is TWO HOPS UP (claim -> meta-analysis -> Elgazzar), exactly like the eggs
    cohort backbone — but here the shared upstream is a withdrawn fraud, not a legitimate cohort.
    Each meta's inclusion of Elgazzar is byte-grounded by a `pools-elgazzar` structural claim
    (no illustrative_LR) against the study-characteristics table shipped in that meta's excerpt.

    The published counterfactual is exact: when Elgazzar was withdrawn (2021-07-14), the meta that
    had leaned on it most (Hill 2021) went null and was itself retracted. `cairn intersect` REFUSES
    the trio and names src-elgazzar-2020.

    HONEST SCOPE LIMIT (recorded, not hidden). This case does NOT say ivermectin is proven
    ineffective, and it does NOT say ivermectin research is uniformly fraudulent. It is a claim
    about corroboration-COUNTING: the positive mortality meta-analyses are not independent votes.
    The contrast proves the boundary the other way: TOGETHER (Reis et al. 2022, NEJM) is a large
    RCT that never ingested Elgazzar — upstream-disjoint — so an Elgazzar-based meta and TOGETHER
    COMBINE. TOGETHER happens to be null, and that is the point: the verdict is about
    provenance-independence, not agreement.
    """
    bryant = load_excerpt("bryant-2021")
    zein = load_excerpt("zein-2021")
    kory = load_excerpt("kory-2021")
    reis = load_excerpt("reis-2022")
    hill = load_excerpt("hill-2021")

    # --- the ROOT: the withdrawn fabricated trial. No excerpt (its "version of record" is now a
    #     withdrawal notice); it is an upstream node, not a grounding source for any claim. ---
    recs["src-elgazzar-2020"] = mk(
        "src-elgazzar-2020", "epi:Source",
        {
            "title": "WITHDRAWN: Efficacy and Safety of Ivermectin for Treatment and prophylaxis "
                     "of COVID-19 Pandemic",
            "authors": "Elgazzar A, Eltaweel A, Youssef SA, Hany B, Hafez M, Moussa H",
            "venue": "Research Square (preprint)", "year": 2020,
            "doi": "10.21203/rs.3.rs-100956/v3",
            "verification": "L2",
            "withdrawal": {
                "status": "WITHDRAWN",
                "date": "2021-07-14",
                "by": "Research Square",
                "notice": "Withdrawn by Research Square on 2021-07-14 following verifiable data-integrity "
                          "concerns communicated to staff (subsequently under investigation by the "
                          "Egyptian Ministry of Higher Education): ~79 duplicated participant records, "
                          "deaths recorded on dates before the trial began, and plagiarism in the text.",
                "reported_by": "J. Lawrence; Reardon, Nature 2021 (d41586-021-02081-w); Sheldrick & "
                               "Meyerowitz-Katz, reanalyses",
            },
            "role": "the single fabricated primary trial the positive ivermectin syntheses pooled. It "
                    "carried the LARGEST weight (largest study by patient number) and the LARGEST drug "
                    "effect in the ivermectin literature; removing it collapses the pooled mortality "
                    "signal. This is the shared upstream the cascade collapses to.",
            "note": "Recorded as a fact about the source; the refusal does not depend on the "
                    "withdrawal — the three syntheses share this upstream whether or not it has been "
                    "withdrawn. The withdrawal only makes the stakes vivid (probe I4).",
        },
        derived_from=[], method="ingest",
    )

    # --- the three positive syntheses, each deriving (TWO HOPS to the claim) from Elgazzar. ---
    for slug, excerpt, sha_key, title, authors, venue, year, doi, pmid, notice, role in [
        ("src-bryant-2021", bryant, "bryant-2021",
         "Ivermectin for Prevention and Treatment of COVID-19 Infection: A Systematic Review, "
         "Meta-analysis, and Trial Sequential Analysis to Inform Clinical Guidelines",
         "Bryant A, Lawrie TA, Dowswell T, Fordham EJ, Mitchell S, Hill SR, Tham TC",
         "American Journal of Therapeutics", 2021, "10.1097/MJT.0000000000001402", "34145166",
         "Expression of Concern: Am J Ther 2022 Feb 17;29(2):e232 (10.1097/MJT.0000000000001482), PMID 35142702",
         "the Am J Ther 2021 meta-analysis (RR 0.38 mortality); pooled Elgazzar (its study-characteristics "
         "table names it); Expression of Concern issued 2022"),
        ("src-zein-2021", zein, "zein-2021",
         "Ivermectin and mortality in patients with COVID-19: A systematic review, meta-analysis, and "
         "meta-regression of randomized controlled trials",
         "Zein AFMZ, Sulistiyana CS, Raffaelo WM, Pranata R",
         "Diabetes & Metabolic Syndrome", 2021, "10.1016/j.dsx.2021.07.021", "34237554",
         None,
         "a second meta-analysis (RR 0.39) — the SAME mortality signal, different authors; its baseline-"
         "characteristics table lists 'Elgazzar 2020 [23]'"),
        ("src-kory-2021", kory, "kory-2021",
         "Review of the Emerging Evidence Demonstrating the Efficacy of Ivermectin in the Prophylaxis "
         "and Treatment of COVID-19",
         "Kory P, Meduri GU, Varon J, Iglesias J, Marik PE",
         "American Journal of Therapeutics", 2021, "10.1097/MJT.0000000000001377", "34375047",
         "Expression of Concern: Am J Ther 2022 Feb 14;29(2):e231 (10.1097/MJT.0000000000001481), PMID 35142703",
         "the FLCCC review asserting 'large, statistically significant reductions in mortality'; its study "
         "table cites Elgazzar by the exact withdrawn preprint DOI (rs.3.rs-100956); Expression of Concern 2022"),
    ]:
        assertion = {
            "title": title, "authors": authors, "venue": venue, "year": year,
            "doi": doi, "pmid": pmid,
            "excerpt_kind": "abstract (version of record) + included-study characteristics table (Europe PMC OA JATS, whitespace-normalized pipe-rows)",
            "excerpt": excerpt, "excerpt_sha256": SOURCES[sha_key]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": f"NCBI E-utilities efetch (PMID {pmid}) for the abstract + Europe PMC OA "
                          "fullTextXML for the study-characteristics table (rows serialized "
                          "' | '.join(cell.itertext()), whitespace-normalized)",
                "sources": [f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": role,
        }
        if notice:
            assertion["expression_of_concern"] = notice
        recs[slug] = mk(slug, "epi:Source", assertion,
                        derived_from=[recs["src-elgazzar-2020"]["id"]], method="ingest")

    # --- TOGETHER: the upstream-disjoint contrast RCT (never ingested Elgazzar). ---
    recs["src-reis-2022"] = mk(
        "src-reis-2022", "epi:Source",
        {
            "title": "Effect of Early Treatment with Ivermectin among Patients with Covid-19",
            "authors": "Reis G, Silva EASM, Silva DCM, Thabane L, ... Mills EJ (TOGETHER trial)",
            "venue": "New England Journal of Medicine", "year": 2022, "volume": "386", "issue": "18",
            "pages": "1721-1731", "doi": "10.1056/NEJMoa2115869", "pmid": "35353979",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": reis, "excerpt_sha256": SOURCES["reis-2022"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 35353979); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=35353979&rettype=abstract&retmode=xml"],
            },
            "verification": "L1",
            "role": "the genuinely INDEPENDENT line (the combinable contrast): a large placebo-controlled "
                    "RCT (n=3515) that never ingested Elgazzar; upstream-disjoint from the fabricated node",
        },
        derived_from=[], method="ingest",
    )

    # --- Hill 2021: the published counterfactual. Its meta had leaned on Elgazzar; on the version of
    #     record (high-risk-of-bias studies excluded) survival is null (RR 0.90), and the paper was
    #     RETRACTED. Kept as a source for the battery / provenance; not part of the laundered DAG. ---
    recs["src-hill-2021"] = mk(
        "src-hill-2021", "epi:Source",
        {
            "title": "Meta-analysis of Randomized Trials of Ivermectin to Treat SARS-CoV-2 Infection",
            "authors": "Hill A, Garratt A, Levi J, Falconer J, ... (Unitaid/WHO ivermectin group)",
            "venue": "Open Forum Infectious Diseases", "year": 2021, "doi": "10.1093/ofid/ofab358",
            "pmid": "34796244",
            "excerpt_kind": "abstract (version of record)",
            "excerpt": hill, "excerpt_sha256": SOURCES["hill-2021"]["sha256"],
            "retrieval": {
                "fetched_at": "2026-07-15",
                "method": "NCBI E-utilities efetch (PMID 34796244); AbstractText via itertext()",
                "sources": ["https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=34796244&rettype=abstract&retmode=xml"],
            },
            "retraction": {
                "status": "RETRACTED",
                "notice": "Retraction: Open Forum Infect Dis 2022 Feb 5;9(3):ofac056 (10.1093/ofid/ofac056), PMID 35146053",
                "note": "Earlier versions of this meta-analysis leaned heavily on Elgazzar; the version of "
                        "record, excluding high-risk-of-bias studies, is null on survival (RR 0.90). The "
                        "COUNTERFACTUAL the case turns on: remove the fabricated node and the signal collapses.",
            },
            "verification": "L1",
            "role": "the published 'remove Elgazzar -> the signal collapses' counterfactual (probe I2/I4). "
                    "Not part of the laundered DAG.",
        },
        derived_from=[], method="ingest",
    )

    # --- the topic entity (subject of the positive lines + the contrast; NOT a derivedFrom edge). ---
    recs["ent-ivermectin-covid-mortality"] = mk(
        "ent-ivermectin-covid-mortality", "epi:Entity",
        {
            "name": "The claim that ivermectin reduces COVID-19 mortality",
            "aliases": ["ivermectin mortality benefit in COVID-19"],
            "kind": "Claimeffect",
            "statement": "The proposition, assessed across the 2020-2022 ivermectin literature, that "
                         "ivermectin treatment lowers mortality in COVID-19.",
            "note": "A TOPIC node (the shared subject of the positive syntheses AND the TOGETHER "
                    "contrast) — deliberately NOT a provenance edge. Sharing a topic is not sharing an "
                    "upstream: TOGETHER is about the same question yet derives from disjoint evidence, "
                    "which is why it COMBINES while the three positive syntheses REFUSE.",
            "verification": "L1",
        },
        derived_from=[],
    )
    topic = "ent-ivermectin-covid-mortality"

    # --- The three "independent" positive mortality lines (the laundered set). ---
    mk_claim(
        recs, "claim-iver-bryant",
        text="A 2021 systematic review and meta-analysis (Bryant et al., Am J Ther) found that "
             "ivermectin reduced the risk of COVID-19 death, with an average risk ratio of 0.38.",
        subject=topic, source_slug="src-bryant-2021", excerpt=bryant,
        quote="ivermectin reduced risk of death compared with no ivermectin (average risk ratio 0.38, "
              "95% confidence interval 0.19-0.73",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-ivermectin-mortality-benefit",
        extractor=EXTRACTOR_BACKTEST,
    )
    mk_claim(
        recs, "claim-iver-zein",
        text="A 2021 meta-analysis (Zein et al.) found ivermectin was associated with decreased "
             "COVID-19 mortality, with a risk ratio of 0.39 — the same signal as Bryant, different authors.",
        subject=topic, source_slug="src-zein-2021", excerpt=zein,
        quote="Ivermectin was associated with decreased mortality (RR 0.39 [95% 0.20-0.74]",
        label="ENTAILS", rung="L5", lr=5.0, polarity="supports-ivermectin-mortality-benefit",
        extractor=EXTRACTOR_BACKTEST,
    )
    mk_claim(
        recs, "claim-iver-kory",
        text="A 2021 review (Kory et al., FLCCC) concluded that meta-analyses of ivermectin treatment "
             "trials found large, statistically significant reductions in COVID-19 mortality.",
        subject=topic, source_slug="src-kory-2021", excerpt=kory,
        quote="have found large, statistically significant reductions in mortality",
        label="ENTAILS", rung="L5", lr=4.0, polarity="supports-ivermectin-mortality-benefit",
        extractor=EXTRACTOR_BACKTEST,
    )

    # --- The byte-grounded inclusion edges: each positive synthesis POOLS the withdrawn Elgazzar
    #     trial. Structural claims (no illustrative_LR) grounded in each meta's included-study table. ---
    mk_claim(
        recs, "claim-iver-bryant-pools-elgazzar",
        text="The Bryant et al. 2021 meta-analysis lists the withdrawn Elgazzar 2020 trial among its "
             "pooled input studies — the fabricated trial the other positive syntheses also pool.",
        subject="src-elgazzar-2020", source_slug="src-bryant-2021", excerpt=bryant,
        quote="Elgazzar 202047 | Egypt | RCT",
        label="ENTAILS", rung="L5", extractor=EXTRACTOR_BACKTEST,
    )
    mk_claim(
        recs, "claim-iver-zein-pools-elgazzar",
        text="The Zein et al. 2021 meta-analysis lists 'Elgazzar 2020' among its included studies — "
             "the same withdrawn trial pooled by the other positive syntheses.",
        subject="src-elgazzar-2020", source_slug="src-zein-2021", excerpt=zein,
        quote="Elgazzar 2020 [23] | RCT | 98 vs 176",
        label="ENTAILS", rung="L5", extractor=EXTRACTOR_BACKTEST,
    )
    mk_claim(
        recs, "claim-iver-kory-pools-elgazzar",
        text="The Kory et al. 2021 review lists Elgazzar's Research Square preprint among the clinical "
             "studies it assesses — citing the exact withdrawn-preprint identifier.",
        subject="src-elgazzar-2020", source_slug="src-kory-2021", excerpt=kory,
        quote="Elgazzar A, Egypt",
        label="ENTAILS", rung="L5", extractor=EXTRACTOR_BACKTEST,
    )

    # --- The contrast: a genuinely INDEPENDENT ivermectin RCT (disjoint upstream). ---
    mk_claim(
        recs, "claim-iver-together",
        text="The TOGETHER randomized controlled trial (Reis et al. 2022, NEJM) found that early "
             "ivermectin treatment did not reduce COVID-19 hospitalization — independent evidence that "
             "does not route through the Elgazzar trial.",
        subject=topic, source_slug="src-reis-2022", excerpt=reis,
        quote="Treatment with ivermectin did not result in a lower incidence of medical admission to a "
              "hospital due to progression of Covid-19",
        label="ENTAILS", rung="L5", polarity="no-ivermectin-benefit", extractor=EXTRACTOR_BACKTEST,
    )



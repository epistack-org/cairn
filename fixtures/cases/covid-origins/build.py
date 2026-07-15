"""Case bundle builder: covid-origins.

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
    worobey_abstract = load_excerpt("worobey")
    pekar_abstract = load_excerpt("pekar")
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


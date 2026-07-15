"""Case bundle builder: eggs-good-for-you.

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



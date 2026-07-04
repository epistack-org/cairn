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

    def claim(slug, text, source_id, source_text, source_sha, quote, label, rung, lr):
        span = span_of(source_text, quote)
        recs[slug] = mk(
            slug, "epi:Claim",
            {
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
            },
            derived_from=[source_id], method="extract",
        )

    # --- The proximity trio (ALL derive from + are grounded in Worobey 2022) ---
    claim(
        "claim-geographic-clustering",
        "The earliest known December-2019 COVID-19 cases were geographically centered "
        "on the Huanan market, including cases with no reported direct market link.",
        worobey, worobey_abstract, worobey_sha,
        "the earliest known COVID-19 cases from December 2019, including those without "
        "reported direct links, were geographically centered on this market",
        "ENTAILS", "L5", 5.0,
    )
    claim(
        "claim-environmental-sampling",
        "Within the Huanan market, SARS-CoV-2-positive environmental samples were "
        "spatially associated with stalls selling live mammals.",
        worobey, worobey_abstract, worobey_sha,
        "within the market, SARS-CoV-2-positive environmental samples were spatially "
        "associated with vendors selling live mammals",
        "SUPPORTS", "L4", 5.0,
    )
    claim(
        "claim-live-mammal-sales",
        "Live SARS-CoV-2-susceptible mammals were sold at the Huanan market in late 2019.",
        worobey, worobey_abstract, worobey_sha,
        "live SARS-CoV-2-susceptible mammals were sold at the market in late 2019",
        "ENTAILS", "L5", 5.0,
    )

    # --- The molecular contrast claim (different upstream: Pekar 2022) ---
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
    )

    # --- self-verify before writing: grounding resolves + trio refuses + contrast combines ---
    store = {r["id"]: r for r in recs.values()}
    report = grounding.check_store(store)
    assert report["ok"], ("grounding failed", report["failed"])
    trio = [recs[s]["id"] for s in (
        "claim-geographic-clustering", "claim-environmental-sampling", "claim-live-mammal-sales")]
    assert provenance.combine_verdict(trio, store)["verdict"] == "REFUSE-TO-COMBINE"
    contrast = [recs["claim-geographic-clustering"]["id"], recs["claim-two-lineages"]["id"]]
    assert provenance.combine_verdict(contrast, store)["verdict"] == "COMBINABLE"

    # --- write one file per record + an index ---
    index = {}
    for slug, rec in recs.items():
        (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        index[slug] = rec["id"]
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2) + "\n")

    print(f"minted {len(recs)} vetted records -> {OUT}")
    print(f"  grounding: {report['grounded']}/{report['checked']} claims resolve, ok={report['ok']}")
    for slug, rid in index.items():
        print(f"  {slug:30s} {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

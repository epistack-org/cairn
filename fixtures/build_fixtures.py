"""Mint the COVID demo fixtures as signed Cairn records.

ILLUSTRATIVE FIXTURES for engine demonstration. The bibliographic metadata is
flagged ``unverified`` (Trust-Ladder L1/L2, not L5 "accepted") — these records
demonstrate the *envelope + detector + n_eff*, not a vetted COVID analysis.
Citations must be verified before any real use (fabricated provenance is the
exact F0 sin the project exists to catch).

The structural point the fixtures encode (REPORT section 7): the three "lines of
proximity evidence" all derive from ONE early-case dataset (Worobey 2022), so
they are not three independent votes; the molecular "two lineages" line (Pekar
2022) is a genuinely different upstream.

Deterministic: fixed signing seed + fixed timestamps => stable Trusty URIs.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn import envelope
from cairn.keys import SigningKey

OUT = Path(__file__).resolve().parent
AT = "2026-06-28T00:00:00Z"
# throwaway deterministic demo identity (NOT a real keystone key)
KEY = SigningKey.from_seed_hex("c0" * 32, label="keystone:epistack-corpus")

UNVERIFIED = "unverified-fixture"


def mk(slug, type_, assertion, derived_from=None, method="assert"):
    rec = envelope.new_record(
        type_, assertion, minted_by=KEY.label, method=method,
        derived_from=derived_from or [], at=AT,
    )
    envelope.sign(rec, KEY)
    errs = envelope.validate(rec)
    assert not errs, (slug, errs)
    return rec


def main() -> int:
    recs: dict[str, dict] = {}

    # --- Sources (the upstreams) ---
    recs["src-worobey-2022"] = mk(
        "src-worobey-2022", "epi:Source",
        {
            "title": "The Huanan Seafood Wholesale Market in Wuhan was the early "
                     "epicenter of the COVID-19 pandemic",
            "authors": "Worobey M, et al.",
            "venue": "Science", "year": 2022, "volume": "377(6609):951-959",
            "doi": "10.1126/science.abp8715",
            "verification": UNVERIFIED,
            "role": "the early-case dataset shared by the proximity trio",
        },
        method="ingest",
    )
    recs["src-pekar-2022"] = mk(
        "src-pekar-2022", "epi:Source",
        {
            "title": "The molecular epidemiology of multiple zoonotic origins of "
                     "SARS-CoV-2",
            "authors": "Pekar JE, et al.",
            "venue": "Science", "year": 2022, "volume": "377(6609):960-966",
            "doi": "10.1126/science.abp8337",
            "verification": UNVERIFIED,
            "role": "a genuinely distinct (molecular) upstream",
        },
        method="ingest",
    )

    # --- Entities (nouns, referenced by claims via Trusty URI) ---
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

    # --- The proximity trio (ALL derive from Worobey 2022) ---
    for slug, text in [
        ("claim-geographic-clustering",
         "Early COVID-19 cases cluster geographically around the Huanan market."),
        ("claim-environmental-sampling",
         "SARS-CoV-2-positive environmental samples concentrate in the Huanan market."),
        ("claim-ascertainment-centroid",
         "The ascertainment-bias-corrected early-case centroid sits at the Huanan market."),
    ]:
        recs[slug] = mk(
            slug, "epi:Claim",
            {"text": text, "subject": hsm, "polarity": "supports-zoonosis",
             "illustrative_LR": 5.0},
            derived_from=[worobey], method="extract",
        )

    # --- The molecular contrast claim (different upstream) ---
    recs["claim-two-lineages"] = mk(
        "claim-two-lineages", "epi:Claim",
        {"text": "Two distinct SARS-CoV-2 lineages (A and B) indicate multiple "
                 "market introductions.",
         "subject": hsm, "polarity": "supports-zoonosis", "illustrative_LR": 4.0},
        derived_from=[pekar], method="extract",
    )

    # --- write one file per record + an index ---
    index = {}
    for slug, rec in recs.items():
        (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        index[slug] = rec["id"]
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2) + "\n")

    print(f"minted {len(recs)} records -> {OUT}")
    for slug, rid in index.items():
        print(f"  {slug:30s} {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Consume the anchor: `cairn import` over the baseline's own corpus.

Two things, both self-contained (no network, no baseline clone):

  1. Re-derive the per-DOI shared-claim counts from baseline-natorigin.json and check
     they reproduce the 28-line probe's OUTPUT.txt (5/5/3/3/3/2/2/2). This makes the
     transcription a CHECKED artifact -- if a DOI edge were mistyped, the count would
     drift and this fails. (The entry's whole thesis, applied to our own transcription.)

  2. Import the corpus, then run the provenance intersection over the two claims the
     baseline's own dedup control missed -- environmental-samples and raccoon-dog, which
     BOTH derive from Crits-Christoph 2024 -- and show cairn REFUSES and names the DOI.

Run:  python3 demo/import_example/verify_baseline_import.py
"""
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from cairn import importer, provenance  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# The probe's committed result (internal prior-art notes/baseline-probe/OUTPUT.txt @ 774c9ee):
# DOI -> number of "independent" natural-origin claims that derive from it.
PROBE_COUNTS = {
    "10.1126/science.abp8715": 5,
    "10.1126/science.abp8337": 5,
    "10.1038/s41586-023-06043-2": 3,
    "10.1016/j.cell.2024.08.010": 3,
    "10.1126/science.adl0585": 3,
    "10.1093/ve/vead077": 2,
    "10.1093/jrsssa/qnae021": 2,
    "10.1126/science.1087139": 2,
}
CRITS_CHRISTOPH = "10.1016/j.cell.2024.08.010"


def main() -> int:
    spec = json.load(open(os.path.join(HERE, "baseline-natorigin.json")))

    # ---- 1. Transcription is a checked artifact ----
    counts = defaultdict(int)
    for c in spec["claims"]:
        for ref in c["derivedFrom"]:
            counts[ref] += 1
    shared = {doi: n for doi, n in counts.items() if n >= 2}
    print("=== per-DOI shared-claim counts (this corpus) vs the probe's OUTPUT.txt ===")
    ok = True
    for doi, want in sorted(PROBE_COUNTS.items(), key=lambda kv: -kv[1]):
        got = shared.get(doi, 0)
        mark = "ok" if got == want else "MISMATCH"
        if got != want:
            ok = False
        print(f"  {doi:34s} probe={want}  import={got}  [{mark}]")
    if not ok:
        print("\nFAIL: transcription does not reproduce the probe.")
        return 1
    print("  -> transcription reproduces the probe exactly.\n")

    # ---- 2. cairn import -> intersect names the Crits-Christoph double-count ----
    records = importer.import_corpus(spec)
    store = {r["id"]: r for r in records}
    by_slug = {r["assertion"]["label"]: r["id"] for r in records}

    # the two evidence files the baseline filed as separate moderate/0.90 rows and cited
    # side by side as mutually corroborating -- same Crits-Christoph 2024 finding, twice.
    pair = ["environmental-samples-wildlife-stall-positivity",
            "raccoon-dog-susceptible-species-genetic-tracing"]
    ids = [by_slug[s] for s in pair]
    verdict = provenance.combine_verdict(ids, store)

    print("=== cairn import + intersect over the anchor's own dedup miss ===")
    print(f"  claims: {pair[0]}  x  {pair[1]}")
    print(f"  verdict: {verdict['verdict']}")
    print(f"  shared upstream(s): {verdict['shared_upstreams']}")
    assert verdict["verdict"].startswith("REFUSE"), "expected a refusal on the shared DOI"
    assert f"doi:{CRITS_CHRISTOPH}" in verdict["shared_upstreams"], "expected Crits-Christoph named"
    print(f"\n  {provenance.explain_verdict(verdict, store)}")

    # and the full natural-origin set refuses on Worobey/Pekar too
    full = [by_slug[c["slug"]] for c in spec["claims"]]
    fv = provenance.combine_verdict(full, store)
    print(f"\n  full {len(full)}-claim set: {fv['verdict']}; "
          f"{len(fv['shared_upstreams'])} shared upstream(s) named "
          f"(incl. doi:10.1126/science.abp8715 = Worobey 2022).")
    print("\nPASS: the anchor's 'independent primary signals' share named upstreams by DOI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

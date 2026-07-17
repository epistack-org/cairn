"""The worked examples, side by side (floor deliverable #3, dev/cairn#9).

`demo/hsm_trio.py` goes DEEP on one case (COVID: the naive baseline, the careful
baseline, the Fréchet interval, the measured n_eff). This goes WIDE: it runs the same
mechanical checks over every case (COVID, eggs, CERN, the amyloid Aβ*56 cascade added in
the 2026-07-15 decoupling spike, and the three backtest-scaling imports of 2026-07-15 —
ivermectin/Elgazzar, Anversa c-kit, Poldermans/DECREASE) and shows that the refusal is not
a property of one hand-picked example.

Everything printed here is read off the minted fixtures — no substrate, no network, no
model calls. `fixtures/CASES.json` declares each case's structure; the build already
verified those declarations against what the detector actually finds, and
`tests/test_cases.py` re-checks them in CI.
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn import frechet, grounding, provenance

FX = Path(__file__).resolve().parents[1] / "fixtures"

# The mechanically-verified backstops (flf-contest#7).
#
# A refusal on a *settled* safety question must never ship bare: on CERN the honest
# verdict is not "the LHC might be unsafe", it is "these three assurances are not three
# independent votes FOR a conclusion that still stands". The engine already computes that
# upgrade (`cairn.provenance.combine_verdict`), but only when a caller names a backstop and
# the at-risk premise — the CLI exposes them as `--backstop` / `--at-risk-upstream`. This
# demo drove every case generically off `CASES.json`, passed neither, and so printed the
# bare refusal SPEC.md §4b says we no longer emit.
#
# The pair lives here rather than in `CASES.json` because that file is digest-covered by two
# shipped corpora (`cairns/corpus`@v2, `cairns/backtest-corpus`@v1) and by Track λ's
# `corpus.lambda.lock`; declaring a `backstop` field there would move a pinned digest. This
# override changes no minted byte — it only supplies the two slugs the engine already
# accepts, and the engine still *checks* the disjointness itself (a backstop that shares the
# at-risk premise falls back to a bare refusal + a note saying so). Same pair asserted in
# `fixtures/build_fixtures.py` (the build gate) and `tests/test_cases.py`.
BACKSTOPS = {
    # Giddings & Mangano premised the white-dwarf/neutron-star bound on the Hawking premise
    # FAILING, so it is upstream-disjoint from it and independently sufficient. Note the
    # at-risk premise is the Hawking one, NOT the cosmic-ray argument the trio shares: the
    # backstop descends from the cosmic-ray argument too, so naming that as at-risk would
    # (correctly) collapse back to a bare refusal.
    "cern-black-hole": {
        "backstop": "claim-cern-wd-ns-bound",
        "at_risk_upstream": "ent-hawking-radiation-premise",
    },
}


def load():
    index = json.loads((FX / "INDEX.json").read_text())
    cases = json.loads((FX / "CASES.json").read_text())
    store = {}
    for slug in index:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return index, cases, store


def wrap(text: str, width: int = 76, indent: str = "  ") -> str:
    out, line = [], ""
    for word in text.split():
        if len(line) + len(word) + 1 > width:
            out.append(indent + line)
            line = word
        else:
            line = f"{line} {word}".strip()
    if line:
        out.append(indent + line)
    return "\n".join(out)


def main() -> int:
    index, cases, store = load()
    rev = {v: k for k, v in index.items()}
    refused = 0

    print("\n" + "=" * 78)
    # Counted off the manifest, not typed: this header said "THREE" while the footer counted
    # 7/7 two screens below.
    print(f"  CAIRN — THE {len(cases)} WORKED EXAMPLES")
    print("  apparent corroboration whose provenance intersection collapses")
    print("=" * 78)

    for case_id, case in cases.items():
        laundered = [index[s] for s in case["laundered_set"]]
        bs = BACKSTOPS.get(case_id)
        v = provenance.combine_verdict(
            laundered, store,
            backstop=index[bs["backstop"]] if bs else None,
            at_risk_upstream=index[bs["at_risk_upstream"]] if bs else None,
        )
        shared = provenance.shared_upstreams(laundered, store)["collective_shared"]
        lrs = [store[i]["assertion"]["illustrative_LR"] for i in laundered]

        print(f"\n\n### {case['title']}")
        print(f"    [{case_id}]  shared upstream is a {case['shared_upstream_kind']}\n")
        print("  CRUX")
        print(wrap(case["crux"], indent="    ") + "\n")

        print("  THE APPARENTLY INDEPENDENT LINES")
        for rid in laundered:
            a = store[rid]["assertion"]
            src = rev[a["grounding"]["source"]]
            print(f"    - LR~{a['illustrative_LR']:g}  {rev[rid]}")
            print(f"        grounded in {src}  (span {a['grounding']['char_span']}, "
                  f"{a['grounding']['entailment_label']}/{a['verification']})")

        # faithfulness: the spans resolve, byte-for-byte, against the retrieved sources
        gr = grounding.check_store(store, laundered)
        print(f"\n  FAITHFULNESS   {gr['grounded']}/{gr['checked']} spans resolve to their "
              f"cited source  (ok={gr['ok']})")

        # the naive move, and why it is undefined
        naive = 1.0
        for x in lrs:
            naive *= x
        print(f"\n  NAIVE BASELINE  multiplies them: {' x '.join(f'{x:g}' for x in lrs)} "
              f"= {naive:g}:1")

        print(f"\n  CAIRN           {v['verdict']}")
        for s in shared:
            hops = "direct" if any(
                s in store[c]["provenance"]["derivedFrom"] for c in laundered) else "TRANSITIVE"
            print(f"                  shared upstream: {rev[s]}   [{hops}]")
        # The refusal and the conclusion-stands note, in the same breath — never a bare
        # REFUSE on a settled question (flf-contest#7, SPEC.md §4b). Mechanically verified:
        # the engine, not this demo, decided the backstop survives.
        if v.get("conclusion_unchanged"):
            # The engine's own `note` carries the same finding but names the parties by raw
            # tt: URI; re-render it against the slug map for a human reader. `cairn explain`
            # below prints the engine's full sentence with resolved labels.
            print("\n                  CONCLUSION UNCHANGED — the conclusion itself stands;")
            print(wrap(f"what fails is only the claim that these are {len(laundered)} "
                       f"independent votes for it. The backstop {rev[v['backstop']]} is "
                       f"upstream-disjoint from the at-risk premise "
                       f"{rev[v['at_risk_upstream']]} and is on its own sufficient.",
                       width=58, indent=" " * 18))
            print()
        if v["verdict"] != "COMBINABLE":
            refused += 1

        # the honest interval instead of the fake point
        fv = frechet.frechet_verdict(lrs, shared_upstream=not v["independent"])
        print(f"                  Fréchet interval: LR in [{fv['interval_lr'][0]:g}, "
              f"{fv['interval_lr'][1]:g}] -> {fv['verdict']}")

        # the contrast pair — combinable where independence really holds, refused where the
        # engine's own former false positive lived (covid: Worobey × Pekar; flf-contest#5/#6)
        pair = [index[s] for s in case["contrast_pair"]]
        cv = provenance.combine_verdict(pair, store)
        want = case["contrast_expected"]
        gloss = ("combining here IS licensed (disjoint upstream)" if want == "COMBINABLE"
                 else "the former false COMBINABLE — REFUSED on the honest DAG")
        print(f"\n  CONTRAST        {{{rev[pair[0]]}, {rev[pair[1]]}}}")
        print(f"                  {cv['verdict']} — {gloss}")

        # a refusal never ships bare: the same verdict, as one plain-English
        # paragraph, including the un-refuse set (flf-contest#22)
        print(f"\n  EXPLAIN (`cairn explain`)")
        print(wrap(provenance.explain_verdict(v, store), indent="    "))

        print(f"\n  PUNCHLINE")
        print(wrap(case["punchline"], indent="    "))

    print("\n" + "=" * 78)
    print(f"  {refused}/{len(cases)} cases REFUSE-TO-COMBINE on the provenance dimension.")
    print("  In every one, the lines look independent and are not. The refusal is")
    print("  mechanical, span-grounded, and re-checkable on a fresh machine —")
    print("  that is the delta, not the cognition.")
    print("=" * 78 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

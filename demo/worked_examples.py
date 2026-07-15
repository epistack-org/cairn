"""The worked examples, side by side (floor deliverable #3, dev/cairn#9).

`demo/hsm_trio.py` goes DEEP on one case (COVID: the naive baseline, the careful
baseline, the Fréchet interval, the measured n_eff). This goes WIDE: it runs the same
mechanical checks over every case (COVID, eggs, CERN, and the amyloid Aβ*56 cascade added
in the 2026-07-15 decoupling spike) and shows that the refusal is not a property of one
hand-picked example.

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
    print("  CAIRN — THE THREE WORKED EXAMPLES")
    print("  apparent corroboration whose provenance intersection collapses")
    print("=" * 78)

    for case_id, case in cases.items():
        laundered = [index[s] for s in case["laundered_set"]]
        v = provenance.combine_verdict(laundered, store)
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

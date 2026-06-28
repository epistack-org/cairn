"""The COVID-HSM-trio head-to-head: a naive transcript vs Cairn.

Runs entirely on the minted fixtures (plain git + one container, no substrate).
Shows the two deltas a single careful Claude-Code transcript structurally cannot
produce: a mechanical shared-upstream proof and a measured n_eff that says when
NOT to multiply.

The provenance verdict is MECHANICAL (read off the fixture derivedFrom edges).
The n_eff agreement vectors are ILLUSTRATIVE of the consequence (claims sharing
an upstream co-move when that upstream is resampled) and are labelled as such.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from cairn import neff, provenance

FX = Path(__file__).resolve().parents[1] / "fixtures"


def load_store():
    index = json.loads((FX / "INDEX.json").read_text())
    store = {}
    for slug in index:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return index, store


def line(c="-", n=70):
    print(c * n)


def main() -> int:
    index, store = load_store()
    trio = [index["claim-geographic-clustering"],
            index["claim-environmental-sampling"],
            index["claim-ascertainment-centroid"]]
    molecular = index["claim-two-lineages"]

    def text(rid):
        return store[rid]["assertion"]["text"]

    def lr(rid):
        return store[rid]["assertion"]["illustrative_LR"]

    print("\n=== COVID HSM proximity trio — naive baseline vs Cairn ===\n")
    print('The three "independent lines of proximity evidence":')
    for rid in trio:
        print(f"  - {text(rid):66s}")
        print(f"      LR~{lr(rid):g}  derivedFrom {store[rid]['provenance']['derivedFrom'][0]}")

    line()
    print("NAIVE BASELINE (what a single transcript does)")
    line()
    naive = math.prod(lr(r) for r in trio)
    print("  treats the 3 lines as independent -> multiplies likelihood ratios:")
    print(f"    combined LR = {' x '.join(f'{lr(r):g}' for r in trio)} = {naive:g}")
    print(f"  => a confident point estimate (~{naive:g}:1 for zoonosis).")

    line()
    print("CAIRN (refuse-to-combine)")
    line()
    verdict = provenance.combine_verdict(trio, store)
    print("  layer-(a) provenance detector over the 3 claims:")
    print(f"    VERDICT: {verdict['verdict']}")
    for up in verdict["shared_upstreams"]:
        print(f"    shared upstream: {up}  ({store[up]['assertion']['title'][:48]}...)")
    print("    => the 3 'lines' trace to ONE dataset; multiplying is undefined.")

    # illustrative co-movement: shared upstream -> vectors move together -> phi_bar=1
    trio_vectors = [[1, 1, 0, 1, 0]] * 3
    r = neff.neff_from_matrix(trio_vectors)
    print("  measured effective independence (illustrative co-movement vectors):")
    print(f"    k={r['k']}, phi_bar={r['phi_bar']:.2f}, n_eff={r['n_eff']:.2f}  (NOT {r['k']})")
    print(f"  honest output: a BOUND from the single strongest line (LR<={max(lr(x) for x in trio):g}),")
    print("    an interval, and the qualitative crux routed to a human"
          " -- never the point estimate.")

    line()
    print("CONTRAST — where independence DOES hold")
    line()
    pair = [trio[0], molecular]
    vc = provenance.combine_verdict(pair, store)
    # genuinely distinct upstreams -> orthogonal (uncorrelated) illustrative vectors
    pair_vectors = [[1, 1, 0, 0], [1, 0, 1, 0]]
    rp = neff.neff_from_matrix(pair_vectors)
    print(f"  {{geographic clustering (Worobey), two lineages (Pekar)}}: ")
    print(f"    VERDICT: {vc['verdict']}  (no shared upstream)")
    print(f"    n_eff over genuinely-distinct lines: k={rp['k']}, "
          f"phi_bar={rp['phi_bar']:.2f}, n_eff={rp['n_eff']:.2f}")
    print("    => here combining is licensed.\n")

    print("Delta the baseline structurally cannot produce: a mechanical "
          "shared-upstream proof")
    print("+ a measured n_eff that knows when NOT to multiply.\n")

    # machine-readable artifact (the Cairn verdict other tools/teams consume)
    out = {
        "trio_verdict": {k: verdict[k] for k in ("independent", "verdict", "shared_upstreams")},
        "trio_neff": r,
        "naive_combined_LR": naive,
        "contrast_verdict": {k: vc[k] for k in ("independent", "verdict")},
        "contrast_neff": rp,
    }
    (FX.parent / "out").mkdir(exist_ok=True)
    (FX.parent / "out" / "hsm_trio_verdict.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote machine-readable verdict -> out/hsm_trio_verdict.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

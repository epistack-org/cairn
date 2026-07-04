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

from cairn import frechet, grounding, neff, provenance

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
            index["claim-live-mammal-sales"]]
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
    print("FAITHFULNESS — every line is span-grounded to a retrieved source (L4/L5)")
    line()
    gr = grounding.check_store(store, trio + [molecular])
    for r in gr["results"]:
        src = store[r["source"]]["assertion"]
        print(f"  {text(r['claim'])[:60]:60s}")
        print(f"    [{r['verification']}/{r['entailment_label']}] {src['excerpt_kind']} of {src['doi']}"
              f"  char_span {r['char_span']} resolves=={r['resolves']}")
    print(f"  => {gr['grounded']}/{gr['checked']} claims mechanically resolve: "
          "source.excerpt[char_span] == quote (re-checkable on a fresh machine).")

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

    # MEASURED effective independence (A2): a heterogeneous assessor panel on the HSM
    # crux. Real votes, pinned in assessment/runs/ and re-checkable with `cairn assess`
    # -- this replaces the earlier illustrative co-movement vectors.
    runs = Path(__file__).resolve().parents[1] / "assessment" / "runs"
    m = json.loads((runs / "heterogeneous.json").read_text())["assertion"]["neff"]
    cm = json.loads((runs / "homogeneous-control.json").read_text())["assertion"]["neff"]
    dm = json.loads((runs / "clean-diverse.json").read_text())["assertion"]["neff"]
    print("  MEASURED effective independence (A2 -- real assessor votes, re-checkable via `cairn assess`):")
    print(f"    homogeneous control (9x same model/evidence/protocol): "
          f"phi_bar={cm['phi_bar']:.2f}, n_eff={cm['n_eff_capped']:.2f}")
    print(f"    clean-diverse (FULL evidence; vary model tier + protocol): "
          f"phi_bar={dm['phi_bar']:.2f}, n_eff={dm['n_eff_capped']:.2f}   <- diversity barely helps")
    print(f"    all levers (+ evidence partition): "
          f"phi_bar={m['phi_bar']:.2f}, n_eff={m['n_eff_capped']:.2f}  (NOT {m['k']}; audit: partition-inflated)")
    gm = json.loads((runs / "glm-diverse.json").read_text())["assertion"]["neff"]
    cv = json.loads((runs / "axis_analysis.json").read_text()).get("cross_vendor") or {}
    print(f"    cross-vendor GLM-4.6 (FULL evidence, non-Anthropic vendor): "
          f"phi_bar={gm['phi_bar']:.2f}, n_eff={gm['n_eff_capped']:.2f}")
    if cv:
        print(f"      within-Anthropic phi={cv['within_anthropic_phi']:.2f} | within-GLM phi={cv['within_glm_phi']:.2f}"
              f" | CROSS-vendor phi={cv['cross_vendor_phi']:.2f}  ->  k=18 combined n_eff={cv['combined_neff']:.2f}")
    # A3 -- the Fréchet/p-box interval. The honest object is an INTERVAL, not a point,
    # and its width is the refusal. `cairn frechet`; pinned in assessment/frechet.json.
    fv = frechet.frechet_verdict([lr(r) for r in trio], shared_upstream=not verdict["independent"],
                                 n_eff=cm["n_eff_capped"])
    def fmt_iv(iv):
        return "[" + ", ".join(("inf" if x == "inf" else f"{x:g}") for x in iv) + "]"
    print("  A3 -- Fréchet/p-box interval (the honest object is an interval, not a point):")
    print(f"    naive point             : LR={fv['naive_lr']:g}  (posterior {fv['naive_posterior']:.3f})   <- the fake certainty")
    print(f"    redundancy interval     : LR in [{fv['interval_lr'][0]:g}, {fv['interval_lr'][1]:g}]  "
          f"(posterior [{fv['interval_posterior'][0]:.3f}, {fv['interval_posterior'][1]:.3f}])  "
          f"width={fv['width_decades']:.2f} decades")
    print(f"    disclosed (not a bound) : PLOD envelope {fmt_iv(fv['plod_envelope_lr'])}  |  "
          f"full-agnostic {fmt_iv(fv['full_frechet_lr'])} = posterior [0,1], VACUOUS")
    print(f"    measured point (n_eff=1): LR={fv['measured']['lr']:g}  -> at the redundant floor, NOT the product")
    print(f"    VERDICT: {fv['verdict']}")
    print(f"      width {fv['width_decades']:.2f} > {fv['max_width_decades']} decades -> cap the claim at LR={fv['honest_bound_lr']:g} "
          "(a cap, not a proven lower bound), emit the interval, route the crux to a human -- never the point.")

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
    fc = frechet.frechet_verdict([lr(trio[0]), lr(molecular)], shared_upstream=not vc["independent"])
    print(f"    Fréchet: {fc['verdict']} -> combined LR={fc['point_lr']:g} "
          f"(posterior {fc['point_posterior']:.3f}); the one licensed cross-family product (never 125x4=500).")
    print("    => here combining is licensed.\n")

    print("Delta the baseline structurally cannot produce: a mechanical "
          "shared-upstream proof")
    print("+ a measured n_eff that knows when NOT to multiply.\n")

    # machine-readable artifact (the Cairn verdict other tools/teams consume)
    out = {
        "grounding": {k: gr[k] for k in ("ok", "checked", "grounded")},
        "trio_verdict": {k: verdict[k] for k in ("independent", "verdict", "shared_upstreams")},
        "panel_neff": m,
        "control_neff": cm,
        "clean_diverse_neff": dm,
        "naive_combined_LR": naive,
        "contrast_verdict": {k: vc[k] for k in ("independent", "verdict")},
        "contrast_neff": rp,
        "frechet_trio": fv,          # A3: the honest interval + refusal (delta 3 + delta 4)
        "frechet_contrast": fc,      # A3: the one licensed cross-family product
    }
    (FX.parent / "out").mkdir(exist_ok=True)
    (FX.parent / "out" / "hsm_trio_verdict.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote machine-readable verdict -> out/hsm_trio_verdict.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

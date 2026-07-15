"""Pin the A3 Fréchet/p-box artifact — deterministic, model-free.

Writes ``assessment/frechet.json``: the trio refuse-to-combine interval, the
disjoint-contrast combinable point, and the n_eff p-box for every pinned A2 panel,
plus the declared policy constants. Everything is a closed form over the pinned
fixtures + the pinned pairwise-φ arrays, so a fresh machine recomputes it exactly
(``test_frechet.py::test_artifact_recompute`` asserts byte/dict equality).

    python assessment/build_frechet.py       # rewrites assessment/frechet.json
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn import frechet, neff, provenance

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
RUNS = ROOT / "assessment" / "runs"
OUT = ROOT / "assessment" / "frechet.json"

PANELS = ["homogeneous-control", "clean-diverse", "glm-diverse", "heterogeneous"]


def load_store() -> tuple[dict, dict]:
    index = json.loads((FX / "INDEX.json").read_text())
    store = {}
    for slug in index:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return index, store


def verdict_over(index, store, slugs, *, neff_run=None) -> dict:
    ids = [index[s] for s in slugs]
    prov = provenance.combine_verdict(ids, store)
    lrs = [store[i]["assertion"]["illustrative_LR"] for i in ids]
    n_eff = None
    if neff_run is not None:
        n_eff = json.loads((RUNS / neff_run).read_text())["assertion"]["neff"]["n_eff_capped"]
    v = frechet.frechet_verdict(lrs, shared_upstream=not prov["independent"], n_eff=n_eff)
    v["claims"] = slugs
    v["provenance"] = {"verdict": prov["verdict"], "shared_upstreams": prov["shared_upstreams"]}
    return v


def build() -> dict:
    index, store = load_store()
    trio = ["claim-geographic-clustering", "claim-environmental-sampling", "claim-live-mammal-sales"]
    # The genuine disjoint COMBINABLE (flf-contest#6): CERN {Hawking evaporation} × {WD/NS
    # survival}. The old contrast (geographic-clustering × two-lineages) was the false COMBINABLE
    # and now REFUSES on the honest DAG (Worobey↔Pekar citation/calibration edges; flf-contest#5).
    contrast = ["claim-cern-hawking-evaporation", "claim-cern-wd-ns-bound"]

    neff_uncertainty = {}
    for name in PANELS:
        d = json.loads((RUNS / f"{name}.json").read_text())
        vectors = d["assertion"]["vectors"]
        r = neff.neff_from_matrix(vectors)
        neff_uncertainty[name] = {
            "k": r["k"], "k_effective": r["k_effective"], "degenerate": r["degenerate"],
            "phi_bar": r["phi_bar"], "kish_ess": r["kish_ess"],
            "eigenvalue_ess": r["eigenvalue_ess"], "bootstrap_ci": r["bootstrap_ci"],
        }

    return {
        "note": "A3 Fréchet interval — deterministic re-derivation over the pinned "
                "fixtures. The n_eff uncertainty is a bootstrap CI on φ̄ (resampled "
                "probes), NOT the removed single-pair min/max p-box (draft-entry#8/#15). "
                "Recompute with assessment/build_frechet.py.",
        "trio": verdict_over(index, store, trio, neff_run="homogeneous-control.json"),
        "contrast": verdict_over(index, store, contrast),
        "neff_uncertainty": neff_uncertainty,
        "policy": {
            "prior": frechet.DEFAULT_PRIOR,
            "base_neg": frechet.ILLUSTRATIVE_BASE_NEG,
            "max_width_decades": frechet.DEFAULT_MAX_WIDTH_DECADES,
        },
    }


def main() -> int:
    art = build()
    OUT.write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n")
    tv, cv = art["trio"], art["contrast"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  trio     : {tv['verdict']} | interval_lr={tv['interval_lr']} "
          f"width={tv['width_decades']:.4f} honest_bound={tv['honest_bound_lr']} "
          f"(naive would be {tv['naive_lr']})")
    print(f"  contrast : {cv['verdict']} | point_lr={cv.get('point_lr')} "
          f"posterior={cv.get('point_posterior'):.4f}")
    for name, u in art["neff_uncertainty"].items():
        ci = u["bootstrap_ci"]
        kish = u["kish_ess"]
        if ci is None:
            print(f"  neff {name:20s}: kish_ess={kish} eig={u['eigenvalue_ess']} (no φ̄ CI)")
        else:
            print(f"  neff {name:20s}: kish_ess={kish:.3f} eig={u['eigenvalue_ess']:.3f} "
                  f"φ̄∈[{ci['phi_bar_lo']:.3f},{ci['phi_bar_hi']:.3f}] "
                  f"n_eff∈[{ci['n_eff_lo']:.3f},{ci['n_eff_hi']:.3f}]"
                  f"{' (CI includes φ̄=1)' if ci['includes_one'] else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

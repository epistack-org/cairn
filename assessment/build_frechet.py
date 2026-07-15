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

from cairn import frechet, provenance

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

    neff_pbox = {}
    for name in PANELS:
        d = json.loads((RUNS / f"{name}.json").read_text())
        k = d["assertion"]["neff"]["k"]
        neff_pbox[name] = frechet.neff_pbox(d["assertion"]["pairwise_phi"], k)

    return {
        "note": "A3 Fréchet/p-box interval — deterministic re-derivation over the pinned "
                "fixtures + pairwise-φ arrays; recompute with assessment/build_frechet.py.",
        "trio": verdict_over(index, store, trio, neff_run="homogeneous-control.json"),
        "contrast": verdict_over(index, store, contrast),
        "neff_pbox": neff_pbox,
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
    for name, box in art["neff_pbox"].items():
        print(f"  pbox {name:20s}: n_eff in [{box['n_eff_lo']:.3f}, {box['n_eff_hi']:.3f}] "
              f"width={box['width']:.3f} point={box['point']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

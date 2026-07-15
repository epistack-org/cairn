"""Recompute n_eff for the six Phase-2 corpus arms with the FIXED engine.

Reads ``assessment/corpus_arms.json`` (affirm-vectors vendored from the pinned,
signed run-records behind ``material/phase2/reveals.json``) and re-derives, per arm,
the corrected statistics through ``cairn.neff.neff_from_matrix``:

  * φ̄ over the NON-degenerate assessors (constant / do-nothing assessors excluded,
    with an explicit k -> k_effective reduction — never coded φ=0),
  * the Kish design-effect ESS (clustering component) and the assumption-lighter
    eigenvalue ESS (k/λ_max),
  * a bootstrap CI on φ̄ (resampled probes) — replacing the min/max n_eff p-box.

Writes ``assessment/neff_recompute.json`` and prints a before/after table. This is
the honest recompute demanded by draft-entry#8: it publishes whatever comes out,
including collapses (eggs partition 4.10 -> ~1.3; eggs persona control 2.0 -> INERT).

    python assessment/recompute_neff.py       # rewrites assessment/neff_recompute.json
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn import neff

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assessment" / "corpus_arms.json"
OUT = ROOT / "assessment" / "neff_recompute.json"


def recompute() -> dict:
    data = json.loads(SRC.read_text())
    result = {
        "note": "Corrected n_eff for the six Phase-2 corpus arms, recomputed with the "
                "fixed cairn engine (draft-entry#8). Degenerate assessors excluded (never "
                "coded φ=0); φ̄ reported for cross-arm comparison since k differs; Kish + "
                "eigenvalue ESS both shipped; bootstrap CI on φ̄ replaces the min/max p-box. "
                "Recompute: python assessment/recompute_neff.py.",
        "source": {"repo": data.get("source_repo"), "path": data.get("source_path")},
        "cases": {},
    }
    for case, cd in data["cases"].items():
        result["cases"][case] = {"battery": cd["battery"], "arms": {}}
        for arm, ad in cd["arms"].items():
            vectors = [a["affirm_vector"] for a in ad["assessors"]]
            r = neff.neff_from_matrix(vectors)
            result["cases"][case]["arms"][arm] = {
                "k": r["k"],
                "k_effective": r["k_effective"],
                "degenerate": r["degenerate"],
                "excluded_assessors": [ad["assessors"][i]["assessor"] for i in r["excluded"]],
                "inert": r["inert"],
                "phi_bar": r["phi_bar"],
                "kish_ess": r["kish_ess"],
                "eigenvalue_ess": r["eigenvalue_ess"],
                "bootstrap_ci": r["bootstrap_ci"],
                "pre_fix": {
                    "phi_bar": ad["pinned_neff_pre_fix"].get("phi_bar"),
                    "n_eff": ad["pinned_neff_pre_fix"].get("n_eff_capped"),
                },
            }
    return result


def _fmt(x, nd=3):
    return "None" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def main() -> int:
    res = recompute()
    OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n")
    hdr = f"{'case':17s} {'arm':9s} {'k':>2s} {'k_eff':>5s} {'φ̄_old':>7s} {'neff_old':>8s} " \
          f"{'φ̄_new':>7s} {'Kish':>6s} {'eig':>6s} {'φ̄ CI':>16s}  flags"
    print(hdr)
    print("-" * len(hdr))
    for case, cd in res["cases"].items():
        for arm, a in cd["arms"].items():
            ci = a["bootstrap_ci"]
            ci_s = f"[{ci['phi_bar_lo']:.2f},{ci['phi_bar_hi']:.2f}]" if ci else "—"
            flags = []
            if a["degenerate"]:
                flags.append(f"excl {len(a['excluded_assessors'])}")
            if a["inert"]:
                flags.append("INERT")
            if ci and ci["includes_one"]:
                flags.append("CI∋1")
            print(f"{case:17s} {arm:9s} {a['k']:>2d} {a['k_effective']:>5d} "
                  f"{_fmt(a['pre_fix']['phi_bar'],4):>7s} {_fmt(a['pre_fix']['n_eff']):>8s} "
                  f"{_fmt(a['phi_bar'],4):>7s} {_fmt(a['kish_ess']):>6s} "
                  f"{_fmt(a['eigenvalue_ess']):>6s} {ci_s:>16s}  {', '.join(flags)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

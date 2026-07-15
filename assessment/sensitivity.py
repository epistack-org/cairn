"""Price the refusal knob — the two sensitivity curves for writeup §5 (draft-entry#18).

The Fréchet interval is a *theorem* (forced by the marginals); the REFUSE is a
*policy* (a chosen ``max_width_decades`` threshold — Chow 1970's reject option, not
mathematical necessity). This makes that policy auditable by publishing:

  1. **verdict-vs-threshold** — sweep ``max_width_decades`` and record where the
     verdict flips. The shared trio refuses for any threshold < log10(25) ≈ 1.398
     decades; the double-count for any < log10(5) ≈ 0.699.
  2. **verdict-vs-LR** — sweep the per-line likelihood ratio across the published
     zoonosis↔lab-leak range (Stansifer 1/10,000 → Rootclaim 13.48) at the default
     0.5-decade threshold, and confirm the trio REFUSE survives the whole range
     (it combines only in a narrow band around LR≈1 where the evidence is ~inert).

The illustrative_LR = 5.0 ×3 → [5, 125] endpoints are OURS: the run labels the
marginals ``illustrative`` and this script re-asserts that flag. The true
dependence-free bound is vacuous ([0,∞] → posterior [0,1]); everything narrower is
a *declared* LR^m redundancy model — kept labelled here.

    python assessment/sensitivity.py       # rewrites assessment/sensitivity.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from cairn import frechet

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assessment" / "sensitivity.json"

# the published LR anchors across the zoonosis <-> lab-leak spectrum
LR_ANCHORS = {
    "stansifer_zoonosis_1e-4": 1.0 / 10000.0,
    "illustrative_corpus_LR": 5.0,
    "rootclaim_lab_leak": 13.48,
}


def _verdict(lrs, threshold):
    v = frechet.frechet_verdict(lrs, shared_upstream=True, max_width_decades=threshold)
    return v["verdict"], v


def threshold_curve() -> dict:
    """Sweep max_width_decades; record verdict for the trio and the double-count."""
    scenarios = {
        "trio_LR5x3": [5.0, 5.0, 5.0],       # width = log10(125/5) = 1.39794
        "double_count_LR5x2": [5.0, 5.0],    # width = log10(25/5)  = 0.69897
    }
    thresholds = [round(0.1 * i, 4) for i in range(0, 21)]  # 0.0 .. 2.0 by 0.1
    out = {}
    for name, lrs in scenarios.items():
        # width is threshold-invariant; compute once
        w = frechet.frechet_verdict(lrs, shared_upstream=True)["width_decades"]
        rows = [{"threshold": t, "verdict": _verdict(lrs, t)[0]} for t in thresholds]
        # exact flip point: REFUSE iff width > threshold, so the boundary is width itself
        out[name] = {
            "width_decades": w,
            "refuses_below_threshold": w,   # any threshold < width -> REFUSE
            "curve": rows,
        }
    return out


def lr_curve() -> dict:
    """Sweep per-line LR for the shared trio at the default 0.5-decade threshold."""
    thr = frechet.DEFAULT_MAX_WIDTH_DECADES
    # geometric grid across the published range, plus the exact combine-band edges
    grid = []
    lr = 1e-4
    while lr <= 20.0 + 1e-9:
        grid.append(lr)
        lr *= 10 ** 0.25
    # analytic combine band for k=3 equal lines: width = 2*|log10 LR|; REFUSE when >thr
    band_lo = 10 ** (-thr / 2.0)   # LR below which (approaching 1 from below) it COMBINES
    band_hi = 10 ** (thr / 2.0)
    for edge in (band_lo, band_hi, 1.0):
        grid.append(edge)
    grid = sorted(set(round(x, 6) for x in grid))

    rows = []
    for lr in grid:
        v = frechet.frechet_verdict([lr, lr, lr], shared_upstream=True, max_width_decades=thr)
        rows.append({
            "LR": lr,
            "width_decades": v["width_decades"],
            "verdict": v["verdict"],
            "interval_lr": v["interval_lr"],
            "illustrative_marginals": v["marginals"]["illustrative"],
        })

    anchors = {}
    for label, lr in LR_ANCHORS.items():
        v = frechet.frechet_verdict([lr, lr, lr], shared_upstream=True, max_width_decades=thr)
        anchors[label] = {
            "LR": lr, "verdict": v["verdict"], "width_decades": v["width_decades"],
            "interval_lr": v["interval_lr"], "illustrative_marginals": v["marginals"]["illustrative"],
        }

    all_anchors_refuse = all(a["verdict"] == "REFUSE-TO-COMBINE-AS-POINT" for a in anchors.values())
    return {
        "threshold_decades": thr,
        "k": 3,
        "combine_band_LR": [band_lo, band_hi],
        "note": ("Trio REFUSES for every LR outside the narrow combine band around LR=1 "
                 "(where per-line evidence is ~inert). All published anchors REFUSE."),
        "all_published_anchors_refuse": all_anchors_refuse,
        "anchors": anchors,
        "curve": rows,
    }


def build() -> dict:
    return {
        "note": "Sensitivity curves for the refusal knob (draft-entry#18). The interval is a "
                "theorem; the threshold is a policy (Chow 1970). The [5,125] endpoints are "
                "illustrative (marginals flagged illustrative). Recompute: assessment/sensitivity.py.",
        "verdict_vs_threshold": threshold_curve(),
        "verdict_vs_LR": lr_curve(),
    }


def main() -> int:
    art = build()
    OUT.write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}\n")
    t = art["verdict_vs_threshold"]
    print("verdict-vs-threshold (REFUSE iff threshold < width):")
    for name, d in t.items():
        print(f"  {name:20s} width={d['width_decades']:.5f} decades "
              f"-> REFUSE for any threshold < {d['refuses_below_threshold']:.5f}")
    lc = art["verdict_vs_LR"]
    print(f"\nverdict-vs-LR (trio, threshold={lc['threshold_decades']} decades):")
    print(f"  combine band LR in ({lc['combine_band_LR'][0]:.4f}, {lc['combine_band_LR'][1]:.4f}); "
          f"outside -> REFUSE")
    print(f"  all published anchors REFUSE: {lc['all_published_anchors_refuse']}")
    for label, a in lc["anchors"].items():
        print(f"    {label:26s} LR={a['LR']:<9g} {a['verdict']:26s} "
              f"width={a['width_decades']:.3f} illustrative={a['illustrative_marginals']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

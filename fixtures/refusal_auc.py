"""Refusal-AUC over the fixture corpus (flf-contest#6).

Abstention scored as **discrimination**, not as a rate. A detector that always
refuses has a trivially perfect "refusal rate" and is worthless; the honest
question is whether the refusal *discriminates* — does it fire on claim-sets whose
provenance structure is known to be entangled, and hold its fire on sets known to be
disjoint? We score that as the AUC of the shared-upstream count over a hand-labeled
panel of known-structure claim-sets (ground truth from the primary literature, not
from the engine).

Score = number of shared upstreams the DAG walk finds (0 for a genuinely disjoint
set). AUC = P(score(entangled) > score(disjoint)) with ties at 0.5 (Mann-Whitney U /
mn). Perfect separation → 1.0. This is deliberately a *small, known-structure* panel
— a handful of sets is enough to show the refusal is not `print("REFUSE")`.

    python fixtures/refusal_auc.py     # recompute + rewrite fixtures/refusal_auc.json
"""
from __future__ import annotations

import json
from itertools import product
from pathlib import Path

from cairn import provenance

FX = Path(__file__).resolve().parent
INDEX = json.loads((FX / "INDEX.json").read_text())


def _store() -> dict[str, dict]:
    store = {}
    for slug in INDEX:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return store


def _naive_store() -> tuple[dict, dict]:
    nd = FX / "naive"
    idx = json.loads((nd / "INDEX.json").read_text())
    store = {}
    for slug in idx:
        rec = json.loads((nd / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return idx, store


# The labeled panel. `label`: 1 == known-entangled (should REFUSE), 0 == known-disjoint
# (should COMBINE). Each carries a one-line ground-truth rationale from the literature.
CASES = [
    # ---- known-ENTANGLED (positives) ----
    (1, "covid-proximity-trio", ["claim-geographic-clustering", "claim-environmental-sampling",
                                 "claim-live-mammal-sales"],
     "one paper (Worobey 2022); two of three also share the PRC early-case investigation"),
    (1, "covid-worobey-x-pekar", ["claim-geographic-clustering", "claim-two-lineages"],
     "Pekar cites Worobey (ref [39]) and calibrates its clock on Worobey 2021 — the former false COMBINABLE"),
    (1, "eggs-meta-analysis-trio", ["claim-eggs-rong-no-association", "claim-eggs-godos-no-association",
                                    "claim-eggs-drouin-no-association"],
     "all re-pool the NHS/HPFS cohort backbone (shared two hops up)"),
    (1, "cern-cosmic-ray-trio", ["claim-cern-astro-stability", "claim-cern-wd-ns-bound",
                                 "claim-cern-moon-strangelet"],
     "three assurances leaning on the one cosmic-ray/astrophysical-survival premise"),
    (1, "eggs-two-meta-analyses", ["claim-eggs-rong-no-association", "claim-eggs-godos-no-association"],
     "two meta-analyses re-pooling the same cohort backbone"),
    (1, "cern-astro-x-moon", ["claim-cern-astro-stability", "claim-cern-moon-strangelet"],
     "two papers, one shared cosmic-ray premise"),
    # ---- backtest-scaling imports (dev/cairn#15): known-answer fraud / non-independence sets ----
    (1, "ivermectin-elgazzar-trio", ["claim-iver-bryant", "claim-iver-zein", "claim-iver-kory"],
     "three positive syntheses all pooling the withdrawn Elgazzar trial (shared two hops up)"),
    (1, "anversa-ckit-trio", ["claim-anversa-origin", "claim-anversa-human", "claim-anversa-scipio"],
     "one lab's c-kit+ CSC characterization + shared cell preps (SCIPIO used the lab's own cells)"),
    (1, "poldermans-decrease-trio", ["claim-decrease-1", "claim-decrease-boersma", "claim-decrease-4"],
     "one compromised research program (the Poldermans/Erasmus DECREASE family)"),
    # ---- known-DISJOINT (negatives) ----
    (0, "eggs-hu-x-djousse", ["claim-eggs-hu-no-association", "claim-eggs-djousse-no-association"],
     "NHS/HPFS vs the disjoint Physicians' Health Study cohort"),
    (0, "cern-hawking-x-wd-ns", ["claim-cern-hawking-evaporation", "claim-cern-wd-ns-bound"],
     "theoretical Hawking evaporation vs the empirical WD/NS bound — disjoint premises by construction"),
    (0, "cern-production-rate-x-astro", ["claim-cern-bh-production-rate", "claim-cern-astro-stability"],
     "a particle-physics rate calc vs the cosmic-ray argument — disjoint upstreams"),
    (0, "covid-single-line", ["claim-geographic-clustering"],
     "a lone claim shares no upstream with itself (singleton guard)"),
    (0, "ivermectin-bryant-x-together", ["claim-iver-bryant", "claim-iver-together"],
     "an Elgazzar-based meta vs the disjoint TOGETHER RCT (which never ingested Elgazzar)"),
    (0, "anversa-x-caduceus", ["claim-anversa-origin", "claim-anversa-caduceus"],
     "the Anversa c-kit+ line vs the disjoint Marbán cardiosphere-derived cells (CADUCEUS)"),
    (0, "poldermans-x-poise", ["claim-decrease-1", "claim-poise"],
     "a DECREASE benefit claim vs the disjoint independent POISE trial"),
]


def score_case(ids, store) -> int:
    v = provenance.combine_verdict(ids, store)
    return len(v["shared_upstreams"])


def auc(scored) -> float:
    pos = [s for lbl, s in scored if lbl == 1]
    neg = [s for lbl, s in scored if lbl == 0]
    if not pos or not neg:
        return float("nan")
    wins = sum((sp > sn) + 0.5 * (sp == sn) for sp, sn in product(pos, neg))
    return wins / (len(pos) * len(neg))


def build() -> dict:
    store = _store()
    naive_idx, naive_store = _naive_store()
    rows, scored = [], []
    for label, name, slugs, why in CASES:
        # the naive-DAG variant of the Worobey×Pekar set is scored from fixtures/naive/
        if name == "covid-worobey-x-pekar-naive":
            continue
        ids = [INDEX[s] for s in slugs]
        v = provenance.combine_verdict(ids, store)
        s = len(v["shared_upstreams"])
        rows.append({"set": name, "label": label, "score": s, "verdict": v["verdict"],
                     "predicted_refuse": s > 0, "correct": (s > 0) == bool(label),
                     "ground_truth": why})
        scored.append((label, s))
    a = auc(scored)
    tp = sum(1 for r in rows if r["label"] == 1 and r["predicted_refuse"])
    fp = sum(1 for r in rows if r["label"] == 0 and r["predicted_refuse"])
    fn = sum(1 for r in rows if r["label"] == 1 and not r["predicted_refuse"])
    tn = sum(1 for r in rows if r["label"] == 0 and not r["predicted_refuse"])
    # cross-check that the naive-DAG Worobey×Pekar (the cautionary run) does NOT refuse
    npair = [naive_idx["claim-geographic-clustering"], naive_idx["claim-two-lineages"]]
    naive_wxp = provenance.combine_verdict(npair, naive_store)["verdict"]
    return {
        "note": "Refusal-AUC over a hand-labeled panel of known-provenance claim-sets "
                "(flf-contest#6). Abstention scored as discrimination, not as a rate. "
                "Score = shared-upstream count; AUC = P(entangled > disjoint), ties 0.5. "
                "Recompute with fixtures/refusal_auc.py.",
        "n_positive": sum(1 for r in rows if r["label"] == 1),
        "n_negative": sum(1 for r in rows if r["label"] == 0),
        "refusal_auc": a,
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "naive_worobey_pekar_verdict": naive_wxp,
        "cases": rows,
    }


def main() -> int:
    art = build()
    (FX / "refusal_auc.json").write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n")
    print(f"refusal-AUC = {art['refusal_auc']:.4f} over {art['n_positive']} entangled "
          f"+ {art['n_negative']} disjoint known-structure sets")
    print(f"  confusion: {art['confusion']}  (naive Worobey×Pekar → {art['naive_worobey_pekar_verdict']})")
    for r in art["cases"]:
        mark = "ok " if r["correct"] else "XX "
        print(f"  {mark}{r['set']:28s} label={r['label']} score={r['score']} -> {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Mechanical re-check of an A2 assessment run — the n_eff analog of grounding.py.

A2 measures *effective independence* over a panel of
heterogeneous assessors. The live run is non-deterministic (model calls); its
**result** is pinned as an ``epi:Cluster`` "assessment-run" record whose assertion
carries every assessor's raw answers, the derived binary matrix, and the computed
n_eff. This module recomputes the matrix and n_eff straight from the recorded
answers + the probe battery and asserts they match what was pinned — so a fresh
machine verifies the headline number with **no model access at all**. ``cairn
assess`` is the CLI door (nonzero exit == a recomputation disagreed).

Binarization (kept here so build- and check-time share one definition):
  * affirm bit — YES -> 1, else (NO | UNCERTAIN | missing) -> 0. The vector fed to
    neff.py; n_eff over affirm-vectors == effective independent votes on the battery.
  * correct bit — keyed probes only: answer == key -> 1, else -> 0. A secondary
    reliability / error-correlation readout (UNCERTAIN counts as not-correct).
"""
from __future__ import annotations

from typing import Any, Sequence

from . import neff

AFFIRM_TRUE = "YES"
ANSWER_SPACE = ("YES", "NO", "UNCERTAIN")
_NEFF_KEYS = ("k", "phi_bar", "n_eff", "n_eff_capped")


def affirm_bit(answer: str) -> int:
    return 1 if answer == AFFIRM_TRUE else 0


def correct_bit(answer: str, key: str) -> int:
    return 1 if answer == key else 0


def probe_ids(battery: dict) -> list[str]:
    return [p["id"] for p in battery["probes"]]


def affirm_vector(answers: dict, battery: dict) -> list[int]:
    """Binary affirm-vector in battery-probe order (missing answer -> UNCERTAIN -> 0)."""
    return [affirm_bit(answers.get(p["id"], "UNCERTAIN")) for p in battery["probes"]]


def reliability(answers: dict, battery: dict) -> dict:
    """Per-assessor keyed-probe reliability: {keyed, correct} over probes with a YES/NO key."""
    keyed = [p for p in battery["probes"] if p.get("key") in ("YES", "NO")]
    hits = sum(correct_bit(answers.get(p["id"], "UNCERTAIN"), p["key"]) for p in keyed)
    return {"keyed": len(keyed), "correct": hits}


def pairwise_phi(vectors: Sequence[Sequence[int]]) -> list[dict]:
    """Flat list of {i, j, phi} over all assessor pairs (material for A3's interval)."""
    out = []
    for i in range(len(vectors)):
        for j in range(i + 1, len(vectors)):
            out.append({"i": i, "j": j, "phi": neff.phi(vectors[i], vectors[j])})
    return out


def hamming(u: Sequence[int], v: Sequence[int]) -> int:
    return sum(1 for a, b in zip(u, v) if a != b)


def mean_pairwise_hamming(vectors: Sequence[Sequence[int]]) -> float:
    """Mean disagreement count over all assessor pairs — an interpretable companion to phi_bar."""
    pairs = [(i, j) for i in range(len(vectors)) for j in range(i + 1, len(vectors))]
    if not pairs:
        return 0.0
    return sum(hamming(vectors[i], vectors[j]) for i, j in pairs) / len(pairs)


def vendor_decomposition(vectors_a: Sequence[Sequence[int]], vectors_b: Sequence[Sequence[int]]) -> dict:
    """Within-A, within-B, and cross (A×B) mean phi + combined n_eff over A∪B.

    Isolates the vendor axis: if cross-vendor phi ≈ within-vendor phi, assessor
    agreement is driven by the evidence, not shared model lineage — cross-vendor
    diversity does not manufacture independence.
    """
    cross_vals = [neff.phi(u, v) for u in vectors_a for v in vectors_b]
    cross = sum(cross_vals) / len(cross_vals) if cross_vals else 0.0
    return {
        "within_a": neff.mean_phi(vectors_a),
        "within_b": neff.mean_phi(vectors_b),
        "cross": cross,
        "combined": neff.neff_from_matrix(list(vectors_a) + list(vectors_b)),
        "n_a": len(vectors_a),
        "n_b": len(vectors_b),
    }


def analyze(answers_by_assessor: Sequence[dict], battery: dict) -> dict:
    """Pure analysis: answers -> vectors -> {vectors, neff, pairwise_phi}. No records."""
    vectors = [affirm_vector(a, battery) for a in answers_by_assessor]
    return {
        "vectors": vectors,
        "neff": neff.neff_from_matrix(vectors),
        "pairwise_phi": pairwise_phi(vectors),
    }


def check_run(run: dict, battery: dict, *, tol: float = 1e-9) -> dict:
    """Recompute matrix + n_eff from the run's recorded answers; compare to pinned.

    ``ok`` is False if any recorded ``affirm_vector``, the matrix, the declared
    probe order, or the pinned ``neff`` disagrees with a fresh recomputation.
    """
    a = run["assertion"]
    ids = probe_ids(battery)
    checks: list[dict] = []
    ok = True

    order_ok = a.get("probe_ids") == ids
    ok = ok and order_ok

    recomputed = []
    for asr in a["assessors"]:
        want = affirm_vector(asr["answers"], battery)
        got = asr.get("affirm_vector")
        vok = got == want
        recomputed.append(want)
        checks.append({
            "assessor": asr.get("assessor"),
            "vector_ok": vok,
            "reliability": reliability(asr["answers"], battery),
        })
        ok = ok and vok

    matrix_ok = a.get("vectors") == recomputed
    ok = ok and matrix_ok

    fresh = neff.neff_from_matrix(recomputed) if recomputed else {k: 0.0 for k in _NEFF_KEYS}
    pinned = a.get("neff", {})

    def _neff_key_ok(k: str) -> bool:
        if k not in pinned:
            return False
        fv, pv = fresh.get(k), pinned.get(k)
        # An inert (all-degenerate) cluster records None for phi_bar/n_eff/n_eff_capped — a valid
        # recorded result (nobody affirmed anything; the instrument is inert), not drift. Match
        # None==None; only float-compare when both endpoints are real numbers.
        if fv is None or pv is None:
            return fv is None and pv is None
        return abs(float(fv) - float(pv)) <= tol

    neff_ok = all(_neff_key_ok(k) for k in _NEFF_KEYS)
    ok = ok and neff_ok

    return {
        "ok": ok,
        "panel": a.get("panel"),
        "probeSet": a.get("probeSet"),
        "order_ok": order_ok,
        "matrix_ok": matrix_ok,
        "neff_ok": neff_ok,
        "recomputed_neff": fresh,
        "k": fresh["k"],
        "phi_bar": fresh["phi_bar"],
        "n_eff": fresh["n_eff"],
        "checks": checks,
    }

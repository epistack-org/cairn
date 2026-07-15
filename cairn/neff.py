"""Kish design-effect ESS (clustering component) over a correlated assessor panel.

**Estimand (one sentence).** The statistic ``k / (1 + (k-1)·φ̄)`` is the *Kish
design-effect effective sample size, clustering component*: the variance-inflation
factor of the panel's mean affirmation. We use it as a **redundancy diagnostic**,
not as an estimator of anything — specifically as a *falsification test on the
provenance DAG* (an n_eff near k on a same-upstream panel would falsify the claim
that those assessors are redundant). It is decidedly **not** the survey-weighting
ESS ``(Σw)²/Σw²`` that "Kish effective sample size" sometimes denotes.

    n_eff = k / (1 + (k - 1) * phi_bar)

``phi_bar`` is the mean pairwise φ coefficient (Pearson correlation on binary
agreement vectors). Refs: Kish, *Survey Sampling* (1965) — the design effect
``deff = 1 + (k-1)ρ``; Shrout & Fleiss (1979) — φ̄ read as an intraclass
correlation over the panel. Empirical anchor: a 9-judge panel across 7 model
families measured n_eff ≈ 2.2 ("Nine Judges, Two Effective Votes",
arXiv:2605.29800) — i.e. φ̄ ≈ 0.386 (this module's anchor test pins it).

**The degeneracy rule (mode-aware, never a silent φ=0).** When an assessor's
affirm-vector is *constant* (affirmed nothing, or affirmed everything) its linear
correlation with anyone is **undefined**, not zero. Coding it as φ=0 would score a
do-nothing assessor as a maximally *independent* vote — inflating n_eff in exactly
the flattering direction. So ``phi`` returns ``nan`` for the constant case, and
``neff_from_matrix`` **excludes** degenerate assessors with an explicit ``k``
reduction (surfacing ``degenerate``/``excluded``/``k_effective``). A panel whose
assessors *all* went constant is **inert**: there is no agreement variance to
measure, and n_eff is reported as ``None`` (undefined), never the ceiling ``k``.

Alongside the Kish clustering ESS we ship the assumption-lighter **eigenvalue ESS**
``k / λ_max`` (λ_max = largest eigenvalue of the panel correlation matrix) and a
**bootstrap CI on φ̄** (resampling probes) so the point estimate travels with its
own uncertainty instead of a single-pair min/max p-box.

Used two ways in Cairn:
  * over *assessors* of one claim (the original Kish use), and
  * over a *set of claims proposed as independent* (their agreement vectors) —
    when they share an upstream (see provenance.py) their vectors co-move,
    φ̄ → 1, n_eff → 1, and the combined number is refused.
"""
from __future__ import annotations

import itertools
import math
import random
from typing import Sequence

Vector = Sequence[int]  # binary 0/1 per item

# deterministic default seed for the φ̄ bootstrap (re-checkable on a fresh machine)
_BOOTSTRAP_SEED = 20260715
_BOOTSTRAP_N = 2000


def is_degenerate(v: Vector) -> bool:
    """A constant affirm-vector (all 0 or all 1) — zero variance, correlation undefined."""
    return len(set(v)) <= 1


def phi(a: Vector, b: Vector) -> float:
    """Phi coefficient = Pearson correlation of two equal-length binary vectors.

    Zero-variance case: if either vector is constant (an always-affirm or
    never-affirm assessor), linear correlation is **undefined** and we return
    ``float('nan')`` — *not* 0.0. Returning 0.0 would report a do-nothing assessor
    as perfectly *independent* (φ=0 → higher n_eff), which understates correlation
    in precisely the direction that flatters an independence headline. Callers that
    aggregate (``mean_phi``, ``neff_from_matrix``) exclude degenerate assessors up
    front so a nan never poisons a mean.
    """
    if len(a) != len(b):
        raise ValueError("vectors must be the same length")
    n = len(a)
    if n == 0:
        raise ValueError("empty vectors")
    sa, sb = sum(a), sum(b)
    sab = sum(x * y for x, y in zip(a, b))
    num = n * sab - sa * sb
    den = math.sqrt((n * sa - sa * sa) * (n * sb - sb * sb))
    if den == 0:
        return float("nan")  # undefined — a constant vector; the caller must exclude it
    return num / den


def mean_phi(vectors: Sequence[Vector]) -> float:
    """Mean pairwise φ over all k·(k-1)/2 pairs of the *given* vectors.

    Assumes the caller has already dropped degenerate (constant) vectors; a
    constant vector here would inject nan. Returns 0.0 when there are no pairs.
    """
    pairs = list(itertools.combinations(range(len(vectors)), 2))
    if not pairs:
        return 0.0
    return sum(phi(vectors[i], vectors[j]) for i, j in pairs) / len(pairs)


def kish_neff(k: int, phi_bar: float) -> float:
    """Kish design-effect ESS (clustering component) from panel size and mean φ.

    Guard: a sufficiently anti-correlated panel drives the denominator to <= 0
    (e.g. a perfectly anti-correlated pair, phi_bar = -1). Effective independent
    votes cannot exceed the real panel size, so we cap at ``k`` there rather than
    returning a blow-up.
    """
    if k <= 1:
        return float(k)
    denom = 1.0 + (k - 1) * phi_bar
    if denom <= 0:
        return float(k)
    return k / denom


def _corr_matrix(vectors: Sequence[Vector]) -> list[list[float]]:
    """Panel correlation matrix (φ off-diagonal, 1.0 on the diagonal). Non-degenerate only."""
    k = len(vectors)
    R = [[1.0] * k for _ in range(k)]
    for i in range(k):
        for j in range(i + 1, k):
            R[i][j] = R[j][i] = phi(vectors[i], vectors[j])
    return R


def _lambda_max(R: Sequence[Sequence[float]], iters: int = 2000, tol: float = 1e-13) -> float:
    """Largest eigenvalue of a symmetric PSD (correlation) matrix, via power iteration.

    Stdlib-only (no numpy). A correlation matrix is PSD so every eigenvalue is >= 0
    and λ_max is the largest in magnitude — exactly what power iteration converges
    to. Returns the Rayleigh quotient of the converged (unit) vector.
    """
    n = len(R)
    if n == 0:
        return 0.0
    if n == 1:
        return float(R[0][0])
    x = [1.0] * n
    lam = 0.0
    for _ in range(iters):
        y = [sum(R[i][j] * x[j] for j in range(n)) for i in range(n)]
        norm = math.sqrt(sum(v * v for v in y))
        if norm == 0.0:
            return 0.0
        x = [v / norm for v in y]
        rq = sum(x[i] * sum(R[i][j] * x[j] for j in range(n)) for i in range(n))
        if abs(rq - lam) < tol:
            return rq
        lam = rq
    return lam


def eigenvalue_ess(vectors: Sequence[Vector]) -> float | None:
    """Eigenvalue ESS = k / λ_max over the panel correlation matrix (assumption-lighter).

    The stat the anchor paper (arXiv:2605.29800) itself runs. Independent of the
    Kish additive-φ̄ model: identical vectors (rank-1 R) give λ_max = k → ESS = 1;
    orthogonal vectors give λ_max = 1 → ESS = k. ``None`` if fewer than one
    non-degenerate assessor remains.
    """
    kept = [v for v in vectors if not is_degenerate(v)]
    if not kept:
        return None
    if len(kept) == 1:
        return 1.0
    lam = _lambda_max(_corr_matrix(kept))
    if lam <= 0.0:
        return float(len(kept))
    return len(kept) / lam


def bootstrap_phi_ci(vectors: Sequence[Vector], *, n_boot: int = _BOOTSTRAP_N,
                     seed: int = _BOOTSTRAP_SEED, ci: float = 0.95) -> dict | None:
    """Percentile bootstrap CI on φ̄ by resampling *probes* (the item axis).

    Replaces the old single-pair min/max p-box on n_eff. Resamples the probe
    columns with replacement ``n_boot`` times; per replicate recomputes φ̄ over the
    non-degenerate assessor pairs (a resample that flattens an assessor to constant
    drops that pair). Deterministic given ``seed``. Also maps the φ̄ CI through Kish
    to an n_eff CI (kish is decreasing in φ, so the endpoints invert). ``None`` when
    fewer than two non-degenerate assessors or no probes remain. ``includes_one`` is
    the honest "φ̄ = 1 is inside the CI" flag (the panel may be fully redundant).
    """
    kept = [list(v) for v in vectors if not is_degenerate(v)]
    k = len(kept)
    m = len(kept[0]) if kept else 0
    if k < 2 or m < 1:
        return None
    rng = random.Random(seed)
    phis: list[float] = []
    for _ in range(n_boot):
        cols = [rng.randrange(m) for _ in range(m)]
        res = [[v[c] for c in cols] for v in kept]
        vals = []
        for i in range(k):
            for j in range(i + 1, k):
                if is_degenerate(res[i]) or is_degenerate(res[j]):
                    continue
                vals.append(phi(res[i], res[j]))
        if vals:
            phis.append(sum(vals) / len(vals))
    if not phis:
        return None
    phis.sort()
    a = (1.0 - ci) / 2.0
    lo = phis[min(len(phis) - 1, int(a * len(phis)))]
    hi = phis[min(len(phis) - 1, int(math.ceil((1.0 - a) * len(phis))) - 1)]
    return {
        "phi_bar_lo": lo, "phi_bar_hi": hi,
        "n_eff_lo": min(float(k), kish_neff(k, hi)),   # kish decreasing: hi φ -> lo n_eff
        "n_eff_hi": min(float(k), kish_neff(k, lo)),
        "n_boot": n_boot, "n_valid": len(phis), "ci": ci, "seed": seed,
        "includes_one": hi >= 1.0 - 1e-9,
    }


def neff_from_matrix(vectors: Sequence[Vector]) -> dict:
    """Kish design-effect ESS (clustering component) from binary agreement vectors.

    **Degenerate assessors are excluded, never coded φ=0.** Constant affirm-vectors
    (affirmed nothing / everything) carry no agreement variance; we drop them and
    reduce ``k`` explicitly, surfacing ``degenerate`` (any dropped), ``excluded``
    (their indices) and ``k_effective`` (the retained count). The reported n_eff is
    over ``k_effective``.

    Keys:
      * ``k`` — the raw panel size (unchanged, for provenance).
      * ``k_effective`` — non-degenerate assessors actually measured.
      * ``degenerate`` / ``excluded`` — the exclusion audit.
      * ``phi_bar`` — mean pairwise φ over retained assessors (``None`` if < 2 kept).
      * ``kish_ess`` — the Kish clustering ESS over ``k_effective`` (== ``n_eff``).
      * ``eigenvalue_ess`` — the assumption-lighter ``k_effective / λ_max`` companion.
      * ``bootstrap_ci`` — percentile CI on φ̄ (+ its n_eff image), or ``None``.
      * ``n_eff`` / ``n_eff_capped`` — back-compat aliases of the Kish ESS
        (``n_eff_capped`` = ``min(n_eff, k_effective)``).
      * ``inert`` — True iff *every* assessor was degenerate (n_eff undefined).

    A wholly degenerate panel is **inert**: ``phi_bar``/``kish_ess``/``n_eff`` are
    ``None``. That is the correct reading of a control in which nobody affirmed
    anything — not the ceiling ``k``.
    """
    k = len(vectors)
    excluded = [i for i, v in enumerate(vectors) if is_degenerate(v)]
    kept = [v for v in vectors if not is_degenerate(v)]
    k_eff = len(kept)
    degenerate = len(excluded) > 0

    base = {
        "k": k, "k_effective": k_eff,
        "degenerate": degenerate, "excluded": excluded,
    }

    if k_eff == 0:
        # every assessor is constant — the instrument is inert, nothing to measure
        base.update({
            "inert": True, "phi_bar": None,
            "kish_ess": None, "eigenvalue_ess": None, "bootstrap_ci": None,
            "n_eff": None, "n_eff_capped": None,
        })
        return base

    if k_eff == 1:
        # a single engaged assessor is exactly one effective vote; no pairs -> no φ̄
        base.update({
            "inert": False, "phi_bar": None,
            "kish_ess": 1.0, "eigenvalue_ess": 1.0, "bootstrap_ci": None,
            "n_eff": 1.0, "n_eff_capped": 1.0,
        })
        return base

    pb = mean_phi(kept)
    kish = kish_neff(k_eff, pb)
    base.update({
        "inert": False, "phi_bar": pb,
        "kish_ess": kish, "eigenvalue_ess": eigenvalue_ess(kept),
        "bootstrap_ci": bootstrap_phi_ci(kept),
        "n_eff": kish, "n_eff_capped": min(kish, float(k_eff)),
    })
    return base

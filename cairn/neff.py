"""Kish effective sample size (n_eff) over correlated assessors.

This is the refuse-to-combine engine, quantified. "N assessors agreed" is a
headline lie when those assessors share errors: the *effective* number of
independent votes is

    n_eff = k / (1 + (k - 1) * phi_bar)

where ``phi_bar`` is the mean pairwise phi coefficient (Pearson correlation on
binary agreement/error vectors). Empirical anchor: a 9-judge panel across 7
model families measured n_eff ~= 2.2 ("Nine Judges, Two Effective Votes",
arXiv:2605.29800) — i.e. phi_bar ~= 0.386 (this module's anchor test pins it).

Used two ways in Cairn:
  * over *assessors* of one claim (the original Kish use), and
  * over a *set of claims proposed as independent* (their agreement vectors) —
    when they share an upstream (see provenance.py) their vectors co-move,
    phi_bar -> 1, n_eff -> 1, and the combined number is refused.
"""
from __future__ import annotations

import itertools
import math
from typing import Sequence

Vector = Sequence[int]  # binary 0/1 per item


def phi(a: Vector, b: Vector) -> float:
    """Phi coefficient = Pearson correlation of two equal-length binary vectors.

    Zero-variance guard: if either vector is constant (an always-agree or
    always-disagree assessor), linear correlation is undefined; we return 0.0
    (no measurable linear dependence) and document it rather than NaN-poison the
    mean. This is conservative for the *headline* direction — it never
    *understates* correlation.
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
        return 0.0
    return num / den


def mean_phi(vectors: Sequence[Vector]) -> float:
    """Mean pairwise phi over all k*(k-1)/2 assessor pairs."""
    pairs = list(itertools.combinations(range(len(vectors)), 2))
    if not pairs:
        return 0.0
    return sum(phi(vectors[i], vectors[j]) for i, j in pairs) / len(pairs)


def kish_neff(k: int, phi_bar: float) -> float:
    """Kish effective sample size from a panel size and mean pairwise correlation.

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


def neff_from_matrix(vectors: Sequence[Vector]) -> dict:
    """Compute n_eff from a list of binary agreement vectors (one per assessor).

    Returns {k, phi_bar, n_eff, n_eff_capped} where ``n_eff_capped`` = min(n_eff, k)
    is the honest "effective independent votes" headline (anti-correlated panels
    can push raw n_eff above k; you still never have more than k real assessors).
    """
    k = len(vectors)
    pb = mean_phi(vectors)
    raw = kish_neff(k, pb)
    return {"k": k, "phi_bar": pb, "n_eff": raw, "n_eff_capped": min(raw, float(k))}

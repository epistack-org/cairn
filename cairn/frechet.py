"""A3 — the Fréchet / p-box interval: an *honest interval* instead of a fake
point posterior, and a mechanical refusal when the interval is too wide to state.

This is the quantitative form of the A1 refuse-to-combine verdict. A naive
transcript that finds k "independent" lines each with likelihood ratio ``LR_i``
multiplies them (``prod LR_i``) into one confident point. When the lines share an
upstream (A1) that product is not just wrong, it is *undefined*: the honest object
is an interval whose **width is the refusal signal**.

Three regimes, correctly labelled and strictly nested — the whole point is to
never pass a tighter one off as a looser one:

  (2) FULL DEPENDENCE-AGNOSTIC FRÉCHET–HOEFFDING  — the *true* bound.
      Per world w, the conjunction P(⋀E_i | w) with marginals q obeys
      ``max(0, Σq-(k-1)) ≤ P(⋀E_i|w) ≤ min q`` (Fréchet–Hoeffding). The H- and
      ¬H-copulas are chosen *independently*, so combined LR ∈ [L_H/U_¬H, U_H/L_¬H].
      For the trio this is **[0, ∞] → posterior [0, 1]**: VACUOUS. With no
      dependence assumption at all, three co-present lines bound nothing — the
      naive 125:1 is not even bounded away from 0. That vacuity *is* delta-4.

  (2b) PLOD ENVELOPE — the positive-dependence envelope (disclosed companion).
      Restrict each world to positive dependence (joint ≥ independence): combined
      LR ∈ [prod(q_H)/min(q_¬H), min(q_H)/prod(q_¬H)]. Trio: **[1.25, 500]**.
      Crucially this is reached by a *single* copula (same coupling both worlds) —
      a copula's local dependence varies with the marginal threshold — so
      "same copula both worlds" buys nothing, and 125 is NOT a ceiling.

  (3) SYMMETRIC-REDUNDANCY INTERVAL — a DECLARED one-parameter model, NOT a bound.
      Interpolate comonotone(fully redundant) ↔ independent: combined LR = LR^{m},
      the effective-independent-count m ∈ [1, k]. Trio: **[5, 125]** = [LR, LR^k].
      This is the working regime the demo shows and where the A2-measured n_eff
      lives — but its floor (5, "the single strongest line") is a **cap on the
      assertion** ("don't multiply to 125"), *not* a proven lower bound: the PLOD
      envelope proves positive dependence can warrant as little as LR≈1.25.

  Nesting:  [5, 125]  ⊂  [1.25, 500]  ⊂  [0, ∞].

The decision rule fuses delta-3 (interval) and delta-4 (refusal): provenance is
the mechanical trigger (shared upstream → REDUNDANT regime), the redundancy
interval's log10-width is the quantitative witness, and a declared width knob
(default 0.5 decades — "a number you can't state within half an order of
magnitude is not a point") flips the verdict to REFUSE-TO-COMBINE-AS-POINT.

Everything here is a closed form over the marginals and the pinned pairwise-φ
arrays — deterministic, model-free, re-checkable on a fresh machine. (An optional
``pba`` cross-check lives in the demo/analysis layer; the core stays stdlib-only.)

Illustrative marginals: the fixtures pin an ``illustrative_LR`` (the *ratio*). A
concrete (p_H, p_¬H) is only needed to place the FULL/PLOD envelopes on the number
line; we realize it as ``p_¬H = base_neg`` (0.1), ``p_H = LR·base_neg`` and label
it illustrative. The redundancy interval and the verdict are ``base_neg``-invariant
for equal marginals.
"""
from __future__ import annotations

import math
from typing import Sequence

from . import neff

# --- declared policy / illustrative constants (all surfaced, none magic) ---
ILLUSTRATIVE_BASE_NEG = 0.1     # p(evidence | ¬H) realization; LR fixes only the ratio
DEFAULT_PRIOR = 0.5             # P(H); with 0.5 the posterior odds equal the combined LR
DEFAULT_MAX_WIDTH_DECADES = 0.5  # a point unstatable within half an order of magnitude is not a point


# --- probability / odds plumbing --------------------------------------------

def posterior(prior: float, lr: float) -> float:
    """Posterior P(H) from a prior and a combined likelihood ratio, via odds.

    ``O0 = prior/(1-prior)``; ``posterior = O0·lr / (1 + O0·lr)``. Strictly
    increasing in ``lr`` (so interval endpoints map order-preservingly), with the
    two limits pinned: ``lr → ∞`` ⇒ 1.0, ``lr ≤ 0`` ⇒ 0.0.
    """
    if lr == math.inf:
        return 1.0
    if lr <= 0.0:
        return 0.0
    if prior <= 0.0:
        return 0.0
    if prior >= 1.0:
        return 1.0
    o = (prior / (1.0 - prior)) * lr
    return o / (1.0 + o)


def marginals_from_lr(lr: float, base_neg: float = ILLUSTRATIVE_BASE_NEG) -> tuple[float, float]:
    """An *illustrative* (p_H, p_¬H) realizing a likelihood ratio ``lr``.

    ``p_¬H = base_neg``, ``p_H = lr·base_neg``. Raises if that pushes ``p_H ≥ 1``
    (an invalid probability) — which happens for ``lr ≥ 1/base_neg``; the corpus
    LRs (4, 5) never trip it, but combine-mode guards it rather than emit garbage.
    """
    p_h = lr * base_neg
    if not (0.0 <= p_h < 1.0):
        raise ValueError(
            f"illustrative p_H = LR·base_neg = {p_h} is not in [0,1) for LR={lr}, "
            f"base_neg={base_neg}; pick a smaller base_neg (LR must be < 1/base_neg)"
        )
    return (p_h, base_neg)


# --- per-world Fréchet–Hoeffding AND-corner bounds --------------------------

def world_and_bounds(marginals: Sequence[float]) -> tuple[float, float]:
    """Fréchet–Hoeffding bounds on P(⋀E_i) given per-item marginals in one world.

    ``L = max(0, Σq - (k-1))`` (the events can be made disjoint down to this),
    ``U = min(q)`` (comonotone). Returns ``(L, U)``.
    """
    q = list(marginals)
    k = len(q)
    lo = max(0.0, sum(q) - (k - 1))
    hi = min(q) if q else 0.0
    return (lo, hi)


# --- (1) naive independence point (what a transcript emits) -----------------

def naive_lr(lrs: Sequence[float]) -> float:
    """The independent-combination point: ``prod(LR_i)`` (the fake certainty)."""
    return math.prod(float(x) for x in lrs)


# --- (2) full dependence-agnostic Fréchet interval (the true delta-3 bound) --

def full_frechet_lr(p_H: Sequence[float], p_notH: Sequence[float]) -> tuple[float, float]:
    """Dependence-agnostic combined-LR interval: numerator/denominator copulas free.

    ``[L_H/U_¬H, U_H/L_¬H]`` with ``/0 → math.inf``. Trio ⇒ ``(0.0, inf)`` — vacuous.
    """
    L_H, U_H = world_and_bounds(p_H)
    L_N, U_N = world_and_bounds(p_notH)
    lo = math.inf if U_N == 0.0 else L_H / U_N
    hi = math.inf if L_N == 0.0 else U_H / L_N
    return (lo, hi)


# --- (2b) PLOD envelope (positive-dependence; disclosed companion) -----------

def plod_envelope_lr(p_H: Sequence[float], p_notH: Sequence[float]) -> tuple[float, float]:
    """Positive-dependence (joint ≥ independence, each world) combined-LR envelope.

    ``[prod(p_H)/min(p_¬H), min(p_H)/prod(p_¬H)]``. Trio ⇒ ``(1.25, 500.0)``.
    Reachable by a single copula, so it also bounds the same-copula case: this is
    why the [LR, LR^k] redundancy interval is a *model*, not a positive-dependence
    bound.
    """
    prod_H, prod_N = math.prod(p_H), math.prod(p_notH)
    min_H, min_N = min(p_H), min(p_notH)
    lo = math.inf if min_N == 0.0 else prod_H / min_N
    hi = math.inf if prod_N == 0.0 else min_H / prod_N
    return (lo, hi)


# --- (3) symmetric-redundancy interval (comonotone ↔ independent) -----------

def redundancy_lr(p_H: Sequence[float], p_notH: Sequence[float]) -> dict:
    """The declared redundancy model's endpoints, computed FROM MARGINALS.

    ``comonotone = min(p_H)/min(p_¬H)`` (full redundancy; == the single strongest
    line only for *equal* marginals), ``independent = prod(p_H)/prod(p_¬H) =
    prod(LR_i)``. Endpoints are sorted so ``floor ≤ ceiling`` (robust to LR<1 items,
    which invert the two — out of scope for the corpus but guarded not to crash).
    """
    comonotone = min(p_H) / min(p_notH)
    # independent-both == the product of the per-item LRs (prod(p_H)/prod(p_notH));
    # form it as prod(p_H_i/p_notH_i) so it is exact from the ratios, not reconstructed
    # magnitudes (0.5/0.1 == 5.0 exactly, whereas 0.125/0.1**3 carries float noise).
    independent = math.prod(h / n for h, n in zip(p_H, p_notH))
    lo, hi = sorted((comonotone, independent))
    return {"floor": lo, "ceiling": hi, "k": len(list(p_H)),
            "comonotone": comonotone, "independent": independent}


def effective_count_lr(floor: float, ceiling: float, k: int, m: float) -> float:
    """Place an effective-independent-count ``m ∈ [1, k]`` inside ``[floor, ceiling]``.

    ``floor·(ceiling/floor)^((m-1)/(k-1))`` — which equals ``LR^m`` for equal LRs
    (m=1 ⇒ floor/comonotone/full-redundancy; m=k ⇒ ceiling/independent). ``m`` is
    clamped to ``[1, k]``; ``k ≤ 1`` returns ``floor`` (no division by zero).
    """
    if k <= 1 or ceiling == floor:
        return floor
    m = max(1.0, min(float(k), float(m)))
    return floor * (ceiling / floor) ** ((m - 1) / (k - 1))


# --- (B) n_eff p-box from a pinned pairwise-φ array --------------------------

def neff_pbox(pairwise_phi: Sequence, k: int) -> dict:
    """Turn a pinned pairwise-φ array into an n_eff *interval* (dependence-structure
    uncertainty, not sampling error).

    ``kish_neff`` is decreasing in φ̄, so the endpoints invert:
    ``n_eff_lo = min(k, kish(k, φ_max))``, ``n_eff_hi = min(k, kish(k, φ_min))`` (both
    capped at k — an all-negative-φ panel would otherwise push either above the real
    panel size). Because φ̄ (a convex mean) lies in ``[φ_min, φ_max]``, the point
    estimate ``kish(k, φ̄)`` is *guaranteed* enclosed. A wide box = the number is untrustworthy (the honest
    reading is the ~1 floor, never the inflated ceiling); a tight box = trustworthy.

    Accepts a flat list of floats or the pinned ``[{"i","j","phi"}, ...]`` shape.
    Degenerate (``k < 2`` or no pairs) ⇒ a zero-width ``[1, 1]`` box.
    """
    phis = [e["phi"] if isinstance(e, dict) else float(e) for e in pairwise_phi]
    if k < 2 or len(phis) < 1:
        return {"phi_support": [1.0, 1.0], "n_eff_lo": 1.0, "n_eff_hi": 1.0,
                "n_eff_hi_uncapped": 1.0, "width": 0.0, "point": 1.0}
    phi_lo, phi_hi = min(phis), max(phis)
    n_lo = min(float(k), neff.kish_neff(k, phi_hi))   # cap at k: phi_max<0 would push kish>k (mirror n_eff_hi)
    n_hi_uncapped = neff.kish_neff(k, phi_lo)
    n_hi = min(float(k), n_hi_uncapped)
    point = min(float(k), neff.kish_neff(k, sum(phis) / len(phis)))
    return {"phi_support": [phi_lo, phi_hi], "n_eff_lo": n_lo, "n_eff_hi": n_hi,
            "n_eff_hi_uncapped": n_hi_uncapped, "width": n_hi - n_lo, "point": point}


# --- the one verdict (CLI + demo call this) ---------------------------------

def _ser(iv: tuple[float, float]) -> list:
    """JSON-safe interval: serialize math.inf as the string "inf"."""
    return [("inf" if x == math.inf else x) for x in iv]


def _ser1(x: float):
    """JSON-safe scalar: serialize math.inf as the string "inf" (matches _ser)."""
    return "inf" if x == math.inf else x


def frechet_verdict(lrs: Sequence[float], *, shared_upstream: bool,
                    prior: float = DEFAULT_PRIOR, base_neg: float = ILLUSTRATIVE_BASE_NEG,
                    n_eff: float | None = None,
                    max_width_decades: float = DEFAULT_MAX_WIDTH_DECADES) -> dict:
    """Combine a set of likelihood ratios into an honest interval + a refuse/combine
    verdict. ``shared_upstream`` (from A1 ``provenance.combine_verdict``) selects the
    regime; ``n_eff`` (from A2, optional) places the measured point in the interval.

    REDUNDANT (shared upstream): interval = the redundancy model ``[floor, ceiling]``;
    if ``log10(ceiling/floor) > max_width_decades`` ⇒ REFUSE-TO-COMBINE-AS-POINT
    (emit the interval + the floor as a capped bound; route the crux to a human),
    else COMBINABLE-WITH-INTERVAL emitting the floor (never the product).

    INDEPENDENT (disjoint upstreams): independence is licensed, so the product *is*
    the honest point; the interval degenerates to ``[prod, prod]`` (width 0) and the
    verdict is COMBINABLE-WITH-INTERVAL.
    """
    lrs = [float(x) for x in lrs]
    k = len(lrs)
    if k == 0:
        raise ValueError("frechet_verdict: no likelihood ratios to combine (empty claim set)")
    # Keep the illustrative marginals valid (p_H = LR*base_neg < 1) even for large LRs;
    # every load-bearing number (naive point, redundancy interval, verdict) is
    # base_neg-invariant, so this only rescales the disclosed companion envelopes.
    if base_neg * max(lrs) >= 1.0:
        base_neg = 0.5 / max(lrs)
    p_H, p_notH = [], []
    for lr in lrs:
        ph, pn = marginals_from_lr(lr, base_neg)
        p_H.append(ph)
        p_notH.append(pn)

    naive = naive_lr(lrs)
    ff = full_frechet_lr(p_H, p_notH)
    plod = plod_envelope_lr(p_H, p_notH)
    red = redundancy_lr(p_H, p_notH)
    floor, ceiling = red["floor"], red["ceiling"]

    def pv(iv):
        return [posterior(prior, iv[0]), posterior(prior, iv[1])]

    out = {
        "prior": prior, "k": k, "lrs": lrs,
        "marginals": {"p_H": p_H, "p_notH": p_notH, "base_neg": base_neg, "illustrative": True},
        "naive_lr": naive, "naive_posterior": posterior(prior, naive),
        "full_frechet_lr": _ser(ff), "full_frechet_posterior": pv(ff),
        "plod_envelope_lr": _ser(plod), "plod_envelope_posterior": pv(plod),
        "max_width_decades": max_width_decades,
    }

    if shared_upstream:
        width = math.log10(ceiling / floor) if floor > 0.0 and ceiling > 0.0 else math.inf
        verdict = "REFUSE-TO-COMBINE-AS-POINT" if width > max_width_decades else "COMBINABLE-WITH-INTERVAL"
        out.update({
            "regime": "REDUNDANT",
            "verdict": verdict,
            "interval_lr": [floor, ceiling],
            "interval_posterior": pv((floor, ceiling)),
            "width_decades": _ser1(width),
            # the comonotone (full-redundancy) value: a CAP on the assertion, not a proven
            # lower bound. Anchored on comonotone (not the sorted floor) so it stays correct
            # for LR<1 lines, where comonotone > independent and the sort would invert it.
            "honest_bound_lr": red["comonotone"],
            "honest_bound_posterior": posterior(prior, red["comonotone"]),
        })
        if n_eff is not None:
            # anchor the effective-count dial on the SEMANTIC endpoints (m=1 -> comonotone,
            # m=k -> independent), not the sorted [floor, ceiling], so n_eff=1 lands on the
            # full-redundancy value for LR<1 lines too (else it would report the product).
            m_lr = effective_count_lr(red["comonotone"], red["independent"], k, n_eff)
            out["measured"] = {"n_eff": n_eff, "lr": m_lr, "posterior": posterior(prior, m_lr)}
        else:
            out["measured"] = None
    else:
        out.update({
            "regime": "INDEPENDENT",
            "verdict": "COMBINABLE-WITH-INTERVAL",
            "interval_lr": [naive, naive],
            "interval_posterior": pv((naive, naive)),
            "width_decades": 0.0,
            "honest_bound_lr": naive,
            "honest_bound_posterior": posterior(prior, naive),
            "point_lr": naive,
            "point_posterior": posterior(prior, naive),
            "measured": None,
        })
    return out

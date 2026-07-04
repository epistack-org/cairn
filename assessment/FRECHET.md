# A3 — the Fréchet / p-box interval: an honest interval, not a fake point posterior

_Roadmap. This is the quantitative form of the A1
refuse-to-combine verdict: where A1 says **whether** you may combine (shared
upstream → no) and A2 measures **how few** effective votes you really have, A3
emits the **interval** you get when you honestly propagate that non-independence —
and refuses to state a point when the interval is too wide._

## 1. Thesis

A naive transcript that finds *k* "independent" lines, each with likelihood ratio
`LR_i`, multiplies them into one confident point (`∏ LR_i`). When the lines share
an upstream that product is not merely wrong, it is **undefined**: the honest
object is an **interval**, and **its width is the refusal signal**.

Three things are fused here:

- **delta 3** — a Fréchet/p-box *interval* replaces the point posterior;
- **delta 4** — a *principled refusal* when that interval is too wide to act on;
- and the trigger is **A1 provenance**: shared upstream → the redundant regime.

## 2. Setup

- **Crux / prior.** Same COVID-HSM crux as A2; prior `π = P(H) = 0.5`, so the
  posterior odds equal the combined LR and the arithmetic is transparent. The LR
  interval is prior-free; only the posterior endpoints assume `π = 0.5`.
- **Illustrative marginals.** The fixtures pin an `illustrative_LR` — a *ratio*,
  not a pair. A concrete `(p_H, p_¬H)` is only needed to place the magnitude
  envelopes; we realize it as `p_¬H = 0.1`, `p_H = LR·0.1` and **label it
  illustrative** (just like the LRs). The redundancy interval and the verdict are
  invariant to this choice for equal marginals.
- **The observation.** All three proximity lines affirmed (geographic clustering,
  environmental sampling, live-mammal sales), each `LR = 5`, **all `derivedFrom`
  the one Worobey-2022 dataset**.

## 3. Three regimes (+ the naive point they refute), correctly labelled and strictly nested

The whole discipline is to never pass a tighter regime off as a looser one.

| regime | trio combined-LR | posterior (π=0.5) | what it assumes |
|---|---:|---:|---|
| **naive point** | `125` | `0.992` | conditional independence (**false here**) |
| **full-agnostic Fréchet** (the true bound) | `[0, ∞]` | `[0, 1]` | *nothing* about dependence → **VACUOUS** |
| **PLOD envelope** (positive dependence) | `[1.25, 500]` | `[0.556, 0.998]` | each world's joint ≥ independence |
| **symmetric-redundancy model** | `[5, 125]` | `[0.833, 0.992]` | a *declared* comonotone↔independent interpolation |

**Nesting:** `[5, 125] ⊂ [1.25, 500] ⊂ [0, ∞]`.

- **Full-agnostic Fréchet–Hoeffding** is the *real* dependence-free bound. Per
  world *w*, `max(0, Σq−(k−1)) ≤ P(⋀E_i|w) ≤ min q`; the H- and ¬H-copulas are
  chosen independently, so for the trio the combined LR ranges over `[0, ∞]` and
  the posterior over `[0, 1]`. With **no** dependence assumption, three co-present
  lines bound *nothing* — the naive 125:1 is not even bounded away from 0. That
  vacuity *is* delta-4: you must refuse to compute.
  _Witnesses_ (`assessment/frechet_pba_check.py` reproduces the 2-event corners in
  the `pba` library): upper — H comonotone (common-U), ¬H a disjoint partition so
  `P(all|¬H)=0`; lower — H empty triple-intersection, ¬H comonotone.

- **PLOD envelope** restricts each world to *positive* dependence (joint ≥
  independence): `[prod(p_H)/min(p_¬H), min(p_H)/prod(p_¬H)] = [1.25, 500]`.
  Crucially a **single** copula reaches these corners — a copula's local dependence
  varies with the marginal threshold — so "same copula both worlds" buys nothing,
  and **125 is not a ceiling** (`pba` reaches an LR of 500 > 125; the double-count
  analogue reaches 50 > 25). This is why the next row is a *model*, not a bound.

- **Symmetric-redundancy model** interpolates comonotone (fully redundant) ↔
  independent along one parameter: `combined LR = LR^{m}`, `m ∈ [1, k]`. Trio:
  `[LR, LR^k] = [5, 125]`. This is the working regime the demo shows and where the
  A2-measured n_eff lives — **but its floor (5) is a *cap on the assertion* ("don't
  multiply to 125"), not a proven lower bound**: the PLOD envelope proves positive
  dependence can warrant as little as `LR ≈ 1.25`. We report all three regimes so
  the tight one is never mistaken for the loose one. (An adversarial verification
  pass — three independent refutations with LP certificates and explicit copula
  witnesses — is what forced this labelling; the first-pass "[5,125] is a Fréchet
  bound" was **refuted**.)

## 4. A1 → A2 → A3 on one DAG

- **A1 (provenance) picks the regime.** The three lines share the Worobey upstream
  → `REFUSE-TO-COMBINE` → the **redundant** regime. Disjoint upstreams (the
  contrast) → independence licensed → the product is the honest point.
- **A2 (measured n_eff) pins the point inside the box.** `combined LR = LR^{n_eff}`
  with `n_eff` the measured effective count. On this crux `n_eff ≈ 1`
  (homogeneous-control 1.00, clean-diverse 1.06, glm-diverse 1.05), so the honest
  estimate sits at the **redundant floor** (`5^1 = 5`, posterior 0.833) — **never**
  the product 125. Sensitivity: `n_eff=1.06 → 5.5`, `1.63 → 13.8`, `3 → 125`.

## 5. The n_eff p-box (dependence-structure uncertainty)

A2 collapsed the 36 pairwise-φ values to their mean φ̄. A3 propagates their
**spread** into an interval on n_eff. Since `kish` is *decreasing* in φ̄ the
endpoints invert: `n_eff_lo = kish(k, φ_max)`, `n_eff_hi = min(k, kish(k, φ_min))`.
Because φ̄ (a convex mean) lies in `[φ_min, φ_max]`, the point estimate is
**guaranteed enclosed**.

| panel | φ support | n_eff p-box | width | reading |
|---|---|---:|---:|---|
| homogeneous-control | `[1.00, 1.00]` | `[1.00, 1.00]` | 0.00 | perfectly trustworthy (= 1) |
| clean-diverse | `[0.71, 1.00]` | `[1.00, 1.34]` | 0.34 | tight → n_eff ≈ 1 is trustworthy |
| glm-diverse | `[0.87, 1.00]` | `[1.00, 1.14]` | 0.14 | tight (cross-vendor) |
| **heterogeneous** | `[−0.03, 1.00]` | `[1.00, 9.00]`¹ | **8.00** | **wide → the 1.63 is untrustworthy** |

¹ capped at `k=9`; uncapped `kish(9, φ_min) ≈ 11.36`, surfaced as
`n_eff_hi_uncapped` (the cap is an artifact of one near-zero pair). The wide box
**mechanizes the A2 audit**: the heterogeneous 1.63 is partition-starvation, not
competence — depending on which pairwise correlation typifies the panel, n_eff
could be anywhere from 1 to 9. The honest number is the floor (~1), never the
ceiling; the *width* is the ignorance.

## 6. The decision rule (delta 3 + delta 4)

Provenance is the mechanical trigger; the redundancy interval's log₁₀-width is the
quantitative witness; a **declared** knob (`max_width_decades`, default **0.5** — "a
number you cannot state within half an order of magnitude is not a point") flips the
verdict.

- **REDUNDANT** (shared upstream): interval `[floor, ceiling]`; if
  `log10(ceiling/floor) > 0.5` → **REFUSE-TO-COMBINE-AS-POINT** (emit the interval,
  the floor as a capped bound, route the crux to a human); else
  **COMBINABLE-WITH-INTERVAL** emitting the floor (never the product).
- **INDEPENDENT** (disjoint upstreams): the product *is* the honest point; the
  interval degenerates to `[prod, prod]`, width 0 → **COMBINABLE-WITH-INTERVAL**.

Worked:

- **Trio** — shared → `[5, 125]`, width `log10(25) = 1.398 > 0.5` → **REFUSE**,
  honest cap `LR ≤ 5`. (`cairn frechet` exits **2**.)
- **Contrast** `{proximity, molecular}` — disjoint upstreams → **COMBINABLE**,
  `LR = 5·4 = 20`, posterior 0.952. Never `125·4 = 500`. (exit **0**.)
- **Double-count** (two shared `LR=5` lines) — `[5, 25]`, width `log10(5) = 0.699 >
  0.5` → **REFUSE** (catches the textbook "don't count the same thing twice").

`cairn frechet` mirrors `cairn intersect`: exit **0** = combinable, **2** = refuse.

## 7. Worked-numbers oracle table (re-checkable to 1e-9)

```
posterior(0.5, LR):  125→0.9920634920634921   5→0.8333333333333334   20→0.9523809523809523
                       4→0.8                  25→0.9615384615384616  1.25→0.5555555555555556
                     500→0.998003992015968    inf→1.0                 0→0.0
naive_lr([5,5,5]) = 125.0
world_and_bounds([.5,.5,.5]) = (0.0, 0.5)     world_and_bounds([.1,.1,.1]) = (0.0, 0.1)
full_frechet (trio)  = (0.0, inf)      -> posterior (0.0, 1.0)   VACUOUS
plod_envelope (trio) = (1.25, 500.0)   -> posterior (0.556, 0.998)
redundancy (trio)    floor=5.0 ceiling=125.0  width_decades=1.3979400086720377
effective_count_lr(5,125,3, m):  m=1→5.0   m=2→25.0   m=3→125.0   (== LR^m)
n_eff p-box:  clean-diverse [1.0, 1.3404255319148937]   heterogeneous [1.0, 9.0] (uncapped ≈ 11.36)
contrast {5,4} disjoint -> point 20.0 (posterior 0.9523809523809523)
```

## 8. Determinism & self-verification (the A1/A2 mirror)

Every number is a **closed form** over the pinned fixtures + the pinned pairwise-φ
arrays — no model access, no Monte-Carlo.

- `assessment/frechet.json` — the pinned artifact (trio verdict, contrast verdict,
  the four n_eff p-boxes, the policy constants). `math.inf` serialized as `"inf"`.
- `assessment/build_frechet.py` — regenerates it; `test_artifact_recompute` asserts
  a fresh model-free recompute is dict-equal to what was pinned.
- **Container** self-verify chain runs `cairn frechet` on the trio and asserts
  **exit 2** — a fresh-machine proof of the refusal — before pytest.
- `tests/test_frechet.py` — 23 checks against the hand-derived oracles above.
- `assessment/frechet_pba_check.py` — the **`pba`** cross-check (an internal library,
  optional): an independent probability-bounds library confirms the Fréchet corners,
  the redundancy floor/ceiling, and that the naive product is not a ceiling. Not in
  the core or the container (`pba` pulls numpy/scipy/matplotlib); `pip install
  cairn[analysis]` to run it.

## 9. Honest limits

- **`[5, 125]` is a model, not a bound.** The floor (5) is a *cap on the
  assertion*, not a proven lower bound — positive dependence alone admits `LR ≈
  1.25`. We ship the true bound (`[0, ∞]`) and the positive-dependence envelope
  (`[1.25, 500]`) alongside it, correctly labelled.
- **Illustrative marginals.** `(0.5, 0.1)` set the magnitude of the full-agnostic /
  PLOD envelopes; they are labelled illustrative, and the redundancy interval /
  verdict are `base_neg`-invariant for equal marginals. `marginals_from_lr` raises
  for `LR ≥ 1/base_neg` (never tripped by the corpus LRs 4, 5).
- **Two populations.** A2's n_eff is over 9 *assessors*; the combine exponent *m*
  is over *k* *lines*. The trio's `m = 1` comes from A1 (three lines, one upstream =
  one effective line); A2's same-evidence `n_eff = 1.0` only *witnesses* it.
- **p-box non-robustness.** The min/max endpoints are single-pair-driven; the
  heterogeneous cap (9.0) is an artifact of one near-zero pair (uncapped ≈ 11.36,
  disclosed). Read **wide = untrustworthy**, and the floor (~1) as the honest
  number — never the ceiling.
- **Width knob.** `max_width_decades = 0.5` is a declared policy knob, surfaced on
  the CLI; the corpus verdicts are robust to it (trio width 1.40, double-count
  0.70, both ≫ 0.5).

## Reproduce

```bash
# deterministic (no model access):
.venv/bin/python assessment/build_frechet.py                       # rewrite the pinned artifact
.venv/bin/cairn frechet fixtures/claim-geographic-clustering.json \
  fixtures/claim-environmental-sampling.json fixtures/claim-live-mammal-sales.json \
  fixtures/src-worobey-2022.json --neff-run assessment/runs/homogeneous-control.json  # -> REFUSE, exit 2
.venv/bin/python -m pytest -q tests/test_frechet.py                # 23 checks

# optional analysis-layer cross-check (needs numpy/scipy/matplotlib):
.venv/bin/pip install pba && .venv/bin/python assessment/frechet_pba_check.py
```

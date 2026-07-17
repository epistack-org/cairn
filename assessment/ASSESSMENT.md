# A2 — Heterogeneous-assessor pass → measured n_eff

_Roadmap. This is the measured half of the Kish `n_eff` story:
`cairn/neff.py` had the formula; A2 feeds it **real agreement vectors** from a panel
of heterogeneous assessors on the COVID-Huanan-Seafood-Market (HSM) crux, replacing
the demo's hand-set `n_eff = 1.00`._

## The crux

> Did SARS-CoV-2 emerge via zoonotic spillover associated with the Huanan Seafood
> Wholesale Market, as opposed to a non-market or non-zoonotic introduction?

The evidence is the A1 corpus: the Worobey 2022 proximity trio + the Pekar 2022
molecular contrast. Assessors answer a **14-probe battery** (`probes.json`) — 8
*faithfulness* probes whose answer is objectively pinned to an A1 source span, plus 6
*inferential* crux probes — each seeing **only its granted evidence partition**
(`partitions.json`), instructed to reason **solely from that evidence**.

## The measured result

Four 9-assessor panels (three Anthropic, one cross-vendor GLM), each answering the
same battery. `phi_bar` (φ̄) is the mean pairwise φ-coefficient over the binary
affirm-vectors; `n_eff = k / (1 + (k-1)·φ̄)`.

| panel | what it isolates | φ̄ | **n_eff** | mean pairwise Hamming |
|---|---|---:|---:|---:|
| **homogeneous-control** — 9× Opus, FULL evidence, LITERAL | stochastic floor | 1.000 | **1.00** | 0.00 |
| **clean-diverse** — FULL evidence, vary model tier × protocol | cross-assessor independence (Anthropic) | 0.937 | **1.06** | 0.44 |
| **glm-diverse** — FULL evidence, vary protocol, **Zhipu GLM-4.6** | cross-*vendor* independence | 0.948 | **1.05** | 0.39 |
| **heterogeneous** — vary model × **evidence-partition** × protocol | all diversity levers | 0.564 | **1.63** | 3.06 |

**Headline: 9 assessors are ~1 effective vote, not 9.** Nine identical-cell Opus
assessors returned **byte-identical** answers (Hamming 0 → φ̄ = 1.00 → n_eff = 1.00).
Giving them genuinely different model tiers (Opus/Sonnet/Haiku/Fable) *and* different
reasoning protocols, but the **same** full evidence, moved n_eff to only **1.06** —
within-vendor assessor diversity buys ≈ 0 independence. This is the *same shape* of
deflation Kohli reports in "Nine Judges, Two Effective Votes" (arXiv:2605.29800) — same
`n_eff` formula, published two months before this entry — but it is not the same
measurement, and we do not claim it is: Kohli computes `n_eff` over **error** vectors
(agreement against a ground-truth label), where ours is over **affirm** vectors
(agreement on the answer itself, no oracle required). Ours is the weaker, cheaper
signal — two assessors can affirm alike and err differently. The direction it points is
the **conservative** one for a refuse-to-combine engine, which is why we report it.

The heterogeneous panel reaches n_eff = 1.63 — but see the audit: that gain is not
competence.

## Cross-vendor test — does a genuinely foreign vendor break the floor?

A2's first pass used only Anthropic models, leaving an honest open question: is the
≈1 effective vote a *within-vendor* artifact (shared pretraining), or a property of
the evidence? With a Zhipu **GLM-4.6** key now on hand, we ran a 9-assessor
**glm-diverse** panel — same FULL evidence and protocol spread as clean-diverse, but a
different vendor, company, and training lineage — and measured correlation *within* vs
*across* vendors:

| pairing | mean φ |
|---|---:|
| within-Anthropic (clean-diverse) | 0.937 |
| within-GLM (glm-diverse) | 0.948 |
| **cross-vendor (Anthropic × GLM)** | **0.946** |

**The floor is not a vendor artifact.** Cross-vendor φ (0.946) is indistinguishable
from within-vendor φ (0.937 / 0.948) — a Claude and a GLM agree at the *same* rate two
Claudes do. The combined **k = 18** two-vendor panel has **n_eff = 1.06**; 7 of 9 GLM
assessors returned a vector identical to the Anthropic consensus. This *refutes* our
own prior hypothesis (that cross-vendor diversity would lower φ̄).

So the redundancy lives in the **evidence**, not the model family. This is the
stronger result: a foreign assessor does not buy an independent vote when the evidence
already determines the answer — precisely the condition cairn's layer-(a) provenance
detector flags (shared upstream → refuse to combine). The honest n_eff on this crux is
~1 regardless of how many vendors you poll.

## Reproducibility (the A1 mirror)

The live assessor run is the non-deterministic *instrument reading*; its **result is
pinned** and re-checkable with zero model access — exactly as A1 pinned its sources:

- `assessment/prompts.json` — the exact, deterministic prompt every assessor saw.
- `assessment/raw_votes.json` — the captured votes (+ one-line reasons), the audit trail.
- `assessment/runs/` — the minted, signed Cairn records:
  - `battery.json` (`epi:Schema`) — the probe-battery instrument;
  - `assessments.json` — 36 `epi:Assessment` records (one per assessor), each
    `derivedFrom` **the source ids it was actually granted**;
  - `heterogeneous.json` / `homogeneous-control.json` / `clean-diverse.json` /
    `glm-diverse.json` (`epi:Cluster`) — each panel's matrix + `neff` + full pairwise-φ;
  - `axis_analysis.json` — the decomposition below.
- **`cairn assess`** recomputes each matrix and n_eff straight from the recorded
  answers and asserts they equal what was pinned (nonzero exit on any drift). It runs
  at container build time and in the test suite — so a fresh machine verifies the
  headline number. Minting is deterministic (fixed keys + timestamp), so the record
  ids are stable across rebuilds.

## The structural payoff — A1 explains A2's correlation

Each `epi:Assessment`'s `provenance.derivedFrom` is the **evidence it saw**. So the
A1 refuse-to-combine engine (`cairn intersect`) reads assessor (non-)independence
mechanically: two assessors granted the same evidence **share an upstream →
REFUSE-TO-COMBINE**; disjoint partitions → **COMBINABLE**. Correlated assessors are
not an assumption here — they are a walkable edge in the same DAG that refuses to
multiply correlated *evidence*. (`test_shared_evidence_refuses_disjoint_combines`.)

## The adversarial audit (`AUDIT.json`) — and why the honest number is ~1

The panel was bracketed by independent auditors (both Opus).

**Battery keys — clean.** Two auditors independently verified all 8 faithfulness
keys against the cited spans: **0 disputes**, and every `grounds.quote` is an exact
substring of its abstract (also enforced mechanically by
`test_keyed_probes_quote_their_source_verbatim`).

**Matrix — the heterogeneous n_eff is confound-inflated.** Both auditors converged:

1. **The model-tier axis contributes ≈ 0.** With evidence held constant, different
   models + protocols barely diverge — the clean-diverse panel's n_eff = 1.06, and
   same-partition pairs in the heterogeneous panel are near-identical (e.g. the
   Haiku/ADVERSARIAL and Opus/BASE_RATE PEKAR_ONLY assessors answered **identically**).
   The models are **not** independent assessors — and the cross-vendor test above shows
   this is not merely shared pretraining: a foreign vendor (GLM-4.6) correlates just as much.
2. **Most of the heterogeneous panel's spread is evidence-partition *starvation*,
   not judgment.** A PEKAR_ONLY assessor answers a Worobey faithfulness probe
   UNCERTAIN (→ 0) because it was **blinded**, not because it disagrees. That
   decorrelation is real but it is not independent competence, so the heterogeneous
   n_eff = 1.63 is an **upper bound inflated by design**, not the honest number.

**One audit finding we checked and rejected.** Both auditors flagged assessor **H5**
(PROXIMITY_TRADE) as "leaking" Pekar content. This is a **false positive**: they were
not given the partition→source map, and `PROXIMITY_TRADE` **does** grant the Pekar
abstract (`partitions.json`), so H5 citing it was in-bounds. We record the flag and
the refutation rather than silently accepting the audit.

**Net honest reading:** effective independent votes on the HSM crux ≈ **1**, rising
to at most ~1.6 only by starving assessors of evidence. Reporting this downward
revision — instead of the flattering 1.63 — *is* the engine's discipline (delta 4,
"knowing when not to compute") applied to its own measurement.

## Diversity levers (roadmap DoD: "record the levers used")

| lever | available? | measured effect on independence |
|---|---|---|
| **evidence-partition** (primary) | yes — 7 disjoint views | large **apparent** effect, but mostly starvation (see audit) |
| **reasoning protocol** (literal / base-rate / adversarial) | yes | small; flips some inferential probes |
| **model tier** (Opus/Sonnet/Haiku/Fable) | yes | **≈ 0** (within-vendor; shared pretraining) |
| **cross-vendor models** (Zhipu GLM-4.6 via z.ai) | **yes** — key retrieved 2026-07-04 | **measured ≈ 0** — cross-vendor φ (0.946) ≈ within-vendor φ; a foreign vendor does not lower the floor |
| **human-at-crux** | slot open | not yet cast; the battery is human-answerable — the operator can add a vote |

## Honest caveats

- **The floor is not within-vendor** (now tested). We originally hypothesized the
  correlation was shared pretraining and that a cross-vendor assessor would lower φ̄.
  **Refuted**: a Zhipu GLM-4.6 panel agrees with the Anthropic panel at the same φ
  (cross-vendor 0.946 ≈ within-vendor 0.937/0.948). The redundancy is in the evidence,
  not the vendor — so n_eff ≈ 1 is not an artifact we can diversify away. (Still open:
  a *human*-at-crux assessor, the one genuinely different epistemic source.)
- **Partition-decorrelation ≠ competence-decorrelation.** Made explicit above; it is
  why the honest headline is the clean-diverse 1.06, not the heterogeneous 1.63.
- **UNCERTAIN → 0** in the affirm-vector (abstention is scored as non-affirmation).
- **Single run, k = 9 per panel.** No replicates yet; the full pairwise-φ arrays are
  pinned in each cluster so A3 can carry the dependence uncertainty into an interval.

## Delivered in A3 (Fréchet interval) — `assessment/FRECHET.md`

Each cluster pins `neff.pairwise_phi` (all 36 pairwise φ values); **A3 consumes them
directly**. It turns the *measured dependence* — its spread, not a point — into a
Fréchet/p-box interval ("interval width = the honesty signal") via
`cairn/frechet.py` + `cairn frechet`:

- The **n_eff p-box** (RETIRED — see `FRECHET.md` §5) read each panel's pairwise-φ *spread* into an n_eff
  interval; it inherited the zero-variance bug and is superseded by a **bootstrap CI on φ̄** + eigenvalue ESS
  (`neff_recompute.json`). The retained figures (heterogeneous `[1.0, 9.0]`, clean-diverse `[1.0, 1.34]`) are
  pre-fix audit record only.
- The **combine interval** places the measured `n_eff ≈ 1` at the redundant floor of
  the trio's `[5, 125]` (via `LR^{n_eff}`), so the honest crux estimate is `LR = 5`,
  never the naive product 125 → **REFUSE-TO-COMBINE-AS-POINT**. See `FRECHET.md` for
  the full model-vs-bound treatment (the naive point is not even a Fréchet ceiling).

## Reproduce

```bash
# deterministic (no model access) — rebuild records from the pinned votes + verify:
.venv/bin/python assessment/build_assessment.py
.venv/bin/cairn assess assessment/runs/heterogeneous.json \
  assessment/runs/homogeneous-control.json assessment/runs/clean-diverse.json \
  assessment/runs/glm-diverse.json --battery assessment/probes.json
.venv/bin/python -m pytest -q tests/test_assessment.py

# re-measure (needs model access) — regenerate the pinned prompts, then re-run panels:
.venv/bin/python assessment/gen_prompts.py       # Anthropic panels run via the ultracode Workflow
.venv/bin/python assessment/zai_assess.py        # cross-vendor GLM panel via z.ai (needs ~/.config/epistack/zai.env)
```

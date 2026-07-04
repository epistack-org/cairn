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

Three 9-assessor panels, each answering the same battery. `phi_bar` (φ̄) is the mean
pairwise φ-coefficient over the binary affirm-vectors; `n_eff = k / (1 + (k-1)·φ̄)`.

| panel | what it isolates | φ̄ | **n_eff** | mean pairwise Hamming |
|---|---|---:|---:|---:|
| **homogeneous-control** — 9× Opus, FULL evidence, LITERAL | stochastic floor | 1.000 | **1.00** | 0.00 |
| **clean-diverse** — FULL evidence, vary model tier × protocol | genuine cross-assessor independence | 0.937 | **1.06** | 0.44 |
| **heterogeneous** — vary model × **evidence-partition** × protocol | all diversity levers | 0.564 | **1.63** | 3.06 |

**Headline: 9 assessors are ~1 effective vote, not 9.** Nine identical-cell Opus
assessors returned **byte-identical** answers (Hamming 0 → φ̄ = 1.00 → n_eff = 1.00).
Giving them genuinely different model tiers (Opus/Sonnet/Haiku/Fable) *and* different
reasoning protocols, but the **same** full evidence, moved n_eff to only **1.06** —
within-vendor assessor diversity buys ≈ 0 independence. This is exactly the
"Nine Judges, Two Effective Votes" (arXiv:2605.29800) deflation, measured on our own
corpus, and it is the **conservative** direction for a refuse-to-combine engine.

The heterogeneous panel reaches n_eff = 1.63 — but see the audit: that gain is not
competence.

## Reproducibility (the A1 mirror)

The live assessor run is the non-deterministic *instrument reading*; its **result is
pinned** and re-checkable with zero model access — exactly as A1 pinned its sources:

- `assessment/prompts.json` — the exact, deterministic prompt every assessor saw.
- `assessment/raw_votes.json` — the captured votes (+ one-line reasons), the audit trail.
- `assessment/runs/` — the minted, signed Cairn records:
  - `battery.json` (`epi:Schema`) — the probe-battery instrument;
  - `assessments.json` — 27 `epi:Assessment` records (one per assessor), each
    `derivedFrom` **the source ids it was actually granted**;
  - `heterogeneous.json` / `homogeneous-control.json` / `clean-diverse.json`
    (`epi:Cluster`) — each panel's matrix + `neff` + full pairwise-φ;
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
   Within-vendor models share pretraining; they are **not** independent assessors.
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
| **cross-vendor models** (LiteLLM) | **no** — no non-Anthropic API keys exist on this host | the only lever that would lower the within-vendor floor; unavailable |
| **human-at-crux** | slot open | not yet cast; the battery is human-answerable — the operator can add a vote |

## Honest caveats

- **Within-vendor floor.** Every assessor is an Anthropic model. Shared pretraining
  is a correlation floor we cannot measure away without cross-vendor keys (none exist
  here). Cross-vendor assessors would only *lower* φ̄ — so our n_eff is a conservative
  (low) estimate of independence, the safe direction.
- **Partition-decorrelation ≠ competence-decorrelation.** Made explicit above; it is
  why the honest headline is the clean-diverse 1.06, not the heterogeneous 1.63.
- **UNCERTAIN → 0** in the affirm-vector (abstention is scored as non-affirmation).
- **Single run, k = 9 per panel.** No replicates yet; the full pairwise-φ arrays are
  pinned in each cluster so A3 can carry the dependence uncertainty into an interval.

## Hand-off to A3 (Fréchet interval)

Each cluster pins `neff.pairwise_phi` (all 36 pairwise φ values). A3 turns the
*measured dependence* — its spread, not a point — into a Fréchet/p-box interval:
"interval width = the honesty signal." The clean-diverse vs heterogeneous gap is the
empirical handle on how much the dependence assumption moves the bound.

## Reproduce

```bash
# deterministic (no model access) — rebuild records from the pinned votes + verify:
.venv/bin/python assessment/build_assessment.py
.venv/bin/cairn assess assessment/runs/heterogeneous.json \
  assessment/runs/homogeneous-control.json assessment/runs/clean-diverse.json \
  --battery assessment/probes.json
.venv/bin/python -m pytest -q tests/test_assessment.py

# re-measure (needs model access) — regenerate the pinned prompts, then re-run the panel:
.venv/bin/python assessment/gen_prompts.py
```

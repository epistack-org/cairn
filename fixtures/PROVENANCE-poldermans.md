# Poldermans / DECREASE mini-corpus — provenance & vetting record

_The 7th worked example, imported in the **2026-07-15 backtest-scaling pass** (dev/cairn#15). Same
vetting standard as the seed cases: every span retrieved first-party and mechanically re-checkable
(`cairn ground`); every judgment call that could not be grounded is **recorded, not papered over**._

## Why this case exists (read this first)

A **backtest** of the eggs node type — a shared research program / database at the root, found without
any single origin paper — carrying an **institutional-misconduct** meta-fact. It is the corpus's
sharpest counterfactual: it is the only case where **removing the fabricated lineage reverses the
conclusion's sign** rather than merely deflating the vote count. Benefit becomes harm.

## The punchline

Perioperative **beta-blockade** to prevent cardiac death in non-cardiac surgery entered European and
American guidelines on what looked like a wall of independent evidence:

| | study | venue | year | contributes | shares |
|---|---|---|---|---|---|
| 1 | Poldermans, … (DECREASE-I) | **NEJM** | 1999 | bisoprolol cuts cardiac death/MI (34% → 3.4%) — the origin | Poldermans/Erasmus DECREASE program |
| 2 | Boersma, Poldermans, … | JAMA | 2001 | beta-blocker recipients have far fewer cardiac events (screening cohort) | same Erasmus vascular-surgery database |
| 3 | Dunkelgrun, … Poldermans (DECREASE-IV) | Ann Surg | 2009 | bisoprolol benefit extends to intermediate-risk | same program |

That wall is **one research program** — the Poldermans/Erasmus **DECREASE** family of trials and its
associated vascular-surgery database. A **2011–2012 Erasmus MC investigation found the DECREASE trials
contained fabricated/fictitious data**. `cairn intersect` refuses the trio and names
`ent-decrease-program`: the shared upstream is the compromised program itself, not any single paper.

## The counterfactual flips the sign

This is the case's distinctive contribution. The independent evidence does not merely fail to
replicate — it **reverses**:

- **POISE** (Devereaux et al. 2008, *Lancet*; n=8351) is a large independent RCT, upstream-disjoint
  from DECREASE. It found perioperative metoprolol cut myocardial infarction but **increased total
  mortality** (and stroke). So `{claim-decrease-1, claim-poise}` returns **COMBINABLE** — POISE is a
  genuinely distinct evidential draw.
- **Bouri et al. 2014** (*Heart*) meta-analysed only the **secure (non-DECREASE)** trials and found that
  initiating perioperative beta-blockade causes a **27% increase in 30-day mortality** (`RR ≈ 1.27`),
  and wrote that "the DECREASE family of trials, the bedrock of evidence for this, are no longer secure"
  and that guideline bodies "should retract their recommendations based on fictitious data."

Removing the fabricated lineage does not just weaken the pooled result; it **flips it from benefit to
harm**. That is a property no other case in the corpus exhibits, and probe `I5` in
`assessment/probes-poldermans.json` exists to pin the direction (an assessor answering "the secure
evidence still shows benefit" is scored wrong).

## What this case does NOT say

**It is a claim about corroboration-counting, not a clinical adjudication.** cairn's refusal says the
DECREASE outputs are not independent votes; whether the intervention is beneficial, useless, or harmful
is answered by the *independent* evidence (POISE; Bouri's secure-trials meta), not by the refusal
itself. Those independent lines do indicate net harm — but that is **their** finding, not cairn's
provenance verdict. Probe `I3` scores "cairn determined the intervention is harmful" as an over-claim:
conflating a provenance refusal with the separate (and stronger) clinical finding overstates what cairn
establishes.

## The ground truth is institutional — recorded precisely, not overclaimed

Like the Anversa case, the answer key is an **institutional misconduct finding**, not a per-node
retraction stamp. `ent-decrease-program` carries the meta-fact (the 2011–2012 Erasmus MC investigation;
the DECREASE family deemed insecure), and the first-party statement of it is **grounded** in Bouri
2014's own abstract (probe `F6`: "family of trials, the bedrock of evidence for this, are no longer
secure"). The refusal is driven by the **shared program**, not by which individual DECREASE papers
carry a retraction notice.

## Sources (retrieved 2026-07-15, sha-pinned)

| record | PMID | DOI | excerpt sha256 (first 12) | role |
|---|---|---|---|---|
| `src-poldermans-1999` (DECREASE-I) | 10588963 | 10.1056/NEJM199912093412402 | `078de8baccf8` | laundered (origin) |
| `src-boersma-2001` | 11308400 | 10.1001/jama.285.14.1865 | `c8c8e0db9069` | laundered (cohort) |
| `src-dunkelgrun-2009` (DECREASE-IV) | 19474688 | 10.1097/SLA.0b013e3181b4c7e8 | `d2c47de80ed8` | laundered (RCT) |
| `src-devereaux-2008` (POISE) | 18479744 | 10.1016/S0140-6736(08)60601-7 | `47b8b5836b57` | disjoint contrast (COMBINABLE) |
| `src-bouri-2014` | 23904357 | 10.1136/heartjnl-2013-304262 | `8a502e70f598` | the sign-flip counterfactual |

**Retrieval method.** `efetch` (PubMed, `rettype=abstract&retmode=xml`); structured abstracts serialized
`LABEL: text` one section per line via `AbstractText` `itertext()`. Raw abstracts ship under
`fixtures/sources/*.abstract.txt`; the build fails if a byte drifts.

## A recorded modeling decision (honest, not hidden)

The three laundered members are **not all RCTs**: `src-boersma-2001` is the DECREASE *screening cohort*
(observational), included because it draws on the same Erasmus/Poldermans vascular-surgery database and
was a major driver of guideline adoption. It is a member of the shared **program**, which is the node
the refusal names — not a fourth independent RCT. The topology (all three share `ent-decrease-program`)
is what carries the case; the mix of one landmark RCT, one cohort, and one confirmatory RCT is the
realistic shape of how a single compromised program presents as "an evidence base."

## Fact-check log

- **DECREASE-I benefit** — CONFIRMED from the abstract conclusion: "Bisoprolol reduces the perioperative
  incidence of death from cardiac causes and nonfatal myocardial infarction in high-risk patients."
- **DECREASE program found to contain fabricated data** — CONFIRMED first-party from Bouri 2014's own
  abstract ("the DECREASE family of trials … are no longer secure"; "recommendations based on fictitious
  data"). Recorded as an institutional meta-fact on `ent-decrease-program`.
- **The sign-flip (27% mortality increase)** — CONFIRMED from Bouri 2014: "caused a 27% risk increase in
  30-day all-cause mortality," with the DECREASE family analysed separately and diverging (p=0.05).
- **POISE is upstream-disjoint and points the other way** — CONFIRMED from the abstract: an 8351-patient
  independent RCT in which "there were more deaths in the metoprolol group than in the placebo group."
- **Scope discipline** — cairn's refusal is about the non-independence of the DECREASE program's outputs.
  The clinical conclusion (net harm) comes from the independent evidence, not from the refusal; probe
  `I3` scores conflating the two as the wrong answer.

# Anversa c-kit+ cardiac stem cell mini-corpus — provenance & vetting record

_The 6th worked example, imported in the **2026-07-15 backtest-scaling pass** (dev/cairn#15). Same
vetting standard as the seed cases: every span retrieved first-party and mechanically re-checkable
(`cairn ground`); every judgment call that could not be grounded is **recorded, not papered over**._

## Why this case exists (read this first)

A **backtest** of the same node type as amyloid — a lab-defined object plus its detection/isolation
method, with the origin source at the root — but where the ground truth is an **institutional
misconduct finding** rather than a retraction stamp on the origin paper. It exercises both
lineage-collapse (one lab's characterization re-measured) and a **literal shared-reagent** dependency
(the SCIPIO trial used the lab's own cell preps).

## The punchline

The **c-kit+ cardiac stem cell** — an adult heart cell claimed to regenerate myocardium — looked
confirmed at every level of evidence:

| | paper | venue | year | contributes | shares |
|---|---|---|---|---|---|
| 1 | Beltrami, …, Anversa | **Cell** | 2003 | c-kit+ cells reconstitute ~70% of infarcted ventricle (rodent) — the origin | — |
| 2 | Bearzi, …, Anversa | PNAS | 2007 | **human** c-kit+ CSCs generate human myocardium | lab + cell type + isolation method |
| 3 | Bolli, …, Anversa | Lancet (**RETRACTED 2019**) | 2011 | **SCIPIO**: autologous CSCs improve LVEF in patients | lab + cell type + **the cell preps themselves** |

All three descend from **one laboratory's originating characterization** (Beltrami 2003) and its
isolation method. The SCIPIO trial did not independently re-derive the cell — it **used the Anversa
lab's own c-kit+ CSC preps**, a literal shared-reagent dependency on top of the shared characterization.
`cairn intersect` refuses the trio and names `ent-anversa-ckit-csc` (and, transitively, the origin
`src-beltrami-2003`).

The shared upstream generalizes the amyloid node one more step: like Aβ*56 it is **both a foundational
RESULT and a shared REAGENT/METHOD**, but here the reagent dependency reaches all the way into a
**clinical trial's cells**, not just an assay.

## What this case does NOT say

**It does not say the heart cannot be repaired, and it does not adjudicate every cell therapy.** It is
a claim about corroboration-**counting** for one cell type. The contrast proves the boundary the other
way:

> **CADUCEUS** (Makkar et al. 2012, *Lancet*) used **cardiosphere-derived cells** — a different cell
> type, a different laboratory (Marbán, Cedars-Sinai), a different preparation, with no derivation from
> the Beltrami 2003 characterization — and reported increased viable heart mass after infarction.

That line is upstream-disjoint from the Anversa c-kit+ cell, so `{claim-anversa-origin,
claim-anversa-caduceus}` returns **COMBINABLE**. Cardiac-regeneration evidence exists that does not
route through Anversa. Probe `I3` in `assessment/probes-anversa.json` scores "the refusal means cardiac
regeneration is impossible" as the wrong answer.

## The ground truth is institutional — recorded precisely, not overclaimed

Unlike amyloid (a per-node PubMed retraction of the origin paper), this case's answer key is an
**institutional misconduct finding plus one retracted downstream node**:

- Harvard Medical School and Brigham and Women's Hospital found **falsified/fabricated data** across
  the Anversa lab and, in **October 2018**, recommended **31 papers** for retraction.
- A **$10M False Claims Act settlement** (2017) resolved allegations that the lab relied on manipulated
  data in NIH grant applications; the lab was closed in 2015.
- The flagship human trial **SCIPIO was retracted** by the *Lancet* in **2019** (Expression of Concern
  2014).

Crucially, **the origin paper (Beltrami 2003, Cell) is not itself individually marked retracted on
PubMed** as of retrieval. The corpus records that honestly: `src-beltrami-2003` carries a
`retraction_status_note` saying so, and `ent-anversa-ckit-csc` carries the institutional meta-fact. The
refusal is driven by **shared derivation**, not by any single retraction stamp — cairn refuses on the
provenance topology whether or not each paper carries a notice (probe `I4`).

## Sources (retrieved 2026-07-15, sha-pinned)

| record | PMID | DOI | excerpt sha256 (first 12) | retraction status |
|---|---|---|---|---|
| `src-beltrami-2003` | 14505575 | 10.1016/S0092-8674(03)00687-1 | `52559bb7c0ee` | not individually retracted (institutional finding) |
| `src-bearzi-2007` | 17709737 | 10.1073/pnas.0706760104 | `c63b7ac1e19c` | not individually retracted (institutional finding) |
| `src-bolli-2011` (SCIPIO) | 22088800 | 10.1016/S0140-6736(11)61590-0 | `33bab0ee2cd8` | **RETRACTED 2019** (EoC 2014) |
| `src-makkar-2012` (CADUCEUS) | 22336189 | 10.1016/S0140-6736(12)60195-0 | `b6de36d79cb6` | — (the disjoint contrast) |

**Retrieval method.** `efetch` (PubMed, `rettype=abstract&retmode=xml`); abstract text via `AbstractText`
`itertext()` (these four are unstructured, so the text is verbatim). The SCIPIO retraction and the 2014
Expression of Concern are first-party from the PubMed `RetractionIn` / `ExpressionOfConcernIn` fields of
PMID 22088800. Raw abstracts ship under `fixtures/sources/*.abstract.txt`; the build fails if a byte drifts.

## Fact-check log

- **Beltrami 2003 is the c-kit+ CSC origin** — CONFIRMED from the abstract: "the existence of Lin(-)
  c-kit(POS) cells with the properties of cardiac stem cells … reconstitute well-differentiated
  myocardium … approximately 70% of the ventricle."
- **SCIPIO used the Anversa lab's cells and is retracted** — CONFIRMED: the abstract names
  "c-kit-positive, lineage-negative cardiac stem cells (CSCs)"; the PubMed record carries the 2019
  `RetractionIn` and 2014 `ExpressionOfConcernIn`.
- **Institutional finding: 31 papers, $10M settlement** — CONFIRMED from contemporaneous reporting
  (STAT / *Science*, Oct 2018; *Science*, on the $10M FCA settlement). Recorded as an institutional
  meta-fact on `ent-anversa-ckit-csc`; **not** asserted as a per-node retraction of Beltrami/Bearzi.
- **Beltrami 2003 / Bearzi 2007 retraction status** — CHECKED against PubMed: neither carries a
  `RetractionIn` field at retrieval. Recorded as such rather than assumed — asserting a retraction that
  PubMed does not show would itself be the fabrication class the project exists to catch.
- **CADUCEUS is upstream-disjoint** — CONFIRMED by abstract: cardiosphere-derived cells grown from
  endomyocardial biopsy, Marbán lab, a different preparation from the Anversa c-kit+ sort.

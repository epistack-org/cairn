# Ivermectin / Elgazzar mini-corpus — provenance & vetting record

_The 5th worked example, imported in the **2026-07-15 backtest-scaling pass** (dev/cairn#15),
from a ranked research sweep of known-answer non-independence cases. Same vetting standard as
the four seed cases: every span was retrieved first-party and is mechanically re-checkable
(`cairn ground`), and every judgment call that could not be grounded was **recorded rather than
papered over**._

## Why this case exists (read this first)

This is a **backtest**: a debate whose meta-fact we already know, imported to check whether a
naive ingest re-surfaces the collapse the way the amyloid corpus re-surfaced Lesné. The answer
key here is unusually clean and unusually consequential — one fabricated primary trial, pooled
by nearly every positive synthesis, whose removal is a *published* counterfactual.

It is also the corpus's **highest-fan-out** node: where amyloid had a shared characterization
re-measured twice, here one fabricated trial fans out across many downstream meta-analyses. The
non-independence lives natively in the citation / forest-plot graph, which is exactly why it is a
clean citation-recoverable backtest.

## The punchline

Several meta-analyses and reviews reported that ivermectin roughly **halves COVID-19 mortality**.
Read as independent replication, that is a wall of evidence. It is not:

| | synthesis | venue | year | headline | shares |
|---|---|---|---|---|---|
| 1 | Bryant, Lawrie, … | Am J Ther (Expression of Concern 2022) | 2021 | mortality **RR 0.38** | pooled **Elgazzar** |
| 2 | Zein, … Pranata | Diab Metab Syndr | 2021 | mortality **RR 0.39** | pooled **Elgazzar** |
| 3 | Kory, … Marik (FLCCC) | Am J Ther (Expression of Concern 2022) | 2021 | "large … reductions in mortality" | pooled **Elgazzar** |

All three pooled the **same single fabricated trial** — Ahmed Elgazzar et al., a Research Square
preprint (`10.21203/rs.3.rs-100956`), **WITHDRAWN 2021-07-14**. Elgazzar was the largest trial by
patient number and carried the largest drug effect in the entire ivermectin literature, so it
dominated each pooled mortality estimate. When it was withdrawn, the meta that had leaned on it
most (**Hill 2021**) went null on survival (RR 0.90) and was itself **retracted**. That RR 0.39 in
Zein is not a second confirmation of Bryant's RR 0.38 — it is the *same fabricated trial's* effect
re-appearing under a different author list.

`cairn intersect` refuses the trio and names `src-elgazzar-2020` — a shared upstream **two hops up**
(claim → meta-analysis → Elgazzar), the same transitive shape as the eggs cohort backbone, but here
the shared node is a withdrawn fraud rather than a legitimate cohort. Each meta's inclusion of
Elgazzar is **byte-grounded** by a `pools-elgazzar` structural claim against the study-characteristics
table shipped in that meta's excerpt (retrieved from Europe PMC OA).

## What this case does NOT say

**It does not say ivermectin is proven ineffective, and it does not say ivermectin research is
uniformly fraudulent.** It is a claim about corroboration-**counting**: the positive syntheses are
not independent votes. The contrast proves the boundary in the other direction:

> **TOGETHER** (Reis et al. 2022, *NEJM*) is a large placebo-controlled RCT (n=3515) that **never
> ingested Elgazzar**. It is upstream-disjoint from the fabricated node, so an Elgazzar-based meta
> and TOGETHER return **COMBINABLE**.

TOGETHER happens to be null — and that is the point. The verdict is about **provenance-independence,
not agreement**: cairn certifies TOGETHER as a genuinely distinct evidential draw regardless of which
way it points. Probe `I3` in `assessment/probes-ivermectin.json` scores "the refusal means ivermectin
is proven useless / the literature is fraud" as the wrong answer.

## Sources (retrieved 2026-07-15, sha-pinned)

| record | PMID / DOI | excerpt kind | excerpt sha256 (first 12) |
|---|---|---|---|
| `src-elgazzar-2020` | doi:10.21203/rs.3.rs-100956 | **no excerpt** (bibliographic + withdrawal notice) | — |
| `src-bryant-2021` | 34145166 | abstract + study-characteristics table | `715af7695573` |
| `src-zein-2021` | 34237554 | abstract + baseline-characteristics table | `a2e9e5fc5c42` |
| `src-kory-2021` | 34375047 | abstract + clinical-studies table | `bd06c3d4a16e` |
| `src-reis-2022` (TOGETHER) | 35353979 | abstract (version of record) | `6908794567ad` |
| `src-hill-2021` (counterfactual) | 34796244 | abstract (version of record) | `f66ca4aea476` |

**Retrieval method.** Abstracts via NCBI E-utilities `efetch` (`AbstractText` `itertext()`, structured
sections serialized `LABEL: text` one per line). For the three positive syntheses the excerpt is the
abstract **plus the complete included-study characteristics table**, extracted from the Europe PMC OA
JATS `fullTextXML` and serialized as whitespace-normalized pipe-rows (`' | '.join(cell.itertext())`) —
the same Table-1 transform the eggs meta-analyses use. That table is where the Elgazzar-inclusion edge
lives; it does not appear in the abstract. Raw excerpts ship under `fixtures/sources/*.abstract.txt`
and the build fails loudly if a byte drifts.

**The Elgazzar node carries no excerpt, on purpose.** Its "version of record" is now a withdrawal
notice. It is an *upstream* node, not a grounding source for any claim, so — like `src-worobey-2021`
in the COVID case — it needs no excerpt. Its `withdrawal` field records the first-party facts
(withdrawn by Research Square 2021-07-14; ~79 duplicated participant records; deaths recorded on dates
before the trial began; plagiarism), sourced to the Research Square notice and Reardon, *Nature* 2021
(`d41586-021-02081-w`). **Neither the withdrawal nor the Expressions of Concern is an input to the
refusal** — the three syntheses share Elgazzar whether or not it has been withdrawn (probe `I4`).

## The footgun this case surfaced

**U+00A0 NO-BREAK SPACE inside a statistic.** The Zein 2021 abstract spells its statistics with
no-break spaces: `p = 0.004`, not `p = 0.004`. A quote hand-typed with ASCII spaces would
**silently fail** the byte-exact span check. The grounded quote for `claim-iver-zein` stops before the
no-break run; the hazard is recorded in each source's `SOURCES` note. This is the amyloid/eggs footgun
class again (U+03B2, U+2009, U+2019) — exactly the error the engine exists to make impossible to commit
silently.

## Fact-check log

- **Elgazzar inclusion in all three syntheses** — CONFIRMED first-party: each meta's Europe PMC OA full
  text names Elgazzar in its study table (Bryant: `Elgazzar 202047 | Egypt | RCT …`; Zein:
  `Elgazzar 2020 [23] …`; Kory cites the exact preprint DOI `rs.3.rs-100956`). These are the bytes the
  `pools-elgazzar` claims ground on — the inclusion edge is not asserted, it is retrieved.
- **Elgazzar withdrawal (2021-07-14) and reasons** — CONFIRMED from the Research Square notice and
  Reardon, *Nature* 2021 (`d41586-021-02081-w`): duplicated records, impossible death dates, plagiarism.
- **Hill 2021 counterfactual + retraction** — CONFIRMED from PubMed: the version-of-record abstract is
  null on survival (RR 0.90) and carries a `RetractionIn` (Open Forum Infect Dis 2022, PMID 35146053).
- **Expressions of Concern on Bryant and Kory** — CONFIRMED from the PubMed `ExpressionOfConcernIn`
  fields (Am J Ther 2022, PMID 35142702 and 35142703).
- **Scope discipline** — the case asserts non-independence of the positive mortality **syntheses** only.
  It does NOT assert ivermectin is ineffective (the independent RCTs, incl. TOGETHER, address that) and
  does NOT brand the literature fraudulent; probe `I3` scores either over-reach as the wrong answer.

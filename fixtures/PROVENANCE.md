# COVID-HSM mini-corpus — provenance & vetting record

> **One of three.** Cairn ships three worked examples; this is the vetting record for the
> COVID case. See also [`PROVENANCE-eggs.md`](PROVENANCE-eggs.md) (the shared **cohort**
> backbone, found transitively) and [`PROVENANCE-cern.md`](PROVENANCE-cern.md) (the shared
> **premise**). Each case's structure is declared in [`CASES.json`](CASES.json) and
> mechanically verified at build time.

_Roadmap A1 (). This corpus replaced the earlier
`unverified-fixture` records with **real, span-grounded, entailment-labeled**
claims. Vetting standard: **fabricated provenance is the F0 sin the project exists
to catch** — so every span here was retrieved first-party and is mechanically
re-checkable (`cairn ground`), and every judgment call that could not be grounded
was recorded rather than papered over._

## Sources (retrieved first-party, byte-verified)

Both abstracts are the **version of record**, retrieved on **2026-07-04** and
confirmed **byte-identical across two independently operated services** — NCBI
E-utilities `efetch` (MEDLINE) and the Europe PMC REST API (EMBL-EBI). The
publisher HTML (`science.org`) was paywalled (HTTP 403); no model summarizer was
used for the verbatim text (a `WebFetch` of the PubMed page was observed to insert
a spurious comma, so only raw bytes were trusted). The exact bytes ship as
`fixtures/sources/*.abstract.txt` and are SHA-256-pinned in `build_fixtures.py`.

| record | paper | DOI · PMID · PMCID | excerpt | sha256(excerpt) |
|---|---|---|---|---|
| `src-worobey-2022` | Worobey M, et al. (18 authors), *Science* 377(6609):951-959 (2022; online 2022-07-26) — "The Huanan Seafood Wholesale Market in Wuhan was the early epicenter of the COVID-19 pandemic" | `10.1126/science.abp8715` · 35881010 · PMC9348750 | abstract, 1017 chars | `93f3dc18…1caba4` |
| `src-pekar-2022` | Pekar JE, et al. (29 authors), *Science* 377(6609):960-966 (2022; online 2022-07-26) — "The molecular epidemiology of multiple zoonotic origins of SARS-CoV-2" | `10.1126/science.abp8337` · 35881005 · PMC9348752 | abstract, 1102 chars | `c046d962…5adbfe` |

**Errata flagged** (recorded on each source record for completeness; neither
changes the abstract text used here): Worobey — *Science* 2024 383(6688):eadp1133
(`10.1126/science.adp1133`); Pekar — `10.1126/science.adl0585` (corrects
overestimated Bayes factors from a coding error; the ≥2-introductions conclusion
stands). *Version-of-record vs accepted-manuscript note:* the PMC full-text HTML
carries the First-Release/accepted-manuscript wording (minor copyedit differences,
e.g. "occurred via" vs "occurred through"); we deliberately grounded to the
**indexed version of record**.

## Claims (each grounded to a real span; `source.excerpt[char_span] == quote`)

| claim | source | rung | entailment | char_span | grounding quote (verbatim substring) |
|---|---|---|---|---|---|
| `claim-geographic-clustering` | Worobey | **L5** | ENTAILS | `[365, 509]` | "the earliest known COVID-19 cases from December 2019, including those without reported direct links, were geographically centered on this market" |
| `claim-environmental-sampling` | Worobey | **L4** | SUPPORTS | `[608, 728]` | "within the market, SARS-CoV-2-positive environmental samples were spatially associated with vendors selling live mammals" |
| `claim-live-mammal-sales` | Worobey | **L5** | ENTAILS | `[526, 598]` | "live SARS-CoV-2-susceptible mammals were sold at the market in late 2019" |
| `claim-two-lineages` | Pekar | **L4** | ENTAILS | `[247, 561]` | "We show that SARS-CoV-2 genomic diversity before February 2020 likely comprised only two distinct viral lineages, denoted \"A\" and \"B.\" Phylodynamic rooting methods, coupled with epidemic simulations, reveal that these lineages were the result of at least two separate cross-species transmission events into humans." |

The three Worobey-grounded proximity lines share the `src-worobey-2022` upstream
(both as `provenance.derivedFrom` **and** `grounding.source`), so `cairn intersect`
returns **REFUSE-TO-COMBINE**; `{geographic-clustering, two-lineages}` span disjoint
upstreams (Worobey vs Pekar) and return **COMBINABLE**.

## Trust-Ladder rungs (internal research notes `toolchest/01`; `internal notes`)

`L1` Observed artifact · `L2` Parsed · `L3` Attributed · `L4` Entailment-checked ·
`L5` Accepted (no open blocking objection) · `L6` Analysis conclusion.

- **Sources → L1.** Observed artifacts: fetched, hashed, cross-verified.
- **Claims → L4/L5.** L5 where the abstract *entails* the claim with no open
  objection (`geographic-clustering`, `live-mammal-sales`). L4 (entailment-checked,
  not yet "accepted") where an open consideration remains: `environmental-sampling`
  is framed in the abstract as a *within-market* spatial association (not an
  explicit market-vs-city contrast); `two-lineages` was reworded during vetting and
  the source carries the Bayes-factor erratum. Promotion to L5 is a review action
  (roadmap A5 / human-at-crux), not something to self-assert here.

## Two honest vetting decisions (recorded, not fabricated)

1. **Retired `claim-ascertainment-centroid`.** The distinctive content of that line
   — an *ascertainment-bias-corrected* early-case centroid — is a paper-body result;
   it does **not** appear in the abstract (the abstract never mentions ascertainment
   bias or a formal centroid). Rather than fabricate a span, it was replaced with
   `claim-live-mammal-sales`, which the abstract entails directly. The
   ascertainment-robustness idea survives in miniature inside
   `claim-geographic-clustering` ("*including those without reported direct links*").
   A future L4 version grounded to the open-access PMC full text is a clean extension.
2. **Reworded `claim-two-lineages`.** The original text asserted the two lineages are
   "consistent with a market origin." The words *market/Huanan/Wuhan* do **not**
   appear anywhere in the Pekar abstract; establishing the market link needs the
   paper body or the Worobey companion. The claim was narrowed to the two-lineages /
   ≥2-zoonotic-introductions core the abstract entails — which is all the demo's
   *disjoint-upstream* contrast requires.

## Reproduce

```bash
.venv/bin/python fixtures/build_fixtures.py         # re-mint (sha-pinned; fails on any byte drift)
cairn ground   'fixtures/*.json'                    # 4/4 spans resolve to their cited source
cairn validate fixtures/claim-geographic-clustering.json
cairn intersect 'fixtures/*.json' --claims <trio ids>   # REFUSE-TO-COMBINE
```

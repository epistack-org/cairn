# Egg / cardiovascular-disease mini-corpus — provenance & vetting record

_Floor deliverable #3 (`dev/cairn#9`). Same vetting standard as A1: **fabricated
provenance is the F0 sin the project exists to catch**, so every span here was
retrieved first-party and is mechanically re-checkable (`cairn ground`), and every
judgment call that could not be grounded was **recorded rather than papered over**._

## The hypothesis we set out to test — and why we cut it

We went looking for the naive story: *"the egg meta-analyses sloppily double-count the
same cohorts inside their own pooled estimates."*

**That story is false. We do not tell it.**

The careful reviews state explicit de-duplication rules. Godos 2021 (body): *"If more than
one study was conducted on the same cohort, only the dataset including the larger number of
individuals, the longest follow-up, or the most comprehensive data"* [is retained]. A 2022
review in *Frontiers in Nutrition* explicitly **finds and removes** participant overlap:
*"we found studies with significant participant overlap, including articles from the
National Health and Nutrition Examination Survey (NHANES) … the Health Professionals
Follow-Up Study (HPFS) … and the China Health and Nutrition Survey (CHNS)"*.

**No within-review double-count is proven anywhere in this literature.** The forest plots
are images; we could not verify one, and we will not assert one. Probe `F5` of
`assessment/probes-eggs.json` exists specifically to catch an assessor — or us — inventing
that villain. A fabricated internal double-count would have made a punchier exhibit and
would have been precisely the lie this engine exists to refuse.

## The real structure (subtler, and worse)

The laundering is **between reviews, at the aggregation layer** — not inside any one of
them.

```
                    ent-nhs-hpfs-cohorts          <-- the shared participant backbone
                        ^              ^
             src-hu-1999                src-drouin-chartier-2020
             (JAMA 1999, NHS+HPFS)      (BMJ 2020, NHS+NHS II+HPFS —
                        ^                the SAME people, longer window)
                        |                        ^
              +---------+------------------------+
              |                                  |
        src-rong-2013                      src-godos-2021
     (BMJ 2013 meta-analysis)      (Eur J Nutr 2021 meta-analysis,
                                    39 studies, "nearly 2 million")
              ^                                  ^
   claim-eggs-rong-no-association    claim-eggs-godos-no-association
                    (+ claim-eggs-drouin-no-association)
```

Three apparently independent reassuring findings — a 2013 *BMJ* dose-response
meta-analysis, a 2021 meta-analysis of 39 studies and *"nearly 2 million individuals"*, and
a 2020 *BMJ* three-cohort study plus updated meta-analysis — **all re-pool the same nurses
and health professionals.** Each review is *locally correct*. The non-independence is a
property of the **composition**, not a defect in any component.

> **"Nearly 2 million individuals" is not 2 million independent people.**
> Reading agreeing meta-analyses as independent confirmations counts one cohort backbone
> several times.

**This is the sophisticated exhibit.** There is no villain, no error to point at, and no
amount of per-paper rigour detects the problem. And the shared upstream is **invisible at
the claim level** — it is *two hops up*. It is found only by walking the DAG.

### It is the first REAL corpus to exercise the transitive detector

`cairn/provenance.py` has always walked the transitive closure, but until now that
capability was proven only against a **synthetic** fixture
(`tests/test_provenance.py::test_transitive_shared_ancestor_is_caught`). The COVID trio is
*flat* — three claims, one paper, one hop. Here the backbone appears in **no** claim's
direct `derivedFrom`, and `tests/test_cases.py::test_eggs_shared_upstream_is_found_only_transitively`
pins that property so it cannot silently regress into a direct edge.

## The grounding limitation that shaped the whole design (recorded)

**The meta-analyses never name their constituent cohorts in their abstracts.** Rong 2013,
Godos 2021, Zhong 2019 and Krittanawong 2021 all report pooled headline numbers and no
cohort list. The inclusion edges exist **only in Table 1**.

An abstract-level reader — human or model — therefore **structurally cannot see the
overlap**. (That is itself the finding, and it is probed as `I6`.)

So the `source_doc` for the two reviews is the **abstract plus the complete, unedited
included-studies table**, extracted deterministically from the Europe PMC open-access JATS
XML: cells whitespace-normalized and joined with `" | "`, rows joined with newlines. **The
full table ships** — trimming to the convenient rows would be cherry-picking.

A1 explicitly anticipated exactly this extension: *"A future L4 version grounded to the
open-access PMC full text is a clean extension."* This is that extension.

## Sources (retrieved first-party, sha-pinned)

| record | paper | ids | excerpt | sha256 |
|---|---|---|---|---|
| `src-hu-1999` | Hu FB, Stampfer MJ, Rimm EB, et al. — "A prospective study of egg consumption and risk of cardiovascular disease in men and women", *JAMA* 281(15):1387-94 | PMID `10217054` · DOI `10.1001/jama.281.15.1387` | abstract | `ce74e4ba…162769` |
| `src-drouin-chartier-2020` | Drouin-Chartier JP, et al. — "Egg consumption and risk of cardiovascular disease: three large prospective US cohort studies, systematic review, and updated meta-analysis", *BMJ* 368:m513 | PMID `32132002` · PMC7190072 | abstract | `69e0dd07…34f786` |
| `src-djousse-2008` | Djoussé L, Gaziano JM — "Egg consumption in relation to cardiovascular disease and mortality: the Physicians' Health Study", *AJCN* 87(4):964-9 | PMID `18400720` · PMC2386667 | abstract | `4b21e2cb…06f8ca` |
| `src-rong-2013` | Rong Y, et al. — "Egg consumption and risk of coronary heart disease and stroke: dose-response meta-analysis of prospective cohort studies", *BMJ* 346:e8539 | PMID `23295181` · PMC3538567 | **abstract + Table 1** | `c0b06aab…f3729c` |
| `src-godos-2021` | Godos J, et al. — "Egg consumption and cardiovascular risk: a dose-response meta-analysis of prospective cohort studies", *Eur J Nutr* 60(4):1833-1862 | PMID `32865658` · PMC8137614 | **abstract + Table 1** | `0cd54915…3a1faf` |

**Retrieval (2026-07-13).** Abstracts via NCBI E-utilities `efetch` (structured
`AbstractText` sections serialized as `LABEL: text`, one per line). Tables via the Europe
PMC OA JATS XML — **two independently operated services**, as A1 required.

### Two encoding traps that will silently break a naive re-typing

* The **BMJ** abstracts use **U+2009 THIN SPACE** as the digit-group separator: `83 349` is
  `83 349`. Retyping it with an ASCII space fails the span check.
* Rong's Table 1 uses **U+2019 RIGHT SINGLE QUOTATION MARK** in *"Nurses’ Health Study"*.
  An ASCII apostrophe does not match.

Both are pinned as retrieved. This is a small illustration of why `cairn ground` checks
*bytes* and not "does the paper support this".

## Claims (each grounded to a real span; `source.excerpt[char_span] == quote`)

**The laundered set** (three "independent" reassuring findings → REFUSE-TO-COMBINE):

| claim | source | rung | grounding quote (verbatim substring) |
|---|---|---|---|
| `claim-eggs-rong-no-association` | Rong 2013 | **L5** | "Higher consumption of eggs (up to one egg per day) is not associated with increased risk of coronary heart disease or stroke." |
| `claim-eggs-godos-no-association` | Godos 2021 | **L5** | "There is no conclusive evidence on the role of egg in CVD risk" |
| `claim-eggs-drouin-no-association` | Drouin-Chartier 2020 | **L5** | "an increase of one egg per day was not associated with cardiovascular disease risk" |

**The structural claims** — their job is to *evidence the `derivedFrom` edges with bytes*,
so the DAG is not asserted by us. They deliberately carry **no `illustrative_LR`**: they are
evidence *about* the DAG, not evidential lines to be combined (enforced by
`test_structural_claims_carry_no_likelihood_ratio`).

| claim | source | grounding quote |
|---|---|---|
| `claim-eggs-rong-pools-nhs-hpfs` | Rong 2013 Table 1 | "Hu et al36 \| 1999 \| Nurses’ Health Study \| USA \| Female" |
| `claim-eggs-godos-pools-nhs-hpfs` | Godos 2021 Table 1 | "Hu [16] \| HPFS, 1986 and NHS, 1980 (US)" |
| `claim-eggs-godos-pools-drouin` | Godos 2021 Table 1 | "Drouin-Chartier [48] \| HPFS, 1986, NHS, 1980, NHS II, 1991 (US)" |

**The contrast** (genuinely independent → COMBINABLE): `claim-eggs-hu-no-association`
(NHS + HPFS) and `claim-eggs-djousse-no-association` (Physicians' Health Study — 21,327
male physicians, a **disjoint participant pool**). Different people, different upstream;
combining is licensed. This mirrors the Worobey-vs-Pekar contrast in the COVID case.

## The scope limit we must not overstep

**The egg evidence base does NOT reduce to the US cohorts, and we do not claim it does.**
Godos's table also carries genuinely independent Asian (JPHC, CKB), European (EPIC, NLCS,
KIHD) and other cohorts, and Drouin-Chartier's own abstract reports a **geographic
interaction** (an inverse association in Asian cohorts). So the effective independence here
is **well above 1** — it is simply far below the number of meta-analyses. The Phase-2
corpus run measured **n_eff = 3.97** for this crux, the *highest* of the three cases.

Probe `I5` scores exactly this boundary: an assessor who answers "the whole literature is
just NHS/HPFS" has **overstated cairn's own finding**, which would be its own kind of
fabrication.

## What we could NOT verify (do-not-assert list)

1. **Zhong 2019's six constituent cohorts — UNCERTAIN.** Its abstract says only *"6
   prospective US cohorts"* and never names them; the names appear only in Godos's Table 1
   footnote (a secondary source), and PMC6439941's full text is not retrievable. **Not
   minted.**
2. **Krittanawong 2021 — UNVERIFIED.** Not open access; we have the abstract but cannot see
   its included-studies list. We do **not** assert it pools NHS/HPFS. **Not minted.**
3. **No egg-specific published critique of cohort double-counting appears to exist.** The
   closest is Senn 2009 (*"Overstating the evidence: double counting in meta-analysis"*,
   BMC Med Res Methodol 9:10) — real, and general/methodological, but **not about eggs**.
   The only egg-specific in-print acknowledgment of the overlap is the *Frontiers in
   Nutrition* 2022 body sentence quoted above, and it **cuts both ways**: that team found
   the overlap and removed it. If our writeup needs "a published paper called this out for
   eggs" — **that paper does not appear to exist, and we will not imply otherwise.**

## Reproduce

```bash
.venv/bin/python fixtures/build_fixtures.py                 # re-mint (sha-pinned; fails on byte drift)
.venv/bin/cairn ground 'fixtures/*.json'                    # all spans resolve to their cited source
.venv/bin/cairn intersect 'fixtures/*.json' --claims \
  $(python3 -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-eggs-rong-no-association','claim-eggs-godos-no-association','claim-eggs-drouin-no-association']))")
# -> REFUSE-TO-COMBINE, collective shared upstream = [ent-nhs-hpfs-cohorts]  (two hops up)
```

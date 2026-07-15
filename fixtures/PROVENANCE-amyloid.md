# Alzheimer's Aβ*56 mini-corpus — provenance & vetting record

_The 4th worked example, added in the **2026-07-15 decoupling spike**. Same vetting
standard as the other three: **fabricated provenance is the F0 sin the project exists to
catch**, so every span here was retrieved first-party from NCBI E-utilities and is
mechanically re-checkable (`cairn ground`), and every judgment call that could not be
grounded was **recorded rather than papered over**._

## Why this case exists (read this first)

The other three worked examples (COVID, eggs, CERN) were co-developed with the engine.
That is a methodological hazard: an engine tuned until three hand-picked cases pass is not
evidence the engine generalizes — it may just be evidence the cases were fitted to it.
This case was added **after** the engine was frozen, from a live scientific controversy
nobody on the team had modelled, to test exactly that. The build's self-verification
(`build_fixtures.py` → `test_cases.py`) passed on the first structurally-correct DAG, and
the two footguns it surfaced are recorded below rather than smoothed over. See
`flf-contest/draft-entry/synthesis/DECOUPLING-SPIKE.md` for the full write-up.

## The punchline

Aβ*56 — a specific 56-kilodalton soluble amyloid-β assembly — became one of the
most-cited soluble-oligomer results in Alzheimer's research. Three findings look like
independent corroboration that it is a real, memory-impairing species:

| | paper | venue | year | what it contributes | shares |
|---|---|---|---|---|---|
| 1 | Lesné, Koh, …, Ashe | **Nature** (RETRACTED 2024) | 2006 | Aβ*56 from Tg2576 mice disrupts memory in rats (the origin) | — |
| 2 | Lesné, Sherman, …, Ashe | Brain | 2013 | Aβ*56 in **human** brain correlates with pathological tau | lab + species + senior author |
| 3 | Sherman & Lesné | Methods Mol Biol | 2011 | the Aβ*56 **detection assay itself** | lab + species + reagent |

All three descend from **one originating characterization** (Lesné 2006) operationalized by
**one laboratory's assay** (Ashe/Lesné, U Minnesota). The human-brain paper and the methods
paper are the *same* characterization re-measured with the *same* reagent — not two more
independent votes. `cairn intersect` refuses the trio and names `ent-abeta56` (and,
transitively, the retracted `src-lesne-2006`).

The shared upstream is unusual, and that is the point: it is **simultaneously a foundational
RESULT and a shared REAGENT/ASSAY**. It generalizes the CERN "shared premise" node one step
further — a shared upstream can be a shared *measurement apparatus*, not only a shared
dataset or argument. Every downstream edge into it is span-grounded by the citing abstract
naming `Aβ*56` / `Abeta*56`.

## What this case does NOT say

**It does not say the amyloid hypothesis is false, and it does not say soluble Aβ oligomers
are harmless.** It is a claim about corroboration-**counting** for one species. The contrast
proves the boundary in the other direction:

> **Shankar et al. 2008** (*Nature Medicine*, Selkoe/Walsh) isolated soluble Aβ **dimers**
> directly from human Alzheimer's brain — a different species, a different lab, a different
> preparation — and showed they impair synapse function.

That line is upstream-disjoint from Aβ*56, so `{claim-abeta56-impairs-memory,
claim-shankar-dimers}` returns **COMBINABLE**. The general "soluble Aβ oligomers are
synaptotoxic" claim has support that does not route through Lesné 2006; only the
*Aβ*56-specific* corroboration count is inflated. Probe `I3` in `assessment/probes-amyloid.json`
exists to stop an assessor — or us — from over-claiming the refusal into "the hypothesis
collapses." This mirrors the eggs case's scope-limit note exactly.

## Sources (all L1, retrieved 2026-07-15, sha-pinned)

| record | PMID | DOI | excerpt sha256 (first 12) | Greek-β form |
|---|---|---|---|---|
| `src-lesne-2006` | 16541076 | 10.1038/nature04533 | `d34840d0a0b4` | **ASCII** `Abeta*56` |
| `src-lesne-2013` | 23576130 | 10.1093/brain/awt062 | `f795a135a829` | **Unicode** `Aβ*56` |
| `src-sherman-2011` | 20967582 | 10.1007/978-1-60761-744-0_4 | `2365ef5e7845` | **Unicode** `Aβ*56` |
| `src-shankar-2008` | 18568035 | 10.1038/nm1782 | `c2991a214c14` | **ASCII** `Abeta` |

**Retrieval method.** `efetch` (PubMed, `rettype=abstract&retmode=xml`); abstract text
extracted with `AbstractText` `itertext()` (the four are unstructured abstracts, so the text
is verbatim). Raw abstracts ship under `fixtures/sources/*.abstract.txt` and the build fails
loudly if a byte drifts.

**The retraction is a first-party fact, not editorializing.** The Lesné 2006 PubMed record
carries a `RetractionIn` reference: *Nature 2024 Jul;631(8019):240 (10.1038/s41586-024-07691-8),
PMID 38914864*. Image-integrity concerns were first raised publicly in 2022 (Schrag, via
Piller, *Science*). The Lesné 2013 record carries an `ErratumIn` (*Brain 2022;145(8):e72-e76*,
10.1093/brain/awac143). Both are recorded on the source records; **neither is an input to the
refusal** — the trio shares its upstream whether or not the origin has been retracted (probe
`I4` pins this).

## The two footguns this case surfaced

### Footgun 1 — the same concept, two byte-strings (`Abeta*56` vs `Aβ*56`)

PubMed changed its Greek-letter serialization between deposits. The 2006 and 2008 records
spell the peptide in **ASCII** (`Abeta`, `Abeta*56`); the 2011 and 2013 records use the
**Unicode** Greek small letter beta, U+03B2 (`Aβ`, `Aβ*56`). The span check is byte-exact, so
a quote copied from the 2013 abstract into a claim grounded in the 2006 abstract would
**silently fail to be a substring** — or, worse, a hand-typed `Aβ*56` (Unicode) would not
match a source that stored `Abeta*56` (ASCII). Every `grounds.quote` and every claim quote is
pinned to the exact bytes of **its own** source; the mismatch is called out in each source's
`retrieval.encoding_note`. This is the amyloid-case analogue of the eggs case's U+2009 THIN
SPACE and U+2019 curly-apostrophe hazards — and it is exactly the class of error the engine
exists to make impossible to commit silently.

### Footgun 2 — which node is the derivation *root* (entity-vs-source)

The first structurally-passing DAG made the **entity** (`ent-abeta56`) the root and had the
2006 paper derive *from* it. That passes every test — the trio still refuses — but it is
**backwards**: it reifies Aβ*56 as a pre-existing thing the three papers independently
observe, and it hides the retracted origin paper from the shared-upstream set the refusal
names. The honest topology makes the **origin source** the root:

```
src-lesne-2006  (derivedFrom [])            ← the true root: Aβ*56 was named in exactly one paper
      ↑
ent-abeta56     (derivedFrom [src-lesne-2006])   ← the species/assay, declared shared upstream
      ↑                    ↑
src-lesne-2013     src-sherman-2011         (each derivedFrom [ent-abeta56] → routes to the origin)
      ↑                    ↑
claim-human-brain   claim-detection-method
```

With this ordering the collective intersection over the trio names **both** `ent-abeta56`
**and** the retracted `src-lesne-2006` — which is the story. The lesson for the corpus: the
detector is purely topological, so it will happily certify a DAG that is locally consistent
but semantically inverted. **The honesty burden is entirely in how the edges are drawn**, and
a passing test is necessary but not sufficient. (This is the same lesson the COVID case's
naive-vs-honest DAG teaches, met here from the other direction.)

## Fact-check log

- **Lesné 2006 retraction** — CONFIRMED from the PubMed `RetractionIn` field of PMID 16541076
  (Nature 631(8019):240, 2024). Not asserted from memory.
- **Byte forms of `Abeta*56` / `Aβ*56`** — CONFIRMED by extracting each abstract and locating
  the literal substring; the ASCII/Unicode split is real and per-record.
- **Shankar 2008 is upstream-disjoint** — CONFIRMED by abstract: "extracted soluble
  amyloid-beta protein (Abeta) oligomers directly from the cerebral cortex of subjects with
  Alzheimer's disease" and "dimers are the smallest synaptotoxic species" — a different
  species, lab (Selkoe/Walsh), and preparation from the Tg2576-derived Aβ*56.
- **Scope discipline** — the case asserts non-independence of the *Aβ*56-specific* corroboration
  count only. It does **not** assert the amyloid hypothesis is false; asserting that would
  itself be the kind of over-reach the engine exists to prevent, and probe `I3` scores it as
  the wrong answer.

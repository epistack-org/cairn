# Cairn — the decoupled epistack scoring engine

Cairn is the small, plain `git + one container` engine behind epistack's
refuse-to-combine thesis. It has **no substrate dependency** —
no orchestrator, no private network, no forge — by design: the *scoring* must run, and be
re-checkable on a fresh machine.

It is the **one artifact schema + the mechanical checks a single careful
Claude-Code transcript structurally cannot produce**:

1. **The Cairn envelope** (`cairn/envelope.py`) — a nanopublication-shaped,
   content-addressed (Trusty-URI over JCS/RFC-8785), ed25519-signed knowledge
   record. One envelope carries both **claims (verbs)** and **entities (nouns)**;
   the signature block is excluded from the content hash, so many teams can
   **endorse one content-id** (the n_eff-over-endorsers promotion model).
2. **Kish design-effect ESS** (`cairn/neff.py`) — `n_eff = k / (1 + (k-1)·φ̄)`, the clustering-component design-effect ESS (a redundancy diagnostic, not an estimator), measured
   effective-independence number. "9 assessors agreed" is a headline lie when they
   share errors. Now **measured on our own corpus** (roadmap A2, `cairn/assessment.py`
   + `cairn assess`): a 9-assessor panel on the COVID-HSM crux gives **n_eff = 1.06**
   when they share the evidence (a homogeneous panel: exactly **1.00**) — within-vendor
   model diversity buys ≈ 0 independence, **and so does cross-vendor**: a Zhipu GLM-4.6
   panel agrees at the same φ (cross-vendor 0.946 ≈ within-vendor 0.937/0.948), so a
   two-vendor k=18 panel is still n_eff ≈ 1 — the redundancy is in the evidence, not the
   model family. See [`assessment/ASSESSMENT.md`](assessment/ASSESSMENT.md). (Anchor:
   "Nine Judges, Two Effective Votes", arXiv:2605.29800.)
3. **The layer-(a) shared-source detector** (`cairn/provenance.py`) — walks the
   `derivedFrom` DAG; if claims proposed as "independent" share an upstream it
   returns **REFUSE-TO-COMBINE**, naming the shared tuple.
4. **Span-grounding / faithfulness** (`cairn/grounding.py`) — every L4/L5 claim
   carries the tuple `(source_doc, char_span, extractor, entailment_label)`;
   `cairn ground` mechanically checks that `source.excerpt[char_span] == quote`
   and that the cited source is a real upstream (`derivedFrom`). Not "the paper
   supports this" as prose — the exact bytes, re-checkable on a fresh machine.
5. **The Fréchet / p-box interval** (`cairn/frechet.py`) — the quantitative form of
   refuse-to-combine (roadmap A3, `cairn frechet`). A naive transcript multiplies the
   trio's likelihood ratios into a point (125:1). Cairn emits an **interval whose
   width is the refusal**: the naive point is only the *independence ceiling* of a
   redundancy interval `[5, 125]` whose floor is the single strongest line, the
   A2-measured `n_eff ≈ 1` places the honest estimate *at that floor* (`LR^{n_eff}`),
   and — since the honest interval spans 25× — the verdict is
   **REFUSE-TO-COMBINE-AS-POINT** (exit 2). It ships the *true* dependence-free bound
   (`[0, ∞]`, vacuous) and the positive-dependence envelope (`[1.25, 500]`) alongside,
   correctly labelled, so a model is never mistaken for a bound. See
   [`assessment/FRECHET.md`](assessment/FRECHET.md).

## The worked examples

Cairn ships **seven** vetted, span-grounded cases. In each one, several lines of evidence
look independent, are treated as independent, and **are not** — and in each one the
refusal is mechanical, byte-checkable, and reproducible on a fresh machine.

| case | the apparently independent lines | what they actually share | how far up |
|---|---|---|---|
| **covid-origins** | 3 proximity lines (geographic clustering, live-mammal sales, environmental sampling) | **one dataset** — Worobey 2022's early-case data | 1 hop |
| **eggs-good-for-you** | 3 reassuring meta-analyses (*BMJ* 2013, *Eur J Nutr* 2021 "nearly 2 million individuals", *BMJ* 2020) | **one cohort backbone** — the same nurses & health professionals (NHS/HPFS) | **2 hops (transitive)** |
| **cern-black-hole** | 3 collider-safety assurances (LSAG 2008, Giddings & Mangano 2008, Jaffe 2000 — *two accelerators, three author teams, eight years apart*) | **one premise** — "cosmic rays have hit astronomical bodies harder for billions of years and they're still here" | 1 hop |
| **amyloid-abeta56** | 3 reports of Aβ*56 as a memory-impairing species (Lesné 2006 mice, Lesné 2013 human brain, Sherman 2011 the assay) | **one foundational result + one assay** — the Lesné 2006 characterization (RETRACTED 2024), carried by one lab | 1 hop |
| **ivermectin-elgazzar** | 3 positive COVID mortality syntheses (Bryant 2021 RR 0.38, Zein 2021 RR 0.39, Kory 2021 review) | **one fabricated primary trial** — the Elgazzar preprint (WITHDRAWN 2021-07-14), pooled by all three | **2 hops (transitive)** |
| **anversa-ckit** | 3 reports that c-kit+ cardiac stem cells regenerate the heart (Beltrami 2003 rodent, Bearzi 2007 human, Bolli 2011 SCIPIO trial) | **one lab's cell + its preps** — the Anversa characterization; SCIPIO used the lab's own cells (RETRACTED 2019) | 1 hop |
| **poldermans-decrease** | 3 pro-benefit perioperative β-blocker findings (DECREASE-I 1999, Boersma 2001, DECREASE-IV 2009) | **one research program** — the Poldermans/Erasmus DECREASE trials, found to rest on fabricated data | 1 hop |

Each case declares its structure in its bundle's `CASE.json`, and the build **mechanically
verifies the declaration against what the detector actually finds** before writing a single
record. "Cairn ships 7 worked examples" is a checked property of the corpus, not a sentence
in this README (`tests/test_cases.py`).

Each case is a **self-contained bundle** under [`fixtures/cases/<case-id>/`](fixtures/cases):
its own `build.py` (which mints the case's records through the shared
[`fixtures/lib/mint.py`](fixtures/lib/mint.py) — one signing seed, timestamp, and JCS
canonicalizer, so no bundle can drift the corpus' Trusty-URIs) and its `CASE.json` manifest
slice. The build assembles the aggregate `fixtures/CASES.json`/`INDEX.json` from the bundles
in the order pinned by [`fixtures/cases/cases.lock`](fixtures/cases/cases.lock), so **adding a
case is a new bundle plus a reviewed `cases.lock` line, not an edit to a monolith**. The lock
carries a content digest per bundle (silent drift fails CI), and `cairn cases verify <bundle>`
runs a case's declared structure — laundered set REFUSES, declared shared upstream, contrast
verdict — against any store, the same crank a fresh or external case repo is checked by.

They are deliberately different *shapes* of shared upstream — a **dataset**, a **cohort**,
a **premise**, a **foundational-result-plus-reagent**, a **fabricated primary trial**, a
**single lab's reagent**, and a whole **compromised research program** — because layer-(a)
non-independence is not only about sharing a corpus. The last three were added in the
2026-07-15 **backtest-scaling** pass (dev/cairn#15) from a ranked sweep of *known-answer*
fraud / non-independence cases: each has a settled meta-fact (a withdrawal, an
institutional misconduct finding), so a naive ingest can be checked against the answer key —
and **poldermans-decrease** is the sharpest of all, the one case where removing the
fabricated lineage does not just deflate the vote count but **flips the pooled result's sign
from benefit to harm**. The amyloid case (added in the 2026-07-15 decoupling spike, from a
controversy the engine was *not* co-developed against) is the generalization test; the eggs
case is the subtlest of the originals:

> Every egg review is **individually correct**. They each de-duplicate properly; there is
> no villain and no error to point at in any single paper. The non-independence is a
> property of the **composition**, and the shared backbone is invisible at the claim level
> — it is two hops up, found only by walking the DAG. *"Nearly 2 million individuals" is
> not 2 million independent people.*

And the CERN case is the sharpest test of the thesis, because it is the case with the
**strongest** expert consensus (Phase 2 measured the highest inter-assessor agreement here,
φ̄ = 0.242, yet n_eff = 2.54). An engine that rewarded consensus would score it as
overwhelming. **It does not say the LHC is unsafe** — it says three assurances that share a
premise are not three votes.

Full vetting records, including what we *could not* verify and the hypotheses we **cut**
because the literature did not support them:
[`fixtures/PROVENANCE.md`](fixtures/PROVENANCE.md) (covid) ·
[`fixtures/PROVENANCE-eggs.md`](fixtures/PROVENANCE-eggs.md) ·
[`fixtures/PROVENANCE-cern.md`](fixtures/PROVENANCE-cern.md) ·
[`fixtures/PROVENANCE-amyloid.md`](fixtures/PROVENANCE-amyloid.md) ·
[`fixtures/PROVENANCE-ivermectin.md`](fixtures/PROVENANCE-ivermectin.md) ·
[`fixtures/PROVENANCE-anversa.md`](fixtures/PROVENANCE-anversa.md) ·
[`fixtures/PROVENANCE-poldermans.md`](fixtures/PROVENANCE-poldermans.md).

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python fixtures/build_fixtures.py     # mint all 7 vetted corpora (sha-pinned)
.venv/bin/python -m pytest -q                   # 195 tests
.venv/bin/python demo/worked_examples.py        # all seven cases, side by side
.venv/bin/cairn ground 'fixtures/*.json'        # 37/37 claim spans resolve to their source
.venv/bin/cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json  # recompute measured n_eff
.venv/bin/cairn frechet fixtures/claim-geographic-clustering.json fixtures/claim-environmental-sampling.json fixtures/claim-live-mammal-sales.json fixtures/src-worobey-2022.json  # -> REFUSE-TO-COMBINE-AS-POINT (exit 2): the honest interval
.venv/bin/cairn explain 'fixtures/*.json' --claims claim-geographic-clustering claim-environmental-sampling claim-live-mammal-sales  # -> the refusal as one plain-English paragraph, incl. what would un-refuse it
.venv/bin/cairn headtohead 'fixtures/*.json'    # -> the four-delta head-to-head vs a careful baseline (exit 2 == delta demonstrated)
.venv/bin/python demo/hsm_trio.py               # the head-to-head (naive + careful baseline vs Cairn)

# the other two cases refuse the same way (exit 2 == refused):
.venv/bin/cairn intersect 'fixtures/*.json' --claims $(python3 -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-eggs-rong-no-association','claim-eggs-godos-no-association','claim-eggs-drouin-no-association']))")
.venv/bin/cairn intersect 'fixtures/*.json' --claims $(python3 -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-cern-astro-stability','claim-cern-wd-ns-bound','claim-cern-moon-strangelet']))")

# generalize beyond the built-in cases: ingest a foreign, DOI-cited corpus and refuse on it.
# Here, the public baseline's OWN natural-origin evidence, imported by DOI (no baseline clone):
.venv/bin/python demo/import_example/verify_baseline_import.py   # names the Crits-Christoph double-count its dedup missed
.venv/bin/cairn import demo/import_example/baseline-natorigin.json --out /tmp/imported
.venv/bin/cairn intersect '/tmp/imported/*.json' --claims import-environmental-samples-wildlife-stall-positivity import-raccoon-dog-susceptible-species-genetic-tracing  # -> REFUSE on doi:10.1016/j.cell.2024.08.010 (exit 2)

# or, fully self-contained:
docker build -t cairn -f Containerfile . && docker run --rm cairn
```

### The deep demo (`demo/hsm_trio.py`)

The COVID "three independent lines of proximity evidence" descend from **one paper,
one author collective**; at the data layer two of the three trace to the same
market-anchored PRC early-case investigation — the third (Xiao 2021) does not, and we
say so. Each is **span-grounded** to its source (`cairn ground` resolves). A naive
transcript multiplies their
likelihood ratios (5×5×5 = 125:1). Cairn:

- **REFUSE-TO-COMBINE** — the three trace to one upstream → multiplying is undefined;
- **measured n_eff** (A2) — a 9-assessor panel on the crux gives n_eff = 1.06 sharing
  evidence (homogeneous 1.00), rising to only 1.63 with *every* diversity lever — 9
  assessors are ~1–2 effective votes, not 9;
- **the Fréchet interval** (A3) — instead of the fake 125:1 point it emits the honest
  interval `[5, 125]` (the naive point is the independence *ceiling*; measured n_eff≈1
  puts the truth at the *floor*), width 1.4 decades → **REFUSE-TO-COMBINE-AS-POINT**;
- and where independence *does* hold (a proximity line + the molecular two-lineages
  line, Pekar 2022 — disjoint upstream) it returns **COMBINABLE** (`LR = 20`, never 500).

That is *knowing when not to compute*, mechanically — the delta the baseline can't produce.
The corpus is **vetted, not illustrative**: real sources, real spans, entailment
labels, Trust-Ladder L4/L5 — see [`fixtures/PROVENANCE.md`](fixtures/PROVENANCE.md).

**A4 — the careful baseline (measured, not asserted).** The `NAIVE BASELINE` above is a
strawman (`math.prod`). A4 adds a **careful** one: a 5-run panel of Claude-Code
investigations on the same crux, evidence-only, no cairn. The honest finding — built to
survive the FLF "Note 1" judge — is that the careful baseline reconstructs the *reasoning*
in prose (5/5 name the shared Worobey source, 5/5 refuse the naive `125:1`, some even
sketch the `[5,125]` interval), yet it cannot emit the reproducible, exit-code-gated
artifacts, and exactly one delta (**measured `n_eff`**) is *structurally impossible* for a
single transcript (`n=1`). The delta is **mechanization + reproducibility + contestability,
not cognition**. See [`assessment/HEAD_TO_HEAD.md`](assessment/HEAD_TO_HEAD.md)
(`cairn headtohead`).

## CLI

```bash
cairn mint record.json --sign           # content-address + sign
cairn validate record.json              # schema + id + signature integrity
cairn neff matrix.json                  # n_eff over a binary agreement matrix
cairn intersect 'fixtures/*.json'       # refuse-to-combine verdict over a claim set
cairn ground 'fixtures/*.json'          # verify claims' spans resolve to their cited source
cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json  # recompute + verify measured n_eff
cairn frechet 'fixtures/claim-*.json' 'fixtures/src-*.json'  # Fréchet/p-box interval + refuse-when-too-wide verdict
cairn headtohead 'fixtures/*.json'      # A4: careful-baseline head-to-head over the four deltas (exit 2 = delta demonstrated)
cairn cases verify fixtures/cases/covid-origins  # run one bundle's declared structure against the store (the reusable crank)
cairn cases list                        # discover the case bundles and check them against cases.lock
```

## Layout

| path | what |
|---|---|
| `cairn/envelope.py` | the record envelope: JCS → Trusty-URI → ed25519 sign/verify, schema validate |
| `cairn/neff.py` | Kish n_eff over correlated assessors |
| `cairn/provenance.py` | the shared-upstream / refuse-to-combine detector |
| `cairn/grounding.py` | the span-grounding / faithfulness check (`source.excerpt[char_span] == quote`) |
| `cairn/frechet.py` | the Fréchet/p-box interval + refuse-as-point verdict (A3) — the honest interval, not a point |
| `cairn/headtohead.py` | the A4 careful-baseline head-to-head — the four deltas, reached-in-prose vs the reproducible artifact |
| `cairn/assessment.py` | recompute + verify the measured n_eff from a pinned assessor run (`cairn assess`) |
| `cairn/trusty.py`, `canonical.py`, `keys.py` | content-addressing, JCS, signing primitives |
| `schemas/cairn.schema.json` | the envelope JSON Schema (Draft 2020-12) incl. the grounding tuple + Trust-Ladder enum |
| `fixtures/` | the **vetted** corpora for all **7 worked examples** — span-grounded claims (L4/L5) + sha-pinned sources |
| `fixtures/cases/<case-id>/` | one **self-contained bundle** per case: `build.py` (mints its records) + `CASE.json` (its manifest slice). Adding a case is a new bundle here |
| `fixtures/cases/cases.lock` | the ordered case registry + a content digest per bundle — pins the aggregate INDEX/CASES order and catches silent bundle drift |
| `fixtures/lib/mint.py` | the shared minting library every bundle imports (seed, timestamp, `SOURCES`, `mk`/`mk_claim`) — the determinism anchor |
| `fixtures/CASES.json`, `INDEX.json` | the aggregate manifests, **assembled from the bundles** in `cases.lock` order. The build verifies each declaration against the detector; CI re-checks it |
| `fixtures/sources/*.abstract.txt` | the byte-exact retrieved sources (the raw `source_doc`s) |
| `fixtures/PROVENANCE.md`, `PROVENANCE-eggs.md`, `PROVENANCE-cern.md` | per-case retrieval record, rung rationale, and the honest vetting decisions — **including the hypotheses we cut and the things we could not verify** |
| `assessment/probes.json`, `probes-eggs.json`, `probes-cern.json` | one probe battery per case (crux + keyed faithfulness probes + inferential probes) |
| `demo/worked_examples.py` | all seven cases side by side — the wide view |
| `demo/hsm_trio.py` | the naive-vs-Cairn head-to-head — the deep view (COVID) |
| `assessment/` | the **measured** A2 assessor pass: probe battery, evidence partitions, panel + pinned runs |
| `assessment/ASSESSMENT.md` | the measured n_eff, the diversity levers, and the adversarial audit's honest caveats |
| `assessment/FRECHET.md` | the A3 interval: the three nested regimes, the bootstrap CI on φ̄, and the model-vs-bound honesty |
| `assessment/HEAD_TO_HEAD.md` | the A4 method: the fair careful-baseline panel, the four-delta table, and the honest concessions |
| `assessment/baseline.json`, `build_headtohead.py` | the pinned careful-baseline panel (captured runs) + the deterministic head-to-head re-score → `head_to_head.json` |
| `assessment/frechet.py`, `frechet_pba_check.py` | pin the A3 interval artifact; cross-check it against the `pba` library (dev-only) |
| `tests/` | 195 pytest checks incl. the n_eff anchor, the grounding leg, the measured-assessor pass, the cross-vendor leg, the Fréchet leg, the refusal-AUC leg, the A4 head-to-head leg + the 7-case structural leg (`test_cases.py`) |

## Disciplines / honest debts

- **JCS for v0** (git-native); RDFC-1.0 (RDF-canonical) is the documented migration —
  switching changes the URI scheme (one-way door).
- **Fixtures are vetted (roadmap A1; all 4 cases).** Every claim is span-grounded to a
  first-party, byte-verified source and carries a Trust-Ladder rung (L1 sources;
  L4/L5 claims) — no record sits at `unverified-fixture` (the value is no longer
  admissible; any record still carrying it fails `cairn validate`). Judgment calls that
  could not be sourced were **recorded, not fabricated** — see the three `PROVENANCE*.md`.
  `n_eff` agreement vectors in the demo remain *illustrative* (measuring them over
  heterogeneous assessors is roadmap A2).
- **Two case hypotheses were CUT because the literature did not support them.** We went
  looking for eggs meta-analyses that double-count cohorts *inside* their own pooled
  estimates — they don't; they de-duplicate properly, and asserting otherwise would have
  been the exact fabrication this engine exists to refuse. And we went looking for "every
  LHC safety assurance leans on the cosmic-ray argument" — the 2003 report's black-hole
  conclusion is *theoretical* (Hawking decay), so the blanket claim is false and the CERN
  crux is stated **conditionally** instead. The real structures turned out to be subtler
  and stronger. Both cuts are documented in the per-case `PROVENANCE`.
- **The CERN corpus has a weaker retrieval guarantee than COVID, and says so.** A1 required
  byte-identical text from two independently operated services. For the arXiv papers,
  INSPIRE-HEP serves an identical abstract but declares its source as **`arXiv`** — it
  *mirrors* the same upstream, so it is not a second witness. (We hit the shared-upstream
  problem inside our own verification pipeline.) Crossref confirms the *bibliographic*
  record but deposits no abstract text. The text is therefore single-sourced, and that is
  recorded on each record rather than glossed.
- **Author-level non-independence is a real gap.** Mangano co-authored both the
  Giddings-Mangano bound and the LSAG review that leans on it. The layer-(a) detector walks
  the provenance DAG and **does not read author lists**, so it cannot currently see this. It
  is recorded on the source record and probed in the battery — an honest debt, not a silent
  one.
- This engine does **layer (a)** (explicit shared source) and the **Fréchet/p-box
  interval** (A3, `cairn/frechet.py`) — the honest interval + principled refusal.
  Legs **(b)** shared derivation (ProvSQL) and **(c)** hidden confounder (causal
  tooling) are the next slices, not yet here.

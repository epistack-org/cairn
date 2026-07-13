# CERN black-hole mini-corpus — provenance & vetting record

_Floor deliverable #3 (`dev/cairn#9`). Same vetting standard as A1: **fabricated
provenance is the F0 sin the project exists to catch**, so every span here was
retrieved first-party and is mechanically re-checkable (`cairn ground`), and every
judgment call that could not be grounded was **recorded rather than papered over**._

## The punchline

Three collider-safety assurances that look **maximally independent** —

| | paper | accelerator | authors | year | catastrophe |
|---|---|---|---|---|---|
| 1 | Ellis et al. (the LSAG report) | LHC | 5 CERN theorists | 2008 | black holes |
| 2 | Giddings & Mangano | LHC | 2 theorists | 2008 | black holes |
| 3 | Jaffe, Busza, Sandweiss, Wilczek | **RHIC** | 4 MIT/Yale theorists | **2000** | **strangelets** |

— all reach "safe" through **one** load-bearing empirical premise:

> *cosmic rays have bombarded astronomical bodies at higher energies for billions of
> years, and those bodies are still here.*

And each paper **says so in its own abstract**. So the shared-upstream edge is
span-grounded, not asserted by us. `cairn intersect` refuses the trio and names
`ent-cosmic-ray-argument`.

**This is the sharpest test of the thesis in the whole corpus**, because it is the case
with the *strongest* expert consensus (the Phase-2 corpus run measured the highest
inter-assessor agreement here, φ̄ = 0.328, and yet n_eff = 2.16). An engine that
rewarded consensus would score this case as overwhelming. Cairn prices it honestly.

### What this case does NOT say

**It does not say the LHC is unsafe.** Giddings & Mangano may be entirely correct. The
finding is about the *arithmetic of combining* assurances, not about the safety
conclusion. Three assurances that share a premise are not three votes — that is all.
Probe `I5` of `assessment/probes-eggs.json`'s sibling battery (`probes-cern.json`) exists
to pin this down explicitly, because misreading a refusal-to-combine as a claim of danger
is the single most damaging way this work could be misused.

## The honest refinement (the hypothesis was too strong, and we cut it back)

The hypothesis we set out to test was *"**every** LHC safety assurance leans on the
cosmic-ray argument."* **That is an overclaim, and we do not make it.**

The literature runs **two** distinct argument families:

* **(A) theoretical** — microscopic black holes evaporate via Hawking radiation;
* **(B) empirical** — the cosmic-ray / astronomical-survival argument.

Family (A) is a **genuinely separate line**. The 2003 LHC Safety Study Group
(CERN-2003-001) rests its black-hole conclusion entirely on it: *"black-hole production
does not present a conceivable risk at the LHC due to the rapid decay of the black hole
through thermal processes."* So the blanket claim is false and is not in the corpus.

**But the crux is conditional, and that is the whole point.** The public concern — and
the reason the 2008 reviews were commissioned — is precisely *"what if it does **not**
decay?"*. Condition on family (A) failing, and everything left standing is family (B),
and family (B) is **one argument**. That conditional is stated in the case crux and in
the battery, and it is what the corpus scores.

## Sources (retrieved first-party, sha-pinned)

| record | paper | ids | excerpt | sha256 |
|---|---|---|---|---|
| `src-ellis-2008` | Ellis J, Giudice G, Mangano ML, Tkachev I, **Wiedemann U** — "Review of the Safety of LHC Collisions", *J. Phys. G* 35:115004 (2008) | arXiv `0806.3414` · DOI `10.1088/0954-3899/35/11/115004` | abstract, 1723 chars | `030c49f7…c68e90` |
| `src-giddings-mangano-2008` | Giddings SB, Mangano MM — "Astrophysical implications of hypothetical stable TeV-scale black holes", *Phys. Rev. D* 78:035009 (2008) | arXiv `0806.3381` · DOI `10.1103/PhysRevD.78.035009` | abstract, 1390 chars | `36ed1846…5d2a33` |
| `src-jaffe-2000` | Jaffe RL, Busza W, Sandweiss J, Wilczek F — "Review of speculative 'disaster scenarios' at RHIC", *Rev. Mod. Phys.* 72:1125-1140 (2000) | arXiv `hep-ph/9910333` · DOI `10.1103/RevModPhys.72.1125` | abstract, 1297 chars | `4f1bf342…14ae9c` |

**Retrieval.** arXiv Atom API (`export.arxiv.org/api/query?id_list=…`), 2026-07-13.
**One normalization, and only one:** `" ".join(text.split())` — arXiv hard-wraps abstracts
and pads the leading line. The exact bytes ship as `fixtures/sources/*.abstract.txt` and
are SHA-256-pinned in `build_fixtures.py`; the build fails loudly on any drift.

### The cross-verification is WEAKER than A1's, and we say so

A1 required the abstract text to be **byte-identical across two independently operated
services** (NCBI E-utilities + Europe PMC). **We cannot honestly claim that here.**

* INSPIRE-HEP serves a byte-identical abstract for all three papers — but it declares its
  abstract's `source` as **`arXiv`**. It *mirrors the same upstream*. Two services agreeing
  is not two witnesses when one copies the other. **That is the exact error this engine
  exists to catch, and we ran into it inside our own verification pipeline.** Recording it
  is more useful than pretending we had independent confirmation.
* Crossref independently confirms the **bibliographic** record (DOI, title, journal,
  volume, pages) but deposits **no abstract text** for APS or IOP.

So: the abstract text is **single-sourced (arXiv)**, with independent *bibliographic*
confirmation. That is a real downgrade from the COVID corpus, and it is stated on each
source record's `retrieval.cross_verification_note`. It does not weaken span-grounding —
the bytes ship in-repo and `cairn ground` re-checks them — it weakens only the claim
"this is definitely what the journal published".

## Claims (each grounded to a real span; `source.excerpt[char_span] == quote`)

| claim | source | rung | entailment | grounding quote (verbatim substring) |
|---|---|---|---|---|
| `claim-cern-astro-stability` | Ellis | **L5** | ENTAILS | "The stability of astronomical bodies indicates that such collisions cannot be dangerous." |
| `claim-cern-wd-ns-bound` | Giddings & Mangano | **L5** | ENTAILS | "black holes produced by cosmic rays impinging on much denser white dwarfs and neutron stars would then catalyze their decay on timescales incompatible with their known lifetimes" |
| `claim-cern-moon-strangelet` | Jaffe | **L5** | ENTAILS | "the continued existence of the Moon, in the form we know it, despite billions of years of cosmic ray exposure, provides powerful empirical evidence against the possibility of dangerous strangelet production" |
| `claim-cern-bh-production-rate` | Jaffe | **L5** | ENTAILS | "We estimate the parameters relevant to black hole production; we find that they are absurdly small." |

The first three carry a `derivedFrom` edge to `ent-cosmic-ray-argument` **and** to their
own paper; `cairn intersect` therefore returns **REFUSE-TO-COMBINE** naming the premise.

## Three honest vetting decisions (recorded, not fabricated)

1. **The premise edge is attached at the CLAIM level, not the paper level.** Attaching
   `derivedFrom: ent-cosmic-ray-argument` to the *source records* would have been tidier
   and would have exercised the transitive detector — but it **over-attributes**. Jaffe's
   theoretical black-hole production estimate does *not* lean on cosmic rays even though
   Jaffe's strangelet conclusion does. A paper-level edge would manufacture a shared
   upstream that is not there. Precision beat cuteness: `claim-cern-bh-production-rate`
   carries **no** premise edge, and is exactly what makes the COMBINABLE contrast honest.

2. **The LSAG report and "Ellis et al. (2008)" are ONE document, not two.** The LHC Safety
   Assessment Group *is* Ellis, Giudice, Mangano, Tkachev and Wiedemann; the J. Phys. G
   paper *is* the LSAG report. Popular accounts sometimes cite them as two independent
   reviews. Minting them as two records would have made the case look stronger and would
   have been a **double-count** — the very sin under audit. One record, one citation.

3. **Only byte-stable abstract text is grounded.** The safety documents contain far richer
   admissions of dependence in their *bodies* — LSAG names the hole in the cosmic-ray
   argument and hands it to "[2]" (= Giddings & Mangano); the CERN SPC endorsement states
   its safety proof is "on the basis of the GM paper" and its panel was given exactly two
   documents (LSAG + GM), making it non-independent *by construction*; Koch et al. (2009)
   reuse GM's growth equations. **None of this is minted.** The CERN Document Server sits
   behind an anti-bot wall, and PDF text extraction is not byte-stable (line-wrap hyphens,
   ligatures, tool-dependent output) — it cannot meet the A1 bar or the "re-runs on a fresh
   machine in 5 minutes" bar. Recorded here as context; grounded nowhere.

## A gap the engine cannot yet close (recorded)

**M. L. Mangano co-authored both `src-giddings-mangano-2008` and `src-ellis-2008`** — the
review that leans on the bound was co-written by the author of the bound. That is
author-level non-independence *on top of* the shared premise, and cairn's layer-(a)
detector **cannot currently see it**: it walks the provenance DAG and does not read author
lists. It is recorded on the source record as `author_overlap_note` and probed by `I6` of
the battery, where cairn's principled answer is "NO, it is not irrelevant" — and cairn
cannot presently prove it. An honest debt, not a silent one.

## Reproduce

```bash
.venv/bin/python fixtures/build_fixtures.py                 # re-mint (sha-pinned; fails on byte drift)
.venv/bin/cairn ground 'fixtures/*.json'                    # all spans resolve to their cited source
.venv/bin/cairn intersect 'fixtures/*.json' --claims \
  $(python3 -c "import json;i=json.load(open('fixtures/INDEX.json'));print(' '.join(i[s] for s in ['claim-cern-astro-stability','claim-cern-wd-ns-bound','claim-cern-moon-strangelet']))")
# -> REFUSE-TO-COMBINE, shared_upstreams = [ent-cosmic-ray-argument]
```

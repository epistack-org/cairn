# Cairn — the decoupled epistack scoring engine

> Working name **"Cairn"** for the artifact/protocol (REPORT ).

This is the **schema-once weld** between the two epistack tracks: the small, plain
`git + one container` engine that (a) produces the July-5 FLF deliverable and
(b) is the seed of the an internal track internal follow-on layer. It has **no
substrate dependency** — no orchestrator, no private network, no forge — by design the moat is non-portable; the *scoring* must run on a fresh machine).

It is the **one artifact schema + the mechanical checks a single careful
Claude-Code transcript structurally cannot produce**:

1. **The Cairn envelope** (`cairn/envelope.py`) — a nanopublication-shaped,
   content-addressed (Trusty-URI over JCS/RFC-8785), ed25519-signed knowledge
   record. One envelope carries both **claims (verbs)** and **entities (nouns)**;
   the signature block is excluded from the content hash, so many teams can
   **endorse one content-id** (the n_eff-over-endorsers promotion model).
2. **Kish n_eff** (`cairn/neff.py`) — `n_eff = k / (1 + (k-1)·φ̄)`, the measured
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

## Run it

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv -e . pytest
.venv/bin/python fixtures/build_fixtures.py     # mint the vetted COVID corpus (sha-pinned)
.venv/bin/python -m pytest -q                   # 41 tests
.venv/bin/cairn ground 'fixtures/*.json'        # 4/4 claim spans resolve to their source
.venv/bin/cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json  # recompute measured n_eff
.venv/bin/python demo/hsm_trio.py               # the head-to-head
# or, fully self-contained:
docker build -t cairn -f Containerfile . && docker run --rm cairn
```

### The demo (`demo/hsm_trio.py`)

The COVID "three independent lines of proximity evidence" all derive from **one**
early-case dataset (Worobey 2022) — and each is **span-grounded** to that paper's
abstract (`cairn ground` → 4/4 resolve). A naive transcript multiplies their
likelihood ratios (5×5×5 = 125:1). Cairn:

- **REFUSE-TO-COMBINE** — the three trace to one upstream → multiplying is undefined;
- **measured n_eff** (A2) — a 9-assessor panel on the crux gives n_eff = 1.06 sharing
  evidence (homogeneous 1.00), rising to only 1.63 with *every* diversity lever — 9
  assessors are ~1–2 effective votes, not 9;
- and where independence *does* hold (a proximity line + the molecular two-lineages
  line, Pekar 2022 — disjoint upstream) it returns **COMBINABLE**.

That is *knowing when not to compute*, mechanically — the delta the baseline can't produce.
The corpus is **vetted, not illustrative**: real sources, real spans, entailment
labels, Trust-Ladder L4/L5 — see [`fixtures/PROVENANCE.md`](fixtures/PROVENANCE.md).

## CLI

```bash
cairn mint record.json --sign           # content-address + sign
cairn validate record.json              # schema + id + signature integrity
cairn neff matrix.json                  # n_eff over a binary agreement matrix
cairn intersect 'fixtures/*.json'       # refuse-to-combine verdict over a claim set
cairn ground 'fixtures/*.json'          # verify claims' spans resolve to their cited source
cairn assess assessment/runs/heterogeneous.json --battery assessment/probes.json  # recompute + verify measured n_eff
```

## Layout

| path | what |
|---|---|
| `cairn/envelope.py` | the record envelope: JCS → Trusty-URI → ed25519 sign/verify, schema validate |
| `cairn/neff.py` | Kish n_eff over correlated assessors |
| `cairn/provenance.py` | the shared-upstream / refuse-to-combine detector |
| `cairn/grounding.py` | the span-grounding / faithfulness check (`source.excerpt[char_span] == quote`) |
| `cairn/assessment.py` | recompute + verify the measured n_eff from a pinned assessor run (`cairn assess`) |
| `cairn/trusty.py`, `canonical.py`, `keys.py` | content-addressing, JCS, signing primitives |
| `schemas/cairn.schema.json` | the envelope JSON Schema (Draft 2020-12) incl. the grounding tuple + Trust-Ladder enum |
| `fixtures/` | the **vetted** COVID corpus — span-grounded claims (L4/L5) + two sha-pinned sources |
| `fixtures/sources/*.abstract.txt` | the byte-exact retrieved abstracts (the raw `source_doc`s) |
| `fixtures/PROVENANCE.md` | retrieval record, rung rationale, and the honest vetting decisions |
| `demo/hsm_trio.py` | the naive-vs-Cairn head-to-head |
| `assessment/` | the **measured** A2 assessor pass: probe battery, evidence partitions, panel + pinned runs |
| `assessment/ASSESSMENT.md` | the measured n_eff, the diversity levers, and the adversarial audit's honest caveats |
| `tests/` | 41 pytest checks incl. the n_eff anchor, the grounding leg, the measured-assessor pass + the cross-vendor leg |

## Disciplines / honest debts

- **JCS for v0** (git-native); RDFC-1.0 (RDF-canonical) is the documented migration —
  switching changes the URI scheme (one-way door).
- **Fixtures are vetted (roadmap A1).** Every claim is span-grounded to a
  first-party, byte-verified source and carries a Trust-Ladder rung (L1 sources;
  L4/L5 claims) — no record sits at `unverified-fixture` (the value is no longer
  admissible; any record still carrying it fails `cairn validate`). Two grounding
  judgment calls that could not be sourced from the abstracts were **recorded, not
  fabricated** — see `fixtures/PROVENANCE.md`. `n_eff` agreement vectors in the demo
  remain *illustrative* (measuring them over heterogeneous assessors is roadmap A2).
- This engine does **layer (a)** (explicit shared source). Legs **(b)** shared
  derivation (ProvSQL) and **(c)** hidden confounder (causal tooling) + the Fréchet
  interval are the next slices, not yet here.


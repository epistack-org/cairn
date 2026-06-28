# Cairn — the decoupled epistack scoring engine

> Working name **"Cairn"** for the artifact/protocol (REPORT ).

This is the **schema-once weld** between the two epistack tracks: the small, plain
`git + one container` engine that (a) produces the July-5 FLF deliverable and
(b) is the seed of the an internal track internal follow-on layer. It has **no
substrate dependency** — no orchestrator, no private network, no forge — by design the moat is non-portable; the *scoring* must run on a fresh machine).

It is the **one artifact schema + the two mechanical checks a single careful
Claude-Code transcript structurally cannot produce**:

1. **The Cairn envelope** (`cairn/envelope.py`) — a nanopublication-shaped,
   content-addressed (Trusty-URI over JCS/RFC-8785), ed25519-signed knowledge
   record. One envelope carries both **claims (verbs)** and **entities (nouns)**;
   the signature block is excluded from the content hash, so many teams can
   **endorse one content-id** (the n_eff-over-endorsers promotion model).
2. **Kish n_eff** (`cairn/neff.py`) — `n_eff = k / (1 + (k-1)·φ̄)`, the measured
   effective-independence number. "9 assessors agreed" at n_eff ≈ 2.2 is a
   headline lie the engine refuses to tell. (Anchored to "Nine Judges, Two
   Effective Votes", arXiv:2605.29800.)
3. **The layer-(a) shared-source detector** (`cairn/provenance.py`) — walks the
   `derivedFrom` DAG; if claims proposed as "independent" share an upstream it
   returns **REFUSE-TO-COMBINE**, naming the shared tuple.

## Run it

```bash
uv venv .venv --python 3.12 && uv pip install --python .venv -e . pytest
.venv/bin/python fixtures/build_fixtures.py     # mint the COVID fixtures
.venv/bin/python -m pytest -q                   # 17 tests
.venv/bin/python demo/hsm_trio.py               # the head-to-head
# or, fully self-contained:
docker build -t cairn -f Containerfile . && docker run --rm cairn
```

### The demo (`demo/hsm_trio.py`)

The COVID "three independent lines of proximity evidence" all derive from **one**
early-case dataset (Worobey 2022). A naive transcript multiplies their likelihood
ratios (5×5×5 = 125:1). Cairn:

- **REFUSE-TO-COMBINE** — the three trace to one upstream → multiplying is undefined;
- **n_eff = 1.00 (not 3)** — they co-move, so they are ~one effective vote;
- and where independence *does* hold (a proximity line + the molecular two-lineages
  line, Pekar 2022 — disjoint upstream) it returns **COMBINABLE**, n_eff ≈ 2.

That is *knowing when not to compute*, mechanically — the delta the baseline can't produce.

## CLI

```bash
cairn mint record.json --sign           # content-address + sign
cairn validate record.json              # schema + id + signature integrity
cairn neff matrix.json                  # n_eff over a binary agreement matrix
cairn intersect 'fixtures/claim-*.json' # refuse-to-combine verdict over a claim set
```

## Layout

| path | what |
|---|---|
| `cairn/envelope.py` | the record envelope: JCS → Trusty-URI → ed25519 sign/verify, schema validate |
| `cairn/neff.py` | Kish n_eff over correlated assessors |
| `cairn/provenance.py` | the shared-upstream / refuse-to-combine detector |
| `cairn/trusty.py`, `canonical.py`, `keys.py` | content-addressing, JCS, signing primitives |
| `schemas/cairn.schema.json` | the envelope JSON Schema (Draft 2020-12) |
| `fixtures/` | the minted COVID demo records (illustrative; bib metadata flagged unverified) |
| `demo/hsm_trio.py` | the naive-vs-Cairn head-to-head |
| `tests/` | 17 pytest checks incl. the published n_eff anchor |

## Disciplines / honest debts

- **JCS for v0** (git-native); RDFC-1.0 (RDF-canonical) is the documented migration —
  switching changes the URI scheme (one-way door).
- **Fixtures are illustrative.** Bibliographic metadata carries
  `verification: "unverified-fixture"` (Trust-Ladder L1/L2, not L5). Citations must
  be verified before any real analysis — fabricated provenance is the F0 sin.
- This engine does **layer (a)** (explicit shared source). Legs **(b)** shared
  derivation (ProvSQL) and **(c)** hidden confounder (causal tooling) + the Fréchet
  interval are the next slices, not yet here.


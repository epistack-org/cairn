# CASE-REPO-SPEC — the self-contained, verify-only case bundle

Status: **cairn-case/1.0**. Manifest schema:
[`schemas/case.schema.json`](schemas/case.schema.json).

A **case** is one worked example — a claim-set the engine must REFUSE-TO-COMBINE because the
"independent" lines launder a single shared upstream, plus (usually) a genuinely-combinable
contrast so the engine is visibly not a refuse-everything oracle. This document specifies the
layout a case bundle has so that it can live in **its own repo** (`cairns/<case-id>`), be
**verified standalone**, and be assembled into a corpus **without the engine or any other case
repo being touched**.

The governing goal: **a case is a repo, self-contained and verify-only.** The signing seed and
the authoring tools stay behind in the engine; a case ships only the pre-minted, checkable
result.

---

## 1. Layout

```
cairns/<case-id>/
├── CASE.json          # required — the structural declaration (schema: schemas/case.schema.json)
├── records/           # required (self-contained) — pre-minted, signed cairn.v0 records
│   ├── claim-….json
│   └── …
├── PROVENANCE.md      # required — retrieval + Trust-Ladder + vetting record
├── engine.pin         # required — the engine-compatibility pin (§4)
├── sources/           # optional — byte-pinned source excerpts, when spans are grounded locally
│   └── ….abstract.txt
├── build.py           # optional, authoring-time only — the minting recipe (NOT a verify dep)
├── spec.json          # optional, authoring-time only — cairn import spec (import-path cases)
└── README.md          # optional
```

### Required vs optional

| File | Required | Role |
|---|---|---|
| `CASE.json` | **yes** | the structural declaration the engine verifies. Governed by [`schemas/case.schema.json`](schemas/case.schema.json). |
| `records/*.json` | **yes** for a self-contained repo | pre-minted, content-addressed, ed25519-signed **cairn.v0** records. This is the artifact a case ships; it is what `cairn cases verify` and assembly consume. |
| `PROVENANCE.md` | **yes** | where the sources came from, the Trust-Ladder rung rationale, and any honest vetting decisions. |
| `engine.pin` | **yes** | which engine contract the records were minted/verified against (§4). |
| `sources/*` | optional | byte-exact source excerpts (version of record) when claims are span-grounded locally. |
| `build.py` | optional | **authoring-time** minting recipe. Never a verify-time dependency — a verifier reads `records/`, it does not run `build.py`. |
| `spec.json` | optional | the foreign-corpus input for `cairn import` (the surgisphere shape); authoring-time only. |
| `README.md` | optional | human orientation. |

> **Verify-only.** A verifier never needs to *mint* anything. It reads `records/`, checks each
> record self-verifies (its `id` re-derives from its content and its signature checks), and runs
> the `CASE.json` structural assertions. `build.py`/`spec.json`/`mint.py` are how the records
> were *authored*; they are not consumed to *check* them.

### The two authoring shapes (both produce the same verify-only bundle)

- **First-party span-vetted** — sources retrieved and byte-pinned under `sources/`, claims
  grounded to character spans, records minted by `build.py` importing the shared
  `mint.py` primitives. The seven grounded cases are this shape.
- **Import-path** — foreign claims carrying only their text and the identifiers they cite;
  records minted by `cairn import` from a `spec.json`, entering at the low rung with **no span
  grounding** (importing cannot launder trust — it can only surface a shared upstream). The
  `surgisphere` bundle is this shape (`import_note` flags it in `CASE.json`).

---

## 2. `CASE.json` — the structural declaration

Full field reference: [`schemas/case.schema.json`](schemas/case.schema.json). Summary:

| Field | Req | Meaning |
|---|---|---|
| `title` | yes | human-readable name. |
| `crux` | yes | the single question the case turns on. Must match the `battery`'s `crux` when a battery is present. |
| `shared_upstream` | yes | the one upstream **every** `laundered_set` line descends from — a record slug or a foreign id (`doi:`/`urn:`/…). May be reached only transitively. |
| `laundered_set` | yes | the ≥2 apparently-independent lines that must collectively REFUSE-TO-COMBINE. |
| `punchline` | yes | one-paragraph plain-English statement of what the case shows. |
| `shared_upstream_kind` | no | prose: what kind of thing the shared upstream is. Descriptive. |
| `contrast_pair` | no | a two-line pair proving the engine is not a refuse-everything oracle. |
| `contrast_expected` | no | the verdict `contrast_pair` must land on (`COMBINABLE` default). SHOULD be set when `contrast_pair` is. |
| `battery` | no | repo-relative path to the probe battery whose `crux` must match. |
| `records` | no | ordered list of record filenames (relative to `records/`) giving the assembly order — see *Record order* below. **Required for a self-contained bundle** to reassemble byte-identically; in-tree bundles omit it. |
| `exercises` / `import_note` | no | curator's notes; not read by the engine. |
| `case_spec_version` | no | the manifest contract version; absent ⇒ `"1.0"`. It is the version component of `engine.pin.case_spec` (§4). |

**What the engine checks** (`cairn.cases.verify_bundle`, mirrored by `tests/test_cases.py`):

1. `combine_verdict(laundered_set)` is `REFUSE-TO-COMBINE`.
2. the resolved `shared_upstream` is in the **collective** shared-upstream set (shared by ALL
   lines, not merely some pair).
3. if `contrast_pair` is present, its `combine_verdict` equals `contrast_expected`.

Slugs in `CASE.json` resolve to Trusty-URIs via the store's filename-stem alias (a record in
`records/claim-x.json` is addressable as `claim-x`), so a manifest is written in readable slugs,
never 43-char hashes.

### Record order

The aggregate `INDEX.json` lists records in **insertion order**, which is **not** alphabetical
(covid-origins begins `src-worobey-2022, src-pekar-2022, ent-prc-early-case-investigation, …`).
An in-tree bundle gets that order from `build.py`. A self-contained bundle has no `build.py` at
assembly time, so it **must** pin the order in `CASE.json`'s `records` manifest — a bare
`sorted()` over `records/` would reorder `INDEX.json` and break byte-identity. This is the one
piece of order a self-contained case carries so the corpus can reassemble deterministically. See
[CORPUS-SPEC.md §2](CORPUS-SPEC.md).

---

## 3. The digest — what "the bundle's bytes" means

`cairn cases verify`/`list` and `corpus.lock` pin a **content digest** per bundle
(`cairn.cases.bundle_digest`). It covers, in this stable order (mirrors
`cairn/cases.py::_digest_relpaths`):

```
CASE.json, build.py, PROVENANCE.md, engine.pin        # those that exist, in this order
records/<sorted files>
sources/<sorted files>
```

Each covered file contributes `relpath \0 bytes \0` to a single SHA-256 →
`sha256:<hex>`. Any byte drift in any covered file flips the digest, so a silent edit to a
covered file is caught the moment its pinned digest is rechecked.

**Coverage notes (intentional, cairn-case/1.0):**
- The covered set is exactly `CASE.json`/`build.py`/`PROVENANCE.md`/`engine.pin` + `records/` +
  `sources/`. `README.md` and `spec.json` are shippable but **intentionally out of the covered
  set** — `spec.json` is authoring input whose *output* (`records/`) is covered, so a drifted
  import is still caught; `README.md` is human orientation with no verify-time meaning.
- For an in-tree **dual-homed** bundle today (`fixtures/cases/<id>/`) only `CASE.json` +
  `build.py` + `engine.pin` exist, so those three are covered; its records are minted centrally
  and live in the corpus root. A migrated self-contained repo additionally carries `records/`,
  `PROVENANCE.md`, and `sources/`, all covered.

So the digest covers exactly the *digest-relevant* bytes the bundle ships — everything whose
drift must invalidate the pin — while leaving `README.md`/`spec.json` deliberately uncovered.

---

## 4. `engine.pin` — the versioned engine↔case interface

The only surviving coupling between the engine and a case is a **versioned interface contract**,
not a code dependency. `engine.pin` (JSON) records which contract a case's records were minted
and verified against:

```json
{
  "pin_schema": "cairn-engine-pin/1.0",
  "record_schema": "cairn.v0",
  "canonicalization": "JCS/RFC-8785",
  "case_spec": "cairn-case/1.0",
  "verified_with": { "engine": "cairn", "version": "0.0.1", "interoperable": ["cairn-cr"] },
  "verified_at": "2026-07-15"
}
```

| Field | Meaning |
|---|---|
| `record_schema` | the envelope schema line the `records/` conform to. **The load-bearing compat axis** — Trusty-URIs are hashes over the canonical form under this schema. |
| `canonicalization` | the byte-form the records are content-addressed/signed over. A different backend (e.g. RDFC-1.0) drifts every URI. |
| `case_spec` | the full `CASE.json` manifest-contract id (`cairn-case/<version>`); its version component equals `CASE.json.case_spec_version` (default `1.0`). |
| `verified_with` | provenance: which engine build minted/verified the records, and interoperable implementations. `cairn` (Python, reference) and `cairn-cr` (Crystal) are byte-for-byte interoperable, so records minted under one verify identically under the other. |
| `verified_at` | the date the pin was asserted. |

### The compatibility rule — what "an engine *satisfies* a pin" means

An assembling/verifying engine **E** satisfies a case's `engine.pin` iff:

1. **E** implements the pinned `record_schema` line (same schema major, `cairn.v0`), **and**
2. **E** uses the same `canonicalization` backend (`JCS/RFC-8785`), **and**
3. **E** supports the pinned `case_spec` version.

`verified_with.version` (the point release, `0.0.1`) is **provenance, not a gate**: a patch
release does not change Trusty-URIs, so it never blocks verification. Compatibility is keyed on
the three axes that actually change a record's bytes or the manifest's meaning
(`record_schema`, `canonicalization`, `case_spec`) — never on the engine's build number.

### Schema evolution is an explicit, dated event

Bumping `record_schema` (`cairn.v0` → `cairn.v1`) or the canonicalization backend is a
**one-way door** (it changes the URI scheme; documented at the engine). A case **opts in** by
re-minting its records under the new line and **re-pinning** `engine.pin` — which flips the
bundle digest, forcing a reviewed `corpus.lock` edit. Until it re-pins, a case stays verifiable
under an engine that still implements its pinned line. No case is ever silently migrated.

`corpus.lock` carries the same `record_schema` at the corpus level and per entry; assembly
refuses if a case's `engine.pin.record_schema` disagrees with the corpus. See
[CORPUS-SPEC.md §2](CORPUS-SPEC.md).

---

## 5. Standalone verification

A case repo proves itself with no access to `dev/cairn`'s fixtures:

```
cairn cases verify .            # runs the CASE.json assertions over this bundle's own records/
```

`cmd_cases_verify` prefers the bundle's own `records/*.json` when present, falling back to the
corpus store otherwise — so a self-contained repo is checked against exactly its own bytes.
Per-repo CI (W5) runs this plus a digest recompute on every push/PR; the corpus never has to be
assembled for a case to know it is green.

---

## 6. Adding a case

1. Create `cairns/<case-id>` from the case-repo template (W2): `CASE.json` (incl. the `records`
   order manifest), `records/`, `PROVENANCE.md`, `engine.pin`.
2. CI proves the declared structure green and the digest stable — independent of `dev/cairn`.
3. Open **one** `corpus.lock` PR in the corpus repo pinning the new repo at a tag + digest.

No `dev/cairn` edit, no monolith. That is the FLF scale lever (W6): an outside or agentic
researcher contributes a case as a repo, not as a patch to a growing central file.

---

## 7. Identity model

A case's **identity** is intrinsic: the Trusty-URIs of its records and its bundle `digest` — the
same bytes wherever the repo lives. *Where* a case lives and *who* curates it (`repo`, `path`, or
a deployed `domain` such as `covid-origins.a.epistack.dev`) is a **locator**, mutable and never
the trust root. Assembly re-verifies the digest in every mode, so a case addressed by domain in
the "domain is identity" federation model is still pinned by its bytes: the domain says who
and where, the digest says what. The full identity/federation model — including the reserved
`domain` resolution mode and its Track-λ curation-graph implications — is specified in
[CORPUS-SPEC.md §8](CORPUS-SPEC.md).

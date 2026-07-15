# CORPUS-SPEC — the `corpus.lock` contract

Status: **cairn-corpus-lock/1.0**. Schema: [`schemas/corpus.schema.json`](schemas/corpus.schema.json).

A **corpus** is a pinned, ordered, curated selection of case bundles presented together. This
document specifies the `corpus.lock` that names that selection and the rules by which
`cairn corpus assemble` (W1) turns it back into a byte-identical corpus. The engine owns the
schema; a `corpus.lock` **instance** lives in a corpus repo (the first is `cairns/corpus`, W3),
built generic so any researcher can fork it and curate their own selection.

This is the third of cairn's three independently-versioned concerns:

| Concern | Home | Owns |
|---|---|---|
| **Engine** | `dev/cairn` | the verifier/assembler + the record & manifest **schemas**. Corpus-agnostic. |
| **Case** | `cairns/<case-id>` | one worked example — self-contained, verify-only. See [CASE-REPO-SPEC.md](CASE-REPO-SPEC.md). |
| **Corpus** | `cairns/corpus` (and forks) | **`corpus.lock`** — the selection — plus the content golden + assembly CI. |

---

## 1. Shape

```json
{
  "corpus_lock_version": "1.0",
  "corpus": {
    "name": "epistack-flf-refuse-to-combine",
    "record_schema": "cairn.v0",
    "canonicalization": "JCS/RFC-8785"
  },
  "cases": [
    { "case_id": "covid-origins", "repo": "cairns/covid-origins", "ref": "v1",
      "digest": "sha256:…", "engine": "cairn.v0" },
    { "case_id": "eggs-good-for-you", "repo": "cairns/eggs-good-for-you", "ref": "v1",
      "digest": "sha256:…", "engine": "cairn.v0" }
  ]
}
```

- **`corpus`** carries corpus-level metadata plus the two compatibility keys every entry
  inherits: `record_schema` (the envelope schema line the records conform to — Trusty-URIs are
  hashes over the canonical form under this schema) and `canonicalization` (the byte-form; a
  different backend drifts every URI). These are the same axes a case's `engine.pin` pins; see
  [CASE-REPO-SPEC.md §4](CASE-REPO-SPEC.md). An optional `corpus.domain` records the corpus'
  deployed identity (§8).
- **`cases`** is the ordered selection. **Array order is assembly order.** It fixes the line
  order of the aggregate `CASES.json` and `INDEX.json`; byte-identity depends on it, so a
  reorder is a deliberate, reviewed change — never an alphabetical glob.

### Per-entry fields

| Field | Required | Meaning |
|---|---|---|
| `case_id` | yes | the bundle's id — its directory name and its **unique** key in `CASES.json`. |
| `digest` | yes | the bundle content digest (`cairn.cases.bundle_digest`, `sha256:…`). Pins the **bytes**; the trust root in every mode (§8). |
| `engine` | no | the compat key for this entry; defaults to `corpus.record_schema`. When present it must equal `corpus.record_schema` **and** the case's own `engine.pin.record_schema`. |

Plus **exactly one resolution mode** (the schema's `oneOf` enforces this):

| Mode | Fields | Meaning |
|---|---|---|
| **repo** | `repo` + `ref` | clone `repo` at the immutable `ref` — a **tag or full 40-hex commit SHA** (a branch name is not reproducible and is rejected, naming the case). A bare slug clones from `${CAIRN_FORGE_BASE:-https://forge.example.org}/<repo>.git`; a `repo` carrying a `://` scheme is used verbatim as the clone URL. The production shape — **wired in W4** (`cairn.corpus`). |
| **local** | `path` | a working-tree-relative path to the bundle. `repo`/`ref`/`domain` **must be absent**. Lets a `corpus.lock` pin the in-tree bundles so **W1 can prove byte-identical assembly before any case repo exists** — the bridge from monolith to trifurcation. |
| **domain** | `domain` | the case's deployed-domain identity (e.g. `covid-origins.a.epistack.dev`). **Reserved** — the schema accepts it; the resolver lands with subdomain-delegation infra. See §8. |

`digest` is mandatory in all three modes: the domain/repo is only a *locator*, never the trust
root.

---

## 2. Assembly (`cairn corpus assemble <corpus.lock>`, implemented in W1)

First, reject a `corpus.lock` whose `cases` contains a **duplicate `case_id`** (JSON Schema
cannot express cross-item uniqueness) — exit nonzero and name the collision. Then, for each
entry **in `cases` order**:

1. **Resolve** the bundle directory — a `path` (working tree); or clone `repo` at `ref` (an
   immutable **tag or full 40-hex SHA** — a branch is rejected — via
   `git clone --filter=blob:none` from `${CAIRN_FORGE_BASE:-…}/<repo>.git` unless `repo` is a full
   URL, then checkout `ref`; the clone ROOT is the bundle dir); or (reserved) the `domain`
   endpoint. A clone is trusted only for **reachability** — step 2 re-verifies the bytes — and
   temp clones are removed after assembly.
2. **Verify digest** — recompute `cairn.cases.bundle_digest(dir)` and require it equals
   `entry.digest`. A drifted or wrong-ref bundle **fails loudly** here; a repo/domain cannot
   silently change under a pin.
3. **Verify structure** — run `cairn cases verify` (the same crank the built-in seven and any
   external case repo are checked by): the `laundered_set` must REFUSE-TO-COMBINE, the declared
   `shared_upstream` must be in the collective shared-upstream set the DAG walk finds, and the
   `contrast_pair` must land on its `contrast_expected`.
4. **Verify engine compatibility** — read the bundle's `engine.pin` and require the running
   engine *satisfies* it (see [CASE-REPO-SPEC.md §4](CASE-REPO-SPEC.md)), and that
   `engine.pin.record_schema == entry.engine (or corpus.record_schema) == corpus.record_schema`.
   Assembly refuses on any disagreement.
5. **Collect** the case's records into the store:
   - **self-contained bundle** (ships `records/`) — read the pre-minted records **in the order
     its `CASE.json` `records` manifest declares** (see *Record order* below). No minting, no
     seed, no `build.py`. This is the steady state (external repos and W4 mirrors).
   - **in-tree dual-homed bundle** (the seven today: `CASE.json` + `build.py`, no `records/`) —
     the monolith→trifurcation **bridge**. Local-mode assembly obtains their records by the
     authoring path (`build.py`, which re-mints deterministically and therefore loads the demo
     signing seed from `fixtures/lib/mint.py`). This bridge is **explicitly outside** the
     verify-only invariant (§3) and is retired when W4 exports each of the seven as a
     self-contained mirror shipping `records/`.

Then write the aggregate outputs **in lock order**:

- **`INDEX.json`** — `{slug: trusty-uri}` for every record, in record-insertion order.
- **`CASES.json`** — `{case_id: CASE.json}` for every entry.

**Byte-form** (must match the reference builder `fixtures/build_fixtures.py` exactly):

| Output | Serialization |
|---|---|
| `INDEX.json` | `json.dumps(index, indent=2)` + trailing `\n` (default `ensure_ascii=True`; the corpus' slugs/URIs are all ASCII, so this is byte-identical to `ensure_ascii=False` today, but the spec pins what is actually emitted). |
| `CASES.json` | `json.dumps(cases, indent=2, ensure_ascii=False)` + trailing `\n` (case prose carries non-ASCII). `cases[case_id]` is the bundle's `CASE.json` **with the `records` key removed** — see the note below. |

> **`records` is assembly-only.** A self-contained bundle's `CASE.json` carries a `records` order
> manifest (*Record order*, below), but that key is **omitted from the aggregate `CASES.json`**:
> `cases[case_id]` is `CASE.json` minus `records`. It is pure assembly-order metadata, not part of a
> case's semantic declaration, so dropping it keeps `CASES.json` **byte-identical whether a case is
> in-tree (no `records`) or a self-contained mirror (ships `records`)** — which is exactly what the
> corpus CI relocation tripwire diffs. `verify_bundle` does not read `records`, so the structure
> gate (step 3) is unaffected.

**Record order.** `INDEX.json` line order is the order records are inserted into the store —
which is **not** alphabetical (e.g. covid-origins begins `src-worobey-2022, src-pekar-2022,
ent-prc-early-case-investigation, …`, not a filesystem sort). For an in-tree bundle that order
is intrinsic to `build.py`. For a self-contained bundle there is no `build.py` at assembly time,
so the order **must** be pinned by the bundle's `CASE.json` `records` manifest; a bare `sorted()`
over `records/` would reorder `INDEX.json` and break byte-identity. This `records` manifest is
consumed here to order `INDEX.json` and is then **stripped from `CASES.json`** (note above). See
[CASE-REPO-SPEC.md §2](CASE-REPO-SPEC.md).

> **A wrong ref, a drifted digest, a duplicate `case_id`, or an engine mismatch fails loudly** —
> steps are gates, not warnings. Exit nonzero and name the offending entry.

---

## 3. Invariants (non-negotiable)

> **Byte-identity.** Assembling the pinned selection reproduces the corpus' record bytes,
> `INDEX.json`, and `CASES.json` **byte-for-byte**. The split changes *where* bytes live, never
> *what* they are. This is the property W1's content golden (relocated to the corpus repo, W3)
> and the pre-split determinism golden both hold the assembler to.
>
> **Order is load-bearing.** `INDEX.json`/`CASES.json` line order is fixed by `cases` order and
> each bundle's record order (intrinsic for in-tree, the `records` manifest for self-contained).
> Byte-identity is only defined against a pinned order.
>
> **Verify-only / no secret — for the self-contained shape.** A self-contained bundle assembles
> by *reading* its pre-minted `records/`; the signing seed and `mint.py`/`build.py` are never a
> dependency. This is the steady state every external case repo and every migrated case uses.
> The in-tree dual-homed bundles are a temporary authoring **bridge** (§2 step 5) whose
> local-mode assembly re-mints via `build.py` and is therefore seed-dependent by construction;
> that bridge is retired by W4. The invariant governs the shape the corpus *ships*, not the
> scaffolding it is lifted out of.

---

## 4. Corpus tags — a reproducible artifact

A corpus **tag** is the unit you hand a reviewer. `cairns/corpus@v1.0` *is* the statement
"exactly these N cases at these commits/digests, assembling to this hash." From a clean machine:

```
git clone cairns/corpus && cd corpus && git checkout v1.0
cairn corpus assemble corpus.lock --out ./assembled
# -> byte-identical to the committed golden; the corpus hash is reproducible
```

Because content is digest-pinned, the tag reproduces from **any** source that satisfies the
digests — so a mirror (or a cache) reproduces the corpus even if an origin repo/domain is gone
(§8). "N worked examples is a checked property" now spans repos: the count, the identities, the
commits, and the assembled bytes are all pinned by `corpus.lock` + the digests it carries.

---

## 5. Relationship to `cases.lock`

`corpus.lock` **is** `fixtures/cases/cases.lock`, relocated out of the engine and enriched:

| `cases.lock` (in-engine, today) | `corpus.lock` (in the corpus repo) |
|---|---|
| `order: [case_id, …]` | the ordered `cases` array (order = array position) |
| `bundles: {case_id: {digest}}` | per-entry `digest` |
| — (bundles are in-tree dirs) | per-entry resolution mode: `repo`+`ref` / `path` / `domain` |
| — (one implicit engine) | per-entry `engine` + corpus-level `record_schema`/`canonicalization` |

`cases.lock` survives inside `dev/cairn` only as the pin for the in-tree authoring bundles;
the *corpus definition* moves to `corpus.lock`. Adding a case becomes: create `cairns/<case>`
→ green CI → **one reviewed `corpus.lock` PR**. Neither the engine nor another case repo is
touched.

---

## 6. Reusability

Nothing in this contract is Epistack-specific. Any researcher forks the corpus template
(W3), points `cases` at any mix of public case repos and their own, and gets the same
guarantees: pinned bytes, structural verification, engine-compat, byte-identical reassembly, a
reproducible tag. We are the first to dogfood it.

---

## 7. Versioning

`corpus_lock_version` pins this contract. A **minor** bump adds optional, backward-compatible
fields; a **major** bump changes how assembly reads the lock and is an explicit, dated event.
`record_schema`/`canonicalization` are enumerated against the engine's current support
(`cairn.v0` / `JCS/RFC-8785`); widening them (e.g. an RDFC-1.0 canonicalization or a
`cairn.v1` schema) is a one-way door documented at the engine, and a corpus opts in by
re-pinning its entries against re-minted cases. See [CASE-REPO-SPEC.md §4](CASE-REPO-SPEC.md)
for the case-level `engine.pin` half of the same story.

---

## 8. Identity model — content-addressing + the "domain is identity" federation layer

Two distinct things get conflated by the word "identity"; the contract keeps them separate.

| | Answers | Kind | In `corpus.lock` |
|---|---|---|---|
| **Identity / trust root** | *what are these bytes?* | intrinsic, immutable | the record Trusty-URI, the bundle `digest`, the assembled corpus hash |
| **Locator / owner** | *where do I fetch it, who curates it?* | extrinsic, mutable | `repo`+`ref`, `path`, or `domain` |

**The digest is the trust root in every resolution mode.** A locator can move, be renamed,
expire, or be seized; the digest can't. So assembly trusts a `repo`/`domain` only for
*reachability*, never for *bytes* (step 2 re-verifies), and any mirror that satisfies the digest
reproduces the corpus. Content-addressing and portable naming compose — they don't compete.

**Domain is identity.** In the federation model the deployed domain of a thing is
its address, and federation is a directed, per-plane edge between a net and its parent. Applied
here: a **team is a subdomain of `epistack.dev`**, and delegating `a.epistack.dev` to team A
makes team A a **sovereign-hub** over its own cases and a **managed-child** of the parent — a
federation edge on the curation plane. A case or corpus MAY then be *addressed by its deployed
domain*:

- `corpus.a.epistack.dev` — team A's curated corpus (also recordable as `corpus.domain`).
- `covid-origins.a.epistack.dev` — a case, resolved via the entry's **domain** mode.

A downstream `corpus.lock` that references team A's case by domain *is* an edge in the
federation graph. The `digest` keeps it honest: team A cannot be impersonated into serving
different bytes, because the consumer pins the digest it expects.

**Status: reserved.** `corpus.schema.json` accepts `domain` today, but the resolver (a
well-known bundle endpoint or git remote at the domain) and per-team hosting land with the
subdomain-delegation infra that is still in progress. `repo` and `path` are the live modes;
`domain` is the forward-compatible seam so it drops in with **no contract break**. Governance
(who delegates `epistack.dev` subdomains) is the parent edge, a convention not code.

> **Trust-root discipline.** Never verify *content* by domain. The domain is authoritative for
> reachability and ownership; the digest/Trusty-URI is authoritative for bytes. Any change that
> would make assembly trust a domain (or repo) for content instead of re-checking the digest is
> a contract violation.

**Forward look (Track λ).** Once curator identity is a domain, the federation graph is itself
analyzable by the same refuse-to-combine machinery: two "independent" corpora that both source a
case from the same curator-domain share an upstream *at the curation layer*, so domain can
become a first-class independence signal. That is a Track-λ direction, downstream of standing up
the corpus at all — not part of assembly in v1.

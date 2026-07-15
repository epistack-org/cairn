# `cairn import` — generalizing beyond the built-in cases

The three worked examples ship as hand-authored `tt:` fixtures. That is fine for a
demonstration and fatal for a general tool: to *use* cairn you would have to hand-author
the `derivedFrom` edges, which are the answer. This directory closes that gap (flf-contest#20;
contest compliance C3 — "judges will run it on cases we've never seen").

## What changed

- **The schema's `derivedFrom` was widened** (backward-compatibly) to accept foreign
  references — `doi:`, `https:`, `arxiv:`, `pmid:`, … — not only local `tt:` Trusty URIs.
  Every existing edge still validates; no minted id or signature changes. A foreign claim
  can now cite a DOI it does not hold locally, and two claims citing the same DOI are caught
  by the same intersection that catches a shared `tt:` source.
- **`cairn import`** turns a foreign, DOI-cited corpus into cairn records: each claim needs
  only its text and the references it already cites. Imported claims enter at the low rung
  (no `grounding`), so importing cannot launder trust — it can only surface shared upstreams.

## Consuming the anchor, reproducibly

`baseline-natorigin.json` is the public baseline's own natural-origin evidence
(`carlomartinucci/flf-epistack-contest` @ `774c9ee`) — its evidence-item slugs and the DOIs
each cites, transcribed from the 28-line probe's committed `OUTPUT.txt`. Run:

```
python3 verify_baseline_import.py
```

It does two things. First it re-derives the per-DOI shared-claim counts from this file and
checks they reproduce the probe exactly (5/5/3/3/3/2/2/2) — so the transcription is a
*checked* artifact, not a remembered one; a mistyped DOI would drift a count and fail. Then
it imports the corpus and runs the intersection over the two evidence items the baseline's
own dedup control filed separately and cited as mutually corroborating —
`environmental-samples-…` and `raccoon-dog-…`, which **both derive from Crits-Christoph 2024**
(`10.1016/j.cell.2024.08.010`). cairn REFUSES and names the DOI. The full 10-claim set refuses
on eight named upstreams, including Worobey 2022.

This is "we consume the anchor" made mechanical and offline: no baseline clone, no network,
no model call. The raw-clone version (parse the DOIs straight out of the baseline repo) is the
28-line `internal prior-art notes/baseline-probe/` in the writeup repo.

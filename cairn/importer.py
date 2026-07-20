"""cairn import: turn a foreign, DOI-cited corpus into cairn records.

The generalization seam (flf-contest#20; contest compliance C3 — "judges will run it
on cases we've never seen"). To use cairn today a judge must hand-author ``tt:``
``derivedFrom`` edges, which *are* the answer. This closes that: a foreign claim needs
only its text and the references it already cites — DOIs/URLs the source corpus prints
itself. Those become ``derivedFrom`` edges directly (the schema's ``derivedFrom`` was
widened, backward-compatibly, to accept foreign refs), so two "independent" claims that
cite the same DOI are caught by the exact intersection that catches a shared ``tt:``
source. No local copy of the cited work is required.

Input spec (JSON), minimal:

    {
      "minted_by": "import:<name>",
      "at": "<iso8601>",                 # optional; set it for a deterministic mint
      "claims": [
        {"slug": "...", "text": "...", "derivedFrom": ["10.1126/science.abp8715", ...]}
      ]
    }

A foreign claim enters at the low rung: it carries no ``grounding``, so it cannot rise
above L0/L1 until a span is re-checked against a source held locally. Importing cannot
launder trust — it can only surface shared upstreams.
"""
from __future__ import annotations

from typing import Mapping

from cairn import envelope

_SCHEMES = ("doi:", "arxiv:", "pmid:", "pmcid:", "urn:", "isbn:", "w3id:", "orcid:")


def normalise_ref(ref: str) -> str:
    """Give a foreign reference a scheme so the widened schema accepts it.

    A bare DOI (``10.x/...``) becomes ``doi:10.x/...``; ``tt:`` URIs, full URLs, and
    already-schemed refs pass through unchanged.
    """
    r = ref.strip()
    low = r.lower()
    if r.startswith("tt:") or "://" in r or low.startswith(_SCHEMES):
        return r
    if low.startswith("10."):
        return "doi:" + r
    return r  # unknown shape; schema validation will reject it if it is not a valid ref


def import_corpus(spec: Mapping) -> list[dict]:
    """Mint one ``epi:Claim`` per foreign claim, with foreign ``derivedFrom`` edges."""
    minted_by = spec.get("minted_by", "import:foreign")
    at = spec.get("at")  # pass through; provide it for a reproducible content id
    out = []
    for c in spec.get("claims", []):
        assertion: dict = {"text": c["text"]}
        if c.get("slug"):
            assertion["label"] = c["slug"]        # readable name for `cairn explain`
        if c.get("support_strength") is not None:  # keep a valid 0 (dev/cairn#37, finding 8)
            assertion["support_strength"] = c["support_strength"]
        edges = [normalise_ref(r) for r in c.get("derivedFrom", [])]
        rec = envelope.new_record(
            "epi:Claim", assertion,
            minted_by=minted_by, method="import", derived_from=edges, at=at,
        )
        envelope.mint(rec)
        out.append(rec)
    return out

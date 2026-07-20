"""Mechanical grounding check — does a claim's evidence actually resolve?

The faithfulness invariant: *every emitted claim node MUST carry*
``(source_doc, char_span, extractor, entailment_label)``; *reject/quarantine any
claim whose stated source span does not entail it.* This module makes that
invariant **mechanical** for the decoupled engine. For a claim it checks:

  * ``grounding.source`` is a **real upstream** — it appears in
    ``provenance.derivedFrom`` (so the shared-source edge the layer-(a) detector
    walks is the *same* edge the claim is grounded on: a provenance fact, not a
    decorative pointer);
  * ``store[source].assertion.excerpt[char_span[0]:char_span[1]] == grounding.quote``
    — the span resolves, byte-for-byte, to the quoted evidence; and
  * an **L4/L5** (entailment-checked / accepted) claim carries a *positive*
    entailment label (``ENTAILS``/``SUPPORTS``) — an unentailed span cannot promote
    a claim onto the entailment-checked rung.

This is a delta a single careful transcript structurally cannot produce: not "the
paper supports this" as prose, but the exact bytes, re-checkable on a fresh machine.
"""
from __future__ import annotations

import hashlib
from typing import Iterable, Mapping, Optional

POSITIVE_ENTAILMENT = {"ENTAILS", "SUPPORTS"}
GROUNDED_RUNGS = {"L4", "L5"}


def _excerpt(source_rec: Optional[Mapping]) -> Optional[str]:
    if not source_rec:
        return None
    return source_rec.get("assertion", {}).get("excerpt")


def resolve_span(source_rec: Optional[Mapping], char_span) -> Optional[str]:
    """Return ``excerpt[a:b]`` for a 2-int span, or ``None`` if unresolvable."""
    text = _excerpt(source_rec)
    if text is None or not isinstance(char_span, (list, tuple)) or len(char_span) != 2:
        return None
    a, b = char_span
    if not (isinstance(a, int) and isinstance(b, int)):
        return None
    if a < 0 or b > len(text) or a > b:
        return None
    return text[a:b]


def check_claim(claim: Mapping, store: Mapping[str, Mapping]) -> dict:
    """Check one claim's grounding against the store. Returns a structured result."""
    a = claim.get("assertion", {})
    g = a.get("grounding")
    verification = a.get("verification")
    cid = claim.get("id", "<unminted>")
    errors: list[str] = []

    if g is None:
        if verification in GROUNDED_RUNGS:
            errors.append(
                f"{verification} claim carries no grounding tuple "
                "(faithfulness invariant: L4/L5 claims must be span-grounded)"
            )
        return {"claim": cid, "grounded": False, "resolves": False,
                "verification": verification, "ok": not errors, "errors": errors}

    source_id = g.get("source")
    src = store.get(source_id)
    derived = set(claim.get("provenance", {}).get("derivedFrom", []))

    if source_id not in derived:
        errors.append(
            f"grounding.source {source_id} is not in provenance.derivedFrom "
            "(a grounding must be a provenance fact, not an assertion)"
        )
    if src is None:
        errors.append(f"grounding.source {source_id} not found in store")

    quote = g.get("quote")
    resolved = resolve_span(src, g.get("char_span")) if src is not None else None
    if resolved is None:
        errors.append("char_span does not resolve against the source excerpt "
                      "(out of range, or source carries no excerpt)")
    elif resolved != quote:
        errors.append("span does not resolve to quote: "
                      "source.excerpt[char_span] != grounding.quote")

    want_sha = g.get("source_sha256")
    if want_sha and src is not None:
        text = _excerpt(src)
        got = hashlib.sha256(text.encode("utf-8")).hexdigest() if text is not None else None
        if got != want_sha:
            errors.append("grounding.source_sha256 does not match sha256(source.excerpt)")

    label = g.get("entailment_label")
    if verification in GROUNDED_RUNGS and label not in POSITIVE_ENTAILMENT:
        errors.append(
            f"{verification} claim requires a positive entailment_label "
            f"{sorted(POSITIVE_ENTAILMENT)}, got {label!r} (would be quarantined)"
        )

    return {
        "claim": cid,
        "grounded": True,
        "resolves": resolved is not None and resolved == quote,
        "source": source_id,
        "char_span": g.get("char_span"),
        "entailment_label": label,
        "verification": verification,
        "ok": not errors,
        "errors": errors,
    }


def check_store(store: Mapping[str, Mapping], claim_ids: Optional[Iterable[str]] = None) -> dict:
    """Check every claim (or a given subset) in the store. Returns a report."""
    if claim_ids is None:
        ids = [rid for rid, r in store.items() if r.get("@type") == "epi:Claim"]
    else:
        ids = list(claim_ids)
    results = [check_claim(store[rid], store) for rid in ids if rid in store]
    return {
        "ok": all(r["ok"] for r in results),
        "checked": len(results),
        "grounded": sum(1 for r in results if r.get("grounded")),
        "failed": [r for r in results if not r["ok"]],
        "results": results,
    }

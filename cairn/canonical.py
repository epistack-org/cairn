"""JCS (RFC 8785) canonicalization — the deterministic byte-form a Cairn record
is content-addressed and signed over.

v0 uses **JCS (RFC 8785)** over the JSON-LD document (the pragmatic, git-native
choice from spike C). It is *not* RDF-canonical: the hash is stable across
key-ordering and whitespace, but NOT across alternate RDF serializations
(TriG vs JSON-LD). The migration path is RDFC-1.0 (w3c.github.io/rdf-canon),
documented in README; switching changes the URI scheme, so it is a one-way door.

We prefer the `rfc8785` library (correct number canonicalization). The pure-stdlib
fallback is exact for our envelope (strings + nested objects, no exotic floats);
it would diverge from JCS only on edge-case number formatting we never emit.
"""
from __future__ import annotations

import json
from typing import Any

try:  # correct JCS
    import rfc8785

    def jcs(obj: Any) -> bytes:
        """Canonical JCS bytes (RFC 8785)."""
        return rfc8785.dumps(obj)

    BACKEND = "rfc8785"
except Exception:  # pragma: no cover - exercised only where rfc8785 is absent

    def jcs(obj: Any) -> bytes:
        """Stdlib approximation of JCS — exact for string/object content."""
        return json.dumps(
            obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")

    BACKEND = "stdlib-fallback"

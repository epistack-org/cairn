"""The Cairn envelope — the one artifact schema the whole stack shares.

A Cairn record is nanopublication-shaped: three named parts —

  * ``assertion``  — *what* is claimed (a Claim) or *what exists* (an Entity/Source)
  * ``provenance`` — *how/where it came from* (``derivedFrom`` upstream Cairn URIs,
                     who minted it, by what method, when) — this is the edge set the
                     non-independence detector walks
  * ``pubinfo``    — *who vouches* (ed25519 signature) + the schema it conforms to

Content addressing: the record's ``id`` is its **Trusty URI** = the hash of its
own canonical content, computed with ``id`` and the signature value blanked (they
cannot be inputs to the hash that produces them). So ``id`` and signature are both
independently re-derivable and checkable — the record self-verifies.

This same envelope carries **claims (verbs) and entities (nouns)**: an "entity" is
just a record whose assertion is an identity assertion. One envelope, one store,
one promotion ladder (spike C).
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import json

from . import trusty
from .canonical import jcs
from .keys import SigningKey, verify as _verify_sig

CONTEXT = "https://epistack.dev/ns/cairn.v0.jsonld"  # v0 context IRI (not yet dereferenceable)

# @type vocabulary (spike C: ~5 core types, extend bottom-up)
TYPES = ("epi:Claim", "epi:Entity", "epi:Source", "epi:Schema", "epi:Cluster", "epi:Assessment")

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "cairn.schema.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def new_record(
    type_: str,
    assertion: dict,
    *,
    minted_by: str,
    method: str = "assert",
    derived_from: Optional[list[str]] = None,
    funded_by: Optional[list[str]] = None,
    at: Optional[str] = None,
    conforms_to: Optional[str] = None,
) -> dict:
    """Build an *unminted, unsigned* record (id and signature are placeholders)."""
    if type_ not in TYPES:
        raise ValueError(f"unknown @type {type_!r}; known: {TYPES}")
    rec: dict[str, Any] = {
        "@context": CONTEXT,
        "@type": type_,
        "id": "",  # filled by mint()
        "assertion": assertion,
        "provenance": {
            "derivedFrom": list(derived_from or []),
            "mintedBy": minted_by,
            "method": method,
            "at": at or _utc_now_iso(),
        },
        "pubinfo": {
            "sig": {"alg": "ed25519", "key": "", "value": "", "by": ""},
        },
    }
    # Omitted entirely when empty, never written as []. The content id is a hash over
    # this dict, so emitting an empty fundedBy on every record would re-mint every id
    # in every corpus and break the pinned goldens. Absent means "not stated".
    if funded_by:
        rec["provenance"]["fundedBy"] = list(funded_by)
    if conforms_to is not None:
        rec["pubinfo"]["conformsTo"] = conforms_to
    return rec


def _blanked(record: dict) -> dict:
    """Copy with the self-referential parts removed, so the content hash is stable.

    Excluded from the content address: ``id`` (it *is* the hash) and the entire
    ``pubinfo.sig`` block (it signs the hash, and excluding it lets many teams
    endorse one content id with separate signatures — the n_eff-over-endorsers
    promotion model). Everything else, including ``pubinfo.conformsTo``, is bound
    into the id.
    """
    r = copy.deepcopy(record)
    r["id"] = ""
    if isinstance(r.get("pubinfo"), dict):
        r["pubinfo"] = {k: v for k, v in r["pubinfo"].items() if k != "sig"}
    return r


def content_digest(record: dict) -> bytes:
    return trusty.sha256(jcs(_blanked(record)))


def content_uri(record: dict) -> str:
    return trusty.encode(content_digest(record))


def mint(record: dict) -> dict:
    """Set ``id`` to the record's content-derived Trusty URI. Returns the record."""
    record["id"] = content_uri(record)
    return record


def sign(record: dict, key: SigningKey) -> dict:
    """Sign the content digest with an ed25519 keystone identity. Mints first if needed."""
    if not trusty.is_trusty(record.get("id", "")):
        mint(record)
    digest = content_digest(record)
    record["pubinfo"]["sig"] = {
        "alg": "ed25519",
        "key": key.public_hex(),
        "value": key.sign(digest),
        "by": key.label,
    }
    return record


def verify(record: dict) -> dict:
    """Re-derive id + check signature. Returns {id_ok, sig_ok, signed}."""
    digest = content_digest(record)
    id_ok = record.get("id", "") == trusty.encode(digest)
    sig = record.get("pubinfo", {}).get("sig", {})
    signed = bool(sig.get("value"))
    sig_ok = signed and _verify_sig(sig.get("key", ""), sig.get("value", ""), digest)
    return {"id_ok": id_ok, "sig_ok": sig_ok, "signed": signed}


@lru_cache(maxsize=1)
def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def validate(record: dict) -> list[str]:
    """Return a list of human-readable schema violations ([] == valid)."""
    from jsonschema import Draft202012Validator

    v = Draft202012Validator(load_schema())
    return [f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}" for e in v.iter_errors(record)]

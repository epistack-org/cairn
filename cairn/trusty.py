"""Trusty-URI content addressing (Cairn v0 scheme).

A Trusty URI *is* the cryptographic hash of the record's canonical content, so
the identifier self-verifies: anyone can recompute it and prove the bytes have
not changed. Two records that cite the same Trusty URI provably cite the *same*
artifact — this mechanizes the (a) "explicit shared source" leg of the
non-independence spectrum at the identifier level.

Scheme (v0): ``tt:`` + base64url(SHA-256(JCS(content)))  — 43 chars, unpadded.

Lineage: nanopublication Trusty URIs (arXiv:1401.5775) use base64 of a typed
hash module over RDF-canonical content. We keep the *idea* (the URI is the
content hash) but hash JCS-of-JSON-LD rather than RDF-canonical RDF for v0. The
``tt:`` prefix marks this Cairn-v0 variant so a future RDFC-1.0 scheme is
distinguishable.
"""
from __future__ import annotations

import base64
import hashlib
import re

PREFIX = "tt:"
URI_RE = re.compile(r"^tt:[A-Za-z0-9_-]{43}$")


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def encode(digest: bytes) -> str:
    """32-byte digest -> ``tt:`` base64url (unpadded) Trusty URI."""
    if len(digest) != 32:
        raise ValueError(f"expected 32-byte SHA-256 digest, got {len(digest)}")
    b = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return PREFIX + b


def is_trusty(uri: str) -> bool:
    return bool(URI_RE.match(uri or ""))

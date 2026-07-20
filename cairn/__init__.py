"""Cairn — the decoupled epistack scoring engine.

The one artifact schema + the two mechanical checks a single transcript cannot
produce: a content-addressed/signed knowledge record (envelope), a measured
effective-independence number (neff), and a shared-upstream refuse-to-combine
detector (provenance).
"""
from __future__ import annotations

from . import envelope, keys, neff, provenance, trusty
from .envelope import CONTEXT, TYPES, mint, new_record, sign, validate, verify
from .keys import SigningKey
from .neff import kish_neff, neff_from_matrix
from .provenance import combine_verdict, shared_upstreams

__version__ = "0.0.1"

__all__ = [
    "envelope",
    "keys",
    "neff",
    "provenance",
    "trusty",
    "CONTEXT",
    "TYPES",
    "new_record",
    "mint",
    "sign",
    "verify",
    "validate",
    "SigningKey",
    "kish_neff",
    "neff_from_matrix",
    "combine_verdict",
    "shared_upstreams",
    "__version__",
]

"""ed25519 signing identity for Cairn records.

Default per the operator decision: **keystone/ed25519 on-substrate** (a team's
deployment/keystone identity is the key). This trades nanopub-rs RSA interop for
on-substrate keys we already mint; we don't need external verifiers yet.

Keys here are raw ed25519 (32-byte seed / 32-byte public key, hex-encoded). In
the real stack the private key is held by the team's keystone identity, not on
disk; this module is the standalone equivalent for the decoupled engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


@dataclass(frozen=True)
class SigningKey:
    """An ed25519 keypair. ``label`` is the on-substrate identity name."""

    _priv: Ed25519PrivateKey
    label: str = "keystone:local"

    @classmethod
    def generate(cls, label: str = "keystone:local") -> "SigningKey":
        return cls(Ed25519PrivateKey.generate(), label)

    @classmethod
    def from_seed_hex(cls, seed_hex: str, label: str = "keystone:local") -> "SigningKey":
        return cls(Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex)), label)

    def seed_hex(self) -> str:
        from cryptography.hazmat.primitives import serialization

        raw = self._priv.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )
        return raw.hex()

    def public_hex(self) -> str:
        from cryptography.hazmat.primitives import serialization

        raw = self._priv.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return raw.hex()

    def sign(self, data: bytes) -> str:
        return self._priv.sign(data).hex()


def verify(public_hex: str, signature_hex: str, data: bytes) -> bool:
    try:
        pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex))
        pub.verify(bytes.fromhex(signature_hex), data)
        return True
    except (InvalidSignature, ValueError):
        return False

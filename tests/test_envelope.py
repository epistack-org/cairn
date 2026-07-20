import copy

import pytest

from cairn import envelope, trusty
from cairn.keys import SigningKey

AT = "2026-06-28T00:00:00Z"


def _rec(text="early cases cluster at the market"):
    return envelope.new_record(
        "epi:Claim",
        {"text": text, "polarity": "supports"},
        minted_by="team:test",
        method="assert",
        at=AT,
    )


def test_mint_produces_trusty_uri_and_validates():
    r = envelope.mint(_rec())
    assert trusty.is_trusty(r["id"])
    assert envelope.validate(r) == []
    assert envelope.verify(r)["id_ok"] is True


def test_mint_is_deterministic_and_content_sensitive():
    a = envelope.mint(_rec("X"))
    b = envelope.mint(_rec("X"))
    c = envelope.mint(_rec("Y"))
    assert a["id"] == b["id"]      # same content -> same id
    assert a["id"] != c["id"]      # different content -> different id


def test_tamper_breaks_id():
    r = envelope.mint(_rec())
    r["assertion"]["text"] = "tampered"
    assert envelope.verify(r)["id_ok"] is False


def test_sign_then_verify_and_tamper_detection():
    key = SigningKey.generate("keystone:team-a")
    r = envelope.sign(_rec(), key)
    v = envelope.verify(r)
    assert v["id_ok"] and v["sig_ok"] and v["signed"]
    assert r["pubinfo"]["sig"]["by"] == "keystone:team-a"
    # tampering after signing breaks both id and signature
    tampered = copy.deepcopy(r)
    tampered["assertion"]["polarity"] = "refutes"
    vt = envelope.verify(tampered)
    assert not vt["id_ok"] and not vt["sig_ok"]


def test_signature_excluded_from_content_hash():
    # signing must not change the id (sig value is blanked in the content hash)
    key = SigningKey.generate()
    r = _rec()
    envelope.mint(r)
    before = r["id"]
    envelope.sign(r, key)
    assert r["id"] == before


def test_schema_rejects_bad_type_and_missing_fields():
    r = envelope.mint(_rec())
    bad_type = copy.deepcopy(r)
    bad_type["@type"] = "epi:Nonsense"
    assert envelope.validate(bad_type)  # nonempty == violations
    missing = copy.deepcopy(r)
    del missing["provenance"]["mintedBy"]
    assert envelope.validate(missing)


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        envelope.new_record("epi:Bogus", {"a": 1}, minted_by="t")


def test_malformed_date_time_is_a_schema_violation():
    # dev/cairn#37 finding 7: `format: date-time` was annotation-only (no FormatChecker),
    # so a garbage `at` validated clean. It must now be a violation.
    r = envelope.mint(_rec())
    r["provenance"]["at"] = "not-a-date"
    errs = envelope.validate(r)
    assert any("date-time" in e for e in errs), errs


def test_bare_date_without_time_is_rejected():
    r = envelope.mint(_rec())
    r["provenance"]["at"] = "2026-07-20"          # a date, but not a date-TIME
    assert any("date-time" in e for e in envelope.validate(r))


def test_well_formed_date_time_still_validates():
    r = envelope.mint(_rec())                      # _rec() uses AT = "...T...Z"
    assert envelope.validate(r) == []

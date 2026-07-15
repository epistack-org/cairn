"""The CASE.json manifest is a versioned, schema-checked contract.

`schemas/case.schema.json` (cairn-case/1.0) is the engine-owned half of the engine<->case
interface that governs the manifest a case bundle declares about itself. This module holds
every in-tree bundle to that schema, so a case repo -- ours or an outside contributor's --
that drifts the manifest shape (a missing crux, a laundered_set of one, a typo'd key) fails
here rather than at assembly time. The record half of the same interface is pinned by
schemas/cairn.schema.json + tests/test_determinism_golden.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "fixtures" / "cases"
SCHEMA_PATH = ROOT / "schemas" / "case.schema.json"

CASE_FILES = sorted(CASES_DIR.glob("*/CASE.json"))


def _validator() -> Draft202012Validator:
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft202012Validator.check_schema(schema)  # the schema itself must be a valid 2020-12 schema
    return Draft202012Validator(schema)


def test_case_files_present():
    assert CASE_FILES, "no CASE.json bundles found under fixtures/cases/"


@pytest.mark.parametrize("case_file", CASE_FILES, ids=lambda p: p.parent.name)
def test_case_manifest_matches_schema(case_file):
    manifest = json.loads(case_file.read_text())
    errors = sorted(_validator().iter_errors(manifest), key=lambda e: e.path)
    assert not errors, [f"{list(e.path)}: {e.message}" for e in errors]


@pytest.mark.parametrize("case_file", CASE_FILES, ids=lambda p: p.parent.name)
def test_contrast_expected_present_when_pair_is(case_file):
    """cairn/cases.py defaults a missing contrast_expected to COMBINABLE; the contract is that a
    declared contrast_pair states its expected verdict explicitly rather than leaning on the default."""
    manifest = json.loads(case_file.read_text())
    if "contrast_pair" in manifest:
        assert "contrast_expected" in manifest, "contrast_pair present without contrast_expected"

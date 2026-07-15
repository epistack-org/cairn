from cairn import envelope, importer, provenance


def test_normalise_ref_schemes_a_bare_doi():
    assert importer.normalise_ref("10.1126/science.abp8715") == "doi:10.1126/science.abp8715"
    assert importer.normalise_ref("doi:10.x/y") == "doi:10.x/y"
    assert importer.normalise_ref("https://example.org/a") == "https://example.org/a"
    tt = "tt:" + "A" * 43
    assert importer.normalise_ref(tt) == tt


def test_imported_records_are_schema_valid_with_foreign_edges():
    # the schema was widened so derivedFrom accepts foreign DOIs (flf-contest#20/#3)
    spec = {
        "minted_by": "import:test", "at": "2026-07-15T00:00:00Z",
        "claims": [
            {"slug": "a", "text": "claim a", "derivedFrom": ["10.1016/j.cell.2024.08.010"]},
            {"slug": "b", "text": "claim b", "derivedFrom": ["10.1016/j.cell.2024.08.010"]},
        ],
    }
    recs = importer.import_corpus(spec)
    assert len(recs) == 2
    for r in recs:
        assert envelope.validate(r) == []          # foreign doi: edge validates
        assert r["id"].startswith("tt:")           # the record itself still content-addresses
        assert r["provenance"]["derivedFrom"] == ["doi:10.1016/j.cell.2024.08.010"]


def test_import_is_deterministic_when_at_is_pinned():
    spec = {"minted_by": "import:test", "at": "2026-07-15T00:00:00Z",
            "claims": [{"slug": "a", "text": "claim a", "derivedFrom": ["10.1/x"]}]}
    a = importer.import_corpus(spec)[0]["id"]
    b = importer.import_corpus(spec)[0]["id"]
    assert a == b                                   # same content -> same Trusty URI


def test_two_imported_claims_sharing_a_doi_refuse():
    spec = {
        "minted_by": "import:test", "at": "2026-07-15T00:00:00Z",
        "claims": [
            {"slug": "env", "text": "env samples", "derivedFrom": ["10.1016/j.cell.2024.08.010"]},
            {"slug": "raccoon", "text": "raccoon tracing", "derivedFrom": ["10.1016/j.cell.2024.08.010"]},
        ],
    }
    recs = importer.import_corpus(spec)
    store = {r["id"]: r for r in recs}
    v = provenance.combine_verdict(list(store), store)
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert "doi:10.1016/j.cell.2024.08.010" in v["shared_upstreams"]


def test_disjoint_imported_claims_combine():
    spec = {
        "minted_by": "import:test", "at": "2026-07-15T00:00:00Z",
        "claims": [
            {"slug": "a", "text": "a", "derivedFrom": ["10.1/x"]},
            {"slug": "b", "text": "b", "derivedFrom": ["10.2/y"]},
        ],
    }
    recs = importer.import_corpus(spec)
    store = {r["id"]: r for r in recs}
    v = provenance.combine_verdict(list(store), store)
    assert v["verdict"] == "COMBINABLE"

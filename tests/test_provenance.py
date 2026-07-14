from cairn import envelope, provenance

AT = "2026-06-28T00:00:00Z"


def _mk(type_, assertion, derived_from=None):
    return envelope.mint(
        envelope.new_record(
            type_, assertion, minted_by="team:test", method="extract",
            derived_from=derived_from or [], at=AT,
        )
    )


def _store(*recs):
    return {r["id"]: r for r in recs}


def test_trio_sharing_one_upstream_is_refused():
    src = _mk("epi:Source", {"title": "Worobey 2022"})
    c1 = _mk("epi:Claim", {"text": "geographic clustering"}, [src["id"]])
    c2 = _mk("epi:Claim", {"text": "environmental sampling"}, [src["id"]])
    c3 = _mk("epi:Claim", {"text": "ascertainment centroid"}, [src["id"]])
    store = _store(src, c1, c2, c3)
    v = provenance.combine_verdict([c1["id"], c2["id"], c3["id"]], store)
    assert v["independent"] is False
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert src["id"] in v["shared_upstreams"]


def test_transitive_shared_ancestor_is_caught():
    root = _mk("epi:Source", {"title": "shared dataset"})
    midA = _mk("epi:Source", {"title": "paper A"}, [root["id"]])
    midB = _mk("epi:Source", {"title": "paper B"}, [root["id"]])
    cA = _mk("epi:Claim", {"text": "from A"}, [midA["id"]])
    cB = _mk("epi:Claim", {"text": "from B"}, [midB["id"]])
    store = _store(root, midA, midB, cA, cB)
    v = provenance.combine_verdict([cA["id"], cB["id"]], store)
    assert v["independent"] is False
    assert root["id"] in v["shared_upstreams"]   # discovered via transitive closure


def test_disjoint_upstreams_are_combinable():
    s1 = _mk("epi:Source", {"title": "Worobey 2022 (proximity)"})
    s2 = _mk("epi:Source", {"title": "Pekar 2022 (molecular)"})
    c1 = _mk("epi:Claim", {"text": "proximity line"}, [s1["id"]])
    c2 = _mk("epi:Claim", {"text": "two lineages"}, [s2["id"]])
    store = _store(s1, s2, c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    assert v["independent"] is True
    assert v["verdict"] == "COMBINABLE"


def test_single_claim_does_not_share_an_upstream_with_itself():
    src = _mk("epi:Source", {"title": "Worobey 2022"})
    c1 = _mk("epi:Claim", {"text": "geographic clustering"}, [src["id"]])
    store = _store(src, c1)
    v = provenance.combine_verdict([c1["id"]], store)
    assert v["independent"] is True
    assert v["verdict"] == "COMBINABLE"
    assert v["shared_upstreams"] == []

    s = provenance.shared_upstreams([c1["id"]], store)
    assert s["collective_shared"] == []
    assert s["ancestors"][c1["id"]] == {src["id"]}   # it still HAS an ancestor


def test_empty_claim_set_is_vacuously_combinable():
    store = _store(_mk("epi:Source", {"title": "unused"}))
    v = provenance.combine_verdict([], store)
    assert v["independent"] is True
    assert v["shared_upstreams"] == []


def test_ancestors_excludes_self_and_terminates_on_cycle_safe_input():
    a = _mk("epi:Source", {"title": "a"})
    b = _mk("epi:Claim", {"text": "b"}, [a["id"]])
    store = _store(a, b)
    assert provenance.ancestors(b["id"], store) == {a["id"]}
    assert provenance.ancestors(a["id"], store) == set()

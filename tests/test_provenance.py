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


def test_backstop_disjoint_from_at_risk_upgrades_to_as_independent():
    # flf-contest#7: a shared premise + a backstop disjoint from the AT-RISK premise ->
    # REFUSE-TO-COMBINE-AS-INDEPENDENT + conclusion_unchanged (the conclusion stands).
    at_risk = _mk("epi:Entity", {"name": "hawking premise"})
    shared = _mk("epi:Entity", {"name": "cosmic-ray premise"})
    c1 = _mk("epi:Claim", {"text": "astro"}, [shared["id"]])
    c2 = _mk("epi:Claim", {"text": "wd/ns backstop"}, [shared["id"]])   # NOT derived from at_risk
    c3 = _mk("epi:Claim", {"text": "moon"}, [shared["id"]])
    store = _store(at_risk, shared, c1, c2, c3)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"], c3["id"]], store,
        backstop=c2["id"], at_risk_upstream=at_risk["id"])
    assert v["verdict"] == "REFUSE-TO-COMBINE-AS-INDEPENDENT"
    assert v["conclusion_unchanged"] is True
    assert v["backstop"] == c2["id"]


def test_backstop_that_shares_at_risk_premise_stays_a_bare_refuse():
    # honest check: a backstop that itself derives from the at-risk premise does NOT survive
    # its failure, so the verdict stays a bare REFUSE-TO-COMBINE (no fake reassurance).
    at_risk = _mk("epi:Source", {"title": "at-risk premise"})
    c1 = _mk("epi:Claim", {"text": "a"}, [at_risk["id"]])
    c2 = _mk("epi:Claim", {"text": "b"}, [at_risk["id"]])
    store = _store(at_risk, c1, c2)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"]], store, backstop=c2["id"], at_risk_upstream=at_risk["id"])
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert v["conclusion_unchanged"] is False


def test_ancestors_excludes_self_and_terminates_on_cycle_safe_input():
    a = _mk("epi:Source", {"title": "a"})
    b = _mk("epi:Claim", {"text": "b"}, [a["id"]])
    store = _store(a, b)
    assert provenance.ancestors(b["id"], store) == {a["id"]}
    assert provenance.ancestors(a["id"], store) == set()


def test_explain_combinable_says_nothing_to_un_refuse():
    s1 = _mk("epi:Source", {"title": "Worobey 2022"})
    s2 = _mk("epi:Source", {"title": "Pekar 2022"})
    c1 = _mk("epi:Claim", {"text": "proximity"}, [s1["id"]])
    c2 = _mk("epi:Claim", {"text": "two lineages"}, [s2["id"]])
    store = _store(s1, s2, c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    text = provenance.explain_verdict(v, store)
    assert "share no upstream" in text
    assert "nothing to un-refuse" in text


def test_explain_refusal_names_shared_parent_and_un_refuse_set():
    # #22: a refusal must carry the shared parent AND what would un-refuse it, in prose.
    src = _mk("epi:Source", {"title": "Worobey 2022"})
    c1 = _mk("epi:Claim", {"text": "geographic clustering", "illustrative_LR": 5.0}, [src["id"]])
    c2 = _mk("epi:Claim", {"text": "environmental sampling", "illustrative_LR": 5.0}, [src["id"]])
    c3 = _mk("epi:Claim", {"text": "susceptible animals", "illustrative_LR": 5.0}, [src["id"]])
    store = _store(src, c1, c2, c3)
    v = provenance.combine_verdict([c1["id"], c2["id"], c3["id"]], store)
    text = provenance.explain_verdict(v, store)
    assert "Worobey 2022" in text                 # names the shared parent, readably
    assert "125:1" in text and "5:1" in text       # LR inflation, honest cap
    assert "un-refuse" in text                     # the discarded un-refuse set, surfaced
    assert "flips to COMBINABLE" in text


def test_explain_conclusion_unchanged_says_the_conclusion_stands():
    at_risk = _mk("epi:Entity", {"name": "hawking premise"})
    shared = _mk("epi:Entity", {"name": "cosmic-ray premise"})
    c1 = _mk("epi:Claim", {"text": "astro"}, [shared["id"]])
    c2 = _mk("epi:Claim", {"text": "wd/ns backstop"}, [shared["id"]])
    c3 = _mk("epi:Claim", {"text": "moon"}, [shared["id"]])
    store = _store(at_risk, shared, c1, c2, c3)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"], c3["id"]], store,
        backstop=c2["id"], at_risk_upstream=at_risk["id"])
    text = provenance.explain_verdict(v, store)
    assert "conclusion itself still stands" in text
    assert "independent votes" in text


def test_explain_label_falls_back_to_id_for_unknown():
    assert provenance.label("tt:unknown", {}) == "tt:unknown"

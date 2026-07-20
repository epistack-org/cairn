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


def test_empty_claim_set_is_invalid_not_vacuously_combinable():
    # dev/cairn#37 finding 2: "no shared upstream" is vacuously true of the empty set, so the
    # old code called it COMBINABLE (exit 0). An empty selection cannot be judged independent
    # — it must fail CLOSED as INVALID.
    store = _store(_mk("epi:Source", {"title": "unused"}))
    v = provenance.combine_verdict([], store)
    assert v["verdict"] == "INVALID"
    assert v["independent"] is False
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


# ---------------------------------------------------------------------------
# dev/cairn#37 — fail-closed at ingestion (adversarial)
# ---------------------------------------------------------------------------

def test_direct_parent_child_derivation_is_refused():
    # dev/cairn#37 finding 1: B is derived DIRECTLY from A. Combining [A, B] as independent
    # must REFUSE — A is B's parent. The old ancestor-set-excludes-self bug made this the
    # central detector's blind spot: refl(A)={A} vs refl(B)={A,B} now intersect on {A}.
    a = _mk("epi:Source", {"title": "parent dataset"})
    b = _mk("epi:Claim", {"text": "derived directly from A"}, [a["id"]])
    store = _store(a, b)
    v = provenance.combine_verdict([a["id"], b["id"]], store)
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert v["independent"] is False
    assert a["id"] in v["shared_upstreams"]


def test_child_parent_order_is_symmetric():
    # order of the two ids must not matter — reachability is undirected for the refusal.
    a = _mk("epi:Source", {"title": "parent"})
    b = _mk("epi:Claim", {"text": "child"}, [a["id"]])
    store = _store(a, b)
    assert provenance.combine_verdict([b["id"], a["id"]], store)["verdict"] == "REFUSE-TO-COMBINE"


def test_grandparent_derivation_is_refused():
    # A -> B -> C chain; combining the endpoints [A, C] must refuse (transitive self-inclusion).
    a = _mk("epi:Source", {"title": "A"})
    b = _mk("epi:Claim", {"text": "B from A"}, [a["id"]])
    c = _mk("epi:Claim", {"text": "C from B"}, [b["id"]])
    store = _store(a, b, c)
    v = provenance.combine_verdict([a["id"], c["id"]], store)
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert a["id"] in v["shared_upstreams"]


def test_missing_only_claim_set_is_invalid_not_combinable():
    # dev/cairn#37 finding 2: two ids that resolve to NO record must be INVALID, never the
    # old vacuous COMBINABLE from treating them as opaque ancestor-free roots.
    store = _store(_mk("epi:Source", {"title": "present"}))
    v = provenance.combine_verdict(["missing-a", "missing-b"], store)
    assert v["verdict"] == "INVALID"
    assert v["independent"] is False
    assert sorted(v["missing"]) == ["missing-a", "missing-b"]


def test_partially_missing_claim_set_is_invalid():
    # even ONE unresolved selected id fails closed — you cannot judge a set you can't load.
    src = _mk("epi:Source", {"title": "s"})
    c1 = _mk("epi:Claim", {"text": "real"}, [src["id"]])
    store = _store(src, c1)
    v = provenance.combine_verdict([c1["id"], "ghost"], store)
    assert v["verdict"] == "INVALID"
    assert v["missing"] == ["ghost"]


def test_backstop_that_does_not_resolve_stays_bare_refuse():
    # dev/cairn#37 finding 3: a typoed / nonexistent backstop must NOT upgrade a refusal.
    at_risk = _mk("epi:Entity", {"name": "at-risk premise"})
    shared = _mk("epi:Entity", {"name": "shared premise"})
    c1 = _mk("epi:Claim", {"text": "a"}, [shared["id"]])
    c2 = _mk("epi:Claim", {"text": "b"}, [shared["id"]])
    store = _store(at_risk, shared, c1, c2)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"]], store,
        backstop="totally-missing-id", at_risk_upstream=at_risk["id"])
    assert v["verdict"] == "REFUSE-TO-COMBINE"           # NOT ...-AS-INDEPENDENT
    assert v["conclusion_unchanged"] is False
    assert "UNRESOLVED" in v["note"]


def test_backstop_upgrade_requires_a_named_at_risk_premise():
    # omitting the at-risk premise must not short-circuit disjointness to True.
    shared = _mk("epi:Entity", {"name": "shared premise"})
    c1 = _mk("epi:Claim", {"text": "a"}, [shared["id"]])
    c2 = _mk("epi:Claim", {"text": "b"}, [shared["id"]])
    store = _store(shared, c1, c2)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"]], store, backstop=c2["id"], at_risk_upstream=None)
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert v["conclusion_unchanged"] is False


def test_backstop_with_missing_at_risk_premise_stays_bare_refuse():
    # a named-but-unresolved at-risk premise is also insufficient for the upgrade.
    shared = _mk("epi:Entity", {"name": "shared premise"})
    c1 = _mk("epi:Claim", {"text": "a"}, [shared["id"]])
    c2 = _mk("epi:Claim", {"text": "b"}, [shared["id"]])
    store = _store(shared, c1, c2)
    v = provenance.combine_verdict(
        [c1["id"], c2["id"]], store, backstop=c2["id"], at_risk_upstream="ghost-premise")
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert v["conclusion_unchanged"] is False


def test_explain_invalid_says_it_cannot_be_judged():
    store = _store(_mk("epi:Source", {"title": "s"}))
    v = provenance.combine_verdict([], store)
    text = provenance.explain_verdict(v, store)
    assert "cannot be judged" in text
    assert "not vacuously combinable" in text


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


# ---------------------------------------------------------------------------
# fundedBy — the disclosure channel (a funder is not an evidence source)
# ---------------------------------------------------------------------------

def _mk_funded(type_, assertion, derived_from=None, funded_by=None):
    return envelope.mint(
        envelope.new_record(
            type_, assertion, minted_by="team:test", method="extract",
            derived_from=derived_from or [], funded_by=funded_by or [], at=AT,
        )
    )


def test_shared_funder_alone_does_not_refuse():
    """The whole point of the channel: a common paymaster is NOT a common source.

    Two studies bankrolled by one funder can still be two genuinely independent
    measurements. If this refused, every NIH-funded pair in any corpus would
    collapse and the engine would become the refuse-everything oracle.
    """
    s1 = _mk_funded("epi:Source", {"title": "Enstrom 2003"})
    s2 = _mk_funded("epi:Source", {"title": "Jenkins 1996"})
    c1 = _mk_funded("epi:Claim", {"text": "ETS effect null (Enstrom)"},
                    [s1["id"]], ["urn:funder:ciar"])
    c2 = _mk_funded("epi:Claim", {"text": "ETS exposure low (Jenkins)"},
                    [s2["id"]], ["urn:funder:ciar"])
    store = _store(s1, s2, c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    assert v["independent"] is True
    assert v["verdict"] == "COMBINABLE"
    assert v["shared_upstreams"] == []
    # ...but the funder is named, not silently dropped
    assert v["shared_funders"] == ["urn:funder:ciar"]
    assert "urn:funder:ciar" in v["reason"]


def test_funder_edge_is_not_walked_as_an_ancestor():
    """fundedBy must never leak into the derivation closure."""
    c = _mk_funded("epi:Claim", {"text": "x"}, [], ["urn:funder:ciar"])
    store = _store(c)
    assert provenance.ancestors(c["id"], store) == set()
    assert provenance.funders(c) == {"urn:funder:ciar"}


def test_shared_funder_is_disclosed_but_refusal_rests_on_derivedfrom():
    """When a real shared upstream exists, the refusal stands on IT — funder is colour."""
    src = _mk_funded("epi:Source", {"title": "Kaiser 2003"})
    c1 = _mk_funded("epi:Claim", {"text": "line A"}, [src["id"]], ["urn:funder:roche"])
    c2 = _mk_funded("epi:Claim", {"text": "line B"}, [src["id"]], ["urn:funder:roche"])
    store = _store(src, c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    assert v["verdict"] == "REFUSE-TO-COMBINE"
    assert v["shared_upstreams"] == [src["id"]]      # the refusal's actual basis
    assert v["shared_funders"] == ["urn:funder:roche"]
    assert "urn:funder:roche" not in v["reason"]     # funder carries no refusal weight


def test_distinct_funders_share_nothing():
    c1 = _mk_funded("epi:Claim", {"text": "a"}, [], ["urn:funder:nih"])
    c2 = _mk_funded("epi:Claim", {"text": "b"}, [], ["urn:funder:erc"])
    store = _store(c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    assert v["verdict"] == "COMBINABLE"
    assert v["shared_funders"] == []


def test_lone_claim_does_not_share_a_funder_with_itself():
    """The same two-party rule shared_upstreams learned the hard way (dev/cairn#9)."""
    c = _mk_funded("epi:Claim", {"text": "solo"}, [], ["urn:funder:ciar"])
    store = _store(c)
    v = provenance.combine_verdict([c["id"]], store)
    assert v["shared_funders"] == []
    assert v["verdict"] == "COMBINABLE"


def test_explain_names_the_funder_and_says_it_is_not_a_refusal():
    s1 = _mk_funded("epi:Source", {"title": "Enstrom 2003"})
    s2 = _mk_funded("epi:Source", {"title": "Jenkins 1996"})
    c1 = _mk_funded("epi:Claim", {"text": "a"}, [s1["id"]], ["urn:funder:ciar"])
    c2 = _mk_funded("epi:Claim", {"text": "b"}, [s2["id"]], ["urn:funder:ciar"])
    store = _store(s1, s2, c1, c2)
    v = provenance.combine_verdict([c1["id"], c2["id"]], store)
    text = provenance.explain_verdict(v, store)
    assert "share a funder" in text
    assert "urn:funder:ciar" in text
    assert "not a reason to refuse" in text


def test_empty_fundedby_is_omitted_so_existing_ids_never_move():
    """The additivity guarantee: no fundedBy => byte-identical to the pre-change record.

    This is what keeps every pinned corpus golden and the cairn-cr parity vectors valid.
    """
    plain = envelope.new_record("epi:Claim", {"text": "x"}, minted_by="team:test",
                                method="extract", derived_from=[], at=AT)
    assert "fundedBy" not in plain["provenance"]
    explicit_empty = envelope.new_record("epi:Claim", {"text": "x"}, minted_by="team:test",
                                         method="extract", derived_from=[], funded_by=[], at=AT)
    assert "fundedBy" not in explicit_empty["provenance"]
    assert envelope.content_uri(plain) == envelope.content_uri(explicit_empty)


def test_funded_record_still_validates_against_the_schema():
    c = _mk_funded("epi:Claim", {"text": "x"}, [], ["urn:funder:ciar"])
    assert envelope.validate(c) == []

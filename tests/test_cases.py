"""The three worked examples, mechanically verified (floor deliverable #3, dev/cairn#9).

`fixtures/CASES.json` DECLARES what each worked example claims: which lines look
independent, what upstream they actually share, and which pair is genuinely combinable.
This module holds those declarations to the fixtures. A case whose laundered set fails
to REFUSE, or whose shared upstream is not the one the detector actually names, fails
CI — so "cairn ships 3 worked examples" is a checked property of the corpus, not a
sentence in the README.

It also checks the two things a worked example could most easily fake:

  * every probe in every battery is span-grounded — each `grounds.quote` must be a
    literal substring of the cited source's sha-pinned excerpt (a battery whose keys
    are not in the sources is a battery that measures nothing); and
  * every claim's grounding quote really is a substring of the retrieved bytes, so a
    fabricated span cannot survive a rebuild.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cairn import envelope, grounding, provenance

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"

CASES = json.loads((FX / "CASES.json").read_text())
INDEX = json.loads((FX / "INDEX.json").read_text())
CASE_IDS = sorted(CASES)


def _store() -> dict[str, dict]:
    store = {}
    for slug in INDEX:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return store


STORE = _store()


def test_worked_examples_ship():
    """The corpus ships four worked examples. Count them from the corpus, not from prose.

    The fourth (amyloid-abeta56) was added in the 2026-07-15 decoupling spike, from a live
    scientific controversy the engine was NOT co-developed against, to demonstrate the
    refusal generalizes beyond the three seed cases (flf-contest supplementary material)."""
    assert len(CASES) == 4, f"expected 4 worked examples, corpus declares {sorted(CASES)}"
    assert set(CASES) == {
        "covid-origins", "eggs-good-for-you", "cern-black-hole", "amyloid-abeta56"
    }


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_laundered_set_is_refused(case_id):
    """The apparently-independent lines must actually be refused."""
    case = CASES[case_id]
    ids = [INDEX[s] for s in case["laundered_set"]]
    v = provenance.combine_verdict(ids, STORE)
    assert v["verdict"] == "REFUSE-TO-COMBINE", (case_id, v["reason"])


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_declared_shared_upstream_is_the_one_the_detector_finds(case_id):
    """The case names its shared upstream; the DAG walk must independently agree —
    and it must be shared by EVERY line, not merely by some pair."""
    case = CASES[case_id]
    ids = [INDEX[s] for s in case["laundered_set"]]
    collective = provenance.shared_upstreams(ids, STORE)["collective_shared"]
    declared = INDEX[case["shared_upstream"]]
    assert declared in collective, (
        case_id,
        f"declared shared upstream {case['shared_upstream']} is not shared by all lines",
    )


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_contrast_pair_matches_declared_verdict(case_id):
    """Each case declares what its contrast pair should do. eggs (Hu×Djousse, disjoint
    cohorts) and cern (Hawking×WD/NS, disjoint premises) must COMBINE — an engine that
    refused everything would be useless. covid's contrast (Worobey×Pekar) was the entry's
    false COMBINABLE and must now REFUSE on the honest DAG (flf-contest#5) — the assertion
    that PR#10 hardened the wrong way, inverted."""
    case = CASES[case_id]
    pair = [INDEX[s] for s in case["contrast_pair"]]
    v = provenance.combine_verdict(pair, STORE)
    want = case["contrast_expected"]
    assert v["verdict"] == want, (case_id, f"contrast verdict != {want}", v["reason"])


def test_worobey_pekar_refuses_on_the_honest_dag():
    """THE gate (flf-contest#5): the false COMBINABLE, killed. geographic-clustering ×
    two-lineages must REFUSE, naming the citation (Worobey 2022) and dataset (PRC early-case
    investigation) upstreams the honest DAG exposes."""
    pair = [INDEX["claim-geographic-clustering"], INDEX["claim-two-lineages"]]
    v = provenance.combine_verdict(pair, STORE)
    assert v["verdict"] == "REFUSE-TO-COMBINE", v["reason"]
    assert INDEX["src-worobey-2022"] in v["shared_upstreams"]           # Pekar cites Worobey (ref [39])
    assert INDEX["ent-prc-early-case-investigation"] in v["shared_upstreams"]  # shared early-case dataset


def test_naive_document_dag_still_combines_worobey_pekar():
    """The cautionary run: on the document-level DAG (fixtures/naive/, no dataset/citation
    edges) the same pair COMBINES — exactly as the entry originally, wrongly, shipped. The
    two runs one command apart ARE the contestability demo."""
    naive_dir = FX / "naive"
    nstore = {}
    for f in naive_dir.glob("*.json"):
        if f.name == "INDEX.json":
            continue
        rec = json.loads(f.read_text())
        nstore[rec["id"]] = rec
    nidx = json.loads((naive_dir / "INDEX.json").read_text())
    pair = [nidx["claim-geographic-clustering"], nidx["claim-two-lineages"]]
    v = provenance.combine_verdict(pair, nstore)
    assert v["verdict"] == "COMBINABLE", v["reason"]


def test_cern_hawking_wd_ns_is_a_genuine_combinable():
    """The true positive a hostile reader cannot break (flf-contest#6): the Hawking-radiation
    evaporation line and the white-dwarf/neutron-star survival bound are upstream-disjoint by
    construction (G&M premised the WD/NS bound on the Hawking premise failing)."""
    pair = [INDEX["claim-cern-hawking-evaporation"], INDEX["claim-cern-wd-ns-bound"]]
    v = provenance.combine_verdict(pair, STORE)
    assert v["verdict"] == "COMBINABLE", v["reason"]


def test_cern_trio_refuses_as_independent_with_conclusion_unchanged():
    """flf-contest#7: CERN must not emit a BARE refuse in front of a cosmologist. With the
    WD/NS backstop (disjoint from the at-risk Hawking premise) the verdict is
    REFUSE-TO-COMBINE-AS-INDEPENDENT + conclusion_unchanged — the safety conclusion stands;
    what fails is the claim that these are three independent votes."""
    trio = [INDEX[s] for s in CASES["cern-black-hole"]["laundered_set"]]
    v = provenance.combine_verdict(
        trio, STORE,
        backstop=INDEX["claim-cern-wd-ns-bound"],
        at_risk_upstream=INDEX["ent-hawking-radiation-premise"])
    assert v["verdict"] == "REFUSE-TO-COMBINE-AS-INDEPENDENT", v
    assert v["conclusion_unchanged"] is True
    assert INDEX["claim-cern-wd-ns-bound"] == v["backstop"]


def test_eggs_shared_upstream_is_found_only_transitively():
    """The eggs case is the first REAL corpus to exercise the transitive detector.

    The shared cohort backbone appears in NO claim's direct `derivedFrom` — it is two
    hops up (claim -> meta-analysis -> primary study -> cohort). If it ever became a
    direct edge, the case would still pass the other tests while silently ceasing to
    demonstrate the thing it exists to demonstrate.
    """
    case = CASES["eggs-good-for-you"]
    backbone = INDEX[case["shared_upstream"]]
    for slug in case["laundered_set"]:
        direct = set(STORE[INDEX[slug]]["provenance"]["derivedFrom"])
        assert backbone not in direct, f"{slug} names the backbone directly — not transitive"
        assert backbone in provenance.ancestors(INDEX[slug], STORE), (
            f"{slug} does not reach the backbone at all"
        )


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_every_battery_probe_is_span_grounded(case_id):
    """A battery whose keyed probes are not grounded in the sources measures nothing.

    Every `grounds.quote` must be a literal substring of the cited source's excerpt —
    the same bar the claims themselves must clear.
    """
    battery = json.loads((ROOT / CASES[case_id]["battery"]).read_text())
    checked = 0
    for probe in battery["probes"]:
        for g in probe.get("grounds", []):
            src = STORE[INDEX[g["source"]]]
            excerpt = src["assertion"]["excerpt"]
            assert g["quote"] in excerpt, (
                case_id, battery["battery_id"], probe["id"],
                f"probe quote is not a literal substring of {g['source']}",
            )
            checked += 1
    assert checked, f"{case_id}: battery has no grounded probes"


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_battery_declares_the_case_crux(case_id):
    battery = json.loads((ROOT / CASES[case_id]["battery"]).read_text())
    assert battery["crux"] == CASES[case_id]["crux"], (
        case_id, "battery crux has drifted from the case manifest"
    )


def test_all_records_valid_and_signed():
    for slug, rid in INDEX.items():
        rec = STORE[rid]
        assert envelope.validate(rec) == [], (slug, envelope.validate(rec))
        v = envelope.verify(rec)
        assert v["id_ok"], f"{slug}: content-id does not match content"
        assert v["sig_ok"], f"{slug}: signature does not verify"


def test_whole_corpus_grounds():
    report = grounding.check_store(STORE)
    assert report["ok"], report["failed"]
    assert report["checked"] == report["grounded"]


def test_refusal_auc_is_perfect_over_known_structure_sets():
    """flf-contest#6: abstention scored as discrimination, not as a rate. The pinned
    output must recompute, and the refusal must perfectly separate known-entangled from
    known-disjoint claim-sets (AUC 1.0) — an engine that always refuses cannot do this."""
    from fixtures.refusal_auc import build
    fresh = build()
    pinned = json.loads((FX / "refusal_auc.json").read_text())
    assert fresh == pinned, "fixtures/refusal_auc.json is stale — run fixtures/refusal_auc.py"
    assert fresh["refusal_auc"] == 1.0
    assert fresh["confusion"] == {"tp": 6, "fp": 0, "fn": 0, "tn": 4}
    assert fresh["naive_worobey_pekar_verdict"] == "COMBINABLE"


def test_structural_claims_carry_no_likelihood_ratio():
    """The claims whose job is to EVIDENCE a derivedFrom edge (e.g. 'this review's
    Table 1 lists the NHS cohort') are evidence about the DAG, not evidential lines.
    They must not carry an illustrative_LR, or `cairn frechet` would sweep them into a
    combination and silently inflate it."""
    for slug in INDEX:
        if "pools" in slug:  # the structural/inclusion-edge claims
            assertion = STORE[INDEX[slug]]["assertion"]
            assert "illustrative_LR" not in assertion, (
                f"{slug} is a structural claim and must not carry an illustrative_LR"
            )

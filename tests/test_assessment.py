"""A2 — deterministic checks over the pinned assessment runs (no model access).

These run on the committed artifacts in assessment/runs/. The live measurement is
non-deterministic; its *result* is pinned, and everything here re-derives from that
pinned data — so CI verifies the measured n_eff on a fresh machine. Skipped (not
failed) until the runs have been built, so the A1 suite stays green in the interim.
"""
import json
from pathlib import Path

import pytest

from cairn import assessment, envelope, provenance

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "assessment" / "runs"
FX = ROOT / "fixtures"
CLUSTER_FILES = ["heterogeneous.json", "homogeneous-control.json", "clean-diverse.json", "glm-diverse.json"]

pytestmark = pytest.mark.skipif(
    not (RUNS / "heterogeneous.json").exists(),
    reason="assessment runs not built yet (run assessment/build_assessment.py)",
)


def _load(p):
    return json.loads(Path(p).read_text())


def battery():
    return _load(ROOT / "assessment" / "probes.json")


def clusters():
    return [_load(RUNS / c) for c in CLUSTER_FILES if (RUNS / c).exists()]


def assessments():
    return _load(RUNS / "assessments.json")


def all_records():
    return [_load(RUNS / "battery.json"), *clusters(), *assessments()]


def neff_by_panel():
    return {c["assertion"]["panel"]: c["assertion"]["neff"] for c in clusters()}


# --- integrity --------------------------------------------------------------
def test_every_record_schema_validates():
    for r in all_records():
        assert envelope.validate(r) == [], (r.get("@type"), r.get("id"))


def test_every_record_id_and_signature_verify():
    for r in all_records():
        v = envelope.verify(r)
        assert v["id_ok"], (r.get("@type"), r.get("id"))
        assert v["sig_ok"], (r.get("@type"), r.get("id"))


def test_record_types():
    assert _load(RUNS / "battery.json")["@type"] == "epi:Schema"
    for c in clusters():
        assert c["@type"] == "epi:Cluster"
    assert all(a["@type"] == "epi:Assessment" for a in assessments())


# --- the mechanical n_eff re-check (what `cairn assess` runs) ----------------
def test_cairn_assess_recomputes_pinned_neff():
    for run in clusters():
        rep = assessment.check_run(run, battery())
        assert rep["ok"], rep
        assert rep["order_ok"] and rep["matrix_ok"] and rep["neff_ok"]


def test_affirm_vectors_match_recomputation():
    bat = battery()
    for run in clusters():
        for asr in run["assertion"]["assessors"]:
            assert asr["affirm_vector"] == assessment.affirm_vector(asr["answers"], bat), asr["assessor"]


def test_each_panel_has_nine_assessors():
    for run in clusters():
        assert run["assertion"]["neff"]["k"] == 9


# --- keyed-probe reliability is present + well-formed ------------------------
def test_reliability_present_over_eight_keyed_probes():
    keyed = [p for p in battery()["probes"] if p.get("key") in ("YES", "NO")]
    assert len(keyed) == 8
    for a in assessments():
        rel = a["assertion"]["reliability"]
        assert rel["keyed"] == 8
        assert 0 <= rel["correct"] <= 8


# --- the structural payoff: A1 provenance explains assessor correlation ------
def test_assessment_derivedfrom_is_the_granted_evidence():
    for a in assessments():
        assert set(a["provenance"]["derivedFrom"]) == set(a["assertion"]["granted"])


def test_shared_evidence_refuses_disjoint_combines():
    store = {}
    for slug in ("src-worobey-2022", "src-pekar-2022"):
        rec = _load(FX / f"{slug}.json")
        store[rec["id"]] = rec
    for a in assessments():
        store[a["id"]] = a
    by_part = {}
    for a in assessments():
        by_part.setdefault(a["assertion"]["partition"], []).append(a["id"])

    shared = provenance.combine_verdict(by_part["FULL"][:2], store)
    assert not shared["independent"], "two FULL assessors share evidence -> must REFUSE"

    disjoint = provenance.combine_verdict([by_part["WOROBEY_ONLY"][0], by_part["PEKAR_ONLY"][0]], store)
    assert disjoint["independent"], "disjoint partitions -> must be COMBINABLE"


# --- battery is grounded in the A1 corpus (ties A2 back to real spans) -------
def test_keyed_probes_quote_their_source_verbatim():
    excerpts = {
        slug: _load(FX / f"{slug}.json")["assertion"]["excerpt"]
        for slug in ("src-worobey-2022", "src-pekar-2022")
    }
    for p in battery()["probes"]:
        for g in p.get("grounds", []):
            assert g["quote"] in excerpts[g["source"]], (p["id"], g["source"])


# --- the measured claim: correlation is real; diversity axes decorrelate -----
def test_homogeneous_control_is_the_correlated_floor():
    # Pinned data. The homogeneous control (same model+evidence+protocol) is the
    # correlated baseline; every diversity lever must lower phi_bar (raise n_eff).
    # If this ever fails, the measurement — not the test — changed: a finding to
    # surface, not silence.
    n = neff_by_panel()
    assert n["homogeneous-control"]["phi_bar"] >= n["heterogeneous"]["phi_bar"]
    assert n["homogeneous-control"]["n_eff_capped"] <= n["heterogeneous"]["n_eff_capped"]


def test_axis_ordering_partition_decorrelates_beyond_model_and_protocol():
    n = neff_by_panel()
    if "clean-diverse" in n:
        # Evidence held FULL (clean-diverse) is more correlated than also varying the
        # evidence partition (heterogeneous): phi control >= clean-diverse >= heterogeneous.
        assert n["homogeneous-control"]["phi_bar"] >= n["clean-diverse"]["phi_bar"]
        assert n["clean-diverse"]["phi_bar"] >= n["heterogeneous"]["phi_bar"]


# --- cross-vendor (GLM) leg -------------------------------------------------
glm_only = pytest.mark.skipif(
    not (RUNS / "glm-diverse.json").exists(), reason="glm-diverse panel not built yet"
)


@glm_only
def test_glm_panel_is_zai_vendor():
    glm = _load(RUNS / "glm-diverse.json")
    assert glm["assertion"]["panel"] == "glm-diverse"
    for a in glm["assertion"]["assessors"]:
        assert a["vendor"] == "zai"
        assert a["model_tier"] == "glm-4.6"


@glm_only
def test_cross_vendor_decomposition_present_and_wellformed():
    cv = _load(RUNS / "axis_analysis.json").get("cross_vendor")
    assert cv is not None, "cross_vendor decomposition missing from axis_analysis.json"
    assert cv["combined_k"] == 18
    for k in ("within_anthropic_phi", "within_glm_phi", "cross_vendor_phi"):
        assert -1.0 <= cv[k] <= 1.0
    assert cv["combined_neff"] >= 1.0

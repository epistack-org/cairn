"""A4 — deterministic checks of the careful-baseline head-to-head (no model access).

Pure-logic tests (synthetic panel + synthetic cairn outputs) always run and
mutation-kill the scoring. Tests that read the pinned baseline / fixtures / A2 runs
are skipped (not failed) until those are built, mirroring test_frechet.py. The
careful-baseline *panel* is a captured measurement; everything scored over it here
is a closed form, re-checkable on a fresh machine.
"""
import json
from pathlib import Path

import pytest

from cairn import cli, frechet, headtohead

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
RUNS = ROOT / "assessment" / "runs"
BASELINE = ROOT / "assessment" / "baseline.json"
ART = ROOT / "assessment" / "head_to_head.json"

needs_baseline = pytest.mark.skipif(
    not BASELINE.exists(), reason="assessment/baseline.json not present (the pinned careful-baseline panel)",
)
needs_fixtures = pytest.mark.skipif(
    not (FX / "INDEX.json").exists(), reason="fixtures not built (run fixtures/build_fixtures.py)",
)
needs_runs = pytest.mark.skipif(
    not (RUNS / "clean-diverse.json").exists(), reason="assessment runs not built (run assessment/build_assessment.py)",
)


# --- synthetic inputs for the pure-logic tests ------------------------------

def _run(**kw):
    d = {
        "framing": "t", "combined_lr_proximity": None, "posterior_proximity": None,
        "gave_single_point": False, "noticed_shared_source": True,
        "flagged_common_confounder": True, "hedged": True,
        "self_report": {
            "computed_neff_over_multiple_assessors": False,
            "emitted_numeric_interval": True,
            "emitted_labelled_nested_regimes": True,
            "issued_machine_actionable_refusal": False,
        },
    }
    d.update(kw)
    return d


def _cairn(*, trio_shared=True):
    trio = frechet.frechet_verdict([5, 5, 5], shared_upstream=trio_shared, n_eff=1.0)
    trio["provenance"] = {"verdict": "REFUSE-TO-COMBINE" if trio_shared else "COMBINABLE",
                          "shared_upstreams": ["tt:x"] if trio_shared else []}
    contrast = frechet.frechet_verdict([5, 4], shared_upstream=False)
    contrast["provenance"] = {"verdict": "COMBINABLE", "shared_upstreams": []}
    neff = {"clean_diverse": 1.06, "homogeneous": 1.0, "k": 9,
            "cross_vendor": 1.06, "cross_vendor_k": 18, "cross_vendor_phi": 0.95}
    return {"trio": trio, "contrast": contrast, "neff": neff}


def _verdicts():
    return [
        {"delta_id": 1, "honest_verdict": "STRUCTURAL-RESIDUAL", "what_baseline_structurally_cannot": "no artifact"},
        {"delta_id": 2, "honest_verdict": "STRUCTURALLY-IMPOSSIBLE", "what_baseline_structurally_cannot": "n=1"},
        {"delta_id": 3, "honest_verdict": "STRUCTURAL-RESIDUAL", "what_baseline_structurally_cannot": "no certificate"},
        {"delta_id": 4, "honest_verdict": "STRUCTURAL-RESIDUAL", "what_baseline_structurally_cannot": "no gate"},
    ]


# --- pure-logic tests (always run) ------------------------------------------

def test_summarize_runs_fractions():
    runs = [
        _run(gave_single_point=True, combined_lr_proximity=10.0),
        _run(gave_single_point=True, combined_lr_proximity=10.0),
        _run(noticed_shared_source=False, hedged=False),
    ]
    c = headtohead.summarize_runs(runs)
    assert c["n"] == 3
    assert c["gave_point_fraction"] == pytest.approx(2 / 3, abs=1e-4)
    assert c["noticed_shared_source_fraction"] == pytest.approx(2 / 3, abs=1e-4)
    assert c["hedged_fraction"] == pytest.approx(2 / 3, abs=1e-4)
    assert c["combined_lr_values"] == [10.0, 10.0]
    assert c["combined_lr_min"] == 10.0 and c["combined_lr_max"] == 10.0
    assert c["any_computed_neff"] is False
    assert c["emitted_interval_count"] == 3


def test_empty_panel_is_safe():
    c = headtohead.summarize_runs([])
    assert c["n"] == 0 and c["gave_point_fraction"] == 0.0
    assert c["combined_lr_min"] is None and c["any_computed_neff"] is False


def test_build_verdict_routing_and_demonstrated():
    art = headtohead.build({"runs": [_run(), _run()], "delta_verdicts": _verdicts()}, _cairn())
    by_id = {r["id"]: r for r in art["deltas"]}
    assert by_id[2]["verdict"] == "STRUCTURALLY-IMPOSSIBLE"
    assert by_id[1]["verdict"] == by_id[3]["verdict"] == by_id[4]["verdict"] == "STRUCTURAL-RESIDUAL"
    assert art["summary"]["structurally_impossible"] == [2]
    assert art["summary"]["structural_residual"] == [1, 3, 4]
    # cairn refuses the trio + no run measured n_eff -> demonstrated
    assert art["summary"]["delta_demonstrated"] is True
    assert art["summary"]["baseline_produced_none_of_the_four_artifacts"] is True


def test_demonstrated_false_when_cairn_combines():
    # if cairn ever COMBINED the trio (regression), the delta is not demonstrated
    art = headtohead.build({"runs": [_run()], "delta_verdicts": _verdicts()}, _cairn(trio_shared=False))
    assert art["cairn"]["trio_verdict"] == "COMBINABLE-WITH-INTERVAL"
    assert art["summary"]["delta_demonstrated"] is False
    assert headtohead.demonstrated(art) is False


def test_neff_artifact_flag_is_measured_not_asserted():
    # delta-2's "produced artifact" tracks the panel: flip one run to "computed n_eff"
    base = {"runs": [_run(), _run()], "delta_verdicts": _verdicts()}
    assert headtohead.build(base, _cairn())["deltas"][1]["baseline_produced_reproducible_artifact"] is False
    base["runs"][0]["self_report"]["computed_neff_over_multiple_assessors"] = True
    got = headtohead.build(base, _cairn())
    assert got["deltas"][1]["baseline_produced_reproducible_artifact"] is True
    # and then it no longer counts as "produced none"
    assert got["summary"]["baseline_produced_none_of_the_four_artifacts"] is False
    # but the *structural* delta-2 (n_eff impossible) is still demonstrated via the trio refusal
    assert got["summary"]["delta_demonstrated"] is False  # any_computed_neff now True


def test_cairn_output_strings_carry_the_numbers():
    art = headtohead.build({"runs": [_run()], "delta_verdicts": _verdicts()}, _cairn())
    out = {r["id"]: r["cairn_output"] for r in art["deltas"]}
    assert "REFUSE-TO-COMBINE" in out[1]
    assert "n_eff=1.06" in out[2] and "k=18" in out[2]
    assert "[5, 125]" in out[3] and "∞" in out[3] and "width 1.40" in out[3]
    assert "exit 2" in out[4] and "LR=20" in out[4]


# --- pinned-artifact + live-CLI tests (need the built corpus) ---------------

@needs_baseline
@needs_fixtures
@needs_runs
def test_artifact_recompute():
    from assessment.build_headtohead import build  # namespace import (mirrors test_frechet)
    assert ART.exists(), "assessment/head_to_head.json not pinned (run assessment/build_headtohead.py)"
    pinned = json.loads(ART.read_text())
    fresh = build()
    assert fresh == pinned, "assessment/head_to_head.json is stale — run assessment/build_headtohead.py"


@needs_baseline
def test_pinned_panel_oracles():
    art = json.loads(ART.read_text())
    c, s = art["baseline_consensus"], art["summary"]
    assert c["n"] == 5
    assert c["noticed_shared_source_fraction"] == 1.0
    assert c["flagged_confounder_fraction"] == 1.0
    assert c["hedged_fraction"] == 1.0
    assert c["any_computed_neff"] is False and c["computed_neff_count"] == 0
    assert 125.0 not in c["combined_lr_values"]  # no careful run bought the naive product
    assert s["delta_demonstrated"] is True
    assert s["structurally_impossible"] == [2]
    assert s["structural_residual"] == [1, 3, 4]
    assert art["cairn"]["trio_verdict"] == "REFUSE-TO-COMBINE-AS-POINT"
    assert art["cairn"]["trio_interval_lr"] == [5.0, 125.0]
    assert art["cairn"]["contrast_point_lr"] == 20.0


@needs_baseline
@needs_fixtures
@needs_runs
def test_cli_headtohead_exit_2():
    # exit 2 == the refusal-delta is demonstrated (mirrors `cairn frechet`)
    rc = cli.main(["headtohead", str(FX / "*.json"),
                   "--baseline", str(BASELINE), "--index", str(FX / "INDEX.json"),
                   "--runs-dir", str(RUNS)])
    assert rc == 2

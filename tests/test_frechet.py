"""A3 — deterministic checks of the Fréchet/p-box interval (no model access).

Pure-math tests always run. Tests that read the pinned A2 runs or the fixtures are
skipped (not failed) until those are built, mirroring test_assessment.py. Every
oracle here is hand-derived and independently re-checkable on a fresh machine.
"""
import json
import math
from pathlib import Path

import pytest

from cairn import cli, frechet, neff

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "assessment" / "runs"
FX = ROOT / "fixtures"
ART = ROOT / "assessment" / "frechet.json"

needs_runs = pytest.mark.skipif(
    not (RUNS / "heterogeneous.json").exists(),
    reason="assessment runs not built (run assessment/build_assessment.py)",
)
needs_fixtures = pytest.mark.skipif(
    not (FX / "INDEX.json").exists(),
    reason="fixtures not built (run fixtures/build_fixtures.py)",
)


# --- probability / odds plumbing --------------------------------------------

def test_posterior_map():
    cases = {125: 0.9920634920634921, 5: 0.8333333333333334, 20: 0.9523809523809523,
             4: 0.8, 25: 0.9615384615384616, 1.25: 0.5555555555555556, 500: 0.998003992015968}
    for lr, exp in cases.items():
        assert math.isclose(frechet.posterior(0.5, lr), exp, rel_tol=1e-12)
    assert frechet.posterior(0.5, math.inf) == 1.0
    assert frechet.posterior(0.5, 0) == 0.0


def test_marginals_from_lr_and_guard():
    assert frechet.marginals_from_lr(5) == (0.5, 0.1)
    assert frechet.marginals_from_lr(4) == (0.4, 0.1)
    with pytest.raises(ValueError):           # LR*base_neg >= 1 (LR>=10 at base_neg=0.1)
        frechet.marginals_from_lr(10)


def test_world_and_bounds():
    assert frechet.world_and_bounds([.5, .5, .5]) == (0.0, 0.5)
    assert frechet.world_and_bounds([.1, .1, .1]) == (0.0, 0.1)
    assert frechet.world_and_bounds([.9, .8]) == (pytest.approx(0.7), 0.8)  # max(0, 1.7-1)=0.7


def test_naive_lr():
    assert frechet.naive_lr([5, 5, 5]) == 125.0
    assert frechet.naive_lr([5, 4]) == 20.0


# --- the three nested regimes -----------------------------------------------

def test_full_frechet_is_vacuous():
    lo, hi = frechet.full_frechet_lr([.5, .5, .5], [.1, .1, .1])
    assert lo == 0.0 and hi == math.inf
    assert frechet.posterior(0.5, lo) == 0.0 and frechet.posterior(0.5, hi) == 1.0  # [0,1]


def test_plod_envelope():
    lo, hi = frechet.plod_envelope_lr([.5, .5, .5], [.1, .1, .1])
    assert math.isclose(lo, 1.25, rel_tol=1e-12)
    assert math.isclose(hi, 500.0, rel_tol=1e-9)   # a single copula reaches this: 125 is NOT a ceiling


def test_redundancy_interval_exact():
    r = frechet.redundancy_lr([.5, .5, .5], [.1, .1, .1])
    assert r["floor"] == 5.0 and r["ceiling"] == 125.0     # exact (prod of per-item ratios)
    assert math.isclose(math.log10(r["ceiling"] / r["floor"]), 1.3979400086720377, rel_tol=1e-12)


def test_redundancy_floor_is_from_marginals_not_max_lr():
    # unequal marginals: comonotone floor = min(p_H)/min(p_notH) = 0.4/0.1 = 4.0,
    # NOT max(LRs)=5. This pins the fix the adversarial verify demanded.
    r = frechet.redundancy_lr([.5, .4], [.1, .1])
    assert r["floor"] == 4.0 and r["ceiling"] == 20.0


def test_redundancy_and_measured_below_1_do_not_invert():
    # LR<1 (evidence AGAINST H) is the ONLY regime where comonotone > independent; the
    # sorted() guard must keep floor<=ceiling, and the measured point / honest_bound must
    # anchor on comonotone (full redundancy), NEVER the multiplied product.
    r = frechet.redundancy_lr([0.05, 0.05], [0.1, 0.1])   # two LR=0.5 lines
    assert r["floor"] == 0.25 and r["ceiling"] == 0.5     # sorted; NOT (0.5, 0.25)
    assert r["floor"] <= r["ceiling"]
    v = frechet.frechet_verdict([0.5, 0.5, 0.5], shared_upstream=True, n_eff=1.0)
    assert v["interval_lr"][0] <= v["interval_lr"][1]     # never an inverted interval
    assert v["width_decades"] >= 0.0                       # never a negative width
    assert v["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"    # 3 redundant lines, span 0.602 > 0.5
    assert v["measured"]["lr"] == 0.5                      # full redundancy = one line, NOT 0.5^3 = 0.125
    assert v["honest_bound_lr"] == 0.5                     # the cap is one line, never the product


def test_nested_regimes_invariant():
    # the honesty invariant: redundancy model ⊂ PLOD envelope ⊂ full-agnostic bound
    pH, pN = [.5, .5, .5], [.1, .1, .1]
    r = frechet.redundancy_lr(pH, pN)
    pl_lo, pl_hi = frechet.plod_envelope_lr(pH, pN)
    ff_lo, ff_hi = frechet.full_frechet_lr(pH, pN)
    assert pl_lo <= r["floor"] and r["ceiling"] <= pl_hi          # [5,125] ⊂ [1.25,500]
    assert ff_lo <= pl_lo and pl_hi <= ff_hi                       # [1.25,500] ⊂ [0,∞]


def test_effective_count_dial():
    assert frechet.effective_count_lr(5, 125, 3, 1) == 5.0        # comonotone / full redundancy
    assert frechet.effective_count_lr(5, 125, 3, 3) == 125.0      # independent
    assert math.isclose(frechet.effective_count_lr(5, 125, 3, 2), 25.0, rel_tol=1e-12)
    # measured-n_eff sensitivity refs (float path == LR**m to ~1e-6)
    assert math.isclose(frechet.effective_count_lr(5, 125, 3, 1.0598130841121496), 5.505256470101931, rel_tol=1e-6)
    assert math.isclose(frechet.effective_count_lr(5, 125, 3, 1.631728341163212), 13.820664587174196, rel_tol=1e-6)
    assert frechet.effective_count_lr(5, 5, 1, 99) == 5.0         # k<=1 guard: no ZeroDivisionError
    assert frechet.effective_count_lr(5, 125, 3, 5) == 125.0      # m>k clamps to ceiling (never above independent)
    assert frechet.effective_count_lr(5, 125, 3, 0) == 5.0        # m<1 clamps to floor (never below comonotone)


# --- n_eff uncertainty: the bootstrap CI on φ̄ (the removed p-box's replacement) --

@needs_runs
def test_bootstrap_ci_encloses_point_and_is_deterministic():
    # the min/max single-pair p-box was REMOVED (draft-entry#8/#15); the honest
    # dependence-structure uncertainty is a bootstrap CI on φ̄ that brackets φ̄.
    for name in ("homogeneous-control", "clean-diverse", "glm-diverse", "heterogeneous"):
        d = json.loads((RUNS / f"{name}.json").read_text())
        vectors = d["assertion"]["vectors"]
        r = neff.neff_from_matrix(vectors)
        ci = r["bootstrap_ci"]
        assert ci is not None
        assert ci == neff.neff_from_matrix(vectors)["bootstrap_ci"]     # deterministic (seeded)
        assert ci["phi_bar_lo"] <= r["phi_bar"] <= ci["phi_bar_hi"] + 1e-9
        assert ci["n_eff_lo"] <= ci["n_eff_hi"]


@needs_runs
def test_homogeneous_control_ci_pins_full_redundancy():
    d = json.loads((RUNS / "homogeneous-control.json").read_text())
    r = neff.neff_from_matrix(d["assertion"]["vectors"])
    # 9 byte-identical assessors -> φ̄ = 1, every resample stays at 1 -> CI includes 1
    assert r["bootstrap_ci"]["includes_one"] is True


def test_pbox_removed():
    # the min/max p-box is gone; the name must not resurrect
    assert not hasattr(frechet, "neff_pbox")


# --- the verdict ------------------------------------------------------------

def test_verdict_trio_refuses():
    v = frechet.frechet_verdict([5, 5, 5], shared_upstream=True, n_eff=1.0)
    assert v["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"
    assert v["regime"] == "REDUNDANT"
    assert v["interval_lr"] == [5.0, 125.0]
    assert v["honest_bound_lr"] == 5.0 and v["naive_lr"] == 125.0
    assert math.isclose(v["width_decades"], 1.3979400086720377, rel_tol=1e-12)
    assert v["full_frechet_lr"] == [0.0, "inf"]
    assert v["measured"]["lr"] == 5.0 and v["measured"]["posterior"] == 0.8333333333333334


def test_verdict_contrast_combines():
    v = frechet.frechet_verdict([5, 4], shared_upstream=False)
    assert v["verdict"] == "COMBINABLE-WITH-INTERVAL"
    assert v["regime"] == "INDEPENDENT"
    assert v["point_lr"] == 20.0
    assert v["point_posterior"] == 0.9523809523809523
    assert v["width_decades"] == 0.0


def test_verdict_double_count_refuses():
    # the textbook "don't count the same thing twice": two shared-upstream LR=5 lines
    v = frechet.frechet_verdict([5, 5], shared_upstream=True)
    assert v["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"
    assert math.isclose(v["width_decades"], 0.6989700043360189, rel_tol=1e-12)


def test_verdict_boundary_is_strict_inequality():
    # pin the headline knob: width EXACTLY == max_width_decades COMBINES (the decision is a
    # strict `>`); a hair tighter REFUSES. No other verdict test sits on the boundary, so a
    # `>`<->`>=` slip or an off-by-epsilon width refactor would otherwise ship silently.
    bnd = math.log10(25.0)   # == the trio width_decades, log10(125/5), bit-exact
    at = frechet.frechet_verdict([5, 5, 5], shared_upstream=True, max_width_decades=bnd)
    assert at["width_decades"] == at["max_width_decades"]        # genuinely on the boundary
    assert at["verdict"] == "COMBINABLE-WITH-INTERVAL"           # at-threshold -> combine
    tighter = frechet.frechet_verdict([5, 5, 5], shared_upstream=True,
                                      max_width_decades=math.nextafter(bnd, 0.0))
    assert tighter["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"    # a hair tighter -> refuse


# --- dev/cairn#37 finding 4: NaN/Inf fail closed at the boundary ------------

def test_nan_width_knob_does_not_launder_a_refusal():
    # `width > nan` is False, so a NaN threshold used to flip a trio that must refuse
    # (width 1.4 > 0.5) into a vacuous COMBINABLE. Now the input is rejected outright.
    with pytest.raises(ValueError):
        frechet.frechet_verdict([5, 5, 5], shared_upstream=True, max_width_decades=float("nan"))


def test_nan_or_inf_lr_is_rejected():
    for bad in (float("nan"), float("inf")):
        with pytest.raises(ValueError):
            frechet.frechet_verdict([5, bad, 5], shared_upstream=True)


def test_nonpositive_lr_is_rejected():
    # a likelihood ratio must be strictly positive
    with pytest.raises(ValueError):
        frechet.frechet_verdict([5, 0.0, 5], shared_upstream=True)


def test_out_of_domain_prior_and_base_neg_rejected():
    with pytest.raises(ValueError):
        frechet.frechet_verdict([5, 5], shared_upstream=True, prior=1.5)
    with pytest.raises(ValueError):
        frechet.frechet_verdict([5, 5], shared_upstream=True, base_neg=0.0)     # base_neg in (0,1)
    with pytest.raises(ValueError):
        frechet.frechet_verdict([5, 5], shared_upstream=True, n_eff=float("nan"))


@needs_fixtures
def test_cli_nan_width_fails_closed_exit_2(capsys):
    # the same NaN attack through the CLI: exit non-zero, no vacuous point emitted.
    code = cli.main(["frechet", str(FX / "*.json"),
                     "--claims", "claim-geographic-clustering", "claim-environmental-sampling",
                     "claim-live-mammal-sales", "--max-width-decades", "nan"])
    assert code == 2
    assert "rejected input" in capsys.readouterr().err


# --- CLI exit-code contract (mirrors intersect: 0 combine / 2 refuse) -------

@needs_fixtures
def test_cli_trio_refuses_exit_2(capsys):
    code = cli.main([
        "frechet",
        str(FX / "claim-geographic-clustering.json"),
        str(FX / "claim-environmental-sampling.json"),
        str(FX / "claim-live-mammal-sales.json"),
        str(FX / "src-worobey-2022.json"),
    ])
    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"
    assert out["honest_bound_lr"] == 5.0
    assert out["provenance"]["verdict"] == "REFUSE-TO-COMBINE"


@needs_fixtures
def test_cli_contrast_refuses_on_honest_dag_exit_2(capsys):
    # flf-contest#5: geographic-clustering × two-lineages was the false COMBINABLE. On the
    # honest DAG (Pekar's citation + calibration edges) it REFUSES as a point → exit 2.
    code = cli.main([
        "frechet",
        str(FX / "claim-geographic-clustering.json"),
        str(FX / "claim-two-lineages.json"),
        str(FX / "src-worobey-2022.json"),
        str(FX / "src-pekar-2022.json"),
    ])
    assert code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "REFUSE-TO-COMBINE-AS-POINT"
    assert out["provenance"]["verdict"] == "REFUSE-TO-COMBINE"


@needs_fixtures
def test_cli_naive_contrast_still_combines_exit_0(capsys):
    # The cautionary run one command apart: on the document-level DAG the pair COMBINES.
    code = cli.main(["frechet", str(FX / "naive" / "*.json"),
                     "--claims", "claim-geographic-clustering", "claim-two-lineages"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "COMBINABLE-WITH-INTERVAL"
    assert out["point_lr"] == 20.0


@needs_fixtures
def test_cli_cern_combinable_exit_0(capsys):
    # flf-contest#6: the genuine COMBINABLE the engine must emit — CERN Hawking × WD/NS.
    code = cli.main(["frechet", str(FX / "*.json"),
                     "--claims", "claim-cern-hawking-evaporation", "claim-cern-wd-ns-bound"])
    assert code == 0
    out = json.loads(capsys.readouterr().out)
    assert out["verdict"] == "COMBINABLE-WITH-INTERVAL"
    assert out["point_lr"] == 20.0


# --- determinism: the pinned artifact recomputes exactly --------------------

@needs_runs
@needs_fixtures
def test_artifact_recompute():
    from assessment.build_frechet import build
    assert ART.exists(), "assessment/frechet.json not pinned (run assessment/build_frechet.py)"
    committed = json.loads(ART.read_text())
    assert build() == committed        # model-free recompute is byte/dict-equal to what was pinned

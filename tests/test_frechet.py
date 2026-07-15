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


# --- n_eff p-box ------------------------------------------------------------

@needs_runs
@pytest.mark.parametrize("name,exp_lo,exp_hi", [
    ("homogeneous-control", 1.0, 1.0),
    ("clean-diverse", 1.0, 1.3404255319148937),
    ("glm-diverse", 1.0, 1.1351878526059485),   # kish(9, sqrt(3)/2), full precision (not 6-dp-rounded)
    ("heterogeneous", 1.0, 9.0),
])
def test_pbox_endpoints(name, exp_lo, exp_hi):
    d = json.loads((RUNS / f"{name}.json").read_text())
    k = d["assertion"]["neff"]["k"]
    box = frechet.neff_pbox(d["assertion"]["pairwise_phi"], k)
    assert box["n_eff_lo"] == exp_lo
    assert math.isclose(box["n_eff_hi"], exp_hi, rel_tol=1e-12)   # exact pin (all four rows)
    # enclosure guarantee: the pinned point n_eff is inside its own box
    pinned = d["assertion"]["neff"]["n_eff_capped"]
    assert box["n_eff_lo"] - 1e-9 <= box["point"] <= box["n_eff_hi"] + 1e-9
    assert math.isclose(box["point"], pinned, rel_tol=1e-6)


@needs_runs
def test_pbox_heterogeneous_cap_is_disclosed():
    d = json.loads((RUNS / "heterogeneous.json").read_text())
    box = frechet.neff_pbox(d["assertion"]["pairwise_phi"], d["assertion"]["neff"]["k"])
    assert box["n_eff_hi"] == 9.0                     # capped at k
    assert box["n_eff_hi_uncapped"] > 9.0             # the honest cap artifact is surfaced (~11.36)
    assert box["width"] == pytest.approx(8.0)         # wide == untrustworthy


@needs_runs
def test_pbox_ordering_mechanizes_the_audit():
    def width(name):
        d = json.loads((RUNS / f"{name}.json").read_text())
        return frechet.neff_pbox(d["assertion"]["pairwise_phi"], d["assertion"]["neff"]["k"])["width"]
    # heterogeneous (partition-starved, audit-flagged) is far wider than clean-diverse
    assert width("heterogeneous") > width("clean-diverse") > width("homogeneous-control")
    assert width("homogeneous-control") == 0.0


def test_pbox_k1_no_crash():
    assert frechet.neff_pbox([], 1) == {
        "phi_support": [1.0, 1.0], "n_eff_lo": 1.0, "n_eff_hi": 1.0,
        "n_eff_hi_uncapped": 1.0, "width": 0.0, "point": 1.0,
    }


def test_pbox_inversion_and_cap_hermetic():
    # fixture-INDEPENDENT oracle for the p-box inversion + cap-at-k (the @needs_runs
    # tests skip on a runs-less machine). kish_neff is DECREASING in phi, so the box
    # endpoints invert (lo <- phi_MAX, hi <- phi_MIN); BOTH cap at k.
    box = frechet.neff_pbox([0.2, 0.8], 3)                      # cap does not bite (kish(3,0.2)=2.14 < 3)
    assert box["n_eff_lo"] == neff.kish_neff(3, 0.8)            # lo from phi_max
    assert box["n_eff_hi"] == min(3.0, neff.kish_neff(3, 0.2))  # hi from phi_min
    assert box["n_eff_lo"] < box["n_eff_hi"]                    # never inverted
    capped = frechet.neff_pbox([-0.05, 1.0], 9)                 # cap bites: kish(9,-0.05)=15.0 > k
    assert capped["n_eff_lo"] == 1.0 and capped["n_eff_hi"] == 9.0
    assert capped["n_eff_hi_uncapped"] == neff.kish_neff(9, -0.05)   # honest cap artifact surfaced
    assert capped["n_eff_lo"] <= capped["point"] <= capped["n_eff_hi"] and capped["width"] >= 0
    allneg = frechet.neff_pbox([-0.5, -0.5], 2)                 # BOTH endpoints cap (the F1 fix)
    assert allneg["n_eff_lo"] <= allneg["point"] <= allneg["n_eff_hi"] and allneg["width"] >= 0


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

import math

import pytest

from cairn.neff import (
    bootstrap_phi_ci,
    eigenvalue_ess,
    is_degenerate,
    kish_neff,
    mean_phi,
    neff_from_matrix,
    phi,
)


def test_published_anchor_nine_judges_two_votes():
    # "Nine Judges, Two Effective Votes" (arXiv:2605.29800): k=9 -> n_eff ~= 2.2,
    # which the Kish clustering ESS reaches at phi_bar ~= 0.386.
    assert math.isclose(kish_neff(9, 0.386), 2.2, abs_tol=0.01)


def test_kish_endpoints():
    assert kish_neff(1, 0.5) == 1.0
    assert kish_neff(5, 0.0) == 5.0          # independent -> n_eff == k
    assert kish_neff(5, 1.0) == 1.0          # identical -> n_eff == 1
    assert kish_neff(2, -1.0) == 2.0         # anti-correlated guard caps at k


def test_phi_known_values():
    assert phi([1, 1, 0, 0], [1, 1, 0, 0]) == 1.0       # identical
    assert phi([1, 1, 0, 0], [0, 0, 1, 1]) == -1.0      # opposite
    assert phi([1, 1, 0, 0], [1, 0, 1, 0]) == 0.0       # orthogonal


def test_phi_constant_is_nan_not_zero():
    # THE GATE FIX: a constant vector's correlation is UNDEFINED, not 0.0. Coding it 0
    # would score a do-nothing assessor as maximally independent (inflates n_eff).
    assert math.isnan(phi([1, 1, 1, 1], [1, 0, 1, 0]))
    assert math.isnan(phi([0, 0, 0, 0], [1, 0, 1, 0]))
    assert math.isnan(phi([0, 0, 0, 0], [0, 0, 0, 0]))


def test_is_degenerate():
    assert is_degenerate([0, 0, 0])
    assert is_degenerate([1, 1, 1])
    assert not is_degenerate([1, 0, 1])


def test_identical_assessors_collapse_to_one():
    r = neff_from_matrix([[1, 0, 1, 0]] * 3)
    assert not r["degenerate"]
    assert math.isclose(r["phi_bar"], 1.0)
    assert math.isclose(r["n_eff"], 1.0)


def test_orthogonal_assessors_reach_k():
    # three pairwise-orthogonal balanced vectors (Hadamard rows) -> phi_bar 0 -> n_eff k
    vectors = [[1, 0, 1, 0], [1, 1, 0, 0], [1, 0, 0, 1]]
    r = neff_from_matrix(vectors)
    assert math.isclose(r["phi_bar"], 0.0, abs_tol=1e-12)
    assert math.isclose(r["n_eff"], 3.0)


def test_capped_never_exceeds_k():
    r = neff_from_matrix([[1, 0, 1, 0], [0, 1, 0, 1]])  # anti-correlated
    assert r["n_eff_capped"] == 2.0


# --- the degeneracy gate ----------------------------------------------------

def test_degenerate_assessors_excluded_with_k_reduction():
    # two engaged assessors + one that affirmed nothing. The constant one is EXCLUDED
    # (k 3 -> k_effective 2), NEVER coded phi=0 and counted as an independent vote.
    r = neff_from_matrix([[1, 0, 1, 0], [1, 1, 0, 0], [0, 0, 0, 0]])
    assert r["degenerate"] is True
    assert r["excluded"] == [2]
    assert r["k"] == 3 and r["k_effective"] == 2
    assert r["n_eff"] <= 2.0                       # over the retained pair, not 3
    assert r["inert"] is False


def test_wholly_degenerate_panel_is_inert_not_ceiling():
    # THE FALSIFIED CONTROL: every assessor affirmed nothing. The old guard returned
    # n_eff = k (the CEILING). The fix reports the instrument inert (n_eff undefined).
    r = neff_from_matrix([[0, 0, 0, 0], [0, 0, 0, 0]])
    assert r["inert"] is True
    assert r["degenerate"] is True
    assert r["k"] == 2 and r["k_effective"] == 0
    assert r["n_eff"] is None and r["phi_bar"] is None
    assert r["kish_ess"] is None and r["eigenvalue_ess"] is None


def test_single_engaged_assessor_is_one_vote():
    r = neff_from_matrix([[1, 0, 1, 0], [0, 0, 0, 0], [1, 1, 1, 1]])
    assert r["k_effective"] == 1
    assert r["n_eff"] == 1.0 and r["kish_ess"] == 1.0
    assert r["phi_bar"] is None


# --- eigenvalue ESS ---------------------------------------------------------

def test_eigenvalue_ess_endpoints():
    # identical vectors -> rank-1 correlation -> lambda_max = k -> ESS = 1
    assert math.isclose(eigenvalue_ess([[1, 0, 1, 0]] * 3), 1.0, rel_tol=1e-9)
    # orthogonal vectors -> identity correlation -> lambda_max = 1 -> ESS = k
    ortho = [[1, 0, 1, 0], [1, 1, 0, 0], [1, 0, 0, 1]]
    assert math.isclose(eigenvalue_ess(ortho), 3.0, rel_tol=1e-6)


def test_eigenvalue_ess_matches_kish_for_k2():
    # for k=2 the correlation matrix eigenvalues are 1 +/- phi, so ESS = 2/(1+phi) = Kish
    v = [[1, 0, 1, 1, 0, 0], [1, 0, 0, 1, 0, 1]]
    pb = mean_phi(v)
    assert math.isclose(eigenvalue_ess(v), kish_neff(2, pb), rel_tol=1e-9)


def test_eigenvalue_ess_excludes_degenerate():
    assert eigenvalue_ess([[0, 0, 0, 0], [0, 0, 0, 0]]) is None


# --- bootstrap CI on phi_bar ------------------------------------------------

def test_bootstrap_ci_is_deterministic_and_brackets_point():
    v = [[1, 0, 1, 0, 1, 0, 1, 0], [1, 1, 0, 0, 1, 1, 0, 0], [1, 0, 0, 1, 1, 0, 0, 1]]
    a = bootstrap_phi_ci(v)
    b = bootstrap_phi_ci(v)
    assert a == b                                  # deterministic (seeded)
    assert a["phi_bar_lo"] <= mean_phi(v) <= a["phi_bar_hi"] + 1e-9
    assert a["n_eff_lo"] <= a["n_eff_hi"]


def test_bootstrap_ci_flags_full_redundancy():
    # identical assessors -> every resample gives phi 1 -> CI is [1,1], includes_one True
    ci = bootstrap_phi_ci([[1, 0, 1, 1, 0], [1, 0, 1, 1, 0]])
    assert ci["includes_one"] is True
    assert math.isclose(ci["phi_bar_hi"], 1.0)


def test_bootstrap_ci_none_when_too_few():
    assert bootstrap_phi_ci([[1, 0, 1, 0]]) is None            # one assessor
    assert bootstrap_phi_ci([[0, 0], [0, 0]]) is None          # all degenerate


# ---------------------------------------------------------------------------
# dev/cairn#37 — eigenvalue / cap / input-validation (adversarial)
# ---------------------------------------------------------------------------

def _pair_with_phi(target):
    """A concrete binary pair whose φ equals ``target`` (searched, so the test is honest)."""
    import itertools
    for la in itertools.product([0, 1], repeat=6):
        for lb in itertools.product([0, 1], repeat=6):
            if len(set(la)) > 1 and len(set(lb)) > 1 and math.isclose(phi(list(la), list(lb)), target, abs_tol=1e-12):
                return [list(la), list(lb)]
    raise AssertionError(f"no binary pair with phi={target}")


def test_eigenvalue_ess_negative_correlation_is_correct():
    # dev/cairn#37 finding 5: power iteration from the all-ones vector returned λ_MIN for a
    # negative-correlation pair (all-ones IS the sub-dominant eigenvector), reporting 3.0
    # where the truth is k/λ_max = 2/(1+1/3) = 1.5. Jacobi diagonalization gets it right.
    v = _pair_with_phi(-1.0 / 3.0)
    assert math.isclose(eigenvalue_ess(v), 1.5, rel_tol=1e-9)


def test_eigenvalue_ess_perfect_anticorrelation_is_one():
    # anti-correlated pair: λ_max = 2, so ESS = k/λ_max = 1.0 (old bug returned 2.0).
    assert math.isclose(eigenvalue_ess([[1, 0, 1, 0], [0, 1, 0, 1]]), 1.0, rel_tol=1e-9)


def test_eigenvalue_ess_block_matrix_via_lambda_max():
    # a 3-vector panel with mixed-sign correlations (an indefinite sample matrix): the
    # eigenvalues must sum to the trace (k=3) and λ_max must be the true maximum.
    from cairn.neff import _jacobi_eigenvalues, _lambda_max
    R = [[1.0, 0.9, -0.5], [0.9, 1.0, -0.5], [-0.5, -0.5, 1.0]]
    eigs = _jacobi_eigenvalues(R)
    assert math.isclose(sum(eigs), 3.0, abs_tol=1e-9)          # trace preserved
    assert math.isclose(_lambda_max(R), max(eigs), rel_tol=1e-12)
    assert _lambda_max(R) > 2.0                                 # dominant, not sub-dominant


def test_kish_neff_never_exceeds_k_for_moderate_negative_phi():
    # dev/cairn#37 finding 6: kish_neff(2, -0.4) = 2/0.6 = 3.33 used to exceed the panel.
    assert kish_neff(2, -0.4) == 2.0
    assert kish_neff(9, -0.05) <= 9.0
    # positive-φ values are unaffected (still below k, never touched by the cap)
    assert math.isclose(kish_neff(9, 0.386), 2.2, abs_tol=0.01)


def test_neff_from_matrix_rejects_ragged_panel():
    with pytest.raises(ValueError):
        neff_from_matrix([[1, 0, 1], [1, 0]])


def test_neff_from_matrix_rejects_non_binary():
    with pytest.raises(ValueError):
        neff_from_matrix([[1, 0, 2], [1, 0, 1]])


def test_phi_rejects_non_binary():
    with pytest.raises(ValueError):
        phi([1, 0, 2, 0], [1, 0, 1, 0])

import math

from cairn.neff import kish_neff, mean_phi, neff_from_matrix, phi


def test_published_anchor_nine_judges_two_votes():
    # "Nine Judges, Two Effective Votes" (arXiv:2605.29800): k=9 -> n_eff ~= 2.2,
    # which the Kish formula reaches at phi_bar ~= 0.386.
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
    assert phi([1, 1, 1, 1], [1, 0, 1, 0]) == 0.0       # zero-variance guard -> 0


def test_identical_assessors_collapse_to_one():
    r = neff_from_matrix([[1, 0, 1, 0]] * 3)
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

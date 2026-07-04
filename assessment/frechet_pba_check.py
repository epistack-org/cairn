"""an internal library cross-check: validate cairn's closed-form Fréchet/p-box bounds
against the `pba` (probability-bounds-analysis) library's copula machinery.

This is the roadmap#4 "add pba-for-python as a demo/analysis-layer module" step: an
INDEPENDENT library confirming our hand-rolled Fréchet math. It is deliberately NOT
part of the stdlib-light core or the self-verifying container — `pba` pulls
numpy/scipy/matplotlib, exactly the weight the scored core must not carry. It is
optional: absent `pba`, it skips cleanly (non-fatal).

    pip install pba        # numpy / scipy / matplotlib (dev only)
    python assessment/frechet_pba_check.py
"""
from __future__ import annotations

import warnings

from cairn import frechet as F


def main() -> int:
    try:
        import pba
    except ImportError:
        print("SKIP: pba not installed. `pip install pba` to run the p-box cross-check "
              "(dev-only; the cairn core and container need no such dependency).")
        return 0
    warnings.simplefilter("ignore")  # pba's Frank copula logs a benign divide-by-zero at s=0

    ok = True

    def check(name, got, exp, tol=1e-9):
        nonlocal ok
        good = abs(got - exp) <= tol * max(1.0, abs(exp))
        ok = ok and good
        print(f"  [{'OK' if good else 'XX'}] {name}: pba={got:.6g}  cairn={exp:.6g}")

    print("cairn A3 Fréchet/p-box bounds vs the pba library's copulas (independent oracle)\n")
    M = pba.M()           # comonotone (Fréchet upper):  C(u,v) = min(u,v)
    W = pba.W()           # countermonotone (Fréchet lower): C(u,v) = max(0, u+v-1)
    indep = pba.indep     # independence: C(u,v) = u*v

    # 1. the 2-event Fréchet–Hoeffding conjunction bounds match cairn.world_and_bounds
    print("1. Fréchet–Hoeffding conjunction bounds (pba M / W) vs cairn.world_and_bounds:")
    for a, b in [(0.5, 0.5), (0.1, 0.1), (0.5, 0.4), (0.9, 0.8)]:
        lo_c, hi_c = F.world_and_bounds([a, b])
        check(f"upper P(A^B)<=min({a},{b})", M.get_cdf(a, b), hi_c)
        check(f"lower P(A^B)>=max(0,{a}+{b}-1)", W.get_cdf(a, b), lo_c)

    # 2. the double-count case (k=2 shared LR=5 lines): redundancy floor/ceiling via copulas
    print("\n2. double-count k=2 redundancy interval, endpoints built from pba copulas:")
    pH, pN = (0.5, 0.5), (0.1, 0.1)
    JH_indep, JN_indep = indep(*pH), indep(*pN)
    JH_comon, JN_comon = M.get_cdf(*pH), M.get_cdf(*pN)
    red = F.redundancy_lr(list(pH), list(pN))
    check("ceiling = indep_H / indep_~H", JH_indep / JN_indep, red["ceiling"])   # 25 = 5^2
    check("floor   = comon_H / comon_~H", JH_comon / JN_comon, red["floor"])     # 5

    # 3. the naive product is NOT a ceiling — a positive-dependent coupling exceeds it
    print("\n3. a positive-dependent coupling EXCEEDS the naive product => [floor, naive] is a MODEL, not a bound:")
    lr_plod_hi = JH_comon / JN_indep     # comonotone in H, independent in ~H (a valid positive-dep pairing)
    plod = F.plod_envelope_lr(list(pH), list(pN))
    check("PLOD upper = comon_H / indep_~H", lr_plod_hi, plod[1])                 # 50 > 25
    print(f"     -> pba reaches combined LR={lr_plod_hi:g} > naive product {red['ceiling']:g}: "
          "cairn is right to label the redundancy interval a model, and its floor a cap, not a bound.")

    # 4. a genuine single-parameter positive copula lands between independence and comonotone
    print("\n4. Frank copulas (one positive-dependence parameter) interpolate independence -> comonotone:")
    for s in (5, 15, 30):
        jh = pba.Frank(s=s).get_cdf(*pH)
        inside = JH_indep - 1e-9 <= jh <= JH_comon + 1e-9
        ok = ok and inside
        print(f"     Frank(s={s:>2}): J_H={jh:.4f}  in [indep {JH_indep:.3f}, comon {JH_comon:.3f}]? {inside}")

    print("\n" + ("ALL pba CROSS-CHECKS PASS — an independent p-box library confirms cairn's Fréchet bounds."
                  if ok else "*** pba CROSS-CHECK MISMATCH ***"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

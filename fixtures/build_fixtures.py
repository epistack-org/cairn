"""Mint the vetted COVID-HSM mini-corpus as signed, span-grounded Cairn records.

VETTED corpus (roadmap A1). Unlike the earlier illustrative fixtures, every claim
is **span-grounded to a real, retrieved source** and carries the faithfulness
tuple ``(source_doc, char_span, extractor, entailment_label)`` (internal research notes
toolchest/02; internal notes:122). No record sits at ``unverified-fixture``.

Sources: the byte-exact **abstracts** (version of record) of Worobey 2022 and
Pekar 2022 ship as raw artifacts under ``fixtures/sources/*.abstract.txt`` and are
pinned by SHA-256 below. They were retrieved first-party and confirmed
byte-identical across two independent services (NCBI E-utilities efetch + Europe
PMC REST); see ``fixtures/PROVENANCE.md`` for the full retrieval record, the
Trust-Ladder rung rationale, and two honest vetting decisions (an ungrounded
"ascertainment centroid" line was retired; the two-lineages claim was reworded to
what the abstract entails).

Structural point (REPORT section 7): the proximity trio all derive from ONE
paper (Worobey) -> not three independent votes -> REFUSE-TO-COMBINE.

The molecular two-lineages line (Pekar) was ORIGINALLY shipped as a genuinely
different upstream -> COMBINABLE. That was this entry's own false positive
(flf-contest#5): Pekar CITES Worobey and both rest on the shared PRC early-case
investigation, so on the honest DAG the pair shares a citation edge AND a dataset
edge and must REFUSE. `main()` asserts that refusal — and that it names both
upstreams — before writing a single byte. The old, wrong COMBINABLE is preserved
deliberately under ``fixtures/naive/``: the same claims with the cross-edges
stripped, so `cairn intersect` on naive-vs-honest is the contestability demo.

Deterministic: fixed signing seed + fixed timestamps => stable Trusty URIs.
Self-verifying: asserts grounding resolves + trio refuses + contrast combines.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path

from cairn import envelope, grounding, provenance
from cairn.keys import SigningKey

# Records/INDEX/CASES/naive are written under OUT; excerpts are read from the real
# sources dir. CAIRN_FIXTURES_OUT redirects only the write target (used by the
# determinism gate to regenerate into a temp dir) — default is byte-identical.
_HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("CAIRN_FIXTURES_OUT") or _HERE)

import sys

# Shared minting primitives now live in fixtures/lib/mint.py so per-case bundle builders
# can import them without forking the signing seed / JCS canonicalizer. Run as a script,
# fixtures/ is sys.path[0]; force it on so `import lib.mint` resolves in every context.
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
from lib.mint import (  # noqa: E402
    EXTRACTOR, EXTRACTOR_AMYLOID, EXTRACTOR_BACKTEST, SOURCES,
    load_excerpt, mk, mk_claim, span_of,
)






# --- The worked examples (floor deliverable #3) -------------------------------------
#
# Each case DECLARES its structure here, and `main()` mechanically verifies the
# declaration against what the provenance detector actually finds before writing a
# single file. A case whose `laundered_set` fails to REFUSE, or whose shared upstream
# is not the one the detector names, fails the build. The README's "3 worked examples"
# is therefore a checked property of the corpus, not a sentence in a markdown file.
#
# `n_eff_corpus_scale` records what the Phase-2 corpus run measured for the same crux
# at 2,261-paper scale. It is a REPORTED number for the writeup,
# not an input to anything here — the fixtures stay substrate-free by construction.








import importlib.util

# Per-case builders live in fixtures/cases/<id>/build.py, loaded by path (case-ids contain
# hyphens) in the pinned insertion order that fixes the aggregate INDEX/CASES line order.
# The order is the registry in fixtures/cases/cases.lock — NEVER a filesystem glob (a glob
# is alphabetical, which is not the historical order). Adding a case is a new bundle dir
# plus a reviewed cases.lock edit, not a change here.
CASE_ORDER = json.loads((_HERE / "cases" / "cases.lock").read_text())["order"]


def _load_bundle(case_id):
    path = _HERE / "cases" / case_id / "build.py"
    spec = importlib.util.spec_from_file_location(
        "cases_" + case_id.replace("-", "_") + "_build", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# The case manifest is assembled from each bundle's CASE.json in the pinned order,
# so the aggregate CASES.json (and its line order) stays byte-stable. Adding a case is
# a new bundle dir, not an edit here.
CASES = {cid: json.loads((_HERE / "cases" / cid / "CASE.json").read_text())
         for cid in CASE_ORDER}


def main() -> int:
    recs: dict[str, dict] = {}
    for case_id in CASE_ORDER:
        _load_bundle(case_id).build(recs)

    # --- self-verify before writing: every case's declared structure must actually hold ---
    store = {r["id"]: r for r in recs.values()}
    report = grounding.check_store(store)
    assert report["ok"], ("grounding failed", report["failed"])

    for case_id, case in CASES.items():
        laundered = [recs[s]["id"] for s in case["laundered_set"]]
        v = provenance.combine_verdict(laundered, store)
        assert v["verdict"] == "REFUSE-TO-COMBINE", (case_id, "laundered set did not refuse", v)
        # The declared upstream must be shared by EVERY line, not merely by some pair —
        # that is the actual claim each case makes, so check the collective intersection.
        collective = provenance.shared_upstreams(laundered, store)["collective_shared"]
        shared = recs[case["shared_upstream"]]["id"]
        assert shared in collective, (
            case_id, "the declared shared upstream is not shared by ALL lines",
            case["shared_upstream"], [r for r in collective])
        if case.get("contrast_pair"):
            pair = [recs[s]["id"] for s in case["contrast_pair"]]
            cv = provenance.combine_verdict(pair, store)
            want = case.get("contrast_expected", "COMBINABLE")
            assert cv["verdict"] == want, (case_id, f"contrast pair verdict != {want}", cv)

    # --- the GATE assertion, inverted (dev/cairn / flf-contest#5): Worobey 2022 x Pekar 2022
    #     was the entry's false COMBINABLE. On the honest (derived) DAG it MUST refuse, and the
    #     shared upstream it names must include Worobey 2022 (the citation edge) and the PRC
    #     early-case investigation (the shared dataset). This is the heart of the fix. ---
    wxp = provenance.combine_verdict(
        [recs["claim-geographic-clustering"]["id"], recs["claim-two-lineages"]["id"]], store)
    assert wxp["verdict"] == "REFUSE-TO-COMBINE", ("Worobey x Pekar must REFUSE on the honest DAG", wxp)
    for s in ("src-worobey-2022", "ent-prc-early-case-investigation"):
        assert recs[s]["id"] in wxp["shared_upstreams"], (
            "the honest Worobey x Pekar refusal must name the citation + dataset upstreams", s)

    # --- the genuine COMBINABLE (#6): CERN {Hawking evaporation} x {WD/NS survival}. ---
    cern_combine = provenance.combine_verdict(
        [recs["claim-cern-hawking-evaporation"]["id"], recs["claim-cern-wd-ns-bound"]["id"]], store)
    assert cern_combine["verdict"] == "COMBINABLE", ("CERN Hawking x WD/NS must COMBINE", cern_combine)

    # --- the CERN CONCLUSION-UNCHANGED refusal (#7): the trio shares the cosmic-ray premise, but
    #     the WD/NS bound is upstream-disjoint from the Hawking premise and independently sufficient. ---
    cern_trio = [recs[s]["id"] for s in CASES["cern-black-hole"]["laundered_set"]]
    cern_as_indep = provenance.combine_verdict(
        cern_trio, store,
        backstop=recs["claim-cern-wd-ns-bound"]["id"],
        at_risk_upstream=recs["ent-hawking-radiation-premise"]["id"])
    assert cern_as_indep["verdict"] == "REFUSE-TO-COMBINE-AS-INDEPENDENT", cern_as_indep
    assert cern_as_indep["conclusion_unchanged"] is True, cern_as_indep

    # --- write one file per record + an index + the case manifest ---
    index = {}
    for slug, rec in recs.items():
        (OUT / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        index[slug] = rec["id"]
    (OUT / "INDEX.json").write_text(json.dumps(index, indent=2) + "\n")
    (OUT / "CASES.json").write_text(json.dumps(CASES, indent=2, ensure_ascii=False) + "\n")

    # --- the NAIVE document-level snapshot: the SAME two claims and sources, but with the
    #     dataset/citation/calibration edges REMOVED (each claim derives only from the paper it
    #     was extracted from). This is the cautionary run: on this DAG Worobey x Pekar COMBINES,
    #     exactly as the entry originally (wrongly) shipped. `cairn intersect` on it vs on the
    #     honest corpus above IS the contestability demo (flf-contest#5). Reproducible:
    #        cairn intersect "fixtures/naive/*.json" --claims claim-geographic-clustering claim-two-lineages   # COMBINABLE
    #        cairn intersect "fixtures/*.json"       --claims claim-geographic-clustering claim-two-lineages   # REFUSE
    naive_dir = OUT / "naive"
    naive_dir.mkdir(exist_ok=True)
    naive = {}
    # the two sources, document-level (byte-identical to the honest corpus — sources never carried
    # cross-edges; only the claims did)
    for s in ("src-worobey-2022", "src-pekar-2022"):
        naive[s] = recs[s]
    # the two claims, stripped back to derivedFrom == [grounding.source] (no dataset/citation edge)
    for s in ("claim-geographic-clustering", "claim-two-lineages"):
        a = copy.deepcopy(recs[s]["assertion"])
        a.pop("provenance_note", None)
        naive[s] = mk(s, "epi:Claim", a, derived_from=[a["grounding"]["source"]], method="extract")
    naive_store = {r["id"]: r for r in naive.values()}
    nv = provenance.combine_verdict(
        [naive["claim-geographic-clustering"]["id"], naive["claim-two-lineages"]["id"]], naive_store)
    assert nv["verdict"] == "COMBINABLE", ("naive document-level DAG must still COMBINE Worobey x Pekar", nv)
    naive_index = {}
    for slug, rec in naive.items():
        (naive_dir / f"{slug}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n")
        naive_index[slug] = rec["id"]
    (naive_dir / "INDEX.json").write_text(json.dumps(naive_index, indent=2) + "\n")

    print(f"minted {len(recs)} vetted records across {len(CASES)} worked examples -> {OUT}")
    print(f"  grounding: {report['grounded']}/{report['checked']} claims resolve, ok={report['ok']}")
    for case_id, case in CASES.items():
        print(f"  [{case_id}] shared upstream = {case['shared_upstream']} "
              f"-> REFUSE over {len(case['laundered_set'])} lines"
              + ("" if case.get("contrast_pair") else "  (no combinable contrast — see PROVENANCE)"))
    for slug, rid in index.items():
        print(f"  {slug:32s} {rid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

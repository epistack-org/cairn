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
paper (Worobey) -> not three independent votes -> REFUSE-TO-COMBINE; the molecular
two-lineages line (Pekar) is a genuinely different upstream -> COMBINABLE.

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
CASES = {
    "covid-origins": {
        "title": "COVID origins — the Huanan-market proximity trio",
        "crux": "Did SARS-CoV-2 emerge via zoonotic spillover associated with the Huanan "
                "Seafood Wholesale Market, as opposed to a non-market or non-zoonotic "
                "introduction?",
        "battery": "assessment/probes.json",
        "shared_upstream": "src-worobey-2022",
        "shared_upstream_kind": "one paper / one author collective; at the data layer two of the "
                                "three (geographic clustering, environmental sampling) descend from "
                                "the same market-anchored PRC early-case investigation, and the third "
                                "(live-mammal sales, Xiao 2021) does not",
        "laundered_set": [
            "claim-geographic-clustering",
            "claim-environmental-sampling",
            "claim-live-mammal-sales",
        ],
        # Worobey 2022 x Pekar 2022 was the entry's false COMBINABLE. On the honest DAG the
        # pair REFUSES: Pekar cites Worobey (ref [39], first-person) and calibrates its clock
        # on Worobey 2021, and both rest on the PRC early-case investigation. The naive
        # document-level DAG (fixtures/naive/) still COMBINES them — that contrast IS the demo.
        "contrast_pair": ["claim-geographic-clustering", "claim-two-lineages"],
        "contrast_expected": "REFUSE-TO-COMBINE",
        "punchline": "Three apparently independent lines of proximity evidence come from ONE paper "
                     "by ONE author collective (Worobey 2022); at the data layer two of the three "
                     "descend from the same market-anchored PRC early-case investigation, and the "
                     "third (Xiao 2021) does not. The naive transcript multiplies 5x5x5 = 125:1; the "
                     "provenance intersection collapses to a single upstream, so the product is undefined.",
    },
    "eggs-good-for-you": {
        "title": "Are eggs good for you — the egg/CVD meta-analyses",
        "crux": "Do the several apparently independent meta-analyses finding no association "
                "between egg consumption and cardiovascular disease constitute independent "
                "confirmations of that null result?",
        "battery": "assessment/probes-eggs.json",
        "shared_upstream": "ent-nhs-hpfs-cohorts",
        "shared_upstream_kind": "cohort (one shared participant backbone, TWO HOPS UP)",
        "laundered_set": [
            "claim-eggs-rong-no-association",     # BMJ 2013 meta-analysis
            "claim-eggs-godos-no-association",    # Eur J Nutr 2021 meta-analysis (39 studies)
            "claim-eggs-drouin-no-association",   # BMJ 2020 cohorts + updated meta-analysis
        ],
        "contrast_pair": ["claim-eggs-hu-no-association", "claim-eggs-djousse-no-association"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Three apparently independent reassuring findings — a 2013 BMJ "
                     "dose-response meta-analysis, a 2021 meta-analysis of 39 studies and "
                     "'nearly 2 million individuals', and a 2020 BMJ three-cohort study plus "
                     "updated meta-analysis — all re-pool the SAME nurses and health "
                     "professionals (NHS/HPFS). Each review de-duplicates internally and is "
                     "locally correct; the laundering happens BETWEEN them, at the aggregation "
                     "layer. 'Nearly 2 million individuals' is not 2 million independent people. "
                     "The shared upstream is invisible at the claim level — it is two hops up, "
                     "found only by walking the DAG.",
        "exercises": "the TRANSITIVE shared-ancestor detector — the first real corpus to do so "
                     "(previously proven only against a synthetic fixture in tests)",
    },
    "cern-black-hole": {
        "title": "CERN black hole — the LHC/RHIC safety assurances",
        # The crux is deliberately CONDITIONAL, and that precision is load-bearing.
        # The safety literature runs two distinct argument families:
        #   (A) theoretical — microscopic black holes evaporate (Hawking radiation);
        #   (B) empirical  — the cosmic-ray / astronomical-survival argument.
        # Family (A) is a genuinely separate line (the 2003 LHC Safety Study Group rests
        # its black-hole conclusion on it), so "every assurance shares one premise" would
        # be an OVERCLAIM and we do not make it. But the public concern — and the reason
        # the 2008 reviews were commissioned — is precisely "what if the black hole does
        # NOT decay?". Conditional on (A) failing, everything left standing is (B), and
        # (B) is one argument. That is the crux this case scores.
        "crux": "IF microscopic black holes produced at the LHC do not decay (i.e. conditional "
                "on the Hawking-radiation argument failing), do the collider-safety reviews "
                "constitute multiple INDEPENDENT lines of evidence that they are still harmless?",
        "battery": "assessment/probes-cern.json",
        "shared_upstream": "ent-cosmic-ray-argument",
        "shared_upstream_kind": "premise (one load-bearing empirical argument)",
        "laundered_set": [
            "claim-cern-astro-stability",     # Ellis et al. 2008 (LSAG) — LHC
            "claim-cern-wd-ns-bound",         # Giddings & Mangano 2008 — LHC
            "claim-cern-moon-strangelet",     # Jaffe et al. 2000 — RHIC
        ],
        # The genuine COMBINABLE (#6): the Hawking-radiation evaporation line (QFT premise) and
        # the white-dwarf/neutron-star survival bound (Giddings & Mangano, premised on stable
        # black holes — i.e. on Hawking FAILING) are upstream-disjoint by construction. A hostile
        # reader cannot break it: the papers themselves build the WD/NS argument to survive the
        # failure of the Hawking premise.
        "contrast_pair": ["claim-cern-hawking-evaporation", "claim-cern-wd-ns-bound"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Three safety assurances that look maximally independent — three papers, "
                     "two accelerators, three author teams, eight years apart, three different "
                     "hypothetical catastrophes — all reach 'safe' through ONE premise: cosmic "
                     "rays have hit astronomical bodies harder for billions of years and they "
                     "are still here. Each paper says so in its own abstract. This is the case "
                     "with the STRONGEST expert consensus, and cairn prices it honestly "
                     "(effective independence ~1) rather than rewarding it. It does NOT say the "
                     "LHC is unsafe — it says three assurances sharing a premise are not three votes.",
    },
    "amyloid-abeta56": {
        "title": "Alzheimer's amyloid — the Aβ*56 corroboration cascade",
        # The crux is deliberately NARROW. It is NOT "is the amyloid hypothesis true" and NOT
        # "do soluble Aβ oligomers impair memory" (the contrast line answers YES to a version of
        # that). It is about ONE specific claimed molecular species and whether its repeated
        # "confirmations" are independent.
        "crux": "Do the multiple reports of Aβ*56 — a specific 56-kDa soluble amyloid-β "
                "assembly — as a discrete, memory-impairing species constitute independent "
                "confirmations that this species exists and is pathogenic?",
        "battery": "assessment/probes-amyloid.json",
        "shared_upstream": "ent-abeta56",
        "shared_upstream_kind": "a lab-defined molecular species + its detection assay whose sole "
                                "originating characterization is one paper — Lesné et al. 2006 "
                                "(Nature), RETRACTED in 2024 — carried forward by the same lab "
                                "(Ashe/Lesné, U Minnesota). A shared foundational-result AND "
                                "shared-reagent upstream at once.",
        "laundered_set": [
            "claim-abeta56-impairs-memory",     # Lesné 2006 (Nature, RETRACTED) — the origin, in mice
            "claim-abeta56-human-brain",        # Lesné 2013 (Brain) — Aβ*56 measured in human brain
            "claim-abeta56-detection-method",   # Sherman & Lesné 2011 — the Aβ*56 detection assay itself
        ],
        # The genuine COMBINABLE: Shankar et al. 2008 (Nat Med, Selkoe lab) isolated soluble Aβ
        # DIMERS directly from human Alzheimer's brain — a different species, a different lab, a
        # different preparation, upstream-disjoint from the Aβ*56 lineage. Pairing an Aβ*56 line
        # with it COMBINES: the general "soluble Aβ oligomers are synaptotoxic" claim has support
        # that does NOT route through Lesné 2006. That is the whole point of shipping the contrast
        # — the refusal is about corroboration-COUNTING for one species, not about the hypothesis.
        "contrast_pair": ["claim-abeta56-impairs-memory", "claim-shankar-dimers"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Aβ*56 became one of the most-cited soluble-oligomer results in the field. But "
                     "the species was defined in exactly one paper (Lesné 2006), by one lab, using "
                     "one detection assay; the human-brain measurement (Lesné 2013) and the "
                     "methods paper (Sherman 2011) are the SAME lab operationalizing the SAME "
                     "originating characterization — not two more independent confirmations. In "
                     "2024 Nature RETRACTED the 2006 paper over image-integrity concerns; the "
                     "corroboration cascade did not un-happen when it did. cairn refuses to count "
                     "three reports of Aβ*56 as three independent votes and names the shared "
                     "upstream. It does NOT say Aβ oligomers are harmless — the Shankar 2008 "
                     "human-brain dimer line is upstream-disjoint and COMBINES.",
        "exercises": "a shared upstream that is simultaneously a foundational RESULT and a "
                     "shared REAGENT/ASSAY, with the originating source formally RETRACTED after "
                     "the fact — the sharpest real-world 'the anchor moved and the citations "
                     "didn't' exhibit in the corpus",
    },
    "ivermectin-elgazzar": {
        "title": "Ivermectin for COVID-19 — the Elgazzar-fabricated meta-analysis cascade",
        # NARROW crux. NOT "does ivermectin work" and NOT "is ivermectin fraudulent". It is about
        # whether the several positive mortality meta-analyses are INDEPENDENT confirmations.
        "crux": "Do the multiple ivermectin meta-analyses reporting a large COVID-19 mortality "
                "reduction constitute independent confirmations of that mortality benefit?",
        "battery": "assessment/probes-ivermectin.json",
        "shared_upstream": "src-elgazzar-2020",
        "shared_upstream_kind": "one fabricated primary trial (the Elgazzar preprint, Research "
                                "Square, WITHDRAWN 2021-07-14), TWO HOPS UP: each positive "
                                "synthesis pooled it, and it carried the largest weight and the "
                                "largest effect. Removing it collapses the pooled mortality signal "
                                "(the published counterfactual: Hill 2021, later retracted).",
        "laundered_set": [
            "claim-iver-bryant",   # Am J Ther 2021 meta (RR 0.38); Expression of Concern
            "claim-iver-zein",     # Diab Metab Syndr 2021 meta (RR 0.39) — the SAME signal, different authors
            "claim-iver-kory",     # Am J Ther 2021 FLCCC review; Expression of Concern
        ],
        # TOGETHER (Reis 2022, NEJM) is a large independent RCT that never ingested Elgazzar. It is
        # upstream-disjoint from the Elgazzar node, so an Elgazzar-based meta and TOGETHER COMBINE:
        # TOGETHER really is a distinct evidential draw. (It happens to be null — the verdict is
        # about provenance-independence, not agreement, which is exactly the discipline to show.)
        "contrast_pair": ["claim-iver-bryant", "claim-iver-together"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Several meta-analyses reported ivermectin roughly halving COVID-19 mortality — "
                     "Bryant 2021 (RR 0.38), Zein 2021 (RR 0.39), and the FLCCC review (Kory 2021) — "
                     "which looks like independent replication. It is not: all three pooled the same "
                     "single fabricated trial (Elgazzar, Research Square), which carried the largest "
                     "weight and the largest effect; when it was WITHDRAWN on 2021-07-14 the pooled "
                     "signal collapsed (Hill 2021, which had leaned on it, went null and was itself "
                     "retracted). The naive reading multiplies three ~5:1 likelihoods to ~100:1; the "
                     "provenance intersection collapses to one upstream, so the product is undefined. "
                     "It does NOT say ivermectin is proven ineffective — TOGETHER (Reis 2022) is an "
                     "upstream-disjoint RCT and COMBINES; the point is that the positive syntheses are "
                     "not independent votes.",
        "exercises": "the highest-fan-out node in the corpus — ONE fabricated primary re-pooled by "
                     "many downstream syntheses (the eggs-style transitive detector, but the shared "
                     "upstream is a retracted/withdrawn fraud rather than a legitimate cohort)",
    },
    "anversa-ckit": {
        "title": "Cardiac stem cells — the Anversa c-kit+ regeneration cascade",
        "crux": "Do the multiple reports that c-kit+ cardiac stem cells regenerate myocardium — "
                "from the rodent origin, to human cells, to the SCIPIO clinical trial — constitute "
                "independent confirmations that such cells regenerate the heart?",
        "battery": "assessment/probes-anversa.json",
        "shared_upstream": "ent-anversa-ckit-csc",
        "shared_upstream_kind": "a lab-defined cell type + its isolation method whose originating "
                                "characterization is one paper (Beltrami et al. 2003, Cell), carried "
                                "forward by the same laboratory (Anversa). Harvard/Brigham "
                                "recommended 31 of the lab's papers for retraction (2018) for "
                                "falsified/fabricated data; the flagship human trial SCIPIO was "
                                "RETRACTED (Lancet 2019) and used the lab's own cell preps — a "
                                "literal shared-reagent dependency.",
        "laundered_set": [
            "claim-anversa-origin",    # Beltrami 2003 (Cell) — c-kit+ cells reconstitute ~70% of infarcted ventricle (rodent)
            "claim-anversa-human",     # Bearzi 2007 (PNAS) — human c-kit+ CSCs generate human myocardium
            "claim-anversa-scipio",    # Bolli 2011 (Lancet, RETRACTED) — SCIPIO: autologous CSCs improve LVEF in patients
        ],
        # CADUCEUS (Makkar 2012, Lancet) used cardiosphere-derived cells (CDCs) — a different cell
        # type, a different laboratory (Marbán, Cedars-Sinai), a different preparation, with no
        # derivation from the Anversa c-kit+ characterization. An Anversa line and the CADUCEUS
        # line COMBINE: cardiac-regeneration evidence exists that does NOT route through Anversa.
        "contrast_pair": ["claim-anversa-origin", "claim-anversa-caduceus"],
        "contrast_expected": "COMBINABLE",
        "punchline": "The c-kit+ cardiac stem cell — an adult heart cell claimed to regenerate "
                     "myocardium — looked confirmed from rodent (Beltrami 2003) to human cells "
                     "(Bearzi 2007) to a phase-1 trial in patients (SCIPIO, Bolli 2011). But all "
                     "three descend from ONE laboratory's originating characterization and its "
                     "isolation method; SCIPIO used that lab's own cell preps. Harvard and the "
                     "Brigham later found falsified/fabricated data across the lab and pressed for 31 "
                     "retractions; SCIPIO was retracted in 2019. cairn refuses to count the three as "
                     "independent votes and names the shared Anversa c-kit+ characterization. It does "
                     "NOT say the heart cannot be repaired — CADUCEUS (cardiosphere-derived cells, a "
                     "different lab and cell type) is upstream-disjoint and COMBINES.",
        "exercises": "the amyloid node type again (a lab-defined object + its assay, origin source at "
                     "the root) but with the meta-fact carried as an INSTITUTIONAL misconduct finding "
                     "plus one retracted downstream node — not a retraction stamp on the origin paper",
    },
    "poldermans-decrease": {
        "title": "Perioperative beta-blockers — the Poldermans/DECREASE cascade that flips sign",
        "crux": "Do the trials and studies supporting perioperative beta-blockade to prevent "
                "cardiac death in non-cardiac surgery constitute independent evidence of that "
                "benefit?",
        "battery": "assessment/probes-poldermans.json",
        "shared_upstream": "ent-decrease-program",
        "shared_upstream_kind": "one research program (the DECREASE family of trials + the "
                                "Erasmus MC vascular-surgery database, run by the Poldermans group). "
                                "A 2011-2012 Erasmus MC investigation found the DECREASE trials "
                                "contained fabricated/fictitious data — an INSTITUTIONAL misconduct "
                                "finding, not a per-node retraction stamp.",
        "laundered_set": [
            "claim-decrease-1",        # DECREASE-I (Poldermans 1999, NEJM) — bisoprolol cuts cardiac death/MI
            "claim-decrease-boersma",  # Boersma 2001 (JAMA) — the DECREASE screening cohort, beta-blocker benefit
            "claim-decrease-4",        # DECREASE-IV (Dunkelgrun 2009, Ann Surg) — bisoprolol benefit, intermediate-risk
        ],
        # POISE (Devereaux 2008, Lancet; 8351 patients) is a large independent RCT, upstream-disjoint
        # from the DECREASE program. A DECREASE benefit claim and the POISE result COMBINE: POISE is a
        # genuinely distinct evidential draw. It happens to point the OTHER way (metoprolol cut MI but
        # INCREASED death) — and once the fabricated DECREASE lineage is removed, the pooled effect
        # flips sign entirely: Bouri 2014's DECREASE-excluded "secure trials" meta finds a 27% mortality
        # INCREASE. The sharpest counterfactual in the corpus: removing the fraud does not just weaken
        # the signal, it reverses it.
        "contrast_pair": ["claim-decrease-1", "claim-poise"],
        "contrast_expected": "COMBINABLE",
        "punchline": "Perioperative beta-blockade to prevent cardiac death entered guidelines on a "
                     "wall of apparent evidence: DECREASE-I (Poldermans 1999), the Boersma 2001 cohort, "
                     "DECREASE-IV (Dunkelgrun 2009), and more. But that wall is one research program — "
                     "the Poldermans/Erasmus DECREASE family — which a 2011-2012 institutional "
                     "investigation found to rest on fabricated data. cairn refuses to count the "
                     "program's outputs as independent votes and names the shared DECREASE upstream. "
                     "The independent evidence points the other way: POISE (Devereaux 2008), an "
                     "upstream-disjoint RCT, COMBINES — and Bouri 2014's DECREASE-excluded meta finds a "
                     "27% mortality INCREASE. Removing the fabricated lineage does not merely weaken the "
                     "pooled result; it flips its sign from benefit to harm.",
        "exercises": "the eggs node type (a shared research program / dataset backbone at the root, "
                     "found without any single origin paper) carrying an institutional-misconduct "
                     "meta-fact — and the only case where the honest counterfactual REVERSES the "
                     "conclusion rather than just deflating the vote count",
    },
}








import importlib.util

# Per-case builders now live in fixtures/cases/<id>/build.py, loaded by path (case-ids
# contain hyphens) in the pinned insertion order that fixes the aggregate INDEX/CASES
# line order. Never derive this order from a filesystem glob.
CASE_ORDER = [
    "covid-origins",
    "eggs-good-for-you",
    "cern-black-hole",
    "amyloid-abeta56",
    "ivermectin-elgazzar",
    "anversa-ckit",
    "poldermans-decrease",
]


def _load_bundle(case_id):
    path = _HERE / "cases" / case_id / "build.py"
    spec = importlib.util.spec_from_file_location(
        "cases_" + case_id.replace("-", "_") + "_build", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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

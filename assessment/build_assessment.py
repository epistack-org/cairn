"""Turn captured assessor votes into pinned, minted Cairn records — and verify.

Input   assessment/raw_votes.json   the instrument reading (committed as audit trail):
          {captured_at, heterogeneous:[{id, answers:{probe_id: YES|NO|UNCERTAIN}}], control:[...]}
Output  assessment/runs/
          battery.json              epi:Schema      the probe-battery instrument
          assessments.json          [epi:Assessment] one signed record per assessor (both panels)
          heterogeneous.json        epi:Cluster     the measured heterogeneous panel (headline n_eff)
          homogeneous-control.json  epi:Cluster     the correlated baseline

Every assessment's provenance.derivedFrom = the SOURCE ids it was actually granted,
so the A1 refuse-to-combine engine explains the measured correlation structurally:
assessors that shared evidence share an upstream. Self-verifies (schema + id/sig +
`cairn assess` recompute) before writing. Deterministic given raw_votes.json.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import panel
from cairn import assessment, envelope
from cairn.keys import SigningKey

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "assessment" / "runs"
RAW = ROOT / "assessment" / "raw_votes.json"

CORPUS_KEY = SigningKey.from_seed_hex("c0" * 32, "keystone:epistack-corpus")
AT = "2026-07-05T00:00:00Z"  # fixed mint time -> reproducible ids
PROBESET = panel.BATTERY["battery_id"]


def _assessor_key(aid: str) -> SigningKey:
    seed = hashlib.sha256(f"epistack-assessor:{aid}".encode()).hexdigest()[:64]
    return SigningKey.from_seed_hex(seed, f"assessor:{aid}")


def build_battery() -> dict:
    rec = envelope.new_record(
        "epi:Schema",
        {"battery_id": PROBESET, "title": panel.BATTERY["title"], "crux": panel.BATTERY["crux"],
         "answer_space": panel.BATTERY["answer_space"], "binarization": panel.BATTERY["binarization"],
         "probes": panel.BATTERY["probes"]},
        minted_by="keystone:epistack-corpus", method="define", at=AT,
    )
    return envelope.sign(rec, CORPUS_KEY)


def build_assessment_record(spec: dict, answers: dict) -> dict:
    rec = envelope.new_record(
        "epi:Assessment",
        {"assessor": spec["id"], "model_tier": spec["tier"], "protocol": spec["protocol"],
         "partition": spec["partition"], "probeSet": PROBESET, "granted": spec["granted"],
         "answers": answers, "affirm_vector": assessment.affirm_vector(answers, panel.BATTERY),
         "reliability": assessment.reliability(answers, panel.BATTERY)},
        minted_by=f"assessor:{spec['id']}", method="assess", at=AT,
        derived_from=spec["granted"],  # the evidence it saw: shared evidence => shared upstream
    )
    return envelope.sign(rec, _assessor_key(spec["id"]))


def build_cluster(panel_name: str, specs: list, votes: dict, battery_id: str, assessment_ids: list) -> dict:
    answers_list = [votes[s["id"]] for s in specs]
    ana = assessment.analyze(answers_list, panel.BATTERY)
    assessors = []
    for s, aid in zip(specs, assessment_ids):
        ans = votes[s["id"]]
        assessors.append({
            "assessor": s["id"], "model_tier": s["tier"], "protocol": s["protocol"],
            "partition": s["partition"], "granted": s["granted"],
            "answers": ans, "affirm_vector": assessment.affirm_vector(ans, panel.BATTERY),
            "assessment_id": aid,
        })
    rec = envelope.new_record(
        "epi:Cluster",
        {"kind": "assessment-run", "panel": panel_name, "probeSet": PROBESET,
         "probe_ids": [p["id"] for p in panel.BATTERY["probes"]],
         "assessors": assessors, "vectors": ana["vectors"], "neff": ana["neff"],
         "pairwise_phi": ana["pairwise_phi"]},
        minted_by="keystone:epistack-corpus", method="aggregate", at=AT,
        derived_from=[battery_id] + assessment_ids,
    )
    return envelope.sign(rec, CORPUS_KEY)


def assemble(raw: dict):
    """Build the battery + one assessment record per assessor + one cluster per panel."""
    panels = panel.hydrated_panels()
    battery = build_battery()
    assessments, clusters = [], {}
    for name, specs in panels.items():
        votes = {v["id"]: v["answers"] for v in raw[name]}
        ids = []
        for s in specs:
            r = build_assessment_record(s, votes[s["id"]])
            assessments.append(r)
            ids.append(r["id"])
        clusters[name] = build_cluster(name, specs, votes, battery["id"], ids)
    return battery, assessments, clusters


def self_verify(battery, assessments, clusters) -> list:
    problems = []
    for r in [battery, *assessments, *clusters.values()]:
        errs = envelope.validate(r)
        v = envelope.verify(r)
        if errs:
            problems.append((r.get("@type"), r.get("id"), errs))
        if not (v["id_ok"] and v["sig_ok"]):
            problems.append((r.get("@type"), r.get("id"), v))
    for name, cl in clusters.items():
        rep = assessment.check_run(cl, panel.BATTERY)
        if not rep["ok"]:
            problems.append((name, "check_run", rep))
    return problems


def axis_analysis(clusters: dict) -> dict:
    """Decompose measured independence across the panels (stochastic / model+protocol / +partition)."""
    panels = {}
    for name, cl in clusters.items():
        vecs = cl["assertion"]["vectors"]
        ne = cl["assertion"]["neff"]
        panels[name] = {
            "k": ne["k"], "phi_bar": ne["phi_bar"], "n_eff": ne["n_eff_capped"],
            "mean_pairwise_hamming": assessment.mean_pairwise_hamming(vecs),
        }
    return {
        "panels": panels,
        "headline": {
            "stochastic_floor_neff": panels.get("homogeneous-control", {}).get("n_eff"),
            "model_and_protocol_neff": panels.get("clean-diverse", {}).get("n_eff"),
            "all_levers_neff": panels.get("heterogeneous", {}).get("n_eff"),
        },
        "reading": (
            "homogeneous-control = stochastic floor (same model+evidence+protocol -> n_eff~=1). "
            "clean-diverse isolates model-tier + protocol independence with evidence held FULL. "
            "heterogeneous additionally varies the evidence partition. Per the adversarial audit "
            "(assessment/AUDIT.json) the clean-diverse -> heterogeneous gap is driven mainly by "
            "evidence-partition starvation, not independent competence; the honest effective-"
            "independence estimate on the HSM crux is ~1-2 votes, not k."
        ),
    }


def main() -> int:
    raw = json.loads(RAW.read_text())
    battery, assessments, clusters = assemble(raw)

    problems = self_verify(battery, assessments, clusters)
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1

    RUNS.mkdir(parents=True, exist_ok=True)
    (RUNS / "battery.json").write_text(json.dumps(battery, indent=2, ensure_ascii=False) + "\n")
    (RUNS / "assessments.json").write_text(json.dumps(assessments, indent=2, ensure_ascii=False) + "\n")
    for name, cl in clusters.items():
        (RUNS / f"{name}.json").write_text(json.dumps(cl, indent=2, ensure_ascii=False) + "\n")

    axis = axis_analysis(clusters)
    (RUNS / "axis_analysis.json").write_text(json.dumps(axis, indent=2, ensure_ascii=False) + "\n")
    for name, cl in clusters.items():
        ne = cl["assertion"]["neff"]
        print(f"OK  {name:22s} k={ne['k']} phi_bar={ne['phi_bar']:.3f} "
              f"n_eff={ne['n_eff_capped']:.2f} meanHam={axis['panels'][name]['mean_pairwise_hamming']:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

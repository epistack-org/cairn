"""Pin the A4 head-to-head artifact — deterministic, model-free.

Reads the pinned careful-baseline panel (``assessment/baseline.json`` — captured
model runs) and re-scores it, delta by delta, against cairn's live closed-form
outputs over the pinned fixtures + A2 runs. Writes ``assessment/head_to_head.json``;
``test_headtohead.py::test_artifact_recompute`` asserts a fresh model-free recompute
is dict-equal to what was pinned.

    python assessment/build_headtohead.py       # rewrites assessment/head_to_head.json
"""
from __future__ import annotations

import json
from pathlib import Path

from cairn import headtohead

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
RUNS = ROOT / "assessment" / "runs"
BASELINE = ROOT / "assessment" / "baseline.json"
OUT = ROOT / "assessment" / "head_to_head.json"


def load_store() -> tuple[dict, dict]:
    index = json.loads((FX / "INDEX.json").read_text())
    store = {}
    for slug in index:
        rec = json.loads((FX / f"{slug}.json").read_text())
        store[rec["id"]] = rec
    return index, store


def build() -> dict:
    index, store = load_store()
    baseline = json.loads(BASELINE.read_text())
    neff_summary, trio_neff = headtohead.load_neff(RUNS)
    cairn = headtohead.cairn_outputs(index, store, neff_summary, trio_neff=trio_neff)
    return headtohead.build(baseline, cairn)


def main() -> int:
    art = build()
    OUT.write_text(json.dumps(art, indent=2, ensure_ascii=False) + "\n")
    c = art["baseline_consensus"]
    s = art["summary"]
    print(f"wrote {OUT.relative_to(ROOT)}")
    print(f"  baseline panel n={c['n']}: noticed shared source {c['noticed_shared_source_fraction']*100:.0f}%, "
          f"flagged confounder {c['flagged_confounder_fraction']*100:.0f}%, hedged {c['hedged_fraction']*100:.0f}%, "
          f"measured n_eff {c['computed_neff_count']}/{c['n']}")
    print(f"  delta_demonstrated={s['delta_demonstrated']}  "
          f"structurally_impossible={s['structurally_impossible']}  residual={s['structural_residual']}")
    for row in art["deltas"]:
        print(f"  delta {row['id']} [{row['verdict']}]: baseline reached in prose — {row['baseline_reached_in_prose']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

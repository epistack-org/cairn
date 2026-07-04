"""Emit assessment/prompts.json — the exact, pinned prompt each assessor is shown.

Deterministic from probes.json + partitions.json + panel.py. Committed so the
measurement is reproducible: anyone can read precisely what each assessor was
asked (and with which model tier), and re-run the panel.
"""
from __future__ import annotations

import json
from pathlib import Path

import panel

OUT = Path(__file__).resolve().parent / "prompts.json"


def _block(specs):
    return [{"id": s["id"], "model": s["tier"], "spec": s, "prompt": panel.build_prompt(s)} for s in specs]


def main() -> int:
    panels = panel.hydrated_panels()
    doc = {
        "battery_id": panel.BATTERY["battery_id"],
        "probe_ids": [p["id"] for p in panel.BATTERY["probes"]],
        "answer_space": panel.BATTERY["answer_space"],
    }
    for name, specs in panels.items():
        doc[name] = _block(specs)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.name}: " + ", ".join(f"{n}={len(doc[n])}" for n in panels))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

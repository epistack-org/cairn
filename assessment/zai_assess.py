"""Measure the cross-vendor (GLM) assessor panel via the z.ai OpenAI-compatible API.

Anthropic assessors run as Workflow subagents; GLM cannot, so this path calls
z.ai directly (glm-4.6) with the SAME pinned prompts (panel.build_prompt) and the
SAME 14-probe battery, then merges the votes into assessment/raw_votes.json under
the "glm-diverse" key. build_assessment.py mints + verifies them like any panel.

The API key is read from ~/.config/epistack/zai.env (never committed). This script
needs network + the key; its OUTPUT (the votes) is the pinned, deterministic artifact
the rest of the pipeline verifies with `cairn assess`.

Usage:
  python assessment/zai_assess.py --test   # one call, print raw shape
  python assessment/zai_assess.py          # full 9-assessor panel -> raw_votes.json
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel  # noqa: E402

ENV = Path.home() / ".config" / "epistack" / "zai.env"
RAW = Path(__file__).resolve().parents[1] / "assessment" / "raw_votes.json"
ENDPOINT = "https://api.z.ai/api/paas/v4/chat/completions"
MODEL = "glm-4.6"
PANEL_KEY = "glm-diverse"
TEMPERATURE = 0.6  # z.ai GLM default; recorded for reproducibility of intent
PROBE_IDS = [p["id"] for p in panel.BATTERY["probes"]]

OUTPUT_INSTR = (
    "\n=== OUTPUT FORMAT ===\n"
    "Respond with ONLY a JSON object (no prose, no markdown fences), of the form:\n"
    '{"answers": [{"probe_id": "F1", "answer": "YES", "reason": "..."}, ...]}\n'
    f"Include all {len(PROBE_IDS)} probe ids exactly once. answer is one of: YES, NO, UNCERTAIN. "
    "Base every answer only on the Evidence in this prompt."
)


def load_key() -> str:
    for line in ENV.read_text().splitlines():
        if line.startswith("ZAI_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"no ZAI_API_KEY in {ENV}")


KEY = load_key()


def call_glm(prompt: str, *, json_mode: bool = True, max_tokens: int = 8000):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    msg = d["choices"][0]["message"]
    return msg.get("content") or "", d.get("usage", {}), d.get("choices", [{}])[0].get("finish_reason")


def parse_answers(content: str):
    s = content.strip()
    if s.startswith("```"):
        s = s.strip("`")
    a, b = s.find("{"), s.rfind("}")
    if a < 0 or b < 0:
        raise ValueError("no JSON object in content")
    obj = json.loads(s[a:b + 1])
    ans = {x["probe_id"]: str(x["answer"]).upper().strip() for x in obj["answers"]}
    reasons = {x["probe_id"]: x.get("reason", "") for x in obj["answers"]}
    for pid in PROBE_IDS:
        if ans.get(pid) not in ("YES", "NO", "UNCERTAIN"):
            raise ValueError(f"bad/missing answer for {pid}: {ans.get(pid)!r}")
    return ans, reasons


def measure_one(spec: dict) -> dict:
    prompt = panel.build_prompt(spec) + OUTPUT_INSTR
    last = None
    for attempt in range(3):
        try:
            content, usage, finish = call_glm(prompt, json_mode=(attempt < 2))
            ans, reasons = parse_answers(content)
            return {"id": spec["id"], "answers": ans, "reasons": reasons, "usage": usage}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:200]!r}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(2 + 2 * attempt)
    raise SystemExit(f"{spec['id']} failed after retries: {last}")


def main(argv) -> int:
    specs = panel.hydrate(panel.PANELS[PANEL_KEY])
    if "--test" in argv:
        s = specs[0]
        prompt = panel.build_prompt(s) + OUTPUT_INSTR
        content, usage, finish = call_glm(prompt)
        print("finish_reason:", finish, "| usage:", usage)
        ans, _ = parse_answers(content)
        print("parsed answers:", ans)
        return 0

    votes = []
    for s in specs:
        v = measure_one(s)
        vec = [1 if v["answers"][p] == "YES" else 0 for p in PROBE_IDS]
        print(f"  {s['id']} ({s['protocol']:11s}) affirm={vec} tok={v['usage'].get('total_tokens', '?')}")
        votes.append({"id": v["id"], "answers": v["answers"], "reasons": v["reasons"]})

    raw = json.loads(RAW.read_text())
    raw[PANEL_KEY] = votes
    RAW.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")
    print(f"merged {len(votes)} {PANEL_KEY} votes into {RAW.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

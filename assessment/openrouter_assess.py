"""P4 staging — measure a genuinely cross-FAMILY assessor panel via OpenRouter.

⛔ OFF-7-19 / Track λ (planning `an internal tracker` milestone P4, issue #20). This is
NOT part of the scored 7/19 deliverable and is not wired into the container, the
default pytest suite, or any pinned artifact. It runs only when an OpenRouter key is
present (post-freeze, per the temporal firewall).

Where A2's `zai_assess.py` measured ONE non-Anthropic vendor (Zhipu GLM-4.6), this
measures several genuinely different open-weight *families* (Llama · Qwen · DeepSeek ·
Mistral · Gemma) behind one OpenAI-compatible key — the cheapest path to the P4 exit
("measured φ over ≥2 cross-family assessors"). "Measured" needs *real* inference, not
*owned* inference, so a hosted aggregator satisfies it; owning the GPU is a separate
(sovereignty) goal.

It reuses the SAME pinned battery + prompts as every other panel (`panel.build_prompt`,
holding evidence FULL so the only axis that varies is the model family — directly
comparable to A2's `clean-diverse`), then computes the cross-family Kish n_eff with
`cairn.neff`. The honest prior (from A2: cross-vendor φ ≈ within-vendor φ) is that this
reproduces "cross-family buys ≈0 on COVID" — so this exists to *measure and confirm*,
cheaply, not to justify a GPU fleet.

Config (never committed): `~/.config/epistack/openrouter.env` with
`OPENROUTER_API_KEY=sk-or-...`.

Usage:
  python assessment/openrouter_assess.py --selftest   # offline asserts, no key/network
  python assessment/openrouter_assess.py --dry-run     # full offline plumbing + mock n_eff
  python assessment/openrouter_assess.py --test        # one live call (needs key)
  python assessment/openrouter_assess.py               # full cross-family panel -> --out
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel  # noqa: E402  (shared, deterministic; no model access)

from cairn import neff  # read-only import of the scored core (Kish n_eff)  # noqa: E402

ENV = Path.home() / ".config" / "epistack" / "openrouter.env"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OUT_DEFAULT = Path(__file__).resolve().parent / "openrouter_votes.json"
PANEL_KEY = "openrouter-crossfamily"
TEMPERATURE = 0.3  # low for assessor stability; recorded for reproducibility of intent
PROBE_IDS = [p["id"] for p in panel.BATTERY["probes"]]

# The cross-FAMILY panel: one assessor per genuinely distinct open-weight lineage,
# evidence held FULL, protocol spread mirroring `clean-diverse` — so the ONLY varying
# axis is the model family and the result is directly comparable to A2. OpenRouter
# slugs as of early 2026; models churn — override with --models "a,b,c". Expand for a
# larger k (repeat a family only if you accept within-family correlation).
CROSS_FAMILY = [
    {"id": "X1", "family": "llama",   "model": "meta-llama/llama-3.3-70b-instruct", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "X2", "family": "qwen",    "model": "qwen/qwen-2.5-72b-instruct",        "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "X3", "family": "deepseek","model": "deepseek/deepseek-chat",            "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "X4", "family": "mistral", "model": "mistralai/mistral-large",           "partition": "FULL", "protocol": "LITERAL"},
    {"id": "X5", "family": "gemma",   "model": "google/gemma-2-27b-it",             "partition": "FULL", "protocol": "ADVERSARIAL"},
]

OUTPUT_INSTR = (
    "\n=== OUTPUT FORMAT ===\n"
    "Respond with ONLY a JSON object (no prose, no markdown fences), of the form:\n"
    '{"answers": [{"probe_id": "F1", "answer": "YES", "reason": "..."}, ...]}\n'
    f"Include all {len(PROBE_IDS)} probe ids exactly once. answer is one of: YES, NO, UNCERTAIN. "
    "Base every answer only on the Evidence in this prompt."
)


def load_key() -> str:
    """Lazily read the OpenRouter key. Not called at import, so the module (and its
    --selftest / --dry-run modes) work with no key present."""
    if not ENV.exists():
        raise SystemExit(f"no OpenRouter key: create {ENV} with OPENROUTER_API_KEY=sk-or-...")
    for line in ENV.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"no OPENROUTER_API_KEY line in {ENV}")


def call_model(model: str, prompt: str, key: str, *, json_mode: bool = True, max_tokens: int = 8000):
    """One OpenAI-compatible chat call to OpenRouter. Returns (content, usage, finish)."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": TEMPERATURE,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        ENDPOINT, data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            # OpenRouter attribution headers (optional, recommended):
            "HTTP-Referer": "https://forge.example.org/dev/cairn",
            "X-Title": "cairn cross-family assessor (P4)",
        },
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        d = json.loads(r.read())
    msg = d["choices"][0]["message"]
    return msg.get("content") or "", d.get("usage", {}), d.get("choices", [{}])[0].get("finish_reason")


def parse_answers(content: str):
    """Extract {probe_id: YES|NO|UNCERTAIN} from a model reply (fence/prose tolerant)."""
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


def affirm_vector(answers: dict) -> list[int]:
    """Binary YES-affirmation vector over the fixed probe order (the n_eff input)."""
    return [1 if answers[p] == "YES" else 0 for p in PROBE_IDS]


def crossfamily_neff(votes: list[dict]) -> dict:
    """Kish n_eff over the cross-family affirmation matrix (via the scored core)."""
    matrix = [affirm_vector(v["answers"]) for v in votes]
    return neff.neff_from_matrix(matrix)


def _mock_answers(seed: int) -> dict:
    """Deterministic offline stand-in for a model reply (dry-run/selftest only).

    Positively-correlated by construction — a shared base pattern with a single
    per-assessor flip — so it mimics the expected real regime (assessors mostly agree
    → n_eff ≈ 1, not k) and keeps the plumbing exercised without being degenerate."""
    base = [1 if i % 2 == 0 else 0 for i in range(len(PROBE_IDS))]
    base[seed % len(PROBE_IDS)] ^= 1  # one bit of disagreement per assessor
    return {p: ("YES" if base[i] else "NO") for i, p in enumerate(PROBE_IDS)}


def measure_one(spec: dict, key: str) -> dict:
    prompt = panel.build_prompt(spec) + OUTPUT_INSTR
    last = None
    for attempt in range(3):
        try:
            content, usage, _ = call_model(spec["model"], prompt, key, json_mode=(attempt < 2))
            ans, reasons = parse_answers(content)
            return {"id": spec["id"], "family": spec["family"], "model": spec["model"],
                    "answers": ans, "reasons": reasons, "usage": usage}
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:200]!r}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(2 + 2 * attempt)
    raise SystemExit(f"{spec['id']} ({spec['model']}) failed after retries: {last}")


def run(specs, *, dry_run: bool, key: str | None) -> list[dict]:
    votes = []
    for i, spec in enumerate(specs):
        if dry_run:
            ans = _mock_answers(i + 1)
            v = {"id": spec["id"], "family": spec["family"], "model": spec["model"],
                 "answers": ans, "reasons": {p: "(dry-run mock)" for p in PROBE_IDS}, "usage": {}}
        else:
            v = measure_one(spec, key)
        vec = affirm_vector(v["answers"])
        tok = v["usage"].get("total_tokens", "dry") if not dry_run else "dry"
        print(f"  {spec['id']} {spec['family']:9s} ({spec['protocol']:11s}) affirm={vec} tok={tok}")
        votes.append({"id": v["id"], "family": v["family"], "model": v["model"],
                      "answers": v["answers"], "reasons": v["reasons"]})
    return votes


def resolve_specs(models_arg: str | None):
    if not models_arg:
        return CROSS_FAMILY
    protocols = ["LITERAL", "BASE_RATE", "ADVERSARIAL"]
    specs = []
    for i, m in enumerate([x.strip() for x in models_arg.split(",") if x.strip()]):
        specs.append({"id": f"X{i+1}", "family": m.split("/")[0], "model": m,
                      "partition": "FULL", "protocol": protocols[i % 3]})
    return specs


def selftest() -> int:
    """Offline invariants — no key, no network. Proves the plumbing end-to-end."""
    # 1. prompts build for every spec and reference the crux
    for spec in CROSS_FAMILY:
        p = panel.build_prompt(spec)
        assert panel.BATTERY["crux"] in p and f"assessor {spec['id']}" in p
    # 2. parse tolerates fenced JSON and validates the full probe set
    sample = '```json\n{"answers": [' + ", ".join(
        f'{{"probe_id": "{pid}", "answer": "YES", "reason": "x"}}' for pid in PROBE_IDS) + ']}\n```'
    ans, _ = parse_answers(sample)
    assert set(ans) == set(PROBE_IDS) and affirm_vector(ans) == [1] * len(PROBE_IDS)
    # 3. a missing/garbage answer is rejected
    try:
        parse_answers('{"answers": [{"probe_id": "F1", "answer": "MAYBE"}]}')
        raise AssertionError("parse_answers should reject a bad answer")
    except ValueError:
        pass
    # 4. dry-run produces a full k×probes matrix and a computable n_eff
    votes = run(CROSS_FAMILY, dry_run=True, key=None)
    assert len(votes) == len(CROSS_FAMILY)
    r = crossfamily_neff(votes)
    assert r["k"] == len(CROSS_FAMILY) and 1.0 <= r["n_eff"] <= r["k"]
    print(f"selftest OK — {len(CROSS_FAMILY)} families, dry-run n_eff={r['n_eff']:.3f} (mock)")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="P4 cross-family assessor panel via OpenRouter (off-7-19)")
    ap.add_argument("--selftest", action="store_true", help="offline invariants; no key/network")
    ap.add_argument("--dry-run", action="store_true", help="full offline plumbing with mock replies")
    ap.add_argument("--test", action="store_true", help="one live call (needs key)")
    ap.add_argument("--models", help="comma-separated OpenRouter model slugs (override the default families)")
    ap.add_argument("--out", default=str(OUT_DEFAULT), help=f"votes output path (default {OUT_DEFAULT.name})")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    specs = resolve_specs(args.models)

    if args.test:
        key = load_key()
        s = specs[0]
        content, usage, finish = call_model(s["model"], panel.build_prompt(s) + OUTPUT_INSTR, key)
        print(f"{s['model']} finish={finish} usage={usage}")
        print("parsed:", parse_answers(content)[0])
        return 0

    key = None if args.dry_run else load_key()
    print(f"cross-family panel (k={len(specs)}, evidence=FULL, {'DRY-RUN' if args.dry_run else 'LIVE'}):")
    votes = run(specs, dry_run=args.dry_run, key=key)
    r = crossfamily_neff(votes)
    print(f"\ncross-family: k={r['k']}  phi_bar={r['phi_bar']:.3f}  n_eff={r['n_eff']:.3f}"
          f"{'  (mock — dry-run)' if args.dry_run else ''}")
    print("  (A2 prior: cross-vendor φ ≈ within-vendor φ → expect n_eff ≈ 1; the redundancy is in the evidence.)")

    out = {
        "note": ("P4 cross-family assessor votes (off-7-19). Measured via OpenRouter; NOT a pinned "
                 "7/19 artifact. Wire into build_assessment.py + the kernel φ-flip post-freeze."),
        "panel_key": PANEL_KEY,
        "endpoint": ENDPOINT,
        "temperature": TEMPERATURE,
        "dry_run": args.dry_run,
        "neff": r,
        "votes": votes,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(votes)} votes -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

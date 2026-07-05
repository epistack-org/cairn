"""P4 staging — cross-FAMILY assessor panel via OpenRouter (hosted, keyed).

⛔ OFF-7-19 / Track λ (`an internal tracker` milestone P4, issue #20). Not in the
container, the default pytest suite, or any pinned artifact. Runs only with a key,
post-freeze, per the temporal firewall.

Several genuinely different open-weight *families* (Llama · Qwen · DeepSeek · Mistral ·
Gemma) behind one OpenAI-compatible key — the cheapest path to the P4 exit ("measured φ
over ≥2 cross-family assessors"). "Measured" needs *real* inference, not *owned* — a
hosted aggregator satisfies it; owning the GPU is a separate (sovereignty) goal, served
by the `ollama_assess.py` sibling. Provider-neutral machinery lives in `oai_assess.py`.

Config (never committed): `~/.config/epistack/openrouter.env` with `OPENROUTER_API_KEY=sk-or-...`.

Usage:
  python assessment/openrouter_assess.py --selftest   # offline asserts, no key/network
  python assessment/openrouter_assess.py --dry-run     # full offline plumbing + mock n_eff
  python assessment/openrouter_assess.py --test        # one live call (needs key)
  python assessment/openrouter_assess.py               # full panel -> openrouter_votes.json
  python assessment/openrouter_assess.py --models "meta-llama/llama-3.3-70b-instruct,qwen/qwen-2.5-72b-instruct"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oai_assess as oai  # noqa: E402

ENV = Path.home() / ".config" / "epistack" / "openrouter.env"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OUT_DEFAULT = Path(__file__).resolve().parent / "openrouter_votes.json"
PANEL_KEY = "openrouter-crossfamily"
TEMPERATURE = 0.3  # low for assessor stability; recorded for reproducibility of intent

# One assessor per genuinely distinct open-weight lineage, evidence held FULL, protocol
# spread — comparable to A2's clean-diverse. OpenRouter slugs as of early 2026; models
# churn, override with --models. Expand for a larger k (repeats add within-family corr).
CROSS_FAMILY = [
    {"id": "X1", "family": "llama",    "model": "meta-llama/llama-3.3-70b-instruct", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "X2", "family": "qwen",     "model": "qwen/qwen-2.5-72b-instruct",        "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "X3", "family": "deepseek", "model": "deepseek/deepseek-chat",            "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "X4", "family": "mistral",  "model": "mistralai/mistral-large",           "partition": "FULL", "protocol": "LITERAL"},
    {"id": "X5", "family": "gemma",    "model": "google/gemma-2-27b-it",             "partition": "FULL", "protocol": "ADVERSARIAL"},
]

NOTE = ("P4 cross-family assessor votes via OpenRouter (off-7-19). Measured, NOT a pinned "
        "7/19 artifact. Wire into build_assessment.py + the kernel φ-flip post-freeze.")


def load_key() -> str:
    if not ENV.exists():
        raise SystemExit(f"no OpenRouter key: create {ENV} with OPENROUTER_API_KEY=sk-or-...")
    for line in ENV.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit(f"no OPENROUTER_API_KEY line in {ENV}")


def _raw_call(key):
    headers = {
        "Authorization": f"Bearer {key}",
        "HTTP-Referer": "https://forge.example.org/dev/cairn",
        "X-Title": "cairn cross-family assessor (P4)",
    }
    return lambda spec, json_mode: oai.call_chat(
        ENDPOINT, spec["model"], oai.prompt_for(spec),
        headers=headers, json_mode=json_mode, temperature=TEMPERATURE)


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="P4 cross-family assessor panel via OpenRouter (off-7-19)")
    ap.add_argument("--selftest", action="store_true", help="offline invariants; no key/network")
    ap.add_argument("--dry-run", action="store_true", help="full offline plumbing with mock replies")
    ap.add_argument("--test", action="store_true", help="one live call (needs key)")
    ap.add_argument("--models", help="comma-separated OpenRouter model slugs (override the default families)")
    ap.add_argument("--out", default=str(OUT_DEFAULT), help=f"votes output path (default {OUT_DEFAULT.name})")
    args = ap.parse_args(argv)

    specs = oai.specs_from_models([m.strip() for m in args.models.split(",") if m.strip()]) if args.models else CROSS_FAMILY

    if args.selftest:
        return oai.selftest(specs, "openrouter")
    if args.test:
        s = specs[0]
        content, usage, fin = _raw_call(load_key())(s, True)
        print(f"{s['model']} finish={fin} usage={usage}\nparsed: {oai.parse_answers(content)[0]}")
        return 0

    raw_call = None if args.dry_run else _raw_call(load_key())
    print(f"cross-family panel (k={len(specs)}, evidence=FULL, {'DRY-RUN' if args.dry_run else 'LIVE'}):")
    votes = oai.run_panel(specs, raw_call, dry_run=args.dry_run)
    oai.finish(votes, out_path=args.out, panel_key=PANEL_KEY, endpoint=ENDPOINT,
               temperature=TEMPERATURE, dry_run=args.dry_run, note=NOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

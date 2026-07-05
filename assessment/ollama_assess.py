"""P4 staging — the OWNED, offline cross-family vote via ollama (M1 Mac Studio).

⛔ OFF-7-19 / Track λ (`an internal tracker` milestone P4, issue #20). Not in the
container, the default pytest suite, or any pinned artifact.

The sovereignty sibling to `openrouter_assess.py`: genuinely different open-weight
families run on hardware *we own* (the 32GB M1 Mac Studio), no key, no network egress —
one or more truly-independent votes that hedge the one real objection to a hosted
aggregator (that "different" hosted models might share a serving stack). Slow (models
load sequentially on 32GB) but free and owned. Same pinned battery + n_eff as every
other panel; provider-neutral machinery lives in `oai_assess.py`.

Runs against ollama's OpenAI-compatible endpoint (`/v1/chat/completions`). No key. Point
it at the Mac over the private network with `--host` or `OLLAMA_HOST`, e.g.
`--host http://localhost:11434`. `ollama pull` each model first.

Usage:
  python assessment/ollama_assess.py --selftest                 # offline asserts, no host
  python assessment/ollama_assess.py --dry-run                   # full offline plumbing + mock n_eff
  python assessment/ollama_assess.py --host http://mac:11434 --test   # one live call
  python assessment/ollama_assess.py --host http://mac:11434          # full owned panel -> ollama_votes.json
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import oai_assess as oai  # noqa: E402

OUT_DEFAULT = Path(__file__).resolve().parent / "ollama_votes.json"
PANEL_KEY = "ollama-owned-crossfamily"
TEMPERATURE = 0.3

# Genuinely distinct families that fit a 32GB M1 at q4 (they load one at a time — slow
# but owned). ollama registry tags; `ollama pull` each first. Override with --models.
OWNED_FAMILY = [
    {"id": "O1", "family": "qwen",    "model": "qwen2.5:14b",     "partition": "FULL", "protocol": "LITERAL"},
    {"id": "O2", "family": "llama",   "model": "llama3.1:8b",     "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "O3", "family": "gemma",   "model": "gemma2:27b",      "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "O4", "family": "mistral", "model": "mistral-nemo:12b", "partition": "FULL", "protocol": "LITERAL"},
]

NOTE = ("P4 OWNED cross-family assessor votes via ollama on the M1 (off-7-19). Measured on "
        "hardware we own; NOT a pinned 7/19 artifact. Wire in post-freeze alongside the "
        "OpenRouter panel; this is the sovereignty vote.")


def base_url(arg_host: str | None) -> str:
    """Resolve the ollama base URL: --host > OLLAMA_HOST > localhost. Adds a scheme."""
    h = arg_host or os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
    if not h.startswith(("http://", "https://")):
        h = "http://" + h
    return h.rstrip("/")


def _raw_call(endpoint):
    # ollama's OpenAI-compat endpoint is keyless (local); no auth header needed.
    return lambda spec, json_mode: oai.call_chat(
        endpoint, spec["model"], oai.prompt_for(spec), json_mode=json_mode, temperature=TEMPERATURE)


def main(argv) -> int:
    ap = argparse.ArgumentParser(description="P4 owned cross-family assessor panel via ollama (off-7-19)")
    ap.add_argument("--selftest", action="store_true", help="offline invariants; no host/network")
    ap.add_argument("--dry-run", action="store_true", help="full offline plumbing with mock replies")
    ap.add_argument("--test", action="store_true", help="one live call (needs a reachable ollama)")
    ap.add_argument("--host", help="ollama base URL (default: $OLLAMA_HOST or http://localhost:11434)")
    ap.add_argument("--models", help="comma-separated ollama model tags (override the default families)")
    ap.add_argument("--out", default=str(OUT_DEFAULT), help=f"votes output path (default {OUT_DEFAULT.name})")
    args = ap.parse_args(argv)

    specs = oai.specs_from_models([m.strip() for m in args.models.split(",") if m.strip()]) if args.models else OWNED_FAMILY

    if args.selftest:
        return oai.selftest(specs, "ollama")

    endpoint = base_url(args.host) + "/v1/chat/completions"
    if args.test:
        s = specs[0]
        content, usage, fin = _raw_call(endpoint)(s, True)
        print(f"{s['model']} @ {endpoint} finish={fin} usage={usage}\nparsed: {oai.parse_answers(content)[0]}")
        return 0

    raw_call = None if args.dry_run else _raw_call(endpoint)
    where = "DRY-RUN" if args.dry_run else f"LIVE @ {endpoint}"
    print(f"owned cross-family panel (k={len(specs)}, evidence=FULL, {where}):")
    votes = oai.run_panel(specs, raw_call, dry_run=args.dry_run)
    oai.finish(votes, out_path=args.out, panel_key=PANEL_KEY, endpoint=endpoint,
               temperature=TEMPERATURE, dry_run=args.dry_run, note=NOTE)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

"""Shared OpenAI-compatible assessor primitives for the P4 cross-family panels.

⛔ OFF-7-19 / Track λ. Used by the provider frontends `openrouter_assess.py`
(hosted, keyed) and `ollama_assess.py` (owned, local/keyless). Not in the container,
the default pytest suite, or any pinned artifact.

Everything provider-neutral lives here — the pinned battery + prompt, one chat call,
answer parsing, the affirmation vector, the cross-family Kish n_eff (via `cairn.neff`),
a positively-correlated offline mock, the retry loop, and the offline selftest. Each
frontend supplies only its endpoint/auth/model-list. `zai_assess.py` predates this and
stays self-contained (it is a merged A2 artifact; not worth churning).
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import panel  # noqa: E402  (shared, deterministic; no model access)

from cairn import neff  # noqa: E402  (read-only import of the scored core)

PROBE_IDS = [p["id"] for p in panel.BATTERY["probes"]]

OUTPUT_INSTR = (
    "\n=== OUTPUT FORMAT ===\n"
    "Respond with ONLY a JSON object (no prose, no markdown fences), of the form:\n"
    '{"answers": [{"probe_id": "F1", "answer": "YES", "reason": "..."}, ...]}\n'
    f"Include all {len(PROBE_IDS)} probe ids exactly once. answer is one of: YES, NO, UNCERTAIN. "
    "Base every answer only on the Evidence in this prompt."
)


def prompt_for(spec: dict) -> str:
    """The exact pinned prompt an assessor is shown (battery + output contract)."""
    return panel.build_prompt(spec) + OUTPUT_INSTR


def specs_from_models(models: list[str], *, partition: str = "FULL") -> list[dict]:
    """Turn a bare model list into cross-family specs (evidence held FULL, protocol
    spread) — so the only varying axis is the model family, comparable to clean-diverse."""
    protocols = ["LITERAL", "BASE_RATE", "ADVERSARIAL"]
    return [
        {"id": f"X{i+1}", "family": m.split("/")[-1].split(":")[0], "model": m,
         "partition": partition, "protocol": protocols[i % 3]}
        for i, m in enumerate(models)
    ]


def call_chat(endpoint: str, model: str, prompt: str, *, headers: dict | None = None,
              json_mode: bool = True, max_tokens: int = 8000, temperature: float = 0.3,
              timeout: int = 300):
    """One OpenAI-compatible /chat/completions call. Returns (content, usage, finish)."""
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode(), headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    msg = d["choices"][0]["message"]
    return msg.get("content") or "", d.get("usage", {}), d.get("choices", [{}])[0].get("finish_reason")


def parse_answers(content: str):
    """Extract {probe_id: YES|NO|UNCERTAIN} from a reply (fence/prose tolerant)."""
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
    return neff.neff_from_matrix([affirm_vector(v["answers"]) for v in votes])


def mock_answers(seed: int) -> dict:
    """Deterministic offline stand-in (dry-run/selftest). Positively-correlated — a
    shared base with one per-assessor flip — so it mimics the expected real regime
    (assessors mostly agree → n_eff ≈ 1) and keeps the plumbing exercised."""
    base = [1 if i % 2 == 0 else 0 for i in range(len(PROBE_IDS))]
    base[seed % len(PROBE_IDS)] ^= 1
    return {p: ("YES" if base[i] else "NO") for i, p in enumerate(PROBE_IDS)}


def measure_one(spec: dict, raw_call) -> tuple[dict, dict, dict]:
    """Retry loop around a provider `raw_call(spec, json_mode) -> (content, usage, finish)`."""
    last = None
    for attempt in range(3):
        try:
            content, usage, _ = raw_call(spec, attempt < 2)
            ans, reasons = parse_answers(content)
            return ans, reasons, usage
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:200]!r}"
        except Exception as e:  # noqa: BLE001
            last = repr(e)
        time.sleep(2 + 2 * attempt)
    raise SystemExit(f"{spec['id']} ({spec.get('model')}) failed after retries: {last}")


def usage_cost(usage: dict) -> dict:
    """Normalize a provider `usage` block to ``{prompt, completion, total, cost_usd}``.

    OpenRouter returns the REAL dollar `cost` per call (upstream-inference cost, not a list price), so
    the honest figure is reported, not modelled from a per-model price table we would have to keep in
    sync. A provider that omits `cost` (or the dry-run's ``{}``) yields ``cost_usd=None`` — recorded as
    "unknown", never silently zero, because a zero we invented is worse than an admitted gap."""
    if not usage:
        return {"prompt": 0, "completion": 0, "total": 0, "cost_usd": None}
    cost = usage.get("cost")
    if cost is None:
        cost = (usage.get("cost_details") or {}).get("upstream_inference_cost")
    return {
        "prompt": usage.get("prompt_tokens", 0),
        "completion": usage.get("completion_tokens", 0),
        "total": usage.get("total_tokens", 0),
        "cost_usd": float(cost) if cost is not None else None,
    }


def panel_cost(votes: list[dict]) -> dict:
    """Total tokens + $ over a panel's votes (each vote carries its own ``usage``). A first-class
    output, not a print — the S2 DoD's "cost recorded honestly" has to point at a persisted number.
    ``cost_usd`` is None if ANY vote lacks a cost (partial totals mislead more than an admitted gap)."""
    costs = [usage_cost(v.get("usage") or {}) for v in votes]
    dollars = [c["cost_usd"] for c in costs]
    return {
        "prompt_tokens": sum(c["prompt"] for c in costs),
        "completion_tokens": sum(c["completion"] for c in costs),
        "total_tokens": sum(c["total"] for c in costs),
        "cost_usd": (round(sum(d for d in dollars if d is not None), 6)
                     if dollars and all(d is not None for d in dollars) else None),
        "priced_votes": sum(1 for d in dollars if d is not None),
        "k": len(votes),
    }


def run_panel(specs: list[dict], raw_call, *, dry_run: bool) -> list[dict]:
    """Collect one vote per spec (live via raw_call, or offline mock). Each vote carries its ``usage``
    (tokens + provider cost) so the panel's spend can be totalled downstream (:func:`panel_cost`)."""
    votes = []
    for i, spec in enumerate(specs):
        if dry_run:
            ans, reasons, usage = mock_answers(i + 1), {p: "(dry-run mock)" for p in PROBE_IDS}, {}
        else:
            ans, reasons, usage = measure_one(spec, raw_call)
        vec = affirm_vector(ans)
        c = usage_cost(usage)
        tok = "dry" if dry_run else c["total"]
        dol = "" if dry_run or c["cost_usd"] is None else f" ${c['cost_usd']:.5f}"
        print(f"  {spec['id']} {spec['family']:12s} ({spec['protocol']:11s}) affirm={vec} tok={tok}{dol}")
        votes.append({"id": spec["id"], "family": spec["family"], "model": spec["model"],
                      "answers": ans, "reasons": reasons, "usage": usage})
    return votes


def finish(votes: list[dict], *, out_path, panel_key: str, endpoint: str, temperature: float,
           dry_run: bool, note: str) -> dict:
    """Compute + print the cross-family n_eff and write the votes artifact (with the panel's spend)."""
    r = crossfamily_neff(votes)
    cost = panel_cost(votes)
    print(f"\ncross-family: k={r['k']}  phi_bar={r['phi_bar']:.3f}  n_eff={r['n_eff']:.3f}"
          f"{'  (mock — dry-run)' if dry_run else ''}")
    if not dry_run:
        usd = f"${cost['cost_usd']:.4f}" if cost["cost_usd"] is not None else "unknown"
        print(f"  spend: {cost['total_tokens']} tokens, {usd} over k={cost['k']} "
              f"({cost['priced_votes']} priced)")
    print("  (A2 prior: cross-vendor φ ≈ within-vendor φ → expect n_eff ≈ 1; the redundancy is in the evidence.)")
    Path(out_path).write_text(json.dumps(
        {"note": note, "panel_key": panel_key, "endpoint": endpoint, "temperature": temperature,
         "dry_run": dry_run, "neff": r, "cost": cost, "votes": votes}, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {len(votes)} votes -> {out_path}")
    return r


def selftest(specs: list[dict], label: str) -> int:
    """Offline invariants — no key, no network. Proves the plumbing end-to-end."""
    for spec in specs:
        p = prompt_for(spec)
        assert panel.BATTERY["crux"] in p and f"assessor {spec['id']}" in p
    sample = '```json\n{"answers": [' + ", ".join(
        f'{{"probe_id": "{pid}", "answer": "YES", "reason": "x"}}' for pid in PROBE_IDS) + ']}\n```'
    ans, _ = parse_answers(sample)
    assert set(ans) == set(PROBE_IDS) and affirm_vector(ans) == [1] * len(PROBE_IDS)
    try:
        parse_answers('{"answers": [{"probe_id": "F1", "answer": "MAYBE"}]}')
        raise AssertionError("parse_answers should reject a bad answer")
    except ValueError:
        pass
    votes = run_panel(specs, raw_call=None, dry_run=True)
    r = crossfamily_neff(votes)
    assert r["k"] == len(specs) and 1.0 <= r["n_eff"] <= r["k"] + 1e-9
    print(f"selftest OK ({label}) — {len(specs)} families, dry-run n_eff={r['n_eff']:.3f} (mock)")
    return 0

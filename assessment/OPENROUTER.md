# P4 · cross-family assessors via OpenRouter (staged, off-7-19)

⛔ **Off the 7/19 scored path** (Track λ, `an internal tracker` milestone P4 / issue #20).
Not in the container, the default pytest suite, or any pinned 7/19 artifact. Runs only
with a key, post-freeze, per the temporal firewall. This file + `openrouter_assess.py`
are the whole staging; nothing here gates cairn.

## Why OpenRouter (not a DIY GPU node)

P4's exit is **"measured φ over ≥2 genuinely cross-family assessors."** The load-bearing
word is *measured* — and **measured needs real inference, not owned inference.** A hosted
aggregator produces measured φ just as well as a GPU you rack yourself; owning the node is
a separate *sovereignty* goal (defer to P5/D8). OpenRouter gives the widest set of genuinely
different open-weight families behind one OpenAI-compatible key, for a few dollars, and
**decouples P4 from the D8 host decision**. The M1 Mac Studio is worth adding as *one* owned,
offline vote (the sovereignty proof), not as the whole panel — that's the `ollama_assess.py`
sibling ([`OLLAMA.md`](OLLAMA.md)); shared machinery lives in `oai_assess.py`.

## Config

Create (never commit):

```
~/.config/epistack/openrouter.env
    OPENROUTER_API_KEY=sk-or-...
```

Mirrors the z.ai pattern (`~/.config/epistack/zai.env`). The key is read lazily, so
`--selftest` / `--dry-run` work with no key.

## Run

```bash
python assessment/openrouter_assess.py --selftest   # offline invariants; no key/network
python assessment/openrouter_assess.py --dry-run     # full offline plumbing + mock n_eff
python assessment/openrouter_assess.py --test        # one live call (needs key)
python assessment/openrouter_assess.py               # full cross-family panel -> openrouter_votes.json
python assessment/openrouter_assess.py --models "meta-llama/llama-3.3-70b-instruct,qwen/qwen-2.5-72b-instruct,deepseek/deepseek-chat"
```

Design: one assessor per genuinely distinct open-weight lineage (Llama · Qwen · DeepSeek ·
Mistral · Gemma), **evidence held FULL**, protocol spread — so the only varying axis is the
model family, directly comparable to A2's `clean-diverse`. It reuses the pinned battery +
`panel.build_prompt`, then computes the cross-family Kish n_eff via `cairn.neff`. Writes to
`assessment/openrouter_votes.json` (a separate off-gate file; it does **not** touch the
pinned `raw_votes.json`).

Cost/time: a k=5 panel ≈ ~5 × ~8k tokens ≈ **well under $1**, minutes. Model slugs are
OpenRouter identifiers as of early 2026 — confirm/adjust them when you run.

## Honest prior (why this is a confirm, not a bet)

A2 already measured cross-vendor (Anthropic × GLM) φ ≈ within-vendor φ — the redundancy is
in the **evidence**, not the model family. So the expected result is **cross-family also
buys ≈0 (n_eff ≈ 1)**, reproducing the honest finding under live open-weight inference. That
is exactly why the cheap path is right: don't spend a GPU fleet to re-confirm what A2
predicts. If cross-family φ came in *materially lower* than within-vendor, that would be the
surprise worth the spend — and this harness is what would detect it.

## Post-freeze wiring (not done here — deliberately)

When the votes exist, the P4 tail is: (1) mint `openrouter-crossfamily` as an `epi:Cluster`
through `build_assessment.py` (add it to `panel.PANELS`); (2) flip the kernel's cross-vendor
`Org.phiBasis` modelled→measured for the calibrated family pair (the `an internal tracker` side);
(3) show a downstream consumer emit *measured* corroboration for that pair while still refusing
un-calibrated channels. All of that lands after the 7/19 freeze.

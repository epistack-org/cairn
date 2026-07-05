# P4 · the owned cross-family vote via ollama / M1 (staged, off-7-19)

⛔ **Off the 7/19 scored path** (Track λ, `an internal tracker` P4 / issue #20). Not in the
container, the default pytest suite, or any pinned artifact. The sovereignty sibling of
[`OPENROUTER.md`](OPENROUTER.md); shared machinery in `oai_assess.py`.

## Why an owned vote at all

OpenRouter gives measured φ cheaply, but every model behind it is *hosted* — the one real
objection is that "different" hosted models could share a serving stack or provider-side
routing. Running genuinely different open-weight families on **hardware we own** (the 32GB
M1 Mac Studio), keyless and with no network egress, produces **one or more truly-independent
votes** that hedge that objection. It is the concrete "we own this vote" datum for the
compute-sovereignty thesis — slow, but free and owned. Not the whole panel (a 32GB box loads
one model at a time); the honest role is a small owned anchor alongside the hosted panel.

## Setup (on the Mac)

```bash
ollama pull qwen2.5:14b llama3.1:8b gemma2:27b mistral-nemo:12b   # ~9/5/16/7 GB at q4
OLLAMA_HOST=0.0.0.0:11434 ollama serve      # expose on the private network (else localhost-only)
```
The M1 runs these sequentially at ~20–40 tok/s, so a 4-family battery is ~40–70 min. Fine for
a one-off calibration; too slow for a fleet.

## Run (from this box, over the private network — or on the Mac itself)

```bash
python assessment/ollama_assess.py --selftest                        # offline; no host needed
python assessment/ollama_assess.py --dry-run                          # offline plumbing + mock n_eff
python assessment/ollama_assess.py --host http://localhost:11434 --test   # one live call
python assessment/ollama_assess.py --host http://localhost:11434          # full owned panel
```

Host resolution: `--host` > `OLLAMA_HOST` > `http://localhost:11434` (a scheme is added if
you pass a bare `host:port`). Uses ollama's OpenAI-compatible `/v1/chat/completions` (keyless).
One assessor per family, evidence held FULL (only the family axis varies — comparable to A2's
`clean-diverse`); writes `assessment/ollama_votes.json` (a separate off-gate file). Model tags
are ollama registry identifiers — adjust with `--models`.

## Same honest prior

Per A2, the expected result is **n_eff ≈ 1** here too (owned open-weight families still share
the *evidence*, which is where the redundancy lives). The owned vote's value is not a *lower*
φ — it's that the vote is genuinely independent of any hosted provider, so it can't be
dismissed as provider-side correlation. Post-freeze, fold `ollama-owned-crossfamily` in
alongside the OpenRouter panel when minting the `epi:Cluster` + flipping the kernel φ.

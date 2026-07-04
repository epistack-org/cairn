"""A2 assessor panel: specs, evidence-partition assembly, and prompt construction.

Pure and deterministic — no model access here. `gen_prompts.py` turns this into
`assessment/prompts.json` (the exact, pinned prompt each assessor is shown);
`build_assessment.py` reuses the specs to attach provenance (which evidence each
assessor was granted -> its derivedFrom edge set).

The three real heterogeneity axes we have without external keys:
  1. model tier      — opus / sonnet / haiku / fable subagents (cross-model, if within-vendor)
  2. evidence-partition — each assessor sees only a disjoint slice of the corpus (primary lever)
  3. reasoning protocol — literal / base-rate / adversarial
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FX = ROOT / "fixtures"
ASSESS = ROOT / "assessment"

BATTERY = json.loads((ASSESS / "probes.json").read_text())
PARTITIONS = json.loads((ASSESS / "partitions.json").read_text())["views"]


def _store() -> dict:
    index = json.loads((FX / "INDEX.json").read_text())
    return {slug: json.loads((FX / f"{slug}.json").read_text()) for slug in index}


STORE = _store()

# --- axis 3: reasoning protocol ---------------------------------------------
PROTOCOLS = {
    "LITERAL": (
        "Protocol LITERAL. Read only what the Evidence explicitly states. Answer YES or NO "
        "only when the Evidence provided explicitly settles the probe; otherwise answer "
        "UNCERTAIN. Do not infer beyond the text."
    ),
    "BASE_RATE": (
        "Protocol BASE_RATE. Begin from an explicit stated prior over {market-associated "
        "zoonosis, other zoonosis, non-zoonotic introduction}; state it in one line, then "
        "update ONLY on the Evidence provided before answering each probe."
    ),
    "ADVERSARIAL": (
        "Protocol ADVERSARIAL. For each probe, first construct the strongest good-faith case "
        "AGAINST answering YES using only the Evidence provided; answer YES only if it "
        "survives that challenge, otherwise NO or UNCERTAIN."
    ),
}

# --- the panels -------------------------------------------------------------
# Heterogeneous: every tier, partition and protocol appears; no two assessors share
# all three axes. Homogeneous control: one identical cell x9 -> the correlated baseline
# that makes the deflation ("nine judges, two votes") visible on our own corpus.
HETEROGENEOUS = [
    {"id": "H1", "tier": "opus",   "partition": "FULL",              "protocol": "LITERAL"},
    {"id": "H2", "tier": "sonnet", "partition": "WOROBEY_ONLY",      "protocol": "BASE_RATE"},
    {"id": "H3", "tier": "haiku",  "partition": "PEKAR_ONLY",        "protocol": "ADVERSARIAL"},
    {"id": "H4", "tier": "fable",  "partition": "PROXIMITY_SPATIAL", "protocol": "LITERAL"},
    {"id": "H5", "tier": "opus",   "partition": "PROXIMITY_TRADE",   "protocol": "BASE_RATE"},
    {"id": "H6", "tier": "sonnet", "partition": "SOURCES_ONLY",      "protocol": "ADVERSARIAL"},
    {"id": "H7", "tier": "haiku",  "partition": "CLAIMS_ONLY",       "protocol": "LITERAL"},
    {"id": "H8", "tier": "fable",  "partition": "FULL",              "protocol": "ADVERSARIAL"},
    {"id": "H9", "tier": "opus",   "partition": "PEKAR_ONLY",        "protocol": "BASE_RATE"},
]
CONTROL = [
    {"id": f"C{i}", "tier": "opus", "partition": "FULL", "protocol": "LITERAL"} for i in range(1, 10)
]
# Axis-isolation panel: evidence held constant at FULL for all, varying ONLY model
# tier x protocol. Removes the evidence-partition starvation confound so we measure
# the *clean* cross-assessor independence (the number the A2 audit demands).
CLEAN = [
    {"id": "D1", "tier": "opus",   "partition": "FULL", "protocol": "LITERAL"},
    {"id": "D2", "tier": "sonnet", "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "D3", "tier": "haiku",  "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "D4", "tier": "fable",  "partition": "FULL", "protocol": "LITERAL"},
    {"id": "D5", "tier": "opus",   "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "D6", "tier": "sonnet", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "D7", "tier": "haiku",  "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "D8", "tier": "fable",  "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "D9", "tier": "opus",   "partition": "FULL", "protocol": "BASE_RATE"},
]

# Cross-vendor panel: genuinely non-Anthropic assessors (Zhipu GLM-4.6 via z.ai),
# FULL evidence, protocol spread mirroring clean-diverse -> isolates the VENDOR axis.
# Measured via the z.ai OpenAI-compatible API (assessment/zai_assess.py), not the
# Workflow (whose subagents are Anthropic-only).
GLM_DIVERSE = [
    {"id": "G1", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "G2", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "G3", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "G4", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "G5", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "G6", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "LITERAL"},
    {"id": "G7", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "BASE_RATE"},
    {"id": "G8", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "ADVERSARIAL"},
    {"id": "G9", "tier": "glm-4.6", "vendor": "zai", "partition": "FULL", "protocol": "BASE_RATE"},
]

# panel name -> specs. Names double as raw_votes.json keys and epi:Cluster panel labels.
PANELS = {
    "heterogeneous": HETEROGENEOUS,
    "homogeneous-control": CONTROL,
    "clean-diverse": CLEAN,
    "glm-diverse": GLM_DIVERSE,
}


def granted_source_ids(partition: str) -> list[str]:
    """The epi:Source Trusty URIs an assessor in this partition was granted (its derivedFrom)."""
    return [STORE[s]["id"] for s in PARTITIONS[partition]["sources"]]


def evidence_block(partition: str) -> str:
    view = PARTITIONS[partition]
    lines: list[str] = []
    for s in view["sources"]:
        rec = STORE[s]["assertion"]
        lines.append(f"[SOURCE] {rec['title']}")
        lines.append(f"         {rec['authors']}. {rec['venue']} {rec['year']}. doi:{rec['doi']}")
        if view["show_excerpts"]:
            lines.append(f'         {rec["excerpt_kind"]}: "{rec["excerpt"]}"')
        else:
            lines.append("         (abstract text withheld in this view)")
    for c in view["claims"]:
        rec = STORE[c]["assertion"]
        lines.append(f"[CLAIM/{rec['verification']}] {rec['text']}")
    if not view["claims"] and not view["show_excerpts"]:
        lines.append("(no evidence granted)")
    return "\n".join(lines)


def build_prompt(spec: dict) -> str:
    view = PARTITIONS[spec["partition"]]
    probes = BATTERY["probes"]
    probe_lines = "\n".join(f"{p['id']}. {p['text']}" for p in probes)
    return f"""You are assessor {spec['id']}, one member of an epistemic-independence panel.
{PROTOCOLS[spec['protocol']]}

CRUX QUESTION: {BATTERY['crux']}

RULES:
- Base every answer ONLY on the Evidence section below. Treat it as the complete
  admissible evidentiary record; do NOT rely on background knowledge of SARS-CoV-2
  origins. If the Evidence you were granted does not settle a probe, answer UNCERTAIN.
- Answer every one of the {len(probes)} probes with exactly one of: YES, NO, UNCERTAIN.
- Give a one-sentence reason per probe, referring only to the Evidence.

=== EVIDENCE (your partition: {spec['partition']} — {view['desc']}) ===
{evidence_block(spec['partition'])}

=== PROBES ===
{probe_lines}
"""


def hydrate(specs):
    """Attach each spec's granted source ids + slugs (its derivedFrom evidence)."""
    return [
        {**s, "granted": granted_source_ids(s["partition"]),
         "granted_slugs": PARTITIONS[s["partition"]]["sources"]}
        for s in specs
    ]


def hydrated_panels() -> dict:
    """{panel_name: [hydrated spec, ...]} for every panel in PANELS."""
    return {name: hydrate(specs) for name, specs in PANELS.items()}


def panel_specs():
    """Back-compat: (heterogeneous, homogeneous-control)."""
    return hydrate(HETEROGENEOUS), hydrate(CONTROL)

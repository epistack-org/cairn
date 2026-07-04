"""``cairn`` CLI — mint/validate/neff/intersect over Cairn records.

Deliberately thin and stdlib-only-plus-deps: this is the plain-container engine,
no substrate. Records are JSON on disk or stdin.
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

from . import assessment, envelope, frechet, grounding, neff, provenance
from .keys import SigningKey


def _read_json(path: str):
    text = sys.stdin.read() if path == "-" else Path(path).read_text()
    return json.loads(text)


def _load_store(patterns: list[str]) -> dict[str, dict]:
    """Load every record JSON matching the glob(s) into a {id: record} store."""
    store: dict[str, dict] = {}
    for pat in patterns:
        for fn in sorted(glob.glob(pat)):
            data = json.loads(Path(fn).read_text())
            for r in data if isinstance(data, list) else [data]:
                if isinstance(r, dict) and "id" in r and "@type" in r:  # skip non-records (e.g. INDEX.json)
                    store[r["id"]] = r
    return store


def cmd_mint(args) -> int:
    rec = _read_json(args.record)
    envelope.mint(rec)
    if args.key_seed_hex or args.sign:
        key = (
            SigningKey.from_seed_hex(args.key_seed_hex, args.label)
            if args.key_seed_hex
            else SigningKey.generate(args.label)
        )
        envelope.sign(rec, key)
    print(json.dumps(rec, indent=2, ensure_ascii=False))
    return 0


def cmd_validate(args) -> int:
    rec = _read_json(args.record)
    errors = envelope.validate(rec)
    v = envelope.verify(rec)
    for e in errors:
        print(f"SCHEMA: {e}", file=sys.stderr)
    if not v["id_ok"]:
        print("INTEGRITY: id does not match content (record was altered or not minted)", file=sys.stderr)
    if v["signed"] and not v["sig_ok"]:
        print("INTEGRITY: signature does not verify", file=sys.stderr)
    ok = not errors and v["id_ok"] and (v["sig_ok"] or not v["signed"])
    print(json.dumps({"valid": not errors, **v, "ok": ok}, indent=2))
    return 0 if ok else 1


def cmd_neff(args) -> int:
    obj = _read_json(args.matrix)
    vectors = obj["vectors"] if isinstance(obj, dict) else obj
    print(json.dumps(neff.neff_from_matrix(vectors), indent=2))
    return 0


def cmd_ground(args) -> int:
    store = _load_store(args.store)
    report = grounding.check_store(store, args.claims)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["ok"] else 1  # nonzero == a span failed to resolve (script-detectable)


def cmd_assess(args) -> int:
    battery = json.loads(Path(args.battery).read_text())
    reports = []
    ok = True
    for pat in args.run:
        for fn in sorted(glob.glob(pat)):
            rep = assessment.check_run(json.loads(Path(fn).read_text()), battery)
            rep["file"] = fn
            reports.append(rep)
            ok = ok and rep["ok"]
    if not reports:
        print("ASSESS: no run files matched", file=sys.stderr)
        return 1
    print(json.dumps(reports[0] if len(reports) == 1 else reports, indent=2))
    return 0 if ok else 1  # nonzero == a recomputed vector/n_eff disagreed with what was pinned


def cmd_frechet(args) -> int:
    store = _load_store(args.store)
    ids = args.claims or [rid for rid, r in store.items() if r.get("@type") == "epi:Claim"]
    ids = [i for i in ids if i in store and "illustrative_LR" in store[i].get("assertion", {})]
    if not ids:
        print("FRECHET: no combinable epi:Claim records (need assertion.illustrative_LR)", file=sys.stderr)
        return 2  # nothing to combine -> cannot assert a point; fail closed, like a refusal
    prov = provenance.combine_verdict(ids, store)
    lrs = [store[i]["assertion"]["illustrative_LR"] for i in ids]
    n_eff = None
    if args.neff_run:
        run = json.loads(Path(args.neff_run).read_text())
        n_eff = run["assertion"]["neff"]["n_eff_capped"]  # A2 same-evidence witness of redundancy
    v = frechet.frechet_verdict(
        lrs, prior=args.prior, shared_upstream=not prov["independent"],
        base_neg=args.base_neg, n_eff=n_eff, max_width_decades=args.max_width_decades,
    )
    v["claims"] = ids
    v["provenance"] = {"verdict": prov["verdict"], "shared_upstreams": prov["shared_upstreams"]}
    print(json.dumps(v, indent=2))
    return 0 if v["verdict"] == "COMBINABLE-WITH-INTERVAL" else 2  # nonzero == refused-as-point (like intersect)


def cmd_intersect(args) -> int:
    store = _load_store(args.store)
    ids = args.claims or list(store.keys())
    verdict = provenance.combine_verdict(ids, store)
    # JSON keys must be strings; flatten the pairwise tuple keys
    verdict["pairwise_shared"] = [
        {"a": a, "b": b, "shared": shared} for (a, b), shared in verdict["pairwise_shared"].items()
    ]
    print(json.dumps(verdict, indent=2))
    return 0 if verdict["independent"] else 2  # nonzero == refused (script-detectable)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cairn", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mint", help="mint (content-address) and optionally sign a record")
    m.add_argument("record", help="path to record JSON, or - for stdin")
    m.add_argument("--sign", action="store_true", help="sign with an ephemeral key")
    m.add_argument("--key-seed-hex", help="ed25519 seed hex to sign with")
    m.add_argument("--label", default="keystone:local", help="signer identity label")
    m.set_defaults(func=cmd_mint)

    v = sub.add_parser("validate", help="schema-validate + verify id/signature")
    v.add_argument("record", help="path to record JSON, or - for stdin")
    v.set_defaults(func=cmd_validate)

    n = sub.add_parser("neff", help="Kish n_eff over a binary agreement matrix")
    n.add_argument("matrix", help="JSON {vectors:[[..],..]} or [[..],..], or - for stdin")
    n.set_defaults(func=cmd_neff)

    i = sub.add_parser("intersect", help="refuse-to-combine verdict over a claim set")
    i.add_argument("store", nargs="+", help="glob(s) of record JSON files (the store)")
    i.add_argument("--claims", nargs="*", help="Trusty URIs to test (default: all in store)")
    i.set_defaults(func=cmd_intersect)

    g = sub.add_parser("ground", help="verify claims' spans resolve to their cited source excerpts")
    g.add_argument("store", nargs="+", help="glob(s) of record JSON files (the store)")
    g.add_argument("--claims", nargs="*", help="Trusty URIs to check (default: all claims in store)")
    g.set_defaults(func=cmd_ground)

    fr = sub.add_parser("frechet", help="Fréchet/p-box interval instead of a fake point posterior; refuse when too wide")
    fr.add_argument("store", nargs="+", help="glob(s) of record JSON files (the store)")
    fr.add_argument("--claims", nargs="*", help="Trusty URIs to combine (default: all epi:Claim in store)")
    fr.add_argument("--prior", type=float, default=frechet.DEFAULT_PRIOR,
                    help="prior P(H) (default 0.5 -> combined LR reads as posterior odds)")
    fr.add_argument("--neff-run", help="pinned epi:Cluster run whose n_eff witnesses line redundancy "
                                       "(e.g. assessment/runs/homogeneous-control.json)")
    fr.add_argument("--base-neg", type=float, default=frechet.ILLUSTRATIVE_BASE_NEG,
                    help="illustrative p(E|~H) realization (auto-shrinks if it would push p_H>=1)")
    fr.add_argument("--max-width-decades", type=float, default=frechet.DEFAULT_MAX_WIDTH_DECADES,
                    help="policy knob: max log10 interval width to still emit a point (default 0.5)")
    fr.set_defaults(func=cmd_frechet)

    a = sub.add_parser("assess", help="recompute + verify measured n_eff over a pinned assessment run")
    a.add_argument("run", nargs="+", help="glob(s) of assessment-run JSON (epi:Cluster records)")
    a.add_argument("--battery", default="assessment/probes.json", help="probe battery JSON (default: assessment/probes.json)")
    a.set_defaults(func=cmd_assess)
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)

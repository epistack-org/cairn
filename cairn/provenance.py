"""Layer-(a) non-independence detector: the mechanical "explicit shared source"
proof a single transcript structurally cannot produce.

Given a set of claims each carrying a ``provenance.derivedFrom`` edge set of
upstream Cairn Trusty URIs, walk the derivation DAG to each claim's *ancestor
set* (transitive closure), then ask: do claims proposed as "independent" share
an upstream?

  * They share an ancestor  -> they are NOT independent along that ancestor ->
    **REFUSE-TO-COMBINE**, naming the shared tuple(s). (You may still report an
    interval; you may not multiply as if independent.)
  * No shared ancestor      -> independence holds on the provenance dimension ->
    combinable (subject to the *other* legs (b)/(c) and a measured n_eff).

This is the COVID-HSM-trio demo's spine: three "independent lines of proximity
evidence" that all derive from one early-case dataset share that upstream, so
their LRs must not be multiplied (REPORT section 7).
"""
from __future__ import annotations

import itertools
from typing import Iterable, Mapping

# The verdict vocabulary the CLI + tests speak. A refusal is never a claim about
# the world's truth; it is a claim about *this operation over this DAG*.
#   * COMBINABLE                       — no shared upstream on the provenance dim.
#   * REFUSE-TO-COMBINE                — shared upstream; combining as independent
#                                        is undefined. Bare (no surviving backstop).
#   * REFUSE-TO-COMBINE-AS-INDEPENDENT — shared upstream, AND a named leg that is
#                                        upstream-disjoint from the at-risk premise
#                                        and independently sufficient survives, so
#                                        the *conclusion* is unchanged (only the
#                                        "these are N independent votes" claim fails).
VERDICTS = ("COMBINABLE", "REFUSE-TO-COMBINE", "REFUSE-TO-COMBINE-AS-INDEPENDENT")


def upstreams(record: Mapping) -> set[str]:
    """Direct ``derivedFrom`` Trusty URIs of one record."""
    return set(record.get("provenance", {}).get("derivedFrom", []))


def ancestors(record_id: str, store: Mapping[str, Mapping], *, _seen: set | None = None) -> set[str]:
    """Transitive closure of ``derivedFrom`` for ``record_id`` (excludes itself).

    ``store`` maps Trusty URI -> record. Unknown URIs are treated as opaque roots
    (still counted as shared ancestors if two claims both reference them).
    """
    seen = set() if _seen is None else _seen
    rec = store.get(record_id)
    direct = upstreams(rec) if rec is not None else set()
    for u in direct:
        if u in seen:
            continue
        seen.add(u)
        ancestors(u, store, _seen=seen)
    return seen


def shared_upstreams(record_ids: Iterable[str], store: Mapping[str, Mapping]) -> dict:
    """Pairwise + collective shared ancestors across a set proposed as independent."""
    ids = list(record_ids)
    anc = {rid: ancestors(rid, store) for rid in ids}
    pairwise = {}
    for i, j in itertools.combinations(range(len(ids)), 2):
        common = anc[ids[i]] & anc[ids[j]]
        if common:
            pairwise[(ids[i], ids[j])] = sorted(common)
    # Sharing requires at least two parties. set.intersection over a single set
    # returns that set, which would report a lone claim as sharing every one of
    # its own ancestors with itself -> a spurious REFUSE-TO-COMBINE.
    collective = set.intersection(*anc.values()) if len(ids) >= 2 else set()
    return {"ancestors": anc, "pairwise_shared": pairwise, "collective_shared": sorted(collective)}


def label(record_id: str, store: Mapping[str, Mapping]) -> str:
    """A short human-readable name for a record id, for explanations.

    Falls back through the fields records actually carry (source title, claim
    text, entity label/name), and finally the raw id — never raises.
    """
    rec = store.get(record_id)
    if rec is None:
        return record_id
    a = rec.get("assertion", {})
    for k in ("title", "label", "name"):
        if a.get(k):
            return str(a[k])
    text = a.get("text")
    if text:
        return text if len(text) <= 80 else text[:77] + "..."
    return record_id


def _lr_inflation(record_ids: Iterable[str], store: Mapping[str, Mapping]) -> tuple | None:
    """(product, single) illustrative LRs, if every claim carries one; else None.

    ``product`` is what treating the claims as independent multiplies to; ``single``
    is the honest cap when the shared parent is counted once (the largest single LR).
    Both are illustrative — the values live on the claims as ``illustrative_LR``.
    """
    lrs = []
    for rid in record_ids:
        rec = store.get(rid) or {}
        lr = rec.get("assertion", {}).get("illustrative_LR")
        if lr is None:
            return None
        lrs.append(float(lr))
    if not lrs:
        return None
    product = 1.0
    for x in lrs:
        product *= x
    return (product, max(lrs))


def explain_verdict(verdict: Mapping, store: Mapping[str, Mapping]) -> str:
    """One plain-English paragraph for a ``combine_verdict`` result.

    A refusal must never ship as bare JSON + an exit code: it carries the named
    shared upstream, what the refusal means, and — the part ``intersect`` already
    computes and throws away — *what would un-refuse it*. This is information the
    verdict dict already holds; ``explain`` just renders it for a human. It takes no
    new position: everything here is a restatement of the mechanical verdict.
    """
    ids = list(verdict.get("claims", []))
    n = len(ids)
    names = [label(i, store) for i in ids]
    claim_list = "; ".join(names)

    if verdict.get("independent"):
        return (
            f"These {n} claims share no upstream on the provenance dimension "
            f"({claim_list}). They may be combined as independent draws, subject to the "
            f"other dependence legs and a measured n_eff. There is nothing to un-refuse."
        )

    shared = verdict.get("shared_upstreams", [])
    _names = [label(s, store) for s in shared]
    if len(_names) <= 3:
        shared_names = "; ".join(_names)
    else:
        shared_names = "; ".join(_names[:3]) + f" (+{len(_names) - 3} more shared upstream(s))"
    parts = [
        f"These {n} claims were proposed as independent ({claim_list}), but they are not: "
        f"they descend from a shared upstream — {shared_names}. Combining them as independent "
        f"draws is undefined; a product would count one source up to {n} times."
    ]

    infl = _lr_inflation(ids, store)
    if infl is not None:
        product, single = infl
        parts.append(
            f"Treated as independent, their illustrative likelihood ratios multiply to "
            f"{product:g}:1; counting the shared parent once, the honest reading is at most "
            f"{single:g}:1."
        )

    parts.append(
        f"What would un-refuse it: contest or drop the derivedFrom edge(s) to {shared_names}. "
        f"If a reviewer shows these claims do not in fact share that upstream, the verdict "
        f"flips to COMBINABLE — the refusal is a claim about this DAG, not about the world."
    )

    if verdict.get("conclusion_unchanged"):
        bs = label(verdict.get("backstop", ""), store)
        ar = label(verdict.get("at_risk_upstream", ""), store)
        parts.append(
            f"The conclusion itself still stands: {bs} is upstream-disjoint from {ar} and "
            f"independently sufficient, so what fails is only the claim that these are {n} "
            f"independent votes."
        )
    elif verdict.get("backstop") is not None and verdict.get("conclusion_unchanged") is False:
        bs = label(verdict.get("backstop", ""), store)
        ar = label(verdict.get("at_risk_upstream", ""), store)
        parts.append(
            f"The proposed backstop {bs} does not survive: it shares the at-risk premise "
            f"{ar}, so it cannot rescue the conclusion — a bare refusal stands."
        )

    return " ".join(parts)


def combine_verdict(
    record_ids: Iterable[str],
    store: Mapping[str, Mapping],
    *,
    backstop: str | None = None,
    at_risk_upstream: str | None = None,
) -> dict:
    """Refuse-to-combine verdict for a set of claims proposed as independent.

    ``backstop`` names a claim proposed as *independently sufficient* even if the
    shared premise fails; ``at_risk_upstream`` names the upstream whose possible
    failure is contemplated (e.g. the Hawking-radiation premise on the CERN case).
    When a set shares an upstream (would refuse) BUT the backstop is *mechanically*
    verified to be upstream-disjoint from ``at_risk_upstream``, the verdict is
    upgraded to ``REFUSE-TO-COMBINE-AS-INDEPENDENT`` with ``conclusion_unchanged``:
    the safety conclusion stands; what fails is only the claim that these are N
    independent votes. The disjointness is *checked*, never asserted — a backstop
    that turns out to share the at-risk premise leaves a bare REFUSE-TO-COMBINE and
    a note saying so.
    """
    ids = list(record_ids)
    s = shared_upstreams(ids, store)
    # the union of all shared upstreams across any pair (the laundered dependence)
    shared_any: set[str] = set(s["collective_shared"])
    for common in s["pairwise_shared"].values():
        shared_any.update(common)
    independent = not shared_any

    if independent:
        return {
            "claims": ids,
            "independent": True,
            "verdict": "COMBINABLE",
            "shared_upstreams": [],
            "pairwise_shared": s["pairwise_shared"],
            "reason": (
                "no shared upstream on the provenance dimension; independence holds "
                "(subject to legs (b)/(c) and a measured n_eff)"
            ),
        }

    out = {
        "claims": ids,
        "independent": False,
        "verdict": "REFUSE-TO-COMBINE",
        "shared_upstreams": sorted(shared_any),
        "pairwise_shared": s["pairwise_shared"],
        "reason": (
            f"claims share upstream(s) {sorted(shared_any)} -> not independent; "
            "combining as independent is undefined"
        ),
    }

    if backstop is not None:
        backstop_closure = ancestors(backstop, store) | {backstop}
        disjoint = at_risk_upstream is None or at_risk_upstream not in backstop_closure
        if disjoint:
            out["verdict"] = "REFUSE-TO-COMBINE-AS-INDEPENDENT"
            out["conclusion_unchanged"] = True
            out["backstop"] = backstop
            out["at_risk_upstream"] = at_risk_upstream
            out["note"] = (
                f"the safety conclusion stands; what fails is the claim that these are "
                f"{len(ids)} independent votes. The backstop {backstop} is upstream-disjoint "
                f"from the at-risk premise {at_risk_upstream} and is on its own sufficient."
            )
        else:
            out["conclusion_unchanged"] = False
            out["backstop"] = backstop
            out["note"] = (
                f"the proposed backstop {backstop} is NOT upstream-disjoint from the at-risk "
                f"premise {at_risk_upstream} (it shares it) -> it does not survive that premise's "
                f"failure; bare REFUSE-TO-COMBINE stands."
            )
    return out

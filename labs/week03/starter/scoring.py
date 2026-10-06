"""Scoring the router. TODO 5.

Two rules carried over from week 2 and one new one.

Carried over: report per route, as counts, never one overall percentage. At
four to seven gold records per route, one misroute moves that route by
fifteen to twenty five points, and a percentage at that sample size is a
lie told with a decimal point.

New this week: the confusion pairs matter more than the accuracy. Knowing
that the router is 20 out of 24 tells you to try harder. Knowing that it
sends requests to info, and only in that direction, tells you which
definition is wrong.
"""

from __future__ import annotations

import collections
from dataclasses import dataclass, field


@dataclass
class RouteScore:
    per_route: dict[str, list[int]] = field(default_factory=dict)   # [hit, n]
    confusion: collections.Counter = field(
        default_factory=collections.Counter)
    policy_fired: collections.Counter = field(
        default_factory=collections.Counter)
    evidence_ok: int = 0
    total: int = 0
    ambiguous_total: int = 0
    ambiguous_hits: int = 0
    confidences: list[float] = field(default_factory=list)

    @property
    def hits(self) -> int:
        return sum(h for h, _ in self.per_route.values())

    @property
    def unambiguous_hits(self) -> int:
        return self.hits - self.ambiguous_hits

    @property
    def unambiguous_total(self) -> int:
        return self.total - self.ambiguous_total


# --------------------------------------------------------------------------
# TODO 5. Count per route, collect the confusion pairs, record the policy.
# --------------------------------------------------------------------------

def score_routes(results, queries) -> RouteScore:
    """Fill in a RouteScore from the routed results.

    `results` is a list of `Routed`, aligned with `queries`.

    One judgment call you have to make deliberately, and it goes in
    DECISIONS.md. Do you score against `applied_route`, which is what the
    system actually did, or against `decision.route`, which is what the
    classifier wanted to do? They differ exactly when your policy fired.

    Scoring the intention flatters the system, because it takes credit for
    routes the policy overrode. Scoring what happened is what the sender
    experienced. Pick one for the headline number and say why.

    Fill in, per query: the per-route counts, the confusion pair when it is
    wrong, whether the evidence was verbatim, which policy check fired, the
    confidence value, and whether the query was one of the ambiguous four.
    """
    score = RouteScore()

    for r, q in zip(results, queries):
        gold = q.gold_route
        applied = r.applied_route

        # 1. Mise à jour du total général
        score.total += 1

        # 2. Compteur par route [hits, total]
        if gold not in score.per_route:
            score.per_route[gold] = [0, 0]
        score.per_route[gold][1] += 1  # Total pour cette route

        is_hit = gold == applied
        if is_hit:
            score.per_route[gold][0] += 1  # Succès pour cette route

        # 3. Matrice de confusion (uniquement en cas d'erreur)
        else:
            score.confusion[(gold, applied)] += 1

        # 4. Traitement des 4 requêtes ambiguës
        if getattr(q, "is_ambiguous", False):
            score.ambiguous_total += 1
            if is_hit:
                score.ambiguous_hits += 1

        # 5. Vérification de l'evidence exacte (verbatim)
        if r.evidence_ok:
            score.evidence_ok += 1

        # 6. Enregistrement de la règle de politique déclenchée
        if r.policy_fired is not None:
            score.policy_fired[r.policy_fired] += 1

        # 7. Collecte des niveaux de confiance du classifieur
        if r.decision is not None:
            score.confidences.append(r.decision.confidence)

    return score
    raise NotImplementedError("TODO 5: score the routes")


# --------------------------------------------------------------------------
# Given.
# --------------------------------------------------------------------------

def report(s: RouteScore, label: str) -> str:
    lines = [f"{label}: {s.hits}/{s.total} routed correctly"]
    lines.append(f"  excluding the ambiguous four: "
                 f"{s.unambiguous_hits}/{s.unambiguous_total}")
    lines.append("  per route: " + "  ".join(
        f"{r} {h}/{n}" for r, (h, n) in sorted(s.per_route.items())))
    lines.append(f"  evidence verbatim: {s.evidence_ok}/{s.total}")
    if s.confidences:
        lo, hi = min(s.confidences), max(s.confidences)
        lines.append(f"  confidence: min {lo:.2f} max {hi:.2f} "
                     f"distinct {len(set(s.confidences))}")
    if s.policy_fired:
        lines.append("  policy fired: " + "  ".join(
            f"{k} {v}" for k, v in s.policy_fired.most_common()))
    if s.confusion:
        lines.append("  confusion pairs, gold to applied:")
        for (g, p), n in s.confusion.most_common(6):
            lines.append(f"    {g:<10} -> {p:<10} {n}")
    return "\n".join(lines)

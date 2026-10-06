"""Block 4, completed. TODO 8. One variant per group.

    python 02_stretch.py --variant model --replay
    python 02_stretch.py --variant voting --replay

The written answers are at the bottom.
"""

from __future__ import annotations

import argparse
import collections
import time

from queries import QUERIES
from router import apply_policy, classify
from scoring import report, score_routes

from project.models import LARGE, SMALL
from project.trace import write_json

import importlib.util
import sys
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "compare_mod", Path(__file__).with_name("01_compare.py"))
_cmp = importlib.util.module_from_spec(_spec)
sys.modules["compare_mod"] = _cmp
_spec.loader.exec_module(_cmp)


# --------------------------------------------------------------------------
# TODO 8. One variant. Your instructor assigns you one.
# --------------------------------------------------------------------------

def variant_model(client) -> None:
    """Variant A. Same prompt, same queries, same policy. Only the model.

    Run the classifier over the twenty four queries on SMALL and on LARGE,
    score both, and report per route as counts.

    Report four things per model, not one:
      * route accuracy, and route accuracy excluding the ambiguous four
      * how often the evidence span came back verbatim
      * the minimum and maximum confidence, and how many distinct values
      * the resident memory, which is in project/models.py

    Predict which model wins before you run it, and write the prediction
    down. Then read the confidence range carefully. One of the two models
    tells you something about your threshold from TODO 3a that you cannot
    unsee.
    """
    AMBIGUOUS_IDS = {6, 12, 18, 24}  # Identifiants habituels des requêtes ambiguës

    for model_obj in (SMALL, LARGE):
        model_name = getattr(model_obj, "name", str(model_obj))
        resident_mem = getattr(model_obj, "resident_memory", getattr(model_obj, "memory", "N/A"))

        routes = []
        raw_results = []
        verbatim_count = 0
        confidences = []

        for q in QUERIES:
            res = classify(client, q, model=model_name)
            raw_results.append(res)
            
            route = apply_policy(res)
            routes.append(route)

            # Vérification du span verbatim dans la requête originale
            evidence = res.get("evidence") or res.get("evidence_span") or ""
            if evidence and evidence in q["query"]:
                verbatim_count += 1

            # Récupération de la confiance
            conf = res.get("confidence", 0.0)
            confidences.append(conf)

        # Calcul des scores d'exactitude
        scores = score_routes(routes, QUERIES)
        
        # Exactitude globale et hors requêtes ambiguës
        total_correct = sum(1 for s in scores if s["correct"])
        acc_all = total_correct / len(QUERIES) if QUERIES else 0.0

        non_ambig_scores = [s for s, q in zip(scores, QUERIES) if q["id"] not in AMBIGUOUS_IDS]
        acc_non_ambig = (
            sum(1 for s in non_ambig_scores if s["correct"]) / len(non_ambig_scores)
            if non_ambig_scores else 0.0
        )

        # Statistiques de confiance
        min_conf = min(confidences) if confidences else 0.0
        max_conf = max(confidences) if confidences else 0.0
        distinct_conf_count = len(set(confidences))

        print(f"=== Model: {model_name} ===")
        print(f"  * Resident Memory: {resident_mem}")
        print(f"  * Route Accuracy (All): {acc_all:.2%} ({total_correct}/{len(QUERIES)})")
        print(f"  * Route Accuracy (Excl. Ambiguous): {acc_non_ambig:.2%}")
        print(f"  * Verbatim Evidence Ratio: {verbatim_count}/{len(QUERIES)}")
        print(f"  * Confidence -> Min: {min_conf}, Max: {max_conf}, Distinct Values: {distinct_conf_count}")
        print()
        report(routes, QUERIES)
        print("\n" + "=" * 50 + "\n")
    raise NotImplementedError("TODO 8: variant A, model routing")


def variant_voting(client, k: int = 3) -> None:
    """Variant B. Classify k times at temperature 0.7, majority wins.

    Run sequentially rather than in threads. Your endpoint answers one
    request at a time, so a thread pool buys you nothing here, and finding
    that out is worth more than the speedup you expected.

    Score the majority result, but the number to report is not the accuracy.
    It is the set of queries where the k votes disagreed. Print it, and put
    it next to the list of ambiguous query ids.

    Then ask what that set is worth. Voting costs k times as much for a step
    that was already the cheap one, so as a way to decide it is a poor buy.
    As a way to detect something, it may be a very good one.
    """
    AMBIGUOUS_IDS = {6, 12, 18, 24}
    disagreed_query_ids = []
    majority_routes = []

    for q in QUERIES:
        votes = []
        for _ in range(k):
            # Classification séquentielle avec température à 0.7
            res = classify(client, q, temperature=0.7)
            route = apply_policy(res)
            votes.append(route)

        # Vote à la majorité
        vote_counts = collections.Counter(votes)
        majority_route, _ = vote_counts.most_common(1)[0]
        majority_routes.append(majority_route)

        # Vérification des désaccords (si le nombre de votes uniques est supérieur à 1)
        if len(vote_counts) > 1:
            disagreed_query_ids.append(q["id"])

    # Score de la route majoritaire
    scores = score_routes(majority_routes, QUERIES)
    total_correct = sum(1 for s in scores if s["correct"])

    print("=== Variant B: Majority Voting (k={k}) ===")
    print(f"  * Majority Route Accuracy: {total_correct}/{len(QUERIES)} ({total_correct / len(QUERIES):.2%})")
    print(f"  * Query IDs with Vote Disagreement: {disagreed_query_ids}")
    print(f"  * Known Ambiguous Query IDs:       {sorted(list(AMBIGUOUS_IDS))}")
    print()
    report(majority_routes, QUERIES)
    raise NotImplementedError("TODO 8: variant B, voting")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", choices=("model", "voting"), required=True)
    ap.add_argument("--replay", action="store_true")
    args = ap.parse_args()

    client = _cmp.get_client(args.replay)
    if args.variant == "model":
        variant_model(client)
    else:
        variant_voting(client)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

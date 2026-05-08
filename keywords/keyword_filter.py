from keywords.embedding_selector import (
    find_similar_canonical_keywords
)


# -----------------------------------
# Semantic Filtering Config
# -----------------------------------

MIN_SIMILARITY_FOR_AI = 0.55

DEBUG_FILTER = False


def filter_candidate_keywords(
    candidate_keywords: list[str]
) -> tuple[list[str], list[str]]:
    """
    Semantic pruning layer.

    Returns:
        (
            filtered_candidates,
            rejected_candidates
        )
    """

    filtered_candidates = []
    rejected_candidates = []

    for keyword in candidate_keywords:

        similar_candidates = (
            find_similar_canonical_keywords(
                keyword
            )
        )

        # -------------------------
        # No embedding neighbors
        # -------------------------
        if not similar_candidates:

            rejected_candidates.append(keyword)

            if DEBUG_FILTER:
                print(
                    f"[FILTER REJECT] "
                    f"{keyword} "
                    f"(no similar candidates)"
                )

            continue

        # -------------------------
        # Best similarity score
        # -------------------------
        best_similarity = max(
            item["similarity"]
            for item in similar_candidates
        )

        # -------------------------
        # Low semantic relevance
        # -------------------------
        if best_similarity < MIN_SIMILARITY_FOR_AI:

            rejected_candidates.append(keyword)

            if DEBUG_FILTER:
                print(
                    f"[FILTER REJECT] "
                    f"{keyword} "
                    f"(similarity={best_similarity:.4f})"
                )

            continue

        # -------------------------
        # Keep candidate
        # -------------------------
        filtered_candidates.append(keyword)

        if DEBUG_FILTER:
            print(
                f"[FILTER PASS] "
                f"{keyword} "
                f"(similarity={best_similarity:.4f})"
            )

    return (
        filtered_candidates,
        rejected_candidates
    )
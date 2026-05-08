from recommender.scorer import (
    score_paper_for_user
)


def calculate_novelty_bonus(
    paper: dict,
    user: dict
) -> float:

    paper_weights = paper.get(
        "paper_keyword_weights",
        {}
    )

    user_weights = user.get(
        "keyword_weights",
        {}
    )

    if not paper_weights:
        return 0.0

    novelty_scores = []

    for keyword in paper_weights:

        user_weight = float(
            user_weights.get(keyword, 0.0)
        )

        novelty = 1.0 - min(user_weight, 1.0)

        novelty_scores.append(novelty)

    if not novelty_scores:
        return 0.0

    return sum(novelty_scores) / len(
        novelty_scores
    )


def calculate_exploration_score(
    paper: dict,
    user: dict
) -> float:

    relevance = score_paper_for_user(
        paper,
        user
    )

    novelty = calculate_novelty_bonus(
        paper,
        user
    )

    exploration_score = (
        0.8 * relevance
        +
        0.2 * novelty
    )

    return round(exploration_score, 4)
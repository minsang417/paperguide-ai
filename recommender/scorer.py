import math


def calculate_vector_norm(vector: dict) -> float:
    total = 0.0

    for value in vector.values():
        total += float(value) ** 2

    return math.sqrt(total)


def normalize_vector(vector: dict) -> dict:
    norm = calculate_vector_norm(vector)

    if norm == 0:
        return {}

    return {
        key: float(value) / norm
        for key, value in vector.items()
    }


def score_paper_for_user(
    paper: dict,
    user: dict
) -> float:
    paper_vector = paper.get(
        "paper_keyword_weights",
        {}
    )

    user_vector = user.get(
        "keyword_weights",
        {}
    )

    if not paper_vector or not user_vector:
        return 0.0

    normalized_paper = normalize_vector(
        paper_vector
    )

    normalized_user = normalize_vector(
        user_vector
    )

    score = 0.0

    for keyword, paper_weight in normalized_paper.items():
        user_weight = normalized_user.get(
            keyword,
            0.0
        )

        score += paper_weight * user_weight

    return round(score, 4)
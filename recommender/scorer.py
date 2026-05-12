import math

from users.vector_utils import (
    expand_vector,
    NEUTRAL_WEIGHT
)

from recommender.vector_utils import (
    sparse_dot_product,
    paper_weights_to_sparse_vector
)

from keywords.vector_index import (
    get_vector_size
)


def _paper_sparse_norm(paper_sparse_vector):
    total = 0.0

    for item in paper_sparse_vector:
        if not isinstance(item, list) or len(item) != 2:
            continue

        _, weight = item
        total += float(weight) ** 2

    return math.sqrt(total)


def _user_norm_for_sparse_dimensions(
    user_vector,
    paper_sparse_vector
):
    total = 0.0

    for item in paper_sparse_vector:
        if not isinstance(item, list) or len(item) != 2:
            continue

        index, _ = item

        if index >= len(user_vector):
            continue

        total += float(user_vector[index]) ** 2

    return math.sqrt(total)


def score_paper_for_user(
    paper: dict,
    user: dict
):
    user_vector = user.get("keyword_vector")

    user_vector = expand_vector(
        user_vector,
        get_vector_size(),
        neutral_weight=NEUTRAL_WEIGHT
    )

    paper_sparse_vector = paper.get("paper_vector")

    if not paper_sparse_vector:
        paper_sparse_vector = paper_weights_to_sparse_vector(
            paper.get("paper_keyword_weights", {})
        )

    dot = sparse_dot_product(
        user_vector,
        paper_sparse_vector
    )

    paper_norm = _paper_sparse_norm(
        paper_sparse_vector
    )

    user_norm = _user_norm_for_sparse_dimensions(
        user_vector,
        paper_sparse_vector
    )

    if paper_norm == 0 or user_norm == 0:
        return 0.0

    return round(
        dot / (paper_norm * user_norm),
        6
    )
from users.data_store import (
    get_user,
    update_user_preferences
)

from users.vector_utils import (
    expand_vector,
    vector_to_weights_dict,
    set_user_keyword_weight,
    NEUTRAL_WEIGHT
)

from keywords.vector_index import (
    get_vector_size
)


MIN_WEIGHT = 0.0
MAX_WEIGHT = 3.0
DEFAULT_WEIGHT = NEUTRAL_WEIGHT
BASE_DELTA = 0.5


def apply_feedback_to_user(
    user_id: str,
    paper: dict,
    liked: bool = True
):

    target_user = get_user(user_id)

    if target_user is None:
        print(f"user not found: {user_id}")
        return

    keyword_vector = expand_vector(
        target_user.get("keyword_vector"),
        get_vector_size(),
        neutral_weight=DEFAULT_WEIGHT
    )

    keyword_weights = vector_to_weights_dict(
        keyword_vector,
        neutral_weight=DEFAULT_WEIGHT
    )

    paper_keyword_weights = paper.get(
        "paper_keyword_weights",
        {}
    )

    keyword_count = max(
        1,
        len(paper_keyword_weights)
    )

    adjustment_scale = 1 / keyword_count
    base_delta = BASE_DELTA * adjustment_scale

    for keyword, paper_weight in (
        paper_keyword_weights.items()
    ):

        current_weight = float(
            keyword_weights.get(
                keyword,
                DEFAULT_WEIGHT
            )
        )

        if liked:
            delta = base_delta
        else:
            delta = -base_delta

        new_weight = current_weight + (
            delta * float(paper_weight)
        )

        new_weight = min(
            MAX_WEIGHT,
            max(
                MIN_WEIGHT,
                round(new_weight, 4)
            )
        )

        keyword_weights[keyword] = new_weight

        keyword_vector = set_user_keyword_weight(
            keyword_vector,
            keyword,
            new_weight,
            neutral_weight=DEFAULT_WEIGHT
        )

    update_user_preferences(
        user_id,
        keyword_weights,
        keyword_vector
    )

    print(
        f"updated keyword vector "
        f"for {user_id}"
    )
from users.data_store import (
    get_user,
    update_keyword_weights
)


MIN_WEIGHT = 0.0
MAX_WEIGHT = 3.0
DEFAULT_WEIGHT = 0.1
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

    keyword_weights = target_user.get(
        "keyword_weights",
        {}
    )

    paper_keyword_weights = paper.get(
        "paper_keyword_weights",
        {}
    )

    for keyword, paper_weight in (
        paper_keyword_weights.items()
    ):

        current_weight = float(
            keyword_weights.get(
                keyword,
                DEFAULT_WEIGHT
            )
        )

        keyword_count = max(
            1,
            len(paper_keyword_weights)
        )

        adjustment_scale = 1 / keyword_count

        base_delta = BASE_DELTA * adjustment_scale

        if liked:
            delta = base_delta
        else:
            delta = -base_delta

        new_weight = current_weight + (
            delta * paper_weight
        )

        new_weight = min(
            MAX_WEIGHT,
            max(
                MIN_WEIGHT,
                round(new_weight, 4)
            )
        )

        keyword_weights[keyword] = new_weight

    update_keyword_weights(
        user_id,
        keyword_weights
    )

    print(
        f"updated keyword weights "
        f"for {user_id}"
    )
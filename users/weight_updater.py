from utils.file_io import load_json, save_json

USERS_PATH = "data/users/users.json"


def apply_feedback_to_user(
    user_id: str,
    paper: dict,
    liked: bool = True
):

    users = load_json(USERS_PATH)

    target_user = None

    for user in users:
        if user.get("user_id") == user_id:
            target_user = user
            break

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
            keyword_weights.get(keyword, 0.1)
        )

        keyword_count = max(
            1,
            len(paper_keyword_weights)
        )

        adjustment_scale = 1 / keyword_count

        base_delta = 0.5 * adjustment_scale

        if liked:
            delta = base_delta
        else:
            delta = -base_delta

        new_weight = current_weight + (
            delta * paper_weight
        )

        new_weight = max(
            0.0,
            round(new_weight, 4)
        )

        keyword_weights[keyword] = new_weight

    target_user["keyword_weights"] = (
        keyword_weights
    )

    save_json(
        USERS_PATH,
        users
    )

    print(
        f"updated keyword weights "
        f"for {user_id}"
    )
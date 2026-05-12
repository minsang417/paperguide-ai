from keywords.vector_index import (
    get_keyword_to_index_map,
    get_vector_size
)


NEUTRAL_WEIGHT = 0.1


def expand_vector(
    vector,
    size: int,
    neutral_weight: float = NEUTRAL_WEIGHT
):
    if not isinstance(vector, list):
        vector = []

    vector = [
        float(value)
        for value in vector
    ]

    if len(vector) < size:
        vector.extend(
            [neutral_weight] * (size - len(vector))
        )

    if len(vector) > size:
        vector = vector[:size]

    return vector


def build_neutral_user_vector(
    neutral_weight: float = NEUTRAL_WEIGHT
):
    size = get_vector_size()

    return [
        neutral_weight
        for _ in range(size)
    ]


def weights_dict_to_vector(
    keyword_weights: dict,
    neutral_weight: float = NEUTRAL_WEIGHT
):
    keyword_to_index = get_keyword_to_index_map()
    vector = build_neutral_user_vector(
        neutral_weight=neutral_weight
    )

    if not isinstance(keyword_weights, dict):
        return vector

    for keyword, weight in keyword_weights.items():
        index = keyword_to_index.get(keyword)

        if index is None:
            continue

        vector[index] = float(weight)

    return vector


def vector_to_weights_dict(
    vector,
    neutral_weight: float = NEUTRAL_WEIGHT
):
    keyword_to_index = get_keyword_to_index_map()

    vector = expand_vector(
        vector,
        get_vector_size(),
        neutral_weight=neutral_weight
    )

    result = {}

    for keyword, index in keyword_to_index.items():
        if index < len(vector):
            result[keyword] = vector[index]

    return result


def set_user_keyword_weight(
    vector,
    keyword: str,
    weight: float,
    neutral_weight: float = NEUTRAL_WEIGHT
):
    keyword_to_index = get_keyword_to_index_map()
    size = get_vector_size()

    vector = expand_vector(
        vector,
        size,
        neutral_weight=neutral_weight
    )

    index = keyword_to_index.get(keyword)

    if index is None:
        return vector

    vector[index] = float(weight)

    return vector
from keywords.vector_index import (
    get_keyword_to_index_map
)


def paper_weights_to_sparse_vector(
    paper_keyword_weights: dict
):
    keyword_to_index = get_keyword_to_index_map()

    sparse_vector = []

    if not isinstance(paper_keyword_weights, dict):
        return sparse_vector

    for keyword, weight in paper_keyword_weights.items():
        index = keyword_to_index.get(keyword)

        if index is None:
            continue

        sparse_vector.append([
            index,
            float(weight)
        ])

    sparse_vector.sort(
        key=lambda item: item[0]
    )

    return sparse_vector


def sparse_dot_product(
    user_vector,
    paper_sparse_vector
):
    if not isinstance(user_vector, list):
        return 0.0

    if not isinstance(paper_sparse_vector, list):
        return 0.0

    score = 0.0

    for item in paper_sparse_vector:
        if not isinstance(item, list) or len(item) != 2:
            continue

        index, paper_weight = item

        if not isinstance(index, int):
            continue

        if index >= len(user_vector):
            continue

        score += float(user_vector[index]) * float(paper_weight)

    return score
from utils.file_io import load_json, save_json


CANONICAL_KEYWORDS_PATH = "data/keywords/canonical_keywords.json"


def load_canonical_keywords():
    data = load_json(CANONICAL_KEYWORDS_PATH)

    if not isinstance(data, list):
        return []

    return data


def save_canonical_keywords(data):
    save_json(
        CANONICAL_KEYWORDS_PATH,
        data
    )


def ensure_vector_indices():
    keywords = load_canonical_keywords()

    used_indices = set()

    for item in keywords:
        index = item.get("vector_index")

        if isinstance(index, int):
            used_indices.add(index)

    next_index = 0

    for item in keywords:
        if isinstance(item.get("vector_index"), int):
            continue

        while next_index in used_indices:
            next_index += 1

        item["vector_index"] = next_index
        used_indices.add(next_index)

    save_canonical_keywords(keywords)

    return keywords


def get_keyword_to_index_map():
    keywords = ensure_vector_indices()

    result = {}

    for item in keywords:
        name = item.get("canonical_name")
        index = item.get("vector_index")

        if name is None or index is None:
            continue

        result[name] = index

    return result


def get_index_to_keyword_map():
    keyword_to_index = get_keyword_to_index_map()

    return {
        index: keyword
        for keyword, index in keyword_to_index.items()
    }


def get_vector_size():
    keyword_to_index = get_keyword_to_index_map()

    if not keyword_to_index:
        return 0

    return max(keyword_to_index.values()) + 1
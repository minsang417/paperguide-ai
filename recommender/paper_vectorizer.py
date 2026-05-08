def build_paper_keyword_weights(paper: dict) -> dict[str, float]:
    matched_keywords = paper.get("matched_keywords", [])

    keyword_weights = {}

    for keyword in matched_keywords:
        keyword_weights[keyword] = 1.0

    return keyword_weights
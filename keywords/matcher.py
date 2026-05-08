from utils.file_io import load_json

CANONICAL_PATH = "data/keywords/canonical_keywords.json"
SYNONYM_PATH = "data/keywords/synonym_map.json"

DEBUG_MATCHER = False


def build_canonical_lookup(canonical_keywords: list[dict]) -> dict:
    lookup = {}

    for item in canonical_keywords:
        canonical_name = item.get("canonical_name", "").strip().lower()
        keyword_id = item.get("keyword_id")

        if canonical_name:
            lookup[canonical_name] = {
                "keyword_id": keyword_id,
                "canonical_name": canonical_name
            }

    return lookup


def normalize_mapped_value(mapped_value) -> list[str]:
    if isinstance(mapped_value, str):
        return [mapped_value.strip().lower()]

    if isinstance(mapped_value, list):
        cleaned = []

        for item in mapped_value:
            item = str(item).strip().lower()

            if item and item not in cleaned:
                cleaned.append(item)

        return cleaned

    return []


def add_matched_keyword(
    mapped_keyword: str,
    canonical_lookup: dict,
    matched_keyword_ids: list[str],
    matched_keywords: list[str]
):
    if mapped_keyword not in canonical_lookup:
        return

    keyword_id = canonical_lookup[mapped_keyword]["keyword_id"]
    canonical_name = canonical_lookup[mapped_keyword]["canonical_name"]

    if keyword_id not in matched_keyword_ids:
        matched_keyword_ids.append(keyword_id)
        matched_keywords.append(canonical_name)


def match_keywords(normalized_keywords: list[str]) -> dict:
    canonical_keywords = load_json(CANONICAL_PATH)
    synonym_map = load_json(SYNONYM_PATH)

    canonical_lookup = build_canonical_lookup(canonical_keywords)

    matched_keyword_ids = []
    matched_keywords = []
    candidate_keywords = []

    for keyword in normalized_keywords:
        keyword = keyword.strip().lower()

        if not keyword:
            continue

        # 1. exact canonical match
        if keyword in canonical_lookup:
            add_matched_keyword(
                keyword,
                canonical_lookup,
                matched_keyword_ids,
                matched_keywords
            )

            if DEBUG_MATCHER:
                print(f"[MATCH] exact: {keyword}")

            continue

        # 2. synonym match
        if keyword in synonym_map:
            mapped_value = synonym_map[keyword]
            mapped_keywords = normalize_mapped_value(mapped_value)

            matched_before = len(matched_keyword_ids)

            for mapped_keyword in mapped_keywords:
                add_matched_keyword(
                    mapped_keyword,
                    canonical_lookup,
                    matched_keyword_ids,
                    matched_keywords
                )

            matched_after = len(matched_keyword_ids)

            if DEBUG_MATCHER:
                print(f"[MATCH] synonym: {keyword} -> {mapped_keywords}")

            # synonym_map에 있긴 한데 canonical에 실제로 연결된 게 없으면 candidate로 보냄
            if matched_after == matched_before:
                if keyword not in candidate_keywords:
                    candidate_keywords.append(keyword)

                    if DEBUG_MATCHER:
                        print(f"[MATCH] candidate: {keyword}")

            continue

        # 3. no match → candidate
        if keyword not in candidate_keywords:
            candidate_keywords.append(keyword)

            if DEBUG_MATCHER:
                print(f"[MATCH] candidate: {keyword}")

    return {
        "matched_keyword_ids": matched_keyword_ids,
        "matched_keywords": matched_keywords,
        "candidate_keywords": candidate_keywords
    }
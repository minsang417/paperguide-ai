from utils.file_io import load_json, save_json

CANDIDATE_PATH = "data/keywords/candidate_keywords.json"


def update_candidate_keywords(candidate_list: list[str], paper_id: str):
    candidates = load_json(CANDIDATE_PATH)

    candidate_map = {item["keyword"]: item for item in candidates}

    for keyword in candidate_list:
        if keyword in candidate_map:
            candidate_map[keyword]["count"] += 1
            candidate_map[keyword]["last_seen"] = paper_id
        else:
            candidate_map[keyword] = {
                "keyword": keyword,
                "count": 1,
                "first_seen": paper_id,
                "last_seen": paper_id,
                "status": "pending"
            }

    updated_candidates = list(candidate_map.values())
    save_json(CANDIDATE_PATH, updated_candidates)


def get_pending_candidates(candidate_list: list[str]) -> list[str]:
    candidates = load_json(CANDIDATE_PATH)
    candidate_map = {item["keyword"]: item for item in candidates}

    pending_keywords = []

    for keyword in candidate_list:
        status = candidate_map.get(keyword, {}).get("status", "pending")
        if status == "pending":
            pending_keywords.append(keyword)

    return pending_keywords
from datetime import datetime
from utils.file_io import load_json, save_json

CANONICAL_PATH = "data/keywords/canonical_keywords.json"
SYNONYM_PATH = "data/keywords/synonym_map.json"
CANDIDATE_PATH = "data/keywords/candidate_keywords.json"
REVIEW_LOG_PATH = "data/keywords/review_log.json"

AUTO_APPLY_THRESHOLD = 0.8


def log_review_action(keyword: str, decision: dict, applied: bool):
    logs = load_json(REVIEW_LOG_PATH)

    logs.append({
        "timestamp": datetime.now().isoformat(),
        "keyword": keyword,
        "action": decision.get("action"),
        "target": decision.get("target"),
        "confidence": decision.get("confidence"),
        "applied": applied,
        "similar_candidates": decision.get("similar_candidates"),
        "raw_response": decision.get("raw_response")
    })

    save_json(REVIEW_LOG_PATH, logs)


def update_candidate_status(keyword: str, new_status: str):
    candidates = load_json(CANDIDATE_PATH)

    for item in candidates:
        if item["keyword"] == keyword:
            item["status"] = new_status
            break

    save_json(CANDIDATE_PATH, candidates)

def apply_map(keyword: str, target):
    synonym_map = load_json(SYNONYM_PATH)

    synonym_map[keyword] = target

    save_json(SYNONYM_PATH, synonym_map)
    update_candidate_status(keyword, "approved")

    print(f"[APPLIED] synonym: {keyword} -> {target}")

def apply_new(keyword: str):
    canonical_keywords = load_json(CANONICAL_PATH)

    existing_names = {item["canonical_name"] for item in canonical_keywords}
    if keyword in existing_names:
        update_candidate_status(keyword, "approved")
        print(f"[SKIP] canonical already exists: {keyword}")
        return

    new_id = f"kw_{len(canonical_keywords)+1:03d}"

    canonical_keywords.append({
        "keyword_id": new_id,
        "canonical_name": keyword,
        "field": "biomedicine",
        "status": "confirmed"
    })

    save_json(CANONICAL_PATH, canonical_keywords)
    update_candidate_status(keyword, "approved")
    print(f"[APPLIED] new canonical: {keyword}")


def apply_reject(keyword: str):
    update_candidate_status(keyword, "rejected")
    print(f"[APPLIED] rejected: {keyword}")


def mark_pending_review(keyword: str):
    update_candidate_status(keyword, "pending_review")
    print(f"[PENDING] review needed: {keyword}")


def apply_ai_decision(keyword: str, decision: dict):
    action = decision.get("action")
    target = decision.get("target")
    confidence = float(decision.get("confidence", 0.0))

    if confidence < AUTO_APPLY_THRESHOLD:
        mark_pending_review(keyword)
        log_review_action(keyword, {
            **decision,
            "action": "pending_review"
        }, applied=False)
        return

    applied = False

    if action == "map" and target:
        apply_map(keyword, target)
        applied = True
    elif action == "new" and target:
        apply_new(target)
        # 원래 candidate keyword 상태도 승인 처리
        update_candidate_status(keyword, "approved")
        applied = True
    elif action == "reject":
        apply_reject(keyword)
        applied = True

    log_review_action(keyword, decision, applied=applied)
import argparse

from config import (
    SHOW_MOCK_COMPARISON,
    ENABLE_FEEDBACK,
    USE_REAL_AI,
    MAX_PAPERS_TO_PROCESS,
    ENABLE_EMAIL_SENDING
)

from keywords.extractor import extract_keywords
from keywords.normalizer import normalize_keywords
from keywords.matcher import match_keywords

from keywords.keyword_manager import (
    update_candidate_keywords,
    get_pending_candidates
)

from keywords.embedding_selector import (
    find_similar_canonical_keywords
)

from keywords.ai_keyword_processor import (
    process_candidate_mock,
    process_candidate_ai
)

from keywords.review_manager import (
    apply_ai_decision
)

from keywords.keyword_filter import (
    filter_candidate_keywords
)

from recommender.scorer import (
    score_paper_for_user
)

from recommender.paper_vectorizer import (
    build_paper_keyword_weights
)

from recommender.vector_utils import (
    paper_weights_to_sparse_vector
)

from recommender.exploration_scorer import (
    calculate_exploration_score
)

from recommender.recommendation_writer import (
    save_weekly_recommendations,
    write_weekly_markdown_report,
    split_recommendations
)

from recommender.insight_generator import (
    generate_easy_insight
)

from recommender.paper_store import (
    get_processed_paper_map,
    save_or_update_processed_paper
)

from utils.file_io import (
    load_json
)

from delivery.email_sender import (
    send_weekly_report_email
)

from users.feedback_sync import (
    sync_feedback_to_user_weights
)

from users.data_store import (
    get_users_by_delivery_frequency
)


PAPER_PATH = "data/papers/processed_papers.json"
RAW_PAPER_PATH = "data/papers/raw_papers.json"

CORE_RECOMMENDATION_COUNT = 3
EXPLORATION_RECOMMENDATION_COUNT = 2


def apply_keyword_matching_to_paper(paper):
    normalized_keywords = normalize_keywords(
        paper["raw_keywords"]
    )

    match_result = match_keywords(
        normalized_keywords
    )

    paper["normalized_keywords"] = normalized_keywords
    paper["matched_keyword_ids"] = (
        match_result["matched_keyword_ids"]
    )
    paper["matched_keywords"] = (
        match_result["matched_keywords"]
    )
    paper["candidate_keywords"] = (
        match_result["candidate_keywords"]
    )

    paper["paper_keyword_weights"] = (
        build_paper_keyword_weights(paper)
    )

    paper["paper_vector"] = paper_weights_to_sparse_vector(
        paper["paper_keyword_weights"]
    )

    return paper, match_result


def process_new_paper(paper):
    paper["raw_keywords"] = extract_keywords(
        paper["title"],
        paper["abstract"]
    )

    paper, match_result = apply_keyword_matching_to_paper(
        paper
    )

    update_candidate_keywords(
        match_result["candidate_keywords"],
        paper["paper_id"]
    )

    filtered_candidates, rejected_candidates = (
        filter_candidate_keywords(
            match_result["candidate_keywords"]
        )
    )

    pending_candidates = get_pending_candidates(
        filtered_candidates
    )

    canonical_updated = False

    for kw in pending_candidates:
        similar_candidates = (
            find_similar_canonical_keywords(kw)
        )

        if not similar_candidates:
            continue

        if SHOW_MOCK_COMPARISON:
            mock_result = process_candidate_mock(kw)
        else:
            mock_result = None

        if USE_REAL_AI:
            ai_result = process_candidate_ai(
                kw,
                similar_candidates
            )

            apply_ai_decision(
                kw,
                ai_result
            )

        else:
            apply_ai_decision(
                kw,
                mock_result
            )

        canonical_updated = True

    if canonical_updated:
        paper, _ = apply_keyword_matching_to_paper(
            paper
        )

    save_or_update_processed_paper(paper)

    return paper


def build_paper_score_item(
    paper,
    user
):
    score = score_paper_for_user(
        paper,
        user
    )

    exploration_score = calculate_exploration_score(
        paper,
        user
    )

    return {
        "paper_id": paper["paper_id"],
        "title": paper["title"],
        "abstract": paper.get("abstract", ""),
        "url": paper.get("url", ""),
        "source": paper.get("source", ""),
        "score": score,
        "exploration_score": exploration_score,
        "keywords": paper.get(
            "matched_keywords",
            []
        ),
        "paper_keyword_weights": paper.get(
            "paper_keyword_weights",
            {}
        ),
        "paper_vector": paper.get(
            "paper_vector",
            []
        ),
        "insight": paper.get("insight")
    }


def get_selected_paper_ids(
    paper_scores
):
    split_result = split_recommendations(
        paper_scores,
        CORE_RECOMMENDATION_COUNT,
        EXPLORATION_RECOMMENDATION_COUNT
    )

    selected_ids = set()

    for item in split_result["highly_relevant"]:
        selected_ids.add(item["paper_id"])

    for item in split_result["explore_nearby_topics"]:
        selected_ids.add(item["paper_id"])

    return selected_ids


def ensure_insight_for_paper(
    paper
):
    if paper.get("insight"):
        print(f"reuse insight: {paper['paper_id']}")
        return paper

    print(f"generate insight: {paper['paper_id']}")

    abstract = paper.get("abstract", "")

    if not abstract:
        paper["insight"] = {
            "one_sentence_summary":
                "초록이 제공되지 않았습니다.",

            "easy_explanation":
                "이 논문은 초록이 없어 신뢰할 수 있는 쉬운 설명을 생성할 수 없습니다.",

            "why_it_matters":
                "논문의 내용을 정확히 이해하려면 초록 또는 본문 정보가 필요합니다.",

            "question_to_explore":
                "이 논문의 초록이나 전문을 확인할 수 있을까요?"
        }

        save_or_update_processed_paper(paper)

        return paper

    paper["insight"] = generate_easy_insight(
        paper["title"],
        abstract
    )

    save_or_update_processed_paper(paper)

    return paper


def main(delivery_frequency="weekly"):
    print("main started")
    print(f"delivery frequency: {delivery_frequency}")

    sync_feedback_to_user_weights()

    users = get_users_by_delivery_frequency(
        delivery_frequency
    )

    if not users:
        print(f"no {delivery_frequency} users found")
        return

    raw_papers = load_json(RAW_PAPER_PATH)

    if not isinstance(raw_papers, list) or not raw_papers:
        print("no raw papers found")
        return

    if MAX_PAPERS_TO_PROCESS is not None:
        raw_papers = raw_papers[:MAX_PAPERS_TO_PROCESS]

    processed_paper_map = get_processed_paper_map()

    processed_papers = []
    processed_by_id = {}

    for paper in raw_papers:
        existing_processed = processed_paper_map.get(
            paper["paper_id"]
        )

        if existing_processed is not None:
            paper = existing_processed
        else:
            paper = process_new_paper(paper)

        processed_papers.append(paper)
        processed_by_id[paper["paper_id"]] = paper

    user_score_map = {}
    all_selected_paper_ids = set()

    for user in users:
        print(
            f"\n=== USER {user.get('name')} "
            f"<{user.get('email')}> ==="
        )

        paper_scores = []

        for paper in processed_papers:
            item = build_paper_score_item(
                paper,
                user
            )

            paper_scores.append(item)

        selected_ids = get_selected_paper_ids(
            paper_scores
        )

        all_selected_paper_ids.update(
            selected_ids
        )

        user_score_map[user["user_id"]] = {
            "user": user,
            "paper_scores": paper_scores
        }

    print(
        f"\nselected papers for recommendation: "
        f"{len(all_selected_paper_ids)}"
    )

    for paper_id in all_selected_paper_ids:
        paper = processed_by_id.get(paper_id)

        if not paper:
            continue

        paper = ensure_insight_for_paper(paper)

        processed_by_id[paper_id] = paper

    for user_id, data in user_score_map.items():
        user = data["user"]
        refreshed_scores = []

        for item in data["paper_scores"]:
            paper = processed_by_id.get(
                item["paper_id"]
            )

            if paper and paper.get("insight"):
                item["insight"] = paper["insight"]

            refreshed_scores.append(item)

        recommendation_data = (
            save_weekly_recommendations(
                user_id=user["user_id"],
                paper_scores=refreshed_scores,
                core_count=CORE_RECOMMENDATION_COUNT,
                exploration_count=EXPLORATION_RECOMMENDATION_COUNT
            )
        )

        write_weekly_markdown_report(
            recommendation_data
        )

        print(
            f"saved recommendations for {user_id}"
        )

        if ENABLE_EMAIL_SENDING:
            send_weekly_report_email(
                user,
                recommendation_data
            )

        if ENABLE_FEEDBACK:
            print(
                "feedback is enabled, but batch feedback "
                "is not implemented in multi-user mode."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--frequency",
        choices=[
            "weekly",
            "daily"
        ],
        default="weekly"
    )

    args = parser.parse_args()

    main(
        delivery_frequency=args.frequency
    )
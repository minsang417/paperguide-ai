import os
from datetime import datetime

from utils.file_io import save_json


def get_user_recommendation_dir(user_id: str) -> str:
    path = f"data/recommendations/{user_id}"
    os.makedirs(path, exist_ok=True)
    return path


def split_recommendations(
    paper_scores,
    core_count=3,
    exploration_count=2
):
    relevant_rankings = sorted(
        paper_scores,
        key=lambda x: x["score"],
        reverse=True
    )

    highly_relevant = relevant_rankings[:core_count]

    shown_ids = {
        item["paper_id"]
        for item in highly_relevant
    }

    exploration_rankings = sorted(
        paper_scores,
        key=lambda x: x["exploration_score"],
        reverse=True
    )

    explore_nearby_topics = []

    for item in exploration_rankings:
        if item["paper_id"] in shown_ids:
            continue

        explore_nearby_topics.append(item)

        if len(explore_nearby_topics) >= exploration_count:
            break

    return {
        "highly_relevant": highly_relevant,
        "explore_nearby_topics": explore_nearby_topics
    }


def save_weekly_recommendations(
    user_id,
    paper_scores,
    core_count=3,
    exploration_count=2
):
    split_result = split_recommendations(
        paper_scores,
        core_count,
        exploration_count
    )

    data = {
        "user_id": user_id,
        "generated_at": datetime.now().isoformat(),
        "highly_relevant": split_result["highly_relevant"],
        "explore_nearby_topics": split_result["explore_nearby_topics"]
    }

    user_dir = get_user_recommendation_dir(user_id)

    save_json(
        f"{user_dir}/weekly_recommendations.json",
        data
    )

    return data


def _format_item(item):
    insight = item.get("insight", {})

    lines = []

    lines.append(f"### {item['title']}\n")

    if item.get("url"):
        lines.append(
            f"[논문 보기]({item['url']})\n"
        )

    if insight:
        lines.append(
            f"**한 줄 요약:** "
            f"{insight.get('one_sentence_summary', '')}\n"
        )

        lines.append(
            f"**쉬운 설명:** "
            f"{insight.get('easy_explanation', '')}\n"
        )

        lines.append(
            f"**왜 중요한가:** "
            f"{insight.get('why_it_matters', '')}\n"
        )

        lines.append(
            f"**더 생각해볼 질문:** "
            f"{insight.get('question_to_explore', '')}\n"
        )

    lines.append(f"- 논문 ID: `{item['paper_id']}`")
    lines.append(f"- 출처: `{item.get('source', '')}`")
    lines.append(f"- 관련도 점수: `{item['score']}`")
    lines.append(f"- 탐색 추천 점수: `{item['exploration_score']}`")

    if item.get("keywords"):
        lines.append(
            f"- 관련 키워드: {', '.join(item['keywords'])}"
        )

    return "\n".join(lines)


def write_weekly_markdown_report(
    recommendation_data
):
    user_id = recommendation_data["user_id"]

    lines = []

    lines.append("# PaperGuide AI 주간 논문 추천\n")
    lines.append(f"사용자: {user_id}\n")
    lines.append(
        f"생성 시각: "
        f"{recommendation_data['generated_at']}\n"
    )

    lines.append("\n## 관심사와 높은 관련성이 있는 논문\n")

    for item in recommendation_data["highly_relevant"]:
        lines.append(_format_item(item))

    lines.append("\n## 관심사와 연결된 새로운 주제의 논문\n")

    for item in recommendation_data["explore_nearby_topics"]:
        lines.append(_format_item(item))

    user_dir = get_user_recommendation_dir(user_id)

    with open(
        f"{user_dir}/weekly_report.md",
        "w",
        encoding="utf-8"
    ) as f:
        f.write("\n\n".join(lines))
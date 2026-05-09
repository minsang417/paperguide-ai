import os
from dotenv import load_dotenv
from supabase import create_client

from utils.file_io import load_json
from users.weight_updater import apply_feedback_to_user


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

PAPER_PATH = "data/papers/processed_papers.json"


supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_unprocessed_feedbacks():
    result = (
        supabase.table("feedback_logs")
        .select("*")
        .eq("processed", False)
        .execute()
    )

    return result.data or []


def mark_feedback_as_processed(feedback_id: int):
    supabase.table("feedback_logs").update(
        {"processed": True}
    ).eq(
        "id", feedback_id
    ).execute()


def get_paper_map():
    papers = load_json(PAPER_PATH)

    if not isinstance(papers, list):
        return {}

    return {
        paper["paper_id"]: paper
        for paper in papers
        if "paper_id" in paper
    }


def sync_feedback_to_user_weights():
    feedbacks = get_unprocessed_feedbacks()

    if not feedbacks:
        print("no unprocessed feedback")
        return

    paper_map = get_paper_map()

    for feedback in feedbacks:
        feedback_id = feedback["id"]
        user_id = feedback["user_id"]
        paper_id = feedback["paper_id"]
        rating = feedback["rating"]

        paper = paper_map.get(paper_id)

        if paper is None:
            print(f"paper not found: {paper_id}")
            continue

        liked = rating == "like"

        apply_feedback_to_user(
            user_id=user_id,
            paper=paper,
            liked=liked,
        )

        mark_feedback_as_processed(feedback_id)

        print(
            f"processed feedback: "
            f"user={user_id}, paper={paper_id}, rating={rating}"
        )


if __name__ == "__main__":
    sync_feedback_to_user_weights()
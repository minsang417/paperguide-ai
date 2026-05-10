import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)


def get_all_processed_papers():
    result = (
        supabase.table("papers")
        .select("*")
        .execute()
    )

    return result.data or []


def get_processed_paper_map():
    papers = get_all_processed_papers()

    return {
        paper["paper_id"]: paper
        for paper in papers
        if paper.get("paper_id")
    }


def save_or_update_processed_paper(paper: dict):
    data = {
        "paper_id": paper["paper_id"],
        "title": paper.get("title", ""),
        "abstract": paper.get("abstract", ""),
        "url": paper.get("url", ""),
        "source": paper.get("source", ""),
        "raw_keywords": paper.get("raw_keywords", []),
        "normalized_keywords": paper.get("normalized_keywords", []),
        "matched_keyword_ids": paper.get("matched_keyword_ids", []),
        "matched_keywords": paper.get("matched_keywords", []),
        "candidate_keywords": paper.get("candidate_keywords", []),
        "paper_keyword_weights": paper.get("paper_keyword_weights", {}),
        "insight": paper.get("insight"),
    }

    result = (
        supabase.table("papers")
        .upsert(
            data,
            on_conflict="paper_id"
        )
        .execute()
    )

    return result.data
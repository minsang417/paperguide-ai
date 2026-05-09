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


def save_recommendation_log(recommendation_data: dict):
    result = (
        supabase.table("recommendation_logs")
        .insert({
            "user_id": recommendation_data["user_id"],
            "generated_at": recommendation_data["generated_at"],
            "highly_relevant": recommendation_data["highly_relevant"],
            "explore_nearby_topics": recommendation_data["explore_nearby_topics"],
        })
        .execute()
    )

    return result.data
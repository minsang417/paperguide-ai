import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_all_users():
    result = supabase.table("users").select("*").execute()
    return result.data or []


def get_user(user_id: str):
    result = (
        supabase.table("users")
        .select("*")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    return result.data


def update_keyword_weights(user_id: str, keyword_weights: dict):
    result = (
        supabase.table("users")
        .update({
            "keyword_weights": keyword_weights
        })
        .eq("user_id", user_id)
        .execute()
    )
    return result.data
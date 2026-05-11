import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client


load_dotenv(
    Path(__file__).resolve().parent.parent / ".env"
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)


def get_all_users():
    result = (
        supabase.table("users")
        .select("*")
        .eq("is_active", True)
        .execute()
    )

    return result.data or []


def get_user(user_id: str):
    result = (
        supabase.table("users")
        .select("*")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def update_keyword_weights(
    user_id: str,
    keyword_weights: dict
):
    result = (
        supabase.table("users")
        .update({
            "keyword_weights": keyword_weights
        })
        .eq("user_id", user_id)
        .execute()
    )

    return result.data


def email_exists(email: str):
    result = (
        supabase.table("users")
        .select("user_id")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    return bool(result.data)


def create_user(
    user_id: str,
    name: str,
    email: str,
    keyword_weights: dict,
    delivery_frequency: str = "weekly"
):
    result = (
        supabase.table("users")
        .insert({
            "user_id": user_id,
            "name": name,
            "email": email,
            "keyword_weights": keyword_weights,
            "is_active": True,
            "delivery_frequency": delivery_frequency
        })
        .execute()
    )

    return result.data

def deactivate_user(user_id: str):
    result = (
        supabase.table("users")
        .update({
            "is_active": False
        })
        .eq("user_id", user_id)
        .execute()
    )

    return result.data

def get_users_by_delivery_frequency(frequency: str):
    result = (
        supabase.table("users")
        .select("*")
        .eq("is_active", True)
        .eq("delivery_frequency", frequency)
        .execute()
    )

    return result.data or []

def update_delivery_frequency(
    email: str,
    frequency: str
):
    result = (
        supabase.table("users")
        .update({
            "delivery_frequency": frequency
        })
        .eq("email", email)
        .execute()
    )

    return result.data
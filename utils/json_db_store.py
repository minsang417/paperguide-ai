import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)

_json_cache = {}


def load_json_document(path: str, default=None):
    if path in _json_cache:
        return _json_cache[path]

    result = (
        supabase.table("json_documents")
        .select("content")
        .eq("path", path)
        .limit(1)
        .execute()
    )

    if not result.data:
        return default

    content = result.data[0]["content"]

    _json_cache[path] = content

    return content


def save_json_document(path: str, content):
    result = (
        supabase.table("json_documents")
        .upsert(
            {
                "path": path,
                "content": content
            },
            on_conflict="path"
        )
        .execute()
    )

    _json_cache[path] = content

    return result.data


def clear_json_cache():
    _json_cache.clear()
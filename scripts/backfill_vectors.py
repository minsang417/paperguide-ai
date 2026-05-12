import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

from keywords.vector_index import (
    ensure_vector_indices
)

from users.vector_utils import (
    weights_dict_to_vector
)

from recommender.vector_utils import (
    paper_weights_to_sparse_vector
)


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv(
    "SUPABASE_SERVICE_ROLE_KEY"
)

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY
)


def backfill_user_vectors():
    result = (
        supabase.table("users")
        .select("user_id, keyword_weights")
        .execute()
    )

    users = result.data or []

    for user in users:
        user_id = user["user_id"]

        keyword_vector = weights_dict_to_vector(
            user.get("keyword_weights", {})
        )

        supabase.table("users").update({
            "keyword_vector": keyword_vector
        }).eq(
            "user_id",
            user_id
        ).execute()

        print(
            f"user vector backfilled: "
            f"{user_id}, dim={len(keyword_vector)}"
        )


def backfill_paper_vectors():
    result = (
        supabase.table("papers")
        .select("paper_id, paper_keyword_weights")
        .execute()
    )

    papers = result.data or []

    for paper in papers:
        paper_id = paper["paper_id"]

        paper_vector = paper_weights_to_sparse_vector(
            paper.get("paper_keyword_weights", {})
        )

        supabase.table("papers").update({
            "paper_vector": paper_vector
        }).eq(
            "paper_id",
            paper_id
        ).execute()

        print(
            f"paper vector backfilled: "
            f"{paper_id}, nnz={len(paper_vector)}"
        )


def main():
    ensure_vector_indices()
    backfill_user_vectors()
    backfill_paper_vectors()


if __name__ == "__main__":
    main()
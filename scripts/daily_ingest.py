from config import MAX_PAPERS_TO_PROCESS

from main import process_new_paper

from utils.supabase_client import supabase

import traceback

def fetch_unprocessed_raw(limit):
    response = (
        supabase.table("raw_papers")
        .select("*")
        .eq("processed", False)
        .limit(limit)
        .execute()
    )

    return response.data or []


def mark_processed(paper_id):
    (
        supabase.table("raw_papers")
        .update({
            "processed": True
        })
        .eq("paper_id", paper_id)
        .execute()
    )


def main():
    print("daily ingest started")

    limit = MAX_PAPERS_TO_PROCESS or 300

    raw_papers = fetch_unprocessed_raw(
        limit
    )

    print(
        f"fetched raw papers: {len(raw_papers)}"
    )

    processed_count = 0
    failed_count = 0

    for raw in raw_papers:
        try:
            process_new_paper(
                raw
            )

            mark_processed(
                raw["paper_id"]
            )

            processed_count += 1

        except Exception as e:
            print(
                f"[FAILED] {raw['paper_id']}: {repr(e)}"
            )
            traceback.print_exc()
            failed_count += 1

    print(
        f"processed={processed_count}, "
        f"failed={failed_count}"
    )


if __name__ == "__main__":
    main()
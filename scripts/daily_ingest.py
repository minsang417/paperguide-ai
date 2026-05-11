from config import MAX_PAPERS_TO_PROCESS

from utils.file_io import load_json
from main import (
    RAW_PAPER_PATH,
    get_processed_paper_map,
    process_new_paper
)


def daily_ingest():
    print("daily ingest started")

    raw_papers = load_json(RAW_PAPER_PATH)

    if not isinstance(raw_papers, list) or not raw_papers:
        print("no raw papers found")
        return

    if MAX_PAPERS_TO_PROCESS is not None:
        raw_papers = raw_papers[:MAX_PAPERS_TO_PROCESS]

    processed_paper_map = get_processed_paper_map()

    processed_count = 0
    skipped_count = 0

    for paper in raw_papers:
        existing_processed = processed_paper_map.get(
            paper["paper_id"]
        )

        if (
            existing_processed
            and existing_processed.get("paper_keyword_weights")
        ):
            skipped_count += 1
            continue

        process_new_paper(paper)
        processed_count += 1

    print(f"processed: {processed_count}")
    print(f"skipped: {skipped_count}")


if __name__ == "__main__":
    daily_ingest()
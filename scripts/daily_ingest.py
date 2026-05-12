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

    processed_paper_map = get_processed_paper_map()

    candidate_papers = []

    for paper in raw_papers:
        paper_id = paper.get("paper_id")

        if not paper_id:
            continue

        existing_processed = processed_paper_map.get(
            paper_id
        )

        if (
            existing_processed
            and existing_processed.get("paper_keyword_weights")
        ):
            continue

        candidate_papers.append(paper)

    total_candidates = len(candidate_papers)

    if MAX_PAPERS_TO_PROCESS is not None:
        candidate_papers = candidate_papers[
            :MAX_PAPERS_TO_PROCESS
        ]

    processed_count = 0
    failed_count = 0

    for paper in candidate_papers:
        try:
            process_new_paper(paper)
            processed_count += 1

        except Exception as e:
            failed_count += 1

            print(
                f"[DAILY INGEST ERROR] "
                f"paper_id={paper.get('paper_id')} "
                f"error={repr(e)}"
            )

    skipped_count = len(raw_papers) - total_candidates

    print(f"raw papers: {len(raw_papers)}")
    print(f"unprocessed candidates: {total_candidates}")
    print(f"processed this run: {processed_count}")
    print(f"failed this run: {failed_count}")
    print(f"already processed skipped: {skipped_count}")


if __name__ == "__main__":
    daily_ingest()
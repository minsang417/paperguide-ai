import os
import time
import argparse
import requests
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from config import (
    OPENALEX_DAYS_BACK,
    OPENALEX_MAX_RESULTS_PER_JOURNAL,
    OPENALEX_PAGE_SIZE
)

from utils.file_io import load_json, save_json


load_dotenv()

BASE_URL = "https://api.openalex.org/works"
RAW_PAPER_PATH = "data/papers/raw_papers.json"

OPENALEX_EMAIL = os.getenv("OPENALEX_EMAIL", "")

TARGET_JOURNALS = [
    "Nature",
    "Nature Medicine",
    "Nature Biotechnology",
    "Nature Genetics",
    "Nature Neuroscience",
    "Nature Cancer",
    "Nature Immunology",
    "Nature Aging",
    "Nature Machine Intelligence",
    "Nature Physics",
    "Nature Methods",
    "Nature Human Behaviour",
    "Nature Communications",
    "Science",
    "New England Journal of Medicine"
]


def normalize_limit(value):
    if value is None:
        return None

    if int(value) <= 0:
        return None

    return int(value)


def get_date_range(days_back: int):
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days_back)

    return start_date.isoformat(), end_date.isoformat()


def reconstruct_abstract(abstract_inverted_index):
    if not abstract_inverted_index:
        return ""

    positions = []

    for word, indices in abstract_inverted_index.items():
        for index in indices:
            positions.append(
                (
                    index,
                    word
                )
            )

    positions.sort(
        key=lambda item: item[0]
    )

    return " ".join(
        word
        for _, word in positions
    )


def normalize_doi(doi):
    if not doi:
        return ""

    doi = str(doi).strip().lower()

    if doi.startswith("https://doi.org/"):
        doi = doi.replace(
            "https://doi.org/",
            ""
        )

    return doi


def get_source_name(work):
    primary_location = work.get(
        "primary_location"
    ) or {}

    source = primary_location.get(
        "source"
    ) or {}

    return source.get("display_name", "")


def get_source_id(work):
    primary_location = work.get(
        "primary_location"
    ) or {}

    source = primary_location.get(
        "source"
    ) or {}

    source_id = source.get("id", "")

    if source_id.startswith("https://openalex.org/"):
        source_id = source_id.replace(
            "https://openalex.org/",
            ""
        )

    return source_id


def get_work_url(work):
    primary_location = work.get(
        "primary_location"
    ) or {}

    landing_page_url = primary_location.get(
        "landing_page_url"
    )

    if landing_page_url:
        return landing_page_url

    doi = normalize_doi(
        work.get("doi")
    )

    if doi:
        return f"https://doi.org/{doi}"

    return work.get("id", "")


def work_to_paper(work, target_journal):
    title = work.get("display_name", "")

    abstract = reconstruct_abstract(
        work.get("abstract_inverted_index")
    )

    if not title or not abstract:
        return None

    doi = normalize_doi(
        work.get("doi")
    )

    if doi:
        paper_id = (
            "openalex_"
            + doi.replace("/", "_")
        )
    else:
        openalex_id = work.get("id", "")
        paper_id = (
            "openalex_"
            + openalex_id.rstrip("/").split("/")[-1]
        )

    journal = get_source_name(work)

    return {
        "paper_id": paper_id,
        "title": title,
        "abstract": abstract,
        "url": get_work_url(work),
        "source": "openalex",
        "journal": journal or target_journal,
        "openalex_source_id": get_source_id(work),
        "published_at": work.get("publication_date", ""),
        "doi": doi,
        "cited_by_count": work.get("cited_by_count", 0),
        "collected_at": datetime.now(timezone.utc).isoformat()
    }


def build_filter(start_date, end_date):
    return ",".join([
        "type:article",
        "has_abstract:true",
        f"from_publication_date:{start_date}",
        f"to_publication_date:{end_date}"
    ])


def fetch_journal_works(
    journal_name,
    days_back: int,
    max_results: int | None,
    page_size: int
):
    start_date, end_date = get_date_range(
        days_back
    )

    works = []
    page = 1

    print(
        f"[OPENALEX] date range: "
        f"{start_date} ~ {end_date}"
    )

    while True:
        params = {
            "search": journal_name,
            "filter": build_filter(
                start_date,
                end_date
            ),
            "per-page": page_size,
            "page": page,
            "sort": "publication_date:desc"
        }

        if OPENALEX_EMAIL:
            params["mailto"] = OPENALEX_EMAIL

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            print(
                f"[OPENALEX ERROR] {journal_name}: "
                f"{response.status_code} {response.text[:300]}"
            )
            break

        data = response.json()
        batch = data.get("results", [])

        if not batch:
            break

        added_this_page = 0

        for work in batch:
            source_name = get_source_name(work)

            if source_name.lower() != journal_name.lower():
                continue

            works.append(work)
            added_this_page += 1

            if (
                max_results is not None
                and len(works) >= max_results
            ):
                break

        print(
            f"[OPENALEX] {journal_name}: "
            f"page={page}, "
            f"batch={len(batch)}, "
            f"accepted={added_this_page}, "
            f"total={len(works)}"
        )

        if (
            max_results is not None
            and len(works) >= max_results
        ):
            break

        if len(batch) < page_size:
            break

        page += 1

        time.sleep(0.2)

    return works


def merge_raw_papers(new_papers):
    existing = load_json(RAW_PAPER_PATH)

    if not isinstance(existing, list):
        existing = []

    paper_map = {
        paper.get("paper_id"): paper
        for paper in existing
        if paper.get("paper_id")
    }

    added = 0
    updated = 0

    for paper in new_papers:
        paper_id = paper.get("paper_id")

        if not paper_id:
            continue

        if paper_id in paper_map:
            updated += 1
        else:
            added += 1

        paper_map[paper_id] = paper

    merged = list(
        paper_map.values()
    )

    save_json(
        RAW_PAPER_PATH,
        merged
    )

    return added, updated, len(merged)


def collect_openalex_papers(
    days_back: int = OPENALEX_DAYS_BACK,
    max_results_per_journal: int | None = OPENALEX_MAX_RESULTS_PER_JOURNAL,
    page_size: int = OPENALEX_PAGE_SIZE
):
    max_results_per_journal = normalize_limit(
        max_results_per_journal
    )

    all_papers = []

    print(
        f"[OPENALEX] settings: "
        f"days_back={days_back}, "
        f"max_results_per_journal={max_results_per_journal}, "
        f"page_size={page_size}"
    )

    for journal_name in TARGET_JOURNALS:
        print(
            f"[OPENALEX] collecting {journal_name}"
        )

        works = fetch_journal_works(
            journal_name,
            days_back=days_back,
            max_results=max_results_per_journal,
            page_size=page_size
        )

        journal_papers = []

        for work in works:
            paper = work_to_paper(
                work,
                journal_name
            )

            if paper:
                journal_papers.append(paper)

        print(
            f"[OPENALEX] {journal_name}: "
            f"{len(journal_papers)} papers"
        )

        all_papers.extend(
            journal_papers
        )

    added, updated, total = merge_raw_papers(
        all_papers
    )

    print(
        f"[OPENALEX] done. "
        f"added={added}, updated={updated}, total_raw={total}"
    )

    return all_papers


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--days",
        type=int,
        default=OPENALEX_DAYS_BACK,
        help="How many days back to collect papers"
    )

    parser.add_argument(
        "--max-per-journal",
        type=int,
        default=OPENALEX_MAX_RESULTS_PER_JOURNAL,
        help="Maximum papers per journal. Use 0 for unlimited."
    )

    parser.add_argument(
        "--page-size",
        type=int,
        default=OPENALEX_PAGE_SIZE,
        help="OpenAlex API page size"
    )

    args = parser.parse_args()

    collect_openalex_papers(
        days_back=args.days,
        max_results_per_journal=args.max_per_journal,
        page_size=args.page_size
    )


if __name__ == "__main__":
    main()
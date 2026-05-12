import os
import time
import requests
from datetime import datetime, timedelta, timezone
from utils.file_io import load_json, save_json

from dotenv import load_dotenv

load_dotenv()

SPRINGER_NATURE_API_KEY = os.getenv("SPRINGER_NATURE_API_KEY")

BASE_URL = "https://api.springernature.com/meta/v2/json"

RAW_PAPER_PATH = "data/papers/raw_papers.json"

NATURE_JOURNALS = [
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
    "Nature Communications"
]

PAGE_SIZE = 50
MAX_RESULTS_PER_JOURNAL = 150


def get_date_range(days_back: int = 7):
    end_date = datetime.now(timezone.utc).date()
    start_date = end_date - timedelta(days=days_back)

    return start_date.isoformat(), end_date.isoformat()


def normalize_text(value):
    if value is None:
        return ""

    if isinstance(value, list):
        return " ".join(
            str(item)
            for item in value
            if item
        ).strip()

    return str(value).strip()


def get_record_doi(record):
    doi = record.get("doi")

    if doi:
        return str(doi).strip().lower()

    identifier = record.get("identifier")

    if isinstance(identifier, str):
        if identifier.lower().startswith("doi:"):
            return identifier[4:].strip().lower()

    if isinstance(identifier, list):
        for item in identifier:
            if isinstance(item, str) and item.lower().startswith("doi:"):
                return item[4:].strip().lower()

    return ""


def get_record_url(record):
    url_items = record.get("url", [])

    if isinstance(url_items, list):
        for item in url_items:
            if isinstance(item, dict):
                value = item.get("value")
                if value:
                    return value

            elif isinstance(item, str):
                return item

    if isinstance(url_items, str):
        return url_items

    doi = get_record_doi(record)

    if doi:
        return f"https://doi.org/{doi}"

    return ""


def record_to_paper(record, journal_name):
    title = normalize_text(record.get("title"))
    abstract = normalize_text(record.get("abstract"))

    if not title or not abstract:
        return None

    doi = get_record_doi(record)

    if doi:
        paper_id = "nature_" + doi.replace("/", "_")
    else:
        fallback_id = (
            title.lower()
            .replace(" ", "_")
            .replace("/", "_")
        )[:120]

        paper_id = f"nature_{fallback_id}"

    publication_date = (
        record.get("publicationDate")
        or record.get("onlineDate")
        or record.get("printDate")
        or ""
    )

    return {
        "paper_id": paper_id,
        "title": title,
        "abstract": abstract,
        "url": get_record_url(record),
        "source": "nature",
        "journal": journal_name,
        "published_at": publication_date,
        "doi": doi
    }


def build_query(journal_name, start_date, end_date):
    return (
        f'publication:"{journal_name}" '
        f'type:JournalArticle '
        f'onlineDatefrom:{start_date} '
        f'onlineDateto:{end_date}'
    )


def fetch_journal_records(
    journal_name,
    days_back: int = 7
):
    if not SPRINGER_NATURE_API_KEY:
        raise RuntimeError(
            "SPRINGER_NATURE_API_KEY is missing"
        )

    start_date, end_date = get_date_range(days_back)

    records = []
    start_index = 1

    while len(records) < MAX_RESULTS_PER_JOURNAL:
        params = {
            "q": build_query(
                journal_name,
                start_date,
                end_date
            ),
            "s": start_index,
            "p": PAGE_SIZE,
            "api_key": SPRINGER_NATURE_API_KEY
        }

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=30
        )

        if response.status_code != 200:
            print(
                f"[NATURE ERROR] {journal_name}: "
                f"{response.status_code} {response.text[:300]}"
            )
            break

        data = response.json()
        batch = data.get("records", [])

        if not batch:
            break

        records.extend(batch)

        if len(batch) < PAGE_SIZE:
            break

        start_index += PAGE_SIZE

        time.sleep(0.3)

    return records


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

    merged = list(paper_map.values())

    save_json(
        RAW_PAPER_PATH,
        merged
    )

    return added, updated, len(merged)


def collect_nature_papers(days_back: int = 7):
    all_papers = []

    for journal_name in NATURE_JOURNALS:
        print(f"[NATURE] collecting {journal_name}")

        records = fetch_journal_records(
            journal_name,
            days_back=days_back
        )

        journal_papers = []

        for record in records:
            paper = record_to_paper(
                record,
                journal_name
            )

            if paper:
                journal_papers.append(paper)

        print(
            f"[NATURE] {journal_name}: "
            f"{len(journal_papers)} papers"
        )

        all_papers.extend(journal_papers)

    added, updated, total = merge_raw_papers(
        all_papers
    )

    print(
        f"[NATURE] done. "
        f"added={added}, updated={updated}, total_raw={total}"
    )

    return all_papers


if __name__ == "__main__":
    collect_nature_papers(days_back=7)
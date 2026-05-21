from utils.supabase_client import supabase
from utils.file_io import load_json

RAW_PATH = "data/papers/raw_papers.json"
BATCH_SIZE = 200


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def normalize_paper(paper):
    return {
        "paper_id": paper.get("paper_id"),
        "title": paper.get("title"),
        "abstract": paper.get("abstract"),
        "source": paper.get("source"),
        "journal": paper.get("journal"),
        "doi": paper.get("doi"),
        "url": paper.get("url"),
        "published_at": paper.get("published_at"),
        "collected_at": paper.get("collected_at"),
        "processed": False
    }


def main():
    papers = load_json(RAW_PATH)

    valid = []

    for paper in papers:
        if not paper.get("paper_id"):
            continue

        if not paper.get("title"):
            continue

        if not paper.get("abstract"):
            continue

        valid.append(
            normalize_paper(paper)
        )

    print(f"valid papers: {len(valid)}")

    total = 0

    for batch in chunk(valid, BATCH_SIZE):
        supabase.table("raw_papers").upsert(batch).execute()
        total += len(batch)
        print(f"migrated: {total}")


if __name__ == "__main__":
    main()
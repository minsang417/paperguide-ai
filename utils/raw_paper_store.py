from utils.supabase_client import supabase

BATCH_SIZE = 200


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def upsert_raw_papers(papers):
    if not papers:
        print("no raw papers to upsert")
        return

    total = 0

    for batch in chunk(papers, BATCH_SIZE):
        supabase.table("raw_papers").upsert(batch).execute()
        total += len(batch)

    print(f"raw upserted: {total}")
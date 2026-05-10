import json
from pathlib import Path

from utils.json_db_store import save_json_document


DATA_DIR = Path("data")


def migrate_json_files():
    json_files = DATA_DIR.rglob("*.json")

    count = 0

    for file_path in json_files:
        normalized_path = file_path.as_posix()

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:
            content = json.load(f)

        save_json_document(
            normalized_path,
            content
        )

        print(f"migrated: {normalized_path}")
        count += 1

    print(f"done. migrated {count} json files.")


if __name__ == "__main__":
    migrate_json_files()
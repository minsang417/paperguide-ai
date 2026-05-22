import json
import os

from utils.json_db_store import (
    load_json_document,
    save_json_document
)

LOCAL_ONLY_PREFIXES = [
    "data/keywords/canonical_embeddings.json",
    "data/keywords/candidate_keywords.json",
    "data/keywords/review_log.json",
]

def load_json(path):
    for prefix in LOCAL_ONLY_PREFIXES:
        if path == prefix:
            if not os.path.exists(path):
                return {}

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

    return load_json_document(path)


def save_json(path, data):
    os.makedirs(
        os.path.dirname(path),
        exist_ok=True
    )

    for prefix in LOCAL_ONLY_PREFIXES:
        if path == prefix:
            with open(
                path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    ensure_ascii=False,
                    indent=2
                )
            return

    save_json_document(path, data)
import json
import os

from utils.json_db_store import (
    load_json_document,
    save_json_document
)


def should_use_db(path: str):
    normalized_path = path.replace("\\", "/")

    return normalized_path.startswith("data/")


def load_json(path):
    if should_use_db(path):
        default = [] if path.endswith(".json") else None
        data = load_json_document(path, default=default)

        if data is None:
            return []

        return data

    if not os.path.exists(path):
        return []

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def save_json(path, data):
    if should_use_db(path):
        save_json_document(path, data)
        return

    folder = os.path.dirname(path)

    if folder:
        os.makedirs(
            folder,
            exist_ok=True
        )

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


def save_or_update_paper(path, paper):
    papers = load_json(path)

    if not isinstance(papers, list):
        papers = []

    paper_id = paper.get("paper_id")

    updated = False

    for index, existing_paper in enumerate(papers):
        if existing_paper.get("paper_id") == paper_id:
            papers[index] = paper
            updated = True
            break

    if not updated:
        papers.append(paper)

    save_json(
        path,
        papers
    )
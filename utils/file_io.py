import json
from pathlib import Path


def load_json(path: str):
    file_path = Path(path)

    if not file_path.exists():
        if path.endswith(".json"):
            if "synonym_map" in path:
                return {}
            return []
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data) -> None:
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_or_update_paper(path: str, paper: dict) -> None:
    papers = load_json(path)

    updated = False
    for i, existing_paper in enumerate(papers):
        if existing_paper.get("paper_id") == paper.get("paper_id"):
            papers[i] = paper
            updated = True
            break

    if not updated:
        papers.append(paper)

    save_json(path, papers)
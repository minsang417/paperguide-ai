from math import log
from utils.file_io import load_json

PAPERS_PATH = "data/papers/processed_papers.json"


def build_document_frequency() -> tuple[int, dict[str, int]]:
    papers = load_json(PAPERS_PATH)

    total_docs = len(papers)
    df = {}

    for paper in papers:
        matched_keywords = set(paper.get("matched_keywords", []))

        for keyword in matched_keywords:
            df[keyword] = df.get(keyword, 0) + 1

    return total_docs, df


def compute_idf(total_docs: int, df: int) -> float:
    # smoothing
    return log((total_docs + 1) / (df + 1))


def build_idf_map() -> dict[str, float]:
    total_docs, df_map = build_document_frequency()

    if total_docs == 0:
        return {}

    idf_map = {}
    for keyword, df in df_map.items():
        idf_map[keyword] = compute_idf(total_docs, df)

    return idf_map


def compute_normalized_factor(keyword: str, idf_map: dict[str, float]) -> float:
    if not idf_map:
        return 1.0

    avg_idf = sum(idf_map.values()) / len(idf_map)
    keyword_idf = idf_map.get(keyword, avg_idf)

    if avg_idf == 0:
        factor = 1.0
    else:
        factor = keyword_idf / avg_idf

    # 너무 크거나 작아지지 않게 제한
    factor = max(0.5, min(2.0, factor))
    return round(factor, 4)
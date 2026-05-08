import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

from utils.file_io import load_json, save_json


RAW_PAPERS_PATH = "data/papers/raw_papers.json"

NCBI_EMAIL = "smartsang417@naver.com"
NCBI_API_KEY = None

PUBMED_SEARCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
)

PUBMED_FETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
)

REQUEST_DELAY_SECONDS = 0.34


def _build_url(base_url: str, params: dict) -> str:
    return f"{base_url}?{urllib.parse.urlencode(params)}"


def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_xml(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8")


def _get_text(element) -> str:
    if element is None:
        return ""

    return "".join(element.itertext()).strip()


def search_pubmed_ids(
    query: str,
    start_date: str,
    end_date: str,
    batch_size: int = 100,
    max_total: int | None = 30
) -> list[str]:

    all_ids = []
    retstart = 0

    while True:
        params = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": batch_size,
            "retstart": retstart,
            "sort": "date",
            "datetype": "pdat",
            "mindate": start_date,
            "maxdate": end_date,
            "tool": "PaperGuideAI",
            "email": NCBI_EMAIL
        }

        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY

        url = _build_url(PUBMED_SEARCH_URL, params)
        data = _get_json(url)

        result = data.get("esearchresult", {})
        count = int(result.get("count", 0))
        ids = result.get("idlist", [])

        if not ids:
            break

        all_ids.extend(ids)

        print(
            f"fetched ids {retstart + 1}~"
            f"{retstart + len(ids)} / total {count}"
        )

        retstart += batch_size

        if max_total is not None and len(all_ids) >= max_total:
            all_ids = all_ids[:max_total]
            break

        if retstart >= count:
            break

        time.sleep(REQUEST_DELAY_SECONDS)

    return all_ids


def fetch_pubmed_details(pubmed_ids: list[str]) -> list[dict]:

    if not pubmed_ids:
        return []

    papers = []

    for i in range(0, len(pubmed_ids), 100):
        batch_ids = pubmed_ids[i:i + 100]

        params = {
            "db": "pubmed",
            "id": ",".join(batch_ids),
            "retmode": "xml",
            "tool": "PaperGuideAI",
            "email": NCBI_EMAIL
        }

        if NCBI_API_KEY:
            params["api_key"] = NCBI_API_KEY

        url = _build_url(PUBMED_FETCH_URL, params)
        xml_text = _get_xml(url)
        root = ET.fromstring(xml_text)

        for article in root.findall(".//PubmedArticle"):

            pmid = _get_text(article.find(".//PMID"))
            title = _get_text(article.find(".//ArticleTitle"))

            abstract_parts = []

            for abstract_text in article.findall(".//AbstractText"):
                text = _get_text(abstract_text)

                if text:
                    abstract_parts.append(text)

            abstract = " ".join(abstract_parts)

            year = ""
            pub_date = article.find(".//PubDate")

            if pub_date is not None:
                year = _get_text(pub_date.find("Year"))

            paper = {
                "paper_id": f"pubmed_{pmid}",
                "source": "PubMed",
                "pmid": pmid,
                "title": title,
                "abstract": abstract,
                "published_year": year,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                "collected_at": datetime.now().isoformat()
            }

            if title and abstract:
                papers.append(paper)

        time.sleep(REQUEST_DELAY_SECONDS)

    return papers


def merge_raw_papers(new_papers: list[dict]) -> list[dict]:

    existing_papers = load_json(RAW_PAPERS_PATH)

    if not isinstance(existing_papers, list):
        existing_papers = []

    paper_map = {
        paper["paper_id"]: paper
        for paper in existing_papers
        if "paper_id" in paper
    }

    added_count = 0
    updated_count = 0

    for paper in new_papers:
        paper_id = paper["paper_id"]

        if paper_id in paper_map:
            paper_map[paper_id].update(paper)
            updated_count += 1
        else:
            paper_map[paper_id] = paper
            added_count += 1

    merged = list(paper_map.values())

    save_json(RAW_PAPERS_PATH, merged)

    print(f"raw papers added: {added_count}")
    print(f"raw papers updated: {updated_count}")
    print(f"raw papers total: {len(merged)}")

    return merged


def collect_recent_pubmed_papers(
    days_back: int = 1,
    max_total: int | None = 30
) -> list[dict]:

    today = date.today()
    start = today - timedelta(days=days_back)

    start_date = start.isoformat()
    end_date = today.isoformat()

    # Broad PubMed query. Later we can restrict sources/journals if needed.
    query = "all[sb]"

    print(
        f"collecting PubMed papers from "
        f"{start_date} to {end_date}"
    )

    pubmed_ids = search_pubmed_ids(
        query=query,
        start_date=start_date,
        end_date=end_date,
        batch_size=100,
        max_total=max_total
    )

    print(f"found ids: {len(pubmed_ids)}")

    papers = fetch_pubmed_details(pubmed_ids)

    print(f"papers with title+abstract: {len(papers)}")

    merge_raw_papers(papers)

    return papers


def main():

    papers = collect_recent_pubmed_papers(
        days_back=1,
        max_total=30
    )

    print(f"collected {len(papers)} new candidate papers")

    for paper in papers:
        print(
            paper["paper_id"],
            "|",
            paper["title"]
        )


if __name__ == "__main__":
    main()
from utils.file_io import load_json, save_json

PAPER_PATH = "data/papers/processed_papers.json"


def main():
    papers = load_json(PAPER_PATH)

    if not isinstance(papers, list):
        print("invalid processed papers")
        return

    count = 0

    for paper in papers:
        if "insight" in paper:
            del paper["insight"]
            count += 1

    save_json(PAPER_PATH, papers)

    print(
        f"removed insight cache from "
        f"{count} papers"
    )


if __name__ == "__main__":
    main()
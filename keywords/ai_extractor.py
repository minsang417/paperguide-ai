import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv(Path(__file__).resolve().parent.parent / ".env")

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

MODEL = "gpt-4o-mini"

MIN_KEYWORDS = 5
MAX_KEYWORDS = 12


def _clean_keyword(keyword: str) -> str:
    keyword = keyword.strip().lower()

    keyword = re.sub(
        r"\s+",
        " ",
        keyword
    )

    keyword = keyword.strip(" .,:;()[]{}\"'")

    return keyword


def _parse_json_response(content: str):
    content = content.strip()

    if content.startswith("```"):
        content = re.sub(
            r"^```json",
            "",
            content
        )
        content = re.sub(
            r"^```",
            "",
            content
        )
        content = re.sub(
            r"```$",
            "",
            content
        )
        content = content.strip()

    return json.loads(content)


def _deduplicate_keywords(keywords: list[str]) -> list[str]:
    cleaned = []

    for keyword in keywords:
        if not isinstance(keyword, str):
            continue

        keyword = _clean_keyword(keyword)

        if not keyword:
            continue

        if len(keyword.split()) > 5:
            continue

        if keyword not in cleaned:
            cleaned.append(keyword)

    return cleaned[:MAX_KEYWORDS]


def extract_keywords_ai_mock(
    title: str,
    abstract: str
) -> list[str]:
    text = f"{title} {abstract}".lower()

    if "cancer" in text and "immunotherapy" in text:
        return [
            "cancer",
            "immunotherapy",
            "t cell",
            "tumor response"
        ]

    if "neuroscience" in text:
        return [
            "neuroscience",
            "protein aggregation",
            "neural cell"
        ]

    if "genetics" in text:
        return [
            "genetics",
            "cell",
            "protein"
        ]

    return [
        "cell"
    ]


def extract_keywords_ai_real(
    title: str,
    abstract: str
) -> list[str]:
    if not title or not abstract:
        return []

    prompt = f"""
You are extracting high-quality academic keywords for a paper recommendation system.

Title:
{title}

Abstract:
{abstract}

Task:
Extract {MIN_KEYWORDS} to {MAX_KEYWORDS} meaningful academic keywords.

Rules:
- Return only important scholarly concepts, methods, diseases, mechanisms, organisms, research fields, technologies, theories, or datasets.
- Do NOT return generic words or sentence fragments.
- Do NOT return phrases like "revealed that", "significant", "patients were", "results suggest", "video abstract", or other non-conceptual text.
- Prefer canonical academic terms over overly specific sentence fragments.
- Use lowercase.
- Use singular nouns when natural.
- Keep each keyword short: usually 1 to 4 words.
- If the paper is biomedical, include disease, mechanism, method, cell type, organism, or treatment terms when relevant.
- If the paper is not biomedical, still extract domain-specific scholarly concepts.
- Return JSON only.

Output format:
{{
  "keywords": [
    "keyword 1",
    "keyword 2"
  ]
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0
    )

    content = response.choices[0].message.content

    try:
        parsed = _parse_json_response(content)
    except Exception as e:
        print(
            f"[KEYWORD AI ERROR] failed to parse response: {repr(e)}"
        )
        return []

    keywords = parsed.get("keywords", [])

    if not isinstance(keywords, list):
        return []

    return _deduplicate_keywords(keywords)
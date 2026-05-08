import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client():

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set."
        )

    return OpenAI(api_key=api_key)


def estimate_keyword_importance(
    title: str,
    abstract: str,
    matched_keywords: list[str]
) -> dict[str, float]:

    if not matched_keywords:
        return {}

    client = _get_client()

    prompt = f"""
You are estimating semantic importance weights
for canonical biomedical keywords in a research paper.

Paper title:
{title}

Paper abstract:
{abstract}

Canonical keywords:
{matched_keywords}

Your task:
Estimate how central each canonical keyword is
to the paper's main scientific meaning.

Rules:
- Return an importance score between 0 and 1.
- Higher = more central to the paper.
- Lower = less important background mention.
- Avoid giving all keywords similar scores.
- Core scientific themes should have high scores.
- Peripheral concepts should have lower scores.

Example:
If a paper is mainly about cancer immunotherapy:
- cancer: high
- immunotherapy: high
- cell: low

Return JSON only.
"""

    response = client.responses.create(

        model="gpt-4.1-mini",

        input=prompt,

        text={
            "format": {
                "type": "json_schema",

                "name": "importance_scores",

                "schema": {
                    "type": "object",

                    "properties": {

                        "scores": {

                            "type": "array",

                            "items": {

                                "type": "object",

                                "properties": {

                                    "keyword": {
                                        "type": "string"
                                    },

                                    "importance": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1
                                    }
                                },

                                "required": [
                                    "keyword",
                                    "importance"
                                ],

                                "additionalProperties": False
                            }
                        }
                    },

                    "required": ["scores"],

                    "additionalProperties": False
                }
            }
        }
    )

    raw_text = response.output_text

    parsed = json.loads(raw_text)

    cleaned = {}

    for item in parsed.get("scores", []):

        keyword = str(
            item.get("keyword", "")
        ).strip()

        try:
            importance = float(
                item.get("importance", 0.0)
            )
        except:
            importance = 0.0

        importance = max(
            0.0,
            min(1.0, importance)
        )

        if keyword in matched_keywords:

            cleaned[keyword] = round(
                importance,
                4
            )

    # missing keywords fallback
    for keyword in matched_keywords:

        if keyword not in cleaned:
            cleaned[keyword] = 0.1

    return cleaned
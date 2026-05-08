import json
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def process_candidate_mock(keyword: str) -> dict[str, Any]:
    keyword = keyword.lower()

    if "tumor" in keyword:
        return {
            "action": "map",
            "target": "cancer",
            "confidence": 0.9
        }

    if "t cell" in keyword:
        return {
            "action": "map",
            "target": "t_cell",
            "confidence": 0.9
        }

    if len(keyword) < 5:
        return {
            "action": "reject",
            "target": None,
            "confidence": 0.8
        }

    return {
        "action": "new",
        "target": keyword,
        "confidence": 0.6
    }


def _validate_decision(data: dict[str, Any]) -> dict[str, Any]:
    action = str(data.get("action", "")).strip().lower()
    target = data.get("target")
    confidence = data.get("confidence", 0.0)

    if action not in {"map", "new", "reject"}:
        action = "reject"

    if isinstance(target, str):
        target = target.strip().lower()
        if target == "":
            target = None

    elif isinstance(target, list):
        cleaned_targets = []

        for item in target:
            cleaned_item = str(item).strip().lower()
            if cleaned_item and cleaned_item not in cleaned_targets:
                cleaned_targets.append(cleaned_item)

        target = cleaned_targets if cleaned_targets else None

    elif target is not None:
        target = None

    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    confidence = max(0.0, min(1.0, confidence))

    return {
        "action": action,
        "target": target,
        "confidence": confidence
    }


def process_candidate_ai(
    keyword: str,
    similar_candidates: list[dict]
) -> dict[str, Any]:
    client = _get_client()

    candidate_names = [
        item["canonical_name"]
        for item in similar_candidates
    ]

    prompt = f"""
You are a biomedical ontology normalization engine
for an AI research paper recommendation system.

Your job is to decide how a candidate keyword
should be handled.

Candidate keyword:
{keyword}

Possible canonical keywords selected
by embedding similarity:
{similar_candidates}

Available canonical keyword names:
{candidate_names}

You must choose ONE action:

1. "map"
- Use this when the candidate is semantically
  equivalent to one or more existing canonical keywords.

2. "new"
- Use this ONLY if the candidate represents
  a biologically meaningful,
  reusable,
  ontology-worthy concept
  that is NOT sufficiently represented
  by existing canonical keywords.

3. "reject"
- Use this for:
  - vague phrases
  - weak concepts
  - noisy extractions
  - incomplete phrases
  - temporary wording
  - generic process descriptions
  - low-information biomedical terms

IMPORTANT RULES:

GENERAL:
- Do NOT choose based only on embedding similarity score.
- Prefer semantically direct mappings.
- Avoid overly broad mappings.

MAPPING:
- Every mapping target MUST come exactly from:
{candidate_names}

- Multiple targets are allowed ONLY if
  multiple concepts are truly central.

- Prefer a single target whenever possible.

NEW CANONICAL RULES:
A "new" canonical keyword MUST satisfy ALL:

1. Biologically meaningful
2. Likely reusable across many papers
3. Stable long-term research concept
4. Useful as a recommendation preference dimension
5. NOT sufficiently represented by existing canonical combinations

DO NOT create new canonicals for:
- adjectives
- temporary phrases
- incomplete concepts
- generic wording
- minor phrase variations

PREFERRED CANONICAL STYLE:
- noun-like concepts
- stable biomedical terminology
- ontology-friendly naming

GOOD examples:
- autophagy
- epigenetics
- ferroptosis
- microbiome
- mutation

BAD examples:
- neurodegenerative
- related response
- activation during
- protein related

If a candidate is meaningful
but still too broad, incomplete, or unstable,
prefer "reject" over "new".

Examples:

candidate:
"genetic"

possible canonical:
["genetics"]

good output:
{{
  "action": "map",
  "target": "genetics",
  "confidence": 0.92
}}

candidate:
"cancer immunotherapy"

possible canonical:
["cancer", "immunotherapy"]

good output:
{{
  "action": "map",
  "target": ["cancer", "immunotherapy"],
  "confidence": 0.90
}}

candidate:
"cell responses"

possible canonical:
["cell"]

good output:
{{
  "action": "reject",
  "target": null,
  "confidence": 0.93
}}

candidate:
"neurodegenerative"

possible canonical:
["neuroscience"]

good output:
{{
  "action": "reject",
  "target": null,
  "confidence": 0.88
}}

candidate:
"ferroptosis"

possible canonical:
[]

good output:
{{
  "action": "new",
  "target": "ferroptosis",
  "confidence": 0.95
}}

Return JSON only.

Output schema:
{{
  "action": "map" | "new" | "reject",
  "target": string | list[string] | null,
  "confidence": number between 0 and 1
}}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "keyword_decision",
                "schema": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["map", "new", "reject"]
                        },
                        "target": {
                            "anyOf": [
                                {"type": "string"},
                                {
                                    "type": "array",
                                    "items": {"type": "string"}
                                },
                                {"type": "null"}
                            ]
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        }
                    },
                    "required": ["action", "target", "confidence"],
                    "additionalProperties": False
                }
            }
        }
    )

    raw_text = response.output_text
    parsed = json.loads(raw_text)

    validated = _validate_decision(parsed)

    if validated["action"] == "map":
        target = validated["target"]

        if isinstance(target, str):
            if target not in candidate_names:
                validated["action"] = "reject"
                validated["target"] = None
                validated["confidence"] = 0.0

        elif isinstance(target, list):
            filtered_targets = [
                item for item in target
                if item in candidate_names
            ]

            if filtered_targets:
                validated["target"] = filtered_targets
            else:
                validated["action"] = "reject"
                validated["target"] = None
                validated["confidence"] = 0.0

        else:
            validated["action"] = "reject"
            validated["target"] = None
            validated["confidence"] = 0.0

    validated["raw_response"] = raw_text
    validated["similar_candidates"] = similar_candidates

    return validated
import json
import os

from openai import OpenAI

from utils.file_io import load_json


CANONICAL_KEYWORDS_PATH = "data/keywords/canonical_keywords.json"

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def extract_canonical_names():
    data = load_json(CANONICAL_KEYWORDS_PATH)

    names = []

    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                names.append(item)

            elif isinstance(item, dict):
                name = (
                    item.get("canonical_name")
                    or item.get("name")
                    or item.get("keyword")
                    or item.get("id")
                )

                if name:
                    names.append(name)

    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str):
                names.append(value)

            elif isinstance(value, dict):
                name = (
                    value.get("canonical_name")
                    or value.get("name")
                    or value.get("keyword")
                    or key
                )

                if name:
                    names.append(name)

            else:
                names.append(key)

    return sorted(set(names))


def map_interest_to_canonical_keywords(
    interest: str,
    max_matches: int = 3
):
    canonical_names = extract_canonical_names()

    if not canonical_names:
        return []

    canonical_text = "\n".join(
        f"- {name}"
        for name in canonical_names
    )

    prompt = f"""
You are mapping a user's free-text academic interest to a fixed canonical keyword list.

User interest:
{interest}

Canonical keyword list:
{canonical_text}

Task:
Choose up to {max_matches} canonical keywords that are clearly semantically relevant to the user interest.

Rules:
- Only choose keywords that appear exactly in the canonical keyword list.
- Do not invent new keywords.
- If no canonical keyword is clearly relevant, return an empty list.
- Prefer precise scientific meaning over broad association.
- Return JSON only.

Output format:
{{
  "matches": [
    {{
      "canonical_name": "keyword_from_list",
      "reason": "short reason"
    }}
  ]
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
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
        parsed = json.loads(content)
    except json.JSONDecodeError:
        return []

    matches = parsed.get("matches", [])

    valid_names = set(canonical_names)

    cleaned_matches = []

    for match in matches:
        canonical_name = match.get("canonical_name")

        if canonical_name in valid_names:
            cleaned_matches.append({
                "canonical_name": canonical_name,
                "reason": match.get("reason", "")
            })

    return cleaned_matches
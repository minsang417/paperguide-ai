import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    return OpenAI(api_key=api_key)


def generate_easy_insight(
    title: str,
    abstract: str
) -> dict:
    client = _get_client()

    prompt = f"""
너는 고등학생이 최신 논문을 쉽게 이해하도록 돕는 과학 설명 도우미다.

논문 제목:
{title}

초록:
{abstract}

반드시 한국어로 설명해라.

JSON 형식으로 아래 4개를 반환해라.

1. one_sentence_summary
- 논문의 핵심 내용을 한 문장으로 요약

2. easy_explanation
- 고등학생도 이해할 수 있게 쉽게 설명
- 전문용어는 필요하면 쉽게 풀어 설명

3. why_it_matters
- 이 연구가 왜 중요한지 설명
- 의학/과학적으로 어떤 의미가 있는지

4. question_to_explore
- 이 논문을 보고 더 생각해볼 질문 1개

규칙:
- 과장 금지
- 초록에 없는 내용 상상 금지
- 불확실하면 불확실하다고 표현
- 자연스러운 한국어 사용
- 너무 길지 않게
- 논문 초록만 근거로 설명
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "paper_insight",
                "schema": {
                    "type": "object",
                    "properties": {
                        "one_sentence_summary": {
                            "type": "string"
                        },
                        "easy_explanation": {
                            "type": "string"
                        },
                        "why_it_matters": {
                            "type": "string"
                        },
                        "question_to_explore": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "one_sentence_summary",
                        "easy_explanation",
                        "why_it_matters",
                        "question_to_explore"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    return json.loads(response.output_text)
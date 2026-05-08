from typing import Any


def extract_keywords_ai_mock(title: str, abstract: str) -> list[str]:
    text = f"{title} {abstract}".lower()

    # 지금은 그냥 테스트용 mock
    if "cancer" in text and "immunotherapy" in text:
        return ["cancer", "immunotherapy", "t cell", "tumor response"]

    if "neuroscience" in text:
        return ["neuroscience", "protein aggregation", "neural cell"]

    if "genetics" in text:
        return ["genetics", "cell", "protein"]

    return ["cell"]


def extract_keywords_ai_real(title: str, abstract: str) -> list[str]:
    # 나중에 실제 AI 붙일 자리
    raise NotImplementedError("Real AI extractor is not enabled yet.")
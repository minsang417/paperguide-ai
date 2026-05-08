from config import EXTRACTOR_MODE
from keywords.rule_extractor import extract_keywords_rule
from keywords.ai_extractor import extract_keywords_ai_mock, extract_keywords_ai_real


def extract_keywords(title: str, abstract: str) -> list[str]:
    if EXTRACTOR_MODE == "rule":
        return extract_keywords_rule(title, abstract)

    elif EXTRACTOR_MODE == "ai_mock":
        return extract_keywords_ai_mock(title, abstract)

    elif EXTRACTOR_MODE == "ai":
        return extract_keywords_ai_real(title, abstract)

    else:
        raise ValueError(f"Unknown EXTRACTOR_MODE: {EXTRACTOR_MODE}")
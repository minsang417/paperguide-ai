def normalize_keywords(raw_keywords: list[str]) -> list[str]:
    removable_keywords = {
        "new", "advances", "advance", "study", "explores",
        "responses", "response", "environments", "environment"
    }

    normalization_map = {
        "tumors": "tumor",
        "cells": "cell",
        "responses": "response",
        "environments": "environment"
    }

    normalized = []

    for keyword in raw_keywords:
        keyword = keyword.strip().lower()

        if keyword in normalization_map:
            keyword = normalization_map[keyword]

        if keyword in removable_keywords:
            continue

        if keyword not in normalized:
            normalized.append(keyword)

    return normalized
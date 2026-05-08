def extract_keywords_rule(title: str, abstract: str) -> list[str]:
    text = f"{title} {abstract}".lower()
    text = text.replace(".", "").replace(",", "").replace("-", " ")
    words = text.split()

    stopwords = {
        "the", "a", "an", "this", "that", "in", "on", "of", "and",
        "to", "for", "with", "is", "are", "study", "explores",
        "we", "our", "these", "those"
    }

    weak_words = {
        "new", "advances", "advance", "response", "responses",
        "environment", "environments", "study", "explores"
    }

    banned_inside = {
        "in", "of", "with", "for", "to", "on", "and"
    }

    keywords = set()
    max_n = 3

    for n in range(1, max_n + 1):
        for i in range(len(words) - n + 1):
            gram_words = words[i:i+n]

            if gram_words[0] in stopwords or gram_words[-1] in stopwords:
                continue

            if all(len(w) <= 2 for w in gram_words):
                continue

            if any(word in banned_inside for word in gram_words[1:-1]):
                continue

            if n == 1 and gram_words[0] in weak_words:
                continue

            weak_count = sum(1 for word in gram_words if word in weak_words)
            if weak_count >= 2:
                continue

            phrase = " ".join(gram_words)
            keywords.add(phrase)

    return list(keywords)
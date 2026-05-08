from keywords.embedding_selector import find_similar_canonical_keywords

test_keywords = [
    "tumor immunity",
    "cancer immunotherapy",
    "t cell activation",
    "protein aggregation",
    "brain cell activity",
    "cell behavior",
    "random changes"
]

for keyword in test_keywords:
    results = find_similar_canonical_keywords(keyword)
    print("\nCandidate:", keyword)
    for item in results:
        print("  ", item)
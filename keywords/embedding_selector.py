from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from utils.file_io import load_json, save_json

CANONICAL_PATH = "data/keywords/canonical_keywords.json"
EMBEDDING_CACHE_PATH = "data/keywords/canonical_embeddings.json"

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

SIMILARITY_THRESHOLD = 0.55
MAX_CANDIDATES = 5

_model = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_text(text: str) -> list[float]:
    model = get_model()
    vector = model.encode(text)
    return vector.tolist()


def build_canonical_embedding_cache():
    canonical_keywords = load_json(CANONICAL_PATH)
    cache = load_json(EMBEDDING_CACHE_PATH)

    if isinstance(cache, list):
        cache = {}

    updated = False

    for item in canonical_keywords:
        keyword = item["canonical_name"]

        if keyword not in cache:
            cache[keyword] = embed_text(keyword)
            updated = True

    if updated:
        save_json(EMBEDDING_CACHE_PATH, cache)

    return cache


def cosine(vec1: list[float], vec2: list[float]) -> float:
    result = cosine_similarity([vec1], [vec2])[0][0]
    return float(result)


def find_similar_canonical_keywords(
    candidate_keyword: str,
    threshold: float = SIMILARITY_THRESHOLD,
    max_candidates: int = MAX_CANDIDATES
) -> list[dict]:
    cache = build_canonical_embedding_cache()
    candidate_vector = embed_text(candidate_keyword)

    results = []

    for canonical_name, canonical_vector in cache.items():
        similarity = cosine(candidate_vector, canonical_vector)

        if similarity >= threshold:
            results.append({
                "canonical_name": canonical_name,
                "similarity": round(similarity, 4)
            })

    results.sort(key=lambda x: x["similarity"], reverse=True)

    return results[:max_candidates]
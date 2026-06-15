"""Dewey-guided library search across books, magazines, and articles.

This module maps a free-text topic to a likely Dewey Decimal class, then
retrieves resources from public catalog APIs:
  - Google Books API (books + magazines)
  - Crossref API (journal articles)
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from . import topic_classifier as tc
from . import dewey_taxonomy as ddt


@dataclass(frozen=True)
class DeweyClass:
    number: str
    name: str
    keywords: tuple[str, ...]


DEWEY_CLASSES: tuple[DeweyClass, ...] = (
    DeweyClass("000", "Computer science, information & general works", (
        "ai", "artificial intelligence", "machine learning", "computer", "software",
        "programming", "coding", "data", "algorithm", "internet", "cybersecurity",
    )),
    DeweyClass("100", "Philosophy & psychology", (
        "philosophy", "ethics", "logic", "psychology", "mind", "consciousness",
    )),
    DeweyClass("200", "Religion", (
        "religion", "theology", "spirituality", "faith", "church", "buddhism", "islam",
    )),
    DeweyClass("300", "Social sciences", (
        "economics", "law", "politics", "education", "society", "culture", "business",
        "marketing", "finance", "management", "sociology",
    )),
    DeweyClass("400", "Language", (
        "language", "linguistics", "translation", "grammar", "vocabulary", "writing",
    )),
    DeweyClass("500", "Science", (
        "science", "physics", "chemistry", "biology", "math", "mathematics", "astronomy",
    )),
    DeweyClass("600", "Technology", (
        "engineering", "medicine", "health", "technology", "robotics", "design",
        "agriculture", "cooking",
    )),
    DeweyClass("700", "Arts & recreation", (
        "art", "music", "film", "sports", "game", "photography", "architecture",
    )),
    DeweyClass("800", "Literature", (
        "literature", "poetry", "novel", "fiction", "drama", "story",
    )),
    DeweyClass("900", "History & geography", (
        "history", "geography", "travel", "war", "country", "world", "civilization",
    )),
)


def infer_dewey(topic: str) -> dict:
    """Infer the best matching Dewey class for a free-text topic."""
    query = (topic or "").strip().lower()
    if not query:
        raise ValueError("Topic is required.")

    scored: list[tuple[int, DeweyClass]] = []
    for entry in DEWEY_CLASSES:
        score = sum(1 for kw in entry.keywords if kw in query)
        scored.append((score, entry))

    scored.sort(key=lambda item: item[0], reverse=True)
    best_score, best = scored[0]
    if best_score == 0:
        best = DEWEY_CLASSES[0]

    alternatives = [
        {
            "number": entry.number,
            "name": entry.name,
        }
        for score, entry in scored[1:4]
        if score > 0
    ]

    return {
        "number": best.number,
        "name": best.name,
        "alternatives": alternatives,
    }


def _embedding_rank(query: str) -> list[tuple[float, DeweyClass]]:
    """Semantic-ish rank using TF-IDF vectors over Dewey names + keywords.

    This keeps dependencies light while improving precision over pure keyword hits.
    """
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return []

    corpus = [f"{entry.name} {' '.join(entry.keywords)}" for entry in DEWEY_CLASSES]
    vect = TfidfVectorizer(ngram_range=(1, 2), stop_words="english")
    matrix = vect.fit_transform(corpus + [query])
    sims = cosine_similarity(matrix[-1], matrix[:-1]).ravel()
    return sorted(
        [(float(sim), DEWEY_CLASSES[i]) for i, sim in enumerate(sims)],
        key=lambda item: item[0],
        reverse=True,
    )


def infer_dewey_with_rerank(topic: str) -> dict:
    """Infer Dewey class using keyword scoring, then TF-IDF reranking when available."""
    query = (topic or "").strip().lower()
    if not query:
        raise ValueError("Topic is required.")

    keyword_rank: list[tuple[float, DeweyClass]] = []
    for entry in DEWEY_CLASSES:
        keyword_hits = sum(1 for kw in entry.keywords if kw in query)
        keyword_rank.append((float(keyword_hits), entry))

    emb_rank = _embedding_rank(query)
    emb_scores = {entry.number: score for score, entry in emb_rank}

    # Combined score prefers keyword certainty but uses embedding similarity to break ties.
    combined: list[tuple[float, DeweyClass]] = []
    for keyword_score, entry in keyword_rank:
        score = (keyword_score * 2.0) + emb_scores.get(entry.number, 0.0)
        combined.append((score, entry))
    combined.sort(key=lambda item: item[0], reverse=True)

    best_score, best = combined[0]
    if best_score <= 0:
        best = DEWEY_CLASSES[0]

    alternatives = [
        {"number": entry.number, "name": entry.name}
        for score, entry in combined[1:4]
        if score > 0
    ]

    return {
        "number": best.number,
        "name": best.name,
        "alternatives": alternatives,
        "method": "keyword+embedding" if emb_rank else "keyword",
    }


def topic_taxonomy_catalog() -> dict:
    """Map all known project topics/categories to Dewey classes."""
    topics: list[dict] = []
    for prompt_topic, topic_label in sorted(tc.PROMPT_TOPIC_LABELS.items()):
        topic_category = tc.PROMPT_TOPIC_CATEGORY.get(prompt_topic, tc.UNKNOWN_CATEGORY)
        dewey = infer_dewey(f"{topic_label} {topic_category}")
        topics.append(
            {
                "prompt_topic": prompt_topic,
                "topic_label": topic_label,
                "topic_category": topic_category,
                "dewey_number": dewey["number"],
                "dewey_name": dewey["name"],
            }
        )

    categories: list[dict] = []
    seen: set[str] = set()
    for topic_category in sorted(tc.PROMPT_TOPIC_CATEGORY.values()):
        if topic_category in seen:
            continue
        seen.add(topic_category)
        dewey = infer_dewey(topic_category)
        categories.append(
            {
                "topic_category": topic_category,
                "dewey_number": dewey["number"],
                "dewey_name": dewey["name"],
            }
        )

    return {
        "topics": topics,
        "categories": categories,
    }


def _catalog_matches(topic: str, catalog_topics: list[dict], *, limit: int = 8) -> list[dict]:
    query = topic.strip().lower()
    if not query:
        return []

    matches = [
        entry
        for entry in catalog_topics
        if query in entry["topic_label"].lower()
        or query in entry["topic_category"].lower()
        or query in entry["prompt_topic"].lower()
    ]
    return matches[:limit]


def _search_google_books(topic: str, *, print_type: str, limit: int, timeout: float) -> list[dict]:
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        "q": topic,
        "printType": print_type,
        "maxResults": min(limit, 40),
    }
    resp = httpx.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()

    items = payload.get("items", [])
    out: list[dict] = []
    for item in items[:limit]:
        info = item.get("volumeInfo", {})
        out.append(
            {
                "id": item.get("id", ""),
                "title": info.get("title", "Untitled"),
                "authors": info.get("authors", []),
                "published": info.get("publishedDate"),
                "source": "google_books",
                "resource_type": "magazine" if print_type == "magazines" else "book",
                "summary": info.get("description"),
                "url": info.get("infoLink"),
            }
        )
    return out


def _first_date_parts(item: dict) -> str | None:
    for key in ("published-print", "published-online", "created", "issued"):
        parts = item.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            values = [str(p) for p in parts[0][:3]]
            return "-".join(values)
    return None


def _search_crossref(topic: str, *, limit: int, timeout: float) -> list[dict]:
    url = "https://api.crossref.org/works"
    params = {
        "query": topic,
        "filter": "type:journal-article",
        "rows": limit,
    }
    resp = httpx.get(url, params=params, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    items = payload.get("message", {}).get("items", [])

    out: list[dict] = []
    for item in items[:limit]:
        title = item.get("title", ["Untitled"])
        container = item.get("container-title", [""])
        authors = []
        for author in item.get("author", [])[:5]:
            full = " ".join(x for x in [author.get("given", ""), author.get("family", "")] if x).strip()
            if full:
                authors.append(full)

        out.append(
            {
                "id": item.get("DOI", ""),
                "title": title[0] if title else "Untitled",
                "authors": authors,
                "published": _first_date_parts(item),
                "source": "crossref",
                "resource_type": "article",
                "journal": container[0] if container else None,
                "url": item.get("URL"),
            }
        )
    return out


def search_library_resources(topic: str, *, max_results_each: int = 5, timeout: float = 8.0) -> dict:
    """Return Dewey match + books/magazines/articles for a topic."""
    dewey = infer_dewey_with_rerank(topic)
    query = f"{topic} {dewey['number']}"
    taxonomy = topic_taxonomy_catalog()

    books: list[dict] = []
    magazines: list[dict] = []
    articles: list[dict] = []
    warnings: list[str] = []

    try:
        books = _search_google_books(query, print_type="books", limit=max_results_each, timeout=timeout)
    except Exception as exc:
        warnings.append(f"Book search unavailable: {exc}")

    try:
        magazines = _search_google_books(
            query,
            print_type="magazines",
            limit=max_results_each,
            timeout=timeout,
        )
    except Exception as exc:
        warnings.append(f"Magazine search unavailable: {exc}")

    try:
        articles = _search_crossref(query, limit=max_results_each, timeout=timeout)
    except Exception as exc:
        warnings.append(f"Article search unavailable: {exc}")

    return {
        "topic": topic,
        "dewey": dewey,
        "catalog_matches": _catalog_matches(topic, taxonomy["topics"]),
        "books": books,
        "magazines": magazines,
        "articles": articles,
        "warnings": warnings,
    }


# ===== DEWEY TAXONOMY API FUNCTIONS =====


def get_taxonomy_overview() -> dict:
    """Return all 10 main Dewey classes with their divisions."""
    result = {}
    for class_id in sorted(ddt.DEWEY_TAXONOMY.keys()):
        class_data = ddt.DEWEY_TAXONOMY[class_id]
        result[class_id] = {
            "name": class_data["name"],
            "divisions": class_data["divisions"],
        }
    return result


def get_taxonomy_class(class_id: str) -> dict | None:
    """Return details for a specific Dewey class with divisions."""
    if class_id not in ddt.DEWEY_TAXONOMY:
        return None
    class_data = ddt.DEWEY_TAXONOMY[class_id]
    return {
        "number": class_id,
        "name": class_data["name"],
        "divisions": class_data["divisions"],
    }


def get_taxonomy_detailed(class_id: str) -> dict | None:
    """Return detailed section-level breakdown for a Dewey class (when available).
    
    Currently detailed breakdowns are available for class 300 (Social Sciences).
    """
    detailed = ddt.get_detailed_breakdown(class_id)
    if not detailed:
        return None
    return detailed


def search_taxonomy(query: str) -> list[dict]:
    """Search Dewey taxonomy by keyword. Returns matching classes and divisions."""
    return ddt.search_taxonomy(query)

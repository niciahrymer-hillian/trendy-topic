"""Topic taxonomy + classifier for WildChat-style conversations.

Two layers:

1. A *mapping* from the dataset's raw ``prompt_topic`` codes (12 of them in the
   country CSV pack) to (a) a human-readable label and (b) a broad category drawn
   from the project spec's topic taxonomy. This is the primary, deterministic path
   because the WildChat sample already ships a ``prompt_topic`` per row.

2. A keyword *fallback* classifier for rows that have no ``prompt_topic`` (e.g. a
   raw Hugging Face export). It scores cleaned text against keyword buckets.

Keeping both means the same dashboard logic works whether topics are pre-labeled
or have to be inferred.
"""

from __future__ import annotations

# --- Layer 1: map raw prompt_topic codes -> readable label + broad category ----

# Readable label for each of the 12 prompt_topic codes in the WildChat pack.
PROMPT_TOPIC_LABELS = {
    "creative_writing": "Creative Writing",
    "entertainment_games": "Entertainment & Games",
    "education_homework": "Education & Homework",
    "business_email": "Business Email",
    "job_career": "Job & Career",
    "data_analysis": "Data Analysis",
    "coding_debugging": "Coding & Debugging",
    "health_general_info": "Health Info",
    "travel_local_help": "Travel & Local Help",
    "personal_planning": "Personal Planning",
    "general_information": "General Information",
    "translation_language": "Translation & Language",
}

# Broad category (from the project spec taxonomy) for each prompt_topic code.
PROMPT_TOPIC_CATEGORY = {
    "creative_writing": "Entertainment & Creativity",
    "entertainment_games": "Entertainment & Creativity",
    "education_homework": "Education",
    "business_email": "Business & Career",
    "job_career": "Business & Career",
    "data_analysis": "Programming & Tech",
    "coding_debugging": "Programming & Tech",
    "health_general_info": "Health & Wellness",
    "travel_local_help": "Travel & Culture",
    "personal_planning": "Daily Life & Planning",
    "general_information": "Daily Life & Planning",
    "translation_language": "Translation & Language",
}

UNKNOWN_LABEL = "Other / unclear"
UNKNOWN_CATEGORY = "Other"


def label_for(prompt_topic: str | None) -> str:
    """Human-readable label for a raw prompt_topic code."""
    if not prompt_topic:
        return UNKNOWN_LABEL
    return PROMPT_TOPIC_LABELS.get(str(prompt_topic).strip().lower(), UNKNOWN_LABEL)


def category_for(prompt_topic: str | None) -> str:
    """Broad spec-taxonomy category for a raw prompt_topic code."""
    if not prompt_topic:
        return UNKNOWN_CATEGORY
    return PROMPT_TOPIC_CATEGORY.get(str(prompt_topic).strip().lower(), UNKNOWN_CATEGORY)


# --- Layer 2: keyword fallback for rows with no prompt_topic --------------------

TOPIC_KEYWORDS = {
    "Coding & Debugging": ["python", "java", "code", "debug", "javascript", "sql", "api", "error"],
    "Education & Homework": ["homework", "study", "school", "lesson", "teacher", "learn", "essay"],
    "Business Email": ["email", "meeting", "client", "proposal", "invoice"],
    "Job & Career": ["resume", "cv", "interview", "career", "job", "cover letter"],
    "Data Analysis": ["dataset", "pandas", "chart", "statistics", "analyze", "summarize"],
    "Health Info": ["health", "doctor", "fitness", "anxiety", "diet", "symptom"],
    "Travel & Local Help": ["travel", "hotel", "flight", "visa", "trip", "directions"],
    "Translation & Language": ["translate", "translation", "grammar", "language", "pronounce"],
    "Creative Writing": ["story", "poem", "song", "character", "novel", "lyrics"],
}


def classify_topic(text: str) -> dict:
    """Keyword fallback. Returns the readable label + a rough confidence.

    Used only when a row has no ``prompt_topic``; the deterministic mapping above
    is preferred whenever the dataset already provides the code.
    """
    clean = (text or "").lower()
    best_label = UNKNOWN_LABEL
    best_count = 0

    for label, keywords in TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in clean)
        if count > best_count:
            best_label = label
            best_count = count

    confidence = min(1.0, best_count / 3)
    return {"topic_label": best_label, "topic_confidence": confidence}

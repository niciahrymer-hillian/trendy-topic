"""ElevenLabs voice briefing placeholder.

Only send safe aggregated summaries to voice APIs. Never send raw sensitive chat content.
"""


def build_country_briefing(country: str, top_topics: list[str], key_insight: str) -> str:
    topics = ", ".join(top_topics)
    return (
        f"Here is the AI conversation trend briefing for {country}. "
        f"The top topics are {topics}. "
        f"Key insight: {key_insight}"
    )

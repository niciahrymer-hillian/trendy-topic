"""Agentic 'Ask the Dataset' assistant.

Instead of feeding the LLM the same fixed stats every time, the assistant:

  1. PLANS which tools to gather data with — the LLM picks tools+args from a
     catalog (with a deterministic regex planner as a no-key/fallback path).
  2. RUNS those tools over the aggregated dataset (counts, shares, sentiment,
     trends, comparisons, Dewey/library lookup) — never raw conversation text.
  3. SYNTHESIZES a grounded answer from exactly the data it gathered.

It also returns structured extras so the UI can render results inline:
  - ``comparison`` (when countries are compared)
  - ``library``   (Dewey-labelled resources when a resource is requested)

The LLM goes through src/llm.chat (Groq primary, Anthropic fallback). Clients are
injectable so the planning/synthesis logic is testable without a key.
"""

from __future__ import annotations

import json
import re

import pandas as pd

from . import analysis as an, dewey_library_search as dls, llm

SYSTEM_SYNTH = (
    "You are the analytics assistant for 'Trendy Topic', a dashboard about what people "
    "ask AI around the world. Answer the user's question using ONLY the JSON data gathered "
    "for you — never invent numbers. Be concise (2-4 sentences), cite the specific figures "
    "you used, and directly answer what was asked (don't just list tables). If a comparison "
    "or resource list was gathered, summarise the takeaway. If the data can't answer, say so "
    "and suggest a question it can answer."
)

SYSTEM_PLAN = (
    "You plan how to answer questions about the 'Trendy Topic' dataset by choosing data tools. "
    "Return ONLY JSON: {\"intent\": <string>, \"calls\": [{\"tool\": <name>, \"args\": {...}}]}. "
    "Pick the fewest tools that fully answer the question. Use exact country/language names from "
    "the provided lists. intent is one of: compare, resource, sentiment, trend, country, topic, overview."
)


# --- Tools: each returns JSON-serialisable aggregates (no raw conversations) ---

def _records(frame: pd.DataFrame) -> list[dict]:
    return frame.to_dict(orient="records")


def tool_global_overview(df: pd.DataFrame) -> dict:
    return {
        "summary": an.global_summary(df),
        "top_topics": _records(an.topic_counts(df).head(8)),
        "by_country": _records(an.country_volume(df)[["country", "conversations"]]),
    }


def tool_country_profile(df: pd.DataFrame, country: str) -> dict:
    sub = df[df["country"] == country]
    if sub.empty:
        return {"country": country, "error": "no data for this country"}
    return {
        "country": country,
        "conversations": int(len(sub)),
        "top_topics": _records(an.topic_counts(sub).head(5)),
        "sentiment": _records(an.sentiment_breakdown(sub)),
        "languages": _records(an.language_distribution(sub)),
    }


def tool_compare_countries(df: pd.DataFrame, countries: list[str]) -> dict:
    bundle = an.country_comparison_bundle(df, countries)
    return {
        "countries": countries,
        "volume": _records(bundle["volume"]),
        "topics": _records(bundle["topics"]),
        "sentiment": _records(bundle["sentiment"]),
        "languages": _records(bundle["languages"]),
    }


def tool_sentiment(df: pd.DataFrame, country: str | None = None) -> dict:
    sub = df if not country else df[df["country"] == country]
    return {"scope": country or "global", "sentiment": _records(an.sentiment_breakdown(sub))}


def tool_trends(df: pd.DataFrame, topic: str | None = None) -> dict:
    return {"topic": topic or "all", "trend": _records(an.trend_over_time(df, topic=topic))}


def tool_top_topics(df: pd.DataFrame, country: str | None = None, language: str | None = None) -> dict:
    sub = df
    if country:
        sub = sub[sub["country"] == country]
    if language:
        sub = sub[sub["language"] == language]
    return {"country": country, "language": language, "top_topics": _records(an.topic_counts(sub).head(8))}


def tool_country_volume(df: pd.DataFrame) -> dict:
    return {"by_country": _records(an.country_volume(df)[["country", "conversations"]])}


def tool_search_library(topic: str) -> dict:
    """Dewey-labelled resource lookup (books/magazines/articles)."""
    return dls.search_library_resources(topic, max_results_each=5)


TOOL_CATALOG = {
    "global_overview": "Headline metrics and global top topics. args: none.",
    "country_profile": "One country's topics, sentiment, and languages. args: country.",
    "country_volume": "Conversation counts per country, ranked. args: none.",
    "compare_countries": "Side-by-side topics/sentiment/languages for 2+ countries. args: countries (list).",
    "sentiment": "Sentiment breakdown, optionally for one country. args: country (optional).",
    "trends": "Topic volume over time, optionally for one topic. args: topic (optional).",
    "top_topics": "Most-asked topics, optionally filtered. args: country (optional), language (optional).",
    "search_library": "Dewey-classified library resources for a subject. args: topic.",
}


# --- Entity matching --------------------------------------------------------

def _known(df: pd.DataFrame, col: str) -> list[str]:
    return sorted(df[col].dropna().unique().tolist())


def _find_countries(question: str, countries: list[str]) -> list[str]:
    q = question.lower()
    found = [c for c in countries if c.lower() in q]
    # common aliases
    for alias, canonical in {"usa": "United States", "us ": "United States", "u.s": "United States",
                             "uk": "United Kingdom", "britain": "United Kingdom", "america": "United States"}.items():
        if alias in q and canonical in countries and canonical not in found:
            found.append(canonical)
    return found


def _find_language(question: str, languages: list[str]) -> str | None:
    q = question.lower()
    return next((lang for lang in languages if lang.lower() in q), None)


# --- Planning ---------------------------------------------------------------

COMPARE_RE = re.compile(r"\b(compare|comparison|versus|vs\.?|difference between|against)\b", re.I)
RESOURCE_RE = re.compile(r"\b(resource|resources|article|articles|book|books|reading|read about|"
                         r"more info|learn more|reference|study|dewey|library)\b", re.I)
SENTIMENT_RE = re.compile(r"\b(sentiment|mood|positive|negative|happy|upbeat|feel|feeling|tone)\b", re.I)
TREND_RE = re.compile(r"\b(trend|trends|over time|growing|rising|declin|change over|trajectory)\b", re.I)
COUNTRY_VOLUME_RE = re.compile(r"\b(by country|which countr|most conversations|fewest conversations|"
                              r"countr\w*\b.*\b(rank|most|volume|count|busiest))\b", re.I)


def rule_plan(df: pd.DataFrame, question: str) -> dict:
    """Deterministic planner — used without an LLM key and as the fallback."""
    countries = _find_countries(question, _known(df, "country"))
    language = _find_language(question, _known(df, "language"))

    if COMPARE_RE.search(question) and len(countries) >= 2:
        return {"intent": "compare", "calls": [{"tool": "compare_countries", "args": {"countries": countries[:3]}}]}
    if RESOURCE_RE.search(question):
        return {"intent": "resource", "calls": [{"tool": "search_library", "args": {"topic": question}}]}
    if SENTIMENT_RE.search(question):
        return {"intent": "sentiment", "calls": [{"tool": "sentiment", "args": {"country": countries[0] if countries else None}}]}
    if TREND_RE.search(question):
        return {"intent": "trend", "calls": [{"tool": "trends", "args": {}}]}
    if COUNTRY_VOLUME_RE.search(question) and not countries:
        return {"intent": "country", "calls": [{"tool": "country_volume", "args": {}}]}
    if countries:
        return {"intent": "country", "calls": [{"tool": "country_profile", "args": {"country": countries[0]}}]}
    if language:
        return {"intent": "topic", "calls": [{"tool": "top_topics", "args": {"language": language}}]}
    return {"intent": "overview", "calls": [{"tool": "global_overview", "args": {}}, {"tool": "top_topics", "args": {}}]}


def llm_plan(df: pd.DataFrame, question: str, client=None) -> dict:
    """Ask the LLM which tools to call. Falls back to rule_plan on any problem."""
    catalog = "\n".join(f"- {name}: {desc}" for name, desc in TOOL_CATALOG.items())
    user = (
        f"Tools:\n{catalog}\n\n"
        f"Countries: {_known(df, 'country')}\nLanguages: {_known(df, 'language')}\n\n"
        f"Question: {question}"
    )
    try:
        raw = llm.chat(SYSTEM_PLAN, user, json_mode=True, groq_client=client)
        plan = json.loads(raw)
        calls = [c for c in plan.get("calls", []) if c.get("tool") in TOOL_CATALOG]
        if not calls:
            return rule_plan(df, question)
        return {"intent": plan.get("intent", "overview"), "calls": calls}
    except Exception:
        return rule_plan(df, question)


# --- Execution --------------------------------------------------------------

def run_tools(df: pd.DataFrame, calls: list[dict]) -> list[dict]:
    """Execute planned tool calls, validating args against known entities."""
    countries = _known(df, "country")
    languages = _known(df, "language")
    results: list[dict] = []
    for call in calls:
        name, args = call.get("tool"), call.get("args", {}) or {}
        try:
            if name == "global_overview":
                out = tool_global_overview(df)
            elif name == "country_profile":
                c = _match(args.get("country"), countries)
                out = tool_country_profile(df, c) if c else {"error": "unknown country"}
            elif name == "compare_countries":
                cs = [m for c in (args.get("countries") or []) if (m := _match(c, countries))]
                out = tool_compare_countries(df, cs) if len(cs) >= 2 else {"error": "need two known countries"}
            elif name == "sentiment":
                out = tool_sentiment(df, _match(args.get("country"), countries))
            elif name == "country_volume":
                out = tool_country_volume(df)
            elif name == "trends":
                out = tool_trends(df, args.get("topic"))
            elif name == "top_topics":
                out = tool_top_topics(df, _match(args.get("country"), countries), _match(args.get("language"), languages))
            elif name == "search_library":
                out = tool_search_library(str(args.get("topic") or ""))
            else:
                continue
            results.append({"tool": name, "result": out})
        except Exception as e:  # noqa: BLE001 — a tool failure shouldn't crash the answer
            results.append({"tool": name, "error": str(e)})
    return results


def _match(value, known: list[str]) -> str | None:
    if not value:
        return None
    v = str(value).strip().lower()
    return next((k for k in known if k.lower() == v), None)


# --- Synthesis + assembly ---------------------------------------------------

def _extras(results: list[dict]) -> dict:
    """Pull structured data out for inline rendering."""
    extras: dict = {}
    for r in results:
        if r.get("tool") == "compare_countries" and "result" in r and "error" not in r["result"]:
            extras["comparison"] = r["result"]
        if r.get("tool") == "search_library" and "result" in r:
            extras["library"] = r["result"]
    return extras


def _primary_table(results: list[dict]) -> list[dict]:
    """A representative table to show under the answer (first topic-ish result)."""
    for r in results:
        res = r.get("result", {})
        for key in ("top_topics", "sentiment", "by_country"):
            if isinstance(res, dict) and res.get(key):
                return res[key]
    return []


def _template_answer(intent: str, results: list[dict]) -> str:
    """Readable answer without an LLM, from the gathered tool results."""
    by_tool = {r["tool"]: r.get("result", {}) for r in results if "result" in r}
    if "compare_countries" in by_tool:
        cs = by_tool["compare_countries"].get("countries", [])
        return f"Comparing {', '.join(cs)} — see the side-by-side topics, sentiment, and languages below."
    if "search_library" in by_tool:
        d = by_tool["search_library"].get("dewey", {})
        n = sum(len(by_tool["search_library"].get(k, [])) for k in ("books", "magazines", "articles"))
        return f"Closest Dewey class is {d.get('number', '?')} — {d.get('name', '')}. Found {n} resources below."
    if "country_profile" in by_tool:
        p = by_tool["country_profile"]
        tops = ", ".join(t["topic_label"] for t in p.get("top_topics", [])[:3])
        return f"In {p.get('country')}: {p.get('conversations')} conversations; top topics are {tops}."
    if "sentiment" in by_tool:
        s = by_tool["sentiment"]
        rows = ", ".join(f"{r['sentiment_label']} {r['conversations']}" for r in s.get("sentiment", []))
        return f"Sentiment ({s.get('scope')}): {rows}."
    if "trends" in by_tool:
        return "Topic volume over time is shown below."
    if "country_volume" in by_tool:
        rows = by_tool["country_volume"].get("by_country", [])
        top = rows[0] if rows else {}
        return f"{top.get('country', '?')} has the most conversations ({top.get('conversations', '?')}). Full ranking below."
    if "top_topics" in by_tool:
        t = by_tool["top_topics"]
        scope = t.get("country") or t.get("language") or "overall"
        tops = ", ".join(x["topic_label"] for x in t.get("top_topics", [])[:3])
        return f"Top topics ({scope}): {tops}."
    ov = by_tool.get("global_overview", {})
    if ov:
        s = ov.get("summary", {})
        return f"The dataset covers {s.get('conversations', '?')} conversations across {s.get('countries', '?')} countries."
    return "Ask about topics, countries, languages, sentiment, trends, comparisons, or resources."


def synthesize(question: str, results: list[dict], client=None) -> str:
    user = f"Gathered data (JSON):\n{json.dumps(results, default=str)}\n\nQuestion: {question}"
    return llm.chat(SYSTEM_SYNTH, user, groq_client=client).strip()


def answer(df: pd.DataFrame, question: str, client=None, groq_available: bool | None = None) -> dict:
    """Agentic answer. Returns {answer, table, source, intent, comparison?, library?}."""
    if not question or not question.strip():
        return {"answer": "Ask about topics, countries, languages, sentiment, trends, comparisons, or "
                          "resources — e.g. 'Compare coding interest in Japan and Brazil.'",
                "table": [], "source": "rules", "intent": "overview"}

    use_llm = client is not None or (groq_available if groq_available is not None else llm.available())
    plan = llm_plan(df, question, client) if use_llm else rule_plan(df, question)
    results = run_tools(df, plan["calls"])

    if use_llm:
        try:
            answer_text, source = synthesize(question, results, client), "ai"
        except Exception:
            answer_text, source = _template_answer(plan["intent"], results), "rules"
    else:
        answer_text, source = _template_answer(plan["intent"], results), "rules"

    return {
        "answer": answer_text,
        "table": _primary_table(results),
        "source": source,
        "intent": plan["intent"],
        **_extras(results),
    }

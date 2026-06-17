"""Export real WildChat rows (native-language prompts) by country from Hugging Face.

Streams the public ``allenai/WildChat-4.8M`` dataset, filters to the project's 8
seed countries, and writes one ``wildchat_<country>.csv`` per country into the
country pack directory using the *exact* schema the dashboard already expects.

Key differences from the older starter script in
``data/wildchat_country_csv_pack/export_actual_wildchat_by_country.py``:
  * Keeps the user's **first prompt in its native language** (the dashboard then
    translates it on demand) instead of a generic preview.
  * Assigns a ``prompt_topic`` code with a small **multilingual keyword
    classifier**, so the topic charts stay meaningful even though the prompts are
    not in English.
  * Emits rows in the same column order as the existing pack CSVs so
    ``scripts/clean_csvs.py`` can consume them with no other changes.

Privacy: never exports ``hashed_ip`` or request headers. Free-text fields are
truncated here and then PII-masked again by ``scripts/clean_csvs.py``.

Run (from repo root, inside the venv):
    python scripts/export_wildchat_real.py
    # then regenerate the cleaned / combined CSVs:
    python scripts/clean_csvs.py

Tunables via env:
    WILDCHAT_MAX_PER_COUNTRY   per-country row cap (default 1200)
    WILDCHAT_MAX_SCAN          stop after scanning this many source rows (default 1_200_000)
"""

from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

from datasets import load_dataset

DATASET_NAME = "allenai/WildChat-4.8M"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET_NAME}"

PACK_DIR = Path(__file__).resolve().parents[1] / "data" / "wildchat_country_csv_pack"

# Reuse the project's credential/PII scrubber so secrets pasted by dataset users
# (e.g. Facebook Graph API tokens) are never written to disk in the first place.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean import mask_pii  # noqa: E402

MAX_PER_COUNTRY = int(os.getenv("WILDCHAT_MAX_PER_COUNTRY", "1200"))
MAX_SCAN = int(os.getenv("WILDCHAT_MAX_SCAN", "1200000"))

# Dataset country value  ->  (file key, iso2, canonical display name)
COUNTRIES = {
    "United States":  ("usa",           "US", "United States"),
    "Canada":         ("canada",        "CA", "Canada"),
    "United Kingdom": ("great_britain", "GB", "United Kingdom"),
    "China":          ("china",         "CN", "China"),
    "Russia":         ("russia",        "RU", "Russia"),
    "France":         ("france",        "FR", "France"),
    "Brazil":         ("brazil",        "BR", "Brazil"),
    "Japan":          ("japan",         "JP", "Japan"),
}

# Column order must match the existing pack CSVs exactly.
HEADERS = [
    "record_id", "dataset_name", "country", "country_filter_value", "iso2",
    "state_or_region", "language", "model_family", "timestamp_utc", "turn_count",
    "prompt_topic", "sample_user_prompt_cleaned", "assistant_response_summary",
    "toxic", "redacted", "privacy_level", "data_status", "source_url", "notes",
]

# ---------------------------------------------------------------------------
# Multilingual topic classifier  (prompt text  ->  prompt_topic code)
# ---------------------------------------------------------------------------
# Keywords are matched as lowercased substrings. Each bucket mixes English with
# native terms for the 8 countries' languages so non-English prompts still land
# in a meaningful topic. Order defines tie-breaking priority (earlier wins).

TOPIC_KEYWORDS: list[tuple[str, list[str]]] = [
    ("coding_debugging", [
        # English / framework + library names (language-neutral, very common)
        "python", "javascript", "typescript", "java", "c++", "c#", "golang",
        "code", "coding", "function", "debug", "compile", "runtime", "stack trace",
        "exception", "syntax", "sql", "html", "css", "json", "regex", "algorithm",
        "api", "endpoint", "script", "react", "vue", "angular", "node", "express",
        "django", "flask", "spring", "docker", "kubernetes", "git", "github",
        "unity", "unreal", "websocket", "webview", "android studio",
        "mvc", "mvp", "frontend", "backend", "database", "query", "array",
        "libwebsockets", "opengl", "tensorflow", "pytorch", "numpy",
        # Russian
        "программ", "код", "ошибк", "функци", "массив", "юнити", "запрос",
        "отлад", "компилир", "переменн", "цикл", "база данных",
        # Chinese
        "代码", "编程", "函数", "报错", "数组", "矩阵", "客户端", "服务器",
        "前端", "后端", "数据库", "编写代码", "调试", "异常", "算法", "脚本",
        # Japanese
        "コード", "プログラ", "エラー", "関数", "配列", "デバッグ", "実装",
        # French / Portuguese / Spanish
        "fonction", "débogage", "erreur", "compiler", "programmation",
        "programa", "código", "programação", "função", "depurar", "erro",
        "función", "compilar",
    ]),
    ("data_analysis", [
        "dataset", "pandas", "excel", "spreadsheet", "regression", "statistic",
        "analyze data", "data analysis", "csv", "dataframe", "pivot table",
        "数据", "分析", "统计", "表格", "データ", "統計", "分析して",
        "données", "analyse", "datos", "análisis", "dados", "анализ данных",
        "данны", "выборк", "корреляц",
    ]),
    ("creative_writing", [
        # English: stories, roleplay, fiction, lyrics
        "story", "poem", "novel", "lyrics", "fiction", "screenplay", "fanfic",
        "act as", "roleplay", "role play", "role-play", "play the role",
        "play a character", "write a scene", "continue the story", "narrative",
        "hypnotiz", "dialogue", "chapter", "protagonist", "plot",
        # Russian
        "рассказ", "стих", "напиши историю", "сюжет", "персонаж", "роль",
        "отыграй", "ролев", "сочини", "напиши сказку", "глава",
        # Chinese
        "故事", "小说", "诗", "写一篇", "扮演", "角色扮演", "剧情", "情节",
        "续写", "对话", "恋爱", "短文",
        # Japanese
        "物語", "小説", "詩", "ロールプレイ", "なりきって", "脚本", "セリフ",
        "恋愛", "シナリオ",
        # French / Portuguese / Spanish
        "histoire", "poème", "roman", "joue le rôle", "scénario", "personnage",
        "historia", "cuento", "poema", "conto", "interprete o papel", "roteiro",
        "personagem", "escreva uma história", "escribe una historia",
    ]),
    ("entertainment_games", [
        "game", "minecraft", "roblox", "pokemon", "anime", "manga", "movie",
        "film", "song", "music", "playlist", "soccer", "football", "sport",
        "游戏", "动漫", "电影", "音乐", "体育", "运动", "ゲーム", "アニメ",
        "映画", "音楽", "jeu", "juego", "jogo", "futebol", "esporte",
        "игра", "película", "filme", "фильм", "спорт", "музык", "аниме",
    ]),
    ("education_homework", [
        # English + academic
        "homework", "essay", "study", "school", "university", "exam", "lesson",
        "explain", "math", "physics", "chemistry", "biology", "history lesson",
        "thesis", "academic paper", "research paper", "questionnaire", "quiz",
        "equation", "theorem", "calculate", "integer", "electric", "atom", "molecule",
        # Chinese
        "作业", "学习", "数学", "论文", "学术", "物理", "化学", "公式", "方程",
        # Japanese
        "宿題", "勉強", "論文",
        # French / Portuguese / Spanish
        "devoir", "étudier", "leçon", "dissertation",
        "tarea", "estudiar", "lección", "ensayo", "dever de casa", "estudar",
        "redação",
        # Russian
        "домашн", "учеб", "реферат", "уравнен", "задач", "контрольн",
        "презентаци", "призентаци", "слайд",
    ]),
    ("business_email", [
        "email", "e-mail", "meeting", "client", "invoice", "proposal",
        "business letter", "memo", "agenda", "contract",
        "邮件", "会议", "客户", "合同", "メール", "会議", "courriel",
        "réunion", "correo", "reunión", "reunião", "письмо", "встреч", "договор",
    ]),
    ("job_career", [
        "resume", "cv", "cover letter", "interview", "career", "salary",
        "job application", "linkedin", "self introduction", "自我介绍",
        "简历", "求职", "面试", "履歴書", "面接", "自己紹介", "entretien",
        "emploi", "currículum", "entrevista", "currículo", "emprego",
        "резюме", "собеседован", "ваканс",
    ]),
    ("health_general_info", [
        "health", "doctor", "symptom", "diet", "fitness", "medicine", "anxiety",
        "depression", "nutrition", "workout", "calorie",
        "健康", "医生", "症状", "医者", "santé", "médecin", "salud", "médico",
        "saúde", "здоров", "врач", "симптом", "лекарств", "болезн",
    ]),
    ("travel_local_help", [
        "travel", "trip", "hotel", "flight", "visa", "tourist", "itinerary",
        "vacation", "sightseeing",
        "旅行", "酒店", "签证", "ホテル", "ビザ", "観光", "voyage", "hôtel",
        "viaje", "viagem", "путешеств", "отель", "виза", "туризм",
    ]),
    ("personal_planning", [
        "schedule", "plan my", "organize", "budget", "routine", "to-do",
        "计划", "安排", "計画", "スケジュール", "planifier", "organiser",
        "planificar", "organizar", "planejar", "планир", "расписан",
    ]),
    ("translation_language", [
        "translate", "translation", "grammar", "pronounce", "翻译", "翻訳",
        "翻译成", "用英语", "用日文", "traduire", "traduction", "traducir",
        "traducción", "traduzir", "перевод", "перевести", "грамматик",
    ]),
]

DEFAULT_TOPIC = "general_information"


def classify_prompt_topic(text: str) -> str:
    """Pick a prompt_topic code from native-or-English prompt text."""
    if not text:
        return DEFAULT_TOPIC
    low = text.lower()
    best_code = DEFAULT_TOPIC
    best_score = 0
    for code, keywords in TOPIC_KEYWORDS:
        score = sum(1 for kw in keywords if kw in low)
        if score > best_score:
            best_score = score
            best_code = code
    return best_code


# ---------------------------------------------------------------------------
# Row helpers
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_MODEL_DATE = re.compile(r"-(?:\d{4}-\d{2}-\d{2}|\d{4}|\d{6})$")


def _collapse(text: str, limit: int) -> str:
    """Single-line, whitespace-collapsed, length-capped."""
    if not text:
        return ""
    return _WS.sub(" ", str(text)).strip()[:limit]


def _model_family(model: str) -> str:
    """gpt-4-0314 -> gpt-4 ; gpt-3.5-turbo-0613 -> gpt-3.5-turbo ; gpt-4o-2024-05-13 -> gpt-4o."""
    if not model:
        return ""
    return _MODEL_DATE.sub("", str(model).strip())


def _first_turns(conversation) -> tuple[str, str]:
    """Return (first_user_content, first_assistant_content)."""
    first_user = ""
    first_assistant = ""
    for turn in conversation or []:
        role = turn.get("role")
        content = turn.get("content") or ""
        if role == "user" and not first_user:
            first_user = content
        elif role == "assistant" and not first_assistant:
            first_assistant = content
        if first_user and first_assistant:
            break
    return first_user, first_assistant


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    files: dict[str, object] = {}
    writers: dict[str, csv.DictWriter] = {}
    counts: dict[str, int] = {key: 0 for _, (key, _, _) in COUNTRIES.items()}

    try:
        for _, (key, _iso2, _name) in COUNTRIES.items():
            fh = (PACK_DIR / f"wildchat_{key}.csv").open(
                "w", newline="", encoding="utf-8"
            )
            files[key] = fh
            writer = csv.DictWriter(fh, fieldnames=HEADERS)
            writer.writeheader()
            writers[key] = writer

        ds = load_dataset(DATASET_NAME, split="train", streaming=True)

        scanned = 0
        for row in ds:
            scanned += 1
            if scanned % 50000 == 0:
                print(f"  scanned {scanned:,} rows | counts={counts}", flush=True)
                sys.stdout.flush()

            country = row.get("country")
            meta = COUNTRIES.get(country)
            if meta is None:
                if scanned >= MAX_SCAN:
                    break
                continue

            key, iso2, name = meta
            if counts[key] >= MAX_PER_COUNTRY:
                if all(c >= MAX_PER_COUNTRY for c in counts.values()):
                    break
                if scanned >= MAX_SCAN:
                    break
                continue

            first_user, first_assistant = _first_turns(row.get("conversation"))
            prompt = mask_pii(_collapse(first_user, 300))
            if not prompt:
                if scanned >= MAX_SCAN:
                    break
                continue

            summary = mask_pii(_collapse(first_assistant, 220))
            counts[key] += 1
            record_id = f"WC_{iso2}_{counts[key]:04d}"

            writers[key].writerow({
                "record_id": record_id,
                "dataset_name": DATASET_NAME,
                "country": name,
                "country_filter_value": name,
                "iso2": iso2,
                "state_or_region": row.get("state") or "",
                "language": row.get("language") or "",
                "model_family": _model_family(row.get("model")),
                "timestamp_utc": str(row.get("timestamp") or ""),
                "turn_count": row.get("turn") or 0,
                "prompt_topic": classify_prompt_topic(prompt),
                "sample_user_prompt_cleaned": prompt,
                "assistant_response_summary": summary,
                "toxic": bool(row.get("toxic")),
                "redacted": bool(row.get("redacted")),
                "privacy_level": "safe_preview_no_hash_no_headers",
                "data_status": "real_huggingface_export",
                "source_url": SOURCE_URL,
                "notes": "Real WildChat row; first user turn kept in native language.",
            })

            if scanned >= MAX_SCAN:
                break
    finally:
        for fh in files.values():
            fh.close()

    print("\nDone. Rows written per country:")
    total = 0
    for _, (key, _iso2, _name) in COUNTRIES.items():
        print(f"  {key:<14} {counts[key]:>6}")
        total += counts[key]
    print(f"  {'TOTAL':<14} {total:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

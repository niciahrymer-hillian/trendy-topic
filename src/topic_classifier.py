"""Topic taxonomy + classifier for WildChat-style conversations.

Two layers:

1. A *mapping* from the dataset's raw ``prompt_topic`` codes to (a) a
   human-readable label and (b) a broad category drawn from the project spec's
   topic taxonomy. This is the primary, deterministic path because the WildChat
   sample already ships a ``prompt_topic`` per row.

2. A shared multilingual keyword *classifier* (``classify_prompt_topic_code`` /
   ``classify_topic``) used both to label raw exports and to classify free-text
   searches, so a search like "basketball" resolves to the same topic the data
   uses (Sports), not an unrelated one.

Keeping both means the same dashboard logic works whether topics are pre-labeled
or have to be inferred.
"""

from __future__ import annotations

import re

# --- Layer 1: map raw prompt_topic codes -> readable label + broad category ----

# Readable label for each prompt_topic code in the WildChat pack.
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
    # Sub-topics carved out of the broad "general_information" bucket so the
    # dashboard spreads out instead of piling everything into one slice.
    "sports": "Sports",
    "science_nature": "Science & Nature",
    "history_culture": "History & Culture",
    "food_cooking": "Food & Cooking",
    "finance_money": "Finance & Money",
    "philosophy_religion": "Philosophy & Religion",
    "news_politics": "News & Politics",
    "transportation": "Transportation",
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
    "sports": "Sports & Recreation",
    "science_nature": "Science & Nature",
    "history_culture": "History & Culture",
    "food_cooking": "Food & Cooking",
    "finance_money": "Finance & Money",
    "philosophy_religion": "Society & Culture",
    "news_politics": "Society & Culture",
    "transportation": "Transportation & Auto",
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


# --- Layer 2: shared multilingual keyword classifier ---------------------------
#
# ``TOPIC_CODE_KEYWORDS`` is the single source of truth used everywhere a topic is
# inferred from free text:
#   * data labeling      — scripts/export_wildchat_real.py + reclassify_topics.py
#   * search / fallback   — classify_topic() below (e.g. "basketball" -> Sports)
#
# Keywords are matched as lowercased substrings and mix English with native terms
# for the 8 countries' languages so non-English prompts still land in a topic.
# Order defines tie-breaking priority (earlier wins), so specific buckets are
# listed before broad ones.

DEFAULT_PROMPT_TOPIC = "general_information"

TOPIC_CODE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("coding_debugging", [
        "python", "javascript", "typescript", "java", "c++", "c#", "golang",
        "code", "coding", "function", "debug", "compile", "runtime", "stack trace",
        "exception", "syntax", "sql", "html", "css", "json", "regex", "algorithm",
        "api", "endpoint", "script", "react", "vue", "angular", "node", "express",
        "django", "flask", "spring", "docker", "kubernetes", "git", "github",
        "unity", "unreal", "websocket", "webview", "android studio",
        "mvc", "mvp", "frontend", "backend", "database", "query",
        "libwebsockets", "opengl", "tensorflow", "pytorch", "numpy",
        "программ", "код", "ошибк", "функци", "массив", "юнити", "запрос",
        "отлад", "компилир", "переменн", "цикл", "база данных",
        "代码", "编程", "函数", "报错", "数组", "矩阵", "客户端", "服务器",
        "前端", "后端", "数据库", "编写代码", "调试", "异常", "算法", "脚本",
        "コード", "プログラ", "エラー", "関数", "配列", "デバッグ", "実装",
        "fonction", "débogage", "erreur", "compiler", "programmation",
        "programa", "código", "programação", "função", "depurar", "erro",
        "función", "compilar",
    ]),
    ("data_analysis", [
        "dataset", "pandas", "excel", "spreadsheet", "regression", "statistic",
        "analyze data", "data analysis", "csv", "dataframe", "pivot table",
        "数据", "统计", "表格", "データ", "統計", "分析して",
        "données", "datos", "dados", "анализ данных", "данны", "выборк", "корреляц",
    ]),
    ("translation_language", [
        "translate", "translation", "grammar", "pronounce", "翻译", "翻訳",
        "翻译成", "用英语", "用日文", "traduire", "traduction", "traducir",
        "traducción", "traduzir", "перевод", "перевести", "грамматик",
    ]),
    ("sports", [
        "football", "soccer", "basketball", "nba", "nfl", "fifa", "world cup",
        "olympic", "olympics", "f1", "formula 1", "fórmula 1", "grand prix",
        "tennis", "golf", "cricket", "rugby", "baseball", "hockey", "athlete",
        "championship", "tournament", "stadium", "brasileirão", "libertadores",
        "campeonato", "copa", "esporte", "deporte", "fútbol", "baloncesto",
        "futebol", "basquete", "足球", "篮球", "世界杯", "联赛", "球赛",
        "サッカー", "野球", "試合", "オリンピック", "футбол", "баскетбол",
        "хоккей", "чемпионат", "олимп",
    ]),
    ("creative_writing", [
        "story", "poem", "novel", "lyrics", "fiction", "screenplay", "fanfic",
        "act as", "roleplay", "role play", "role-play", "play the role",
        "play a character", "write a scene", "continue the story", "narrative",
        "hypnotiz", "dialogue", "chapter", "protagonist", "plot",
        "рассказ", "стих", "напиши историю", "сюжет", "персонаж", "роль",
        "отыграй", "ролев", "сочини", "напиши сказку", "глава",
        "故事", "小说", "诗", "写一篇", "扮演", "角色扮演", "剧情", "情节",
        "续写", "对话", "恋爱", "短文",
        "物語", "小説", "詩", "ロールプレイ", "なりきって", "脚本", "セリフ",
        "恋愛", "シナリオ",
        "histoire", "poème", "roman", "joue le rôle", "scénario", "personnage",
        "historia", "cuento", "poema", "conto", "interprete o papel", "roteiro",
        "personagem", "escreva uma história", "escribe una historia",
    ]),
    ("entertainment_games", [
        "game", "minecraft", "roblox", "pokemon", "anime", "manga", "movie",
        "film", "song", "music", "playlist", "video game", "gaming",
        "游戏", "动漫", "电影", "音乐", "ゲーム", "アニメ", "映画", "音楽",
        "jeu", "juego", "jogo", "игра", "película", "filme", "фильм", "музык",
        "аниме",
    ]),
    ("food_cooking", [
        "recipe", "cook", "cooking", "cuisine", "bake", "baking", "ingredient",
        "meal", "dish", "food", "restaurant menu", "食谱", "料理", "美食",
        "烹饪", "レシピ", "食べ物", "рецепт", "готов", "receita", "comida",
        "culinária", "cozinhar", "recette", "recetas",
    ]),
    ("health_general_info", [
        "health", "doctor", "symptom", "diet", "fitness", "medicine", "anxiety",
        "depression", "nutrition", "workout", "calorie",
        "健康", "医生", "症状", "医者", "santé", "médecin", "salud", "médico",
        "saúde", "здоров", "врач", "симптом", "лекарств", "болезн",
    ]),
    ("finance_money", [
        "invest", "stock", "finance", "financial", "money", "crypto", "bitcoin",
        "tax", "loan", "mortgage", "interest rate", "economics", "economy",
        "经济", "投资", "股票", "金融", "投資", "株", "税金", "эконом", "инвест",
        "налог", "dinheiro", "imposto", "investimento", "economia", "finanças",
        "finanzas", "impuesto",
    ]),
    ("job_career", [
        "resume", "cv", "cover letter", "interview", "career", "salary",
        "job application", "linkedin", "self introduction", "自我介绍",
        "简历", "求职", "面试", "履歴書", "面接", "自己紹介", "entretien",
        "emploi", "currículum", "entrevista", "currículo", "emprego",
        "резюме", "собеседован", "ваканс",
    ]),
    ("business_email", [
        "email", "e-mail", "meeting", "client", "invoice", "proposal",
        "business letter", "memo", "agenda", "contract",
        "邮件", "会议", "客户", "合同", "メール", "会議", "courriel",
        "réunion", "correo", "reunión", "reunião", "письмо", "встреч", "договор",
    ]),
    ("transportation", [
        "car", "cars", "automobile", "vehicle", "truck", "motorcycle", "bus",
        "train", "trains", "railway", "railroad", "subway", "metro", "tram",
        "bicycle", "bike", "scooter", "airplane", "aircraft", "airline",
        "transportation", "transport", "transit", "commute", "traffic",
        "engine", "ev", "electric vehicle", "tesla",
        "汽车", "火车", "地铁", "公交", "自行车", "飞机", "交通", "高铁",
        "車", "電車", "新幹線", "地下鉄", "バス", "自転車", "交通機関",
        "voiture", "train", "métro", "vélo", "avion", "transport",
        "coche", "carro", "tren", "metro", "avión", "transporte", "ônibus",
        "trem", "metrô", "bicicleta", "avião",
        "машин", "автомоб", "поезд", "метро", "велосипед", "самолёт",
        "транспорт", "электромоб",
    ]),
    ("travel_local_help", [
        "travel", "trip", "hotel", "flight", "visa", "tourist", "itinerary",
        "vacation", "sightseeing",
        "旅行", "酒店", "签证", "ホテル", "ビザ", "観光", "voyage", "hôtel",
        "viaje", "viagem", "путешеств", "отель", "виза", "туризм",
    ]),
    ("education_homework", [
        "homework", "essay", "study", "school", "university", "exam", "lesson",
        "explain", "math", "thesis", "academic paper", "research paper",
        "questionnaire", "quiz", "equation", "theorem", "calculate",
        "作业", "学习", "数学", "论文", "学术", "公式", "方程",
        "宿題", "勉強", "論文", "devoir", "étudier", "leçon", "dissertation",
        "tarea", "estudiar", "lección", "ensayo", "dever de casa", "estudar",
        "redação", "домашн", "учеб", "реферат", "уравнен", "задач", "контрольн",
        "презентаци", "призентаци", "слайд",
    ]),
    ("science_nature", [
        "physics", "chemistry", "biology", "astronomy", "solar system", "planet",
        "galaxy", "universe", "molecule", "atom", "quantum", "neuron", "gene",
        "dna", "evolution", "species", "ecosystem", "climate", "volcano",
        "earthquake", "chemical", "scientific",
        "科学", "物理", "化学", "生物", "宇宙", "量子", "进化", "细胞",
        "物理学", "化学", "生物学", "наук", "физик", "хими", "биолог",
        "вселенн", "ciência", "física", "química", "biologia", "evolução",
        "universo",
    ]),
    ("history_culture", [
        "history", "historical", "world war", "ancient", "medieval", "empire",
        "dynasty", "civilization", "century", "geography", "heritage",
        "历史", "战争", "古代", "王朝", "文化", "歴史", "戦争",
        "истори", "войн", "древн", "культур", "história", "guerra", "império",
        "cultura", "civilização",
    ]),
    ("philosophy_religion", [
        "philosophy", "philosopher", "ethics", "moral", "existential", "religion",
        "god", "faith", "prayer", "buddhism", "christianity", "islam", "hindu",
        "bible", "quran", "soul", "spiritual", "meditation",
        "哲学", "宗教", "信仰", "佛教", "基督", "上帝", "神",
        "философ", "религи", "бог", "душа", "filosofia", "religião", "deus",
        "alma", "espiritual", "filosofía", "religión", "dios",
    ]),
    ("news_politics", [
        "politics", "political", "government", "election", "president",
        "prime minister", "parliament", "congress", "senator", "policy",
        "democracy", "communism", "capitalism", "law", "legal",
        "政治", "政府", "选举", "总统", "選挙", "политик", "правительств",
        "выбор", "президент", "política", "governo", "eleição", "presidente",
        "gobierno",
    ]),
    ("personal_planning", [
        "schedule", "plan my", "organize", "budget", "routine", "to-do",
        "计划", "安排", "計画", "スケジュール", "planifier", "organiser",
        "planificar", "organizar", "planejar", "планир", "расписан",
    ]),
]

# Fast lookup for confidence scoring.
_KEYWORDS_BY_CODE: dict[str, list[str]] = dict(TOPIC_CODE_KEYWORDS)


def _compile_keyword(kw: str):
    """Compile one keyword into a matcher.

    Latin/ASCII keywords get a *leading* word boundary so a short word can't match
    inside a longer one (``"story"`` must NOT fire on ``"history"``). We use only a
    leading boundary — not a trailing one — so intentional prefix stems still match
    their suffix variants (``"hypnotiz"`` -> hypnotize / hypnotized / hypnotizing).
    CJK keywords have no word boundaries, so they keep plain substring matching.
    """
    if kw.isascii():
        return re.compile(rf"(?<![a-z0-9]){re.escape(kw)}", re.IGNORECASE)
    return kw  # substring sentinel for non-ASCII


_COMPILED_KEYWORDS: list[tuple[str, list]] = [
    (code, [_compile_keyword(kw) for kw in keywords])
    for code, keywords in TOPIC_CODE_KEYWORDS
]
_COMPILED_BY_CODE: dict[str, list] = dict(_COMPILED_KEYWORDS)


def _count_matches(compiled: list, low: str) -> int:
    return sum(
        1
        for m in compiled
        if ((m in low) if isinstance(m, str) else bool(m.search(low)))
    )


def classify_prompt_topic_code(text: str | None) -> str:
    """Infer a raw prompt_topic *code* from native-or-English text.

    Returns ``general_information`` when nothing matches. This is the function the
    data-export and reclassification scripts call so the labels they write stay in
    lock-step with what search/``classify_topic`` would produce.
    """
    if not text:
        return DEFAULT_PROMPT_TOPIC
    low = str(text).lower()
    best_code = DEFAULT_PROMPT_TOPIC
    best_score = 0
    for code, compiled in _COMPILED_KEYWORDS:
        score = _count_matches(compiled, low)
        if score > best_score:
            best_score = score
            best_code = code
    return best_code


def classify_topic(text: str) -> dict:
    """Keyword classifier for free text (search box, or rows with no prompt_topic).

    Returns the readable label + a rough confidence. Unmatched / empty text yields
    ``UNKNOWN_LABEL`` so callers can tell "nothing recognised" apart from a real
    topic. A recognised search like ``"basketball"`` resolves to ``"Sports"``.
    """
    low = (text or "").lower()
    code = classify_prompt_topic_code(low)
    score = _count_matches(_COMPILED_BY_CODE.get(code, []), low)
    if score == 0:
        return {"topic_label": UNKNOWN_LABEL, "topic_confidence": 0.0}
    return {"topic_label": label_for(code), "topic_confidence": min(1.0, score / 3)}

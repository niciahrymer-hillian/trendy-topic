// Typed fetch client. All paths are relative (/api/...) so the Vite dev proxy and
// any reverse proxy in production both work without changing app code.

import type {
  AskResponse,
  CountryDetail,
  CountryComparisonResponse,
  CountryProfile,
  CuriosityItem,
  ExtractParams,
  ExtractResponse,
  HeatmapCell,
  LanguageCount,
  LanguageTopicCell,
  CountryClustersResponse,
  SentimentCount,
  SimilarSummaryResponse,
  Summary,
  TopicCount,
  TopicDetail,
  TopicHierarchyItem,
  TranslationResult,
  TranslationSummary,
  TrendMetric,
  TrendPoint,
  VoiceScript,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return (await res.json()) as T;
}

// POST with no body (params go in the query string). Surfaces the API's error
// `detail` (e.g. the 503 "GROQ_API_KEY is not configured") so the UI can explain it.
async function post<T>(path: string): Promise<T> {
  const res = await fetch(path, { method: "POST" });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      /* non-JSON error body */
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export const api = {
  summary: () => get<Summary>("/api/summary"),
  countries: () => get<CountryProfile[]>("/api/countries"),
  country: (iso3: string) => get<CountryDetail>(`/api/country/${iso3}`),
  countryCompare: (countries: string[]) =>
    get<CountryComparisonResponse>(`/api/country-compare?${countries.map((c) => `countries=${encodeURIComponent(c)}`).join("&")}`),
  topics: (by: "label" | "category" = "label", country?: string, language?: string) => {
    const q = new URLSearchParams({ by });
    if (country) q.set("country", country);
    if (language) q.set("language", language);
    return get<TopicCount[]>(`/api/topics?${q.toString()}`);
  },
  topicHierarchy: () => get<TopicHierarchyItem[]>("/api/topic-hierarchy"),
  topic: (label: string) => get<TopicDetail>(`/api/topic/${encodeURIComponent(label)}`),
  languages: () => get<LanguageCount[]>("/api/languages"),
  sentiment: (by?: "country" | "topic_label" | "language") =>
    get<SentimentCount[]>(`/api/sentiment${by ? `?by=${by}` : ""}`),
  curiosity: (n = 15) => get<CuriosityItem[]>(`/api/curiosity?n=${n}`),
  trends: () => get<TrendPoint[]>("/api/trends"),
  trendMetrics: (limit = 40, latestOnly = true) =>
    get<TrendMetric[]>(`/api/trend-metrics?limit=${limit}&latest_only=${latestOnly}`),
  translationSummaries: (limit = 50, language?: string) =>
    get<TranslationSummary[]>(
      `/api/translation-summaries?limit=${limit}${language ? `&language=${encodeURIComponent(language)}` : ""}`
    ),
  similarSummaries: (conversationId: string, limit = 8) =>
    get<SimilarSummaryResponse>(
      `/api/similar-summaries?conversation_id=${encodeURIComponent(conversationId)}&limit=${limit}`
    ),
  countryClusters: (nClusters = 3) =>
    get<CountryClustersResponse>(`/api/country-clusters?n_clusters=${nClusters}`),
  translateSummary: (conversationId: string, targetLanguage: string) =>
    post<TranslationResult>(
      `/api/translate-summary?conversation_id=${encodeURIComponent(conversationId)}&target_language=${encodeURIComponent(targetLanguage)}`
    ),
  heatmap: () => get<HeatmapCell[]>("/api/heatmap"),
  languageTopics: () => get<LanguageTopicCell[]>("/api/language-topics"),
  ask: (q: string) => get<AskResponse>(`/api/ask?q=${encodeURIComponent(q)}`),
  extract: (p: ExtractParams) => {
    const q = new URLSearchParams();
    if (p.country) q.set("country", p.country);
    if (p.topic) q.set("topic", p.topic);
    if (p.language) q.set("language", p.language);
    if (p.limit) q.set("limit", String(p.limit));
    return post<ExtractResponse>(`/api/extract?${q.toString()}`);
  },
  voiceScript: (country?: string, topic?: string) => {
    const q = new URLSearchParams();
    if (country) q.set("country", country);
    if (topic) q.set("topic", topic);
    return get<VoiceScript>(`/api/voice/script?${q.toString()}`);
  },
  // Returns audio bytes (MP3) as a Blob for playback; surfaces the API error detail.
  voiceAudio: async (country?: string, topic?: string, language?: string): Promise<Blob> => {
    const q = new URLSearchParams();
    if (country) q.set("country", country);
    if (topic) q.set("topic", topic);
    if (language) q.set("language", language);
    const res = await fetch(`/api/voice/audio?${q.toString()}`, { method: "POST" });
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try {
        const body = await res.json();
        if (body?.detail) detail = body.detail;
      } catch {
        /* non-JSON error body */
      }
      throw new Error(detail);
    }
    return res.blob();
  },
};

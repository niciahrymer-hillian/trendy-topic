// Typed fetch client. All paths are relative (/api/...) so the Vite dev proxy and
// any reverse proxy in production both work without changing app code.

import type {
  AskResponse,
  CountryDetail,
  CountryProfile,
  CuriosityItem,
  ExtractParams,
  ExtractResponse,
  HeatmapCell,
  LanguageCount,
  LanguageTopicCell,
  SentimentCount,
  Summary,
  TopicCount,
  TopicDetail,
  TrendPoint,
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
  topics: (by: "label" | "category" = "label") =>
    get<TopicCount[]>(`/api/topics?by=${by}`),
  topic: (label: string) => get<TopicDetail>(`/api/topic/${encodeURIComponent(label)}`),
  languages: () => get<LanguageCount[]>("/api/languages"),
  sentiment: (by?: "country" | "topic_label" | "language") =>
    get<SentimentCount[]>(`/api/sentiment${by ? `?by=${by}` : ""}`),
  curiosity: (n = 15) => get<CuriosityItem[]>(`/api/curiosity?n=${n}`),
  trends: () => get<TrendPoint[]>("/api/trends"),
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
};

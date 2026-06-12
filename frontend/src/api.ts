// Typed fetch client. All paths are relative (/api/...) so the Vite dev proxy and
// any reverse proxy in production both work without changing app code.

import type {
  AskResponse,
  CountryDetail,
  CountryProfile,
  CuriosityItem,
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
};

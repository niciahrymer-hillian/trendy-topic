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
  DeweyPromptSearchResponse,
  DeweyIndexJobStatus,
  DeweyIndexJobsResponse,
  DeweyIndexRunResponse,
  DeweyTaxonomyOverview,
  DeweyTaxonomyClass,
  DeweyTaxonomyDetailed,
  DeweyTaxonomySearchResult,
  LibrarySearchResponse,
  LibraryTaxonomyResponse,
  SentimentCount,
  SimilarSummaryResponse,
  Summary,
  TopicCount,
  TopicDetail,
  TopicHierarchyItem,
  TranslationResult,
  CountryTranslation,
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

async function getWithHeaders<T>(path: string, headers: HeadersInit): Promise<T> {
  const res = await fetch(path, { headers });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${path}`);
  return (await res.json()) as T;
}

async function postWithHeaders<T>(path: string, headers: HeadersInit): Promise<T> {
  const res = await fetch(path, { method: "POST", headers });
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

function adminHeaders(token?: string): HeadersInit {
  return token ? { "x-admin-token": token } : {};
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
  translateCountry: (country: string) =>
    get<CountryTranslation>(`/api/translate-country?country=${encodeURIComponent(country)}`),
  // Generic ElevenLabs TTS — the default AI-assistant voice. Returns MP3 bytes.
  tts: async (text: string): Promise<Blob> => {
    const res = await fetch(`/api/tts?text=${encodeURIComponent(text.slice(0, 1500))}`, { method: "POST" });
    if (!res.ok) {
      let detail = `${res.status} ${res.statusText}`;
      try { const body = await res.json(); if (body?.detail) detail = body.detail; } catch { /* non-JSON */ }
      throw new Error(detail);
    }
    return res.blob();
  },
  heatmap: () => get<HeatmapCell[]>("/api/heatmap"),
  languageTopics: () => get<LanguageTopicCell[]>("/api/language-topics"),
  ask: (q: string) => get<AskResponse>(`/api/ask?q=${encodeURIComponent(q)}`),
  librarySearch: (topic: string, limit = 5) =>
    get<LibrarySearchResponse>(
      `/api/library-search?topic=${encodeURIComponent(topic)}&limit=${limit}`
    ),
  libraryTaxonomy: () => get<LibraryTaxonomyResponse>("/api/library-taxonomy"),
  deweyPrompts: (params: { dewey?: string; q?: string; limit?: number; offset?: number } = {}) => {
    const q = new URLSearchParams();
    if (params.dewey) q.set("dewey", params.dewey);
    if (params.q) q.set("q", params.q);
    q.set("limit", String(params.limit ?? 100));
    q.set("offset", String(params.offset ?? 0));
    return get<DeweyPromptSearchResponse>(`/api/dewey-prompts?${q.toString()}`);
  },
  deweyIndexJobs: (token?: string, limit = 25) =>
    getWithHeaders<DeweyIndexJobsResponse>(`/api/admin/dewey-index/jobs?limit=${limit}`, adminHeaders(token)),
  deweyIndexJob: (jobId: string, token?: string) =>
    getWithHeaders<DeweyIndexJobStatus>(`/api/admin/dewey-index/jobs/${encodeURIComponent(jobId)}`, adminHeaders(token)),
  startDeweyIndexJob: (
    params: {
      dataset?: string;
      split?: string;
      config?: string;
      limit?: number;
      outCsv?: string;
      toDb?: boolean;
      replaceDb?: boolean;
      checkpointPath?: string;
      resume?: boolean;
      batchSize?: number;
      checkpointEvery?: number;
      replaceOutput?: boolean;
    },
    token?: string,
  ) => {
    const q = new URLSearchParams();
    if (params.dataset) q.set("dataset", params.dataset);
    if (params.split) q.set("split", params.split);
    if (params.config) q.set("config", params.config);
    if (params.limit) q.set("limit", String(params.limit));
    if (params.outCsv) q.set("out_csv", params.outCsv);
    if (params.toDb) q.set("to_db", "true");
    if (params.replaceDb) q.set("replace_db", "true");
    if (params.checkpointPath) q.set("checkpoint_path", params.checkpointPath);
    if (params.resume) q.set("resume", "true");
    if (params.batchSize) q.set("batch_size", String(params.batchSize));
    if (params.checkpointEvery) q.set("checkpoint_every", String(params.checkpointEvery));
    if (params.replaceOutput) q.set("replace_output", "true");
    return postWithHeaders<DeweyIndexRunResponse>(`/api/admin/dewey-index/run?${q.toString()}`, adminHeaders(token));
  },
  cancelDeweyIndexJob: (jobId: string, token?: string) =>
    postWithHeaders<{ job_id: string; status: string; cancel_requested: boolean; message: string }>(
      `/api/admin/dewey-index/jobs/${encodeURIComponent(jobId)}/cancel`,
      adminHeaders(token)
    ),
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
  deweyTaxonomyOverview: () => get<DeweyTaxonomyOverview>("/api/dewey-taxonomy/overview"),
  deweyTaxonomyClass: (classId: string) =>
    get<DeweyTaxonomyClass>(`/api/dewey-taxonomy/${encodeURIComponent(classId)}`),
  deweyTaxonomyDetailed: (classId: string) =>
    get<DeweyTaxonomyDetailed>(
      `/api/dewey-taxonomy/${encodeURIComponent(classId)}/detailed`
    ),
  deweyTaxonomySearch: (query: string) =>
    get<DeweyTaxonomySearchResult[]>(
      `/api/dewey-taxonomy/search?q=${encodeURIComponent(query)}`
    ),
};

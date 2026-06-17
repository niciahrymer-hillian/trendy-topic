// Shapes returned by the FastAPI backend (api/main.py). Keeping these in one place
// means every component/page shares the same contract with the server.

export interface Summary {
  conversations: number;
  countries: number;
  languages: number;
  topics: number;
  avg_turns: number;
  redacted_pct: number;
}

export interface CountryProfile {
  country: string;
  iso3: string;
  conversations: number;
  avg_turns: number;
  top_language: string;
  dominant_topic: string;
  top_topics: string;
  dominant_sentiment: string;
  positive_pct: number;
  lat: number;
  lng: number;
}

export interface TopicCount {
  topic_label?: string;
  topic_category?: string;
  conversations: number;
}

export interface TopicHierarchyItem {
  topic_category: string;
  topic_label: string;
  conversations: number;
}

export interface LanguageCount {
  language: string;
  conversations: number;
  share_pct: number;
}

export interface SentimentCount {
  sentiment_label: string;
  conversations: number;
  [dimension: string]: string | number; // e.g. country / topic_label / language
}

export interface CuriosityItem {
  rank: number;
  conversations: number;
  topic_label: string;
  sample_user_prompt_cleaned: string;
}

export interface QuestionRow {
  topic_label: string;
  language: string;
  sample_user_prompt_cleaned: string;
}

export interface CountryDetail {
  country: string;
  iso3: string;
  topics: TopicCount[];
  sentiment: SentimentCount[];
  languages: LanguageCount[];
  questions: QuestionRow[];
}

export interface CountryComparisonResponse {
  countries: string[];
  volume: { country: string; conversations: number }[];
  topics: { country: string; topic_category: string; conversations: number }[];
  sentiment: { country: string; sentiment_label: string; conversations: number }[];
  languages: { country: string; language: string; conversations: number }[];
}

export interface TopicDetail {
  topic: string;
  by_country: { country: string; conversations: number }[];
  trend: { month: string; conversations: number }[];
}

export interface TrendPoint {
  month: string;
  topic_label: string;
  conversations: number;
}

export interface TrendMetric {
  metric_date: string;
  country: string;
  language: string;
  topic_category: string;
  conversation_count: number;
  previous_period_count: number;
  growth_rate: number | null;
  trend_rank: number;
}

export interface TranslationSummary {
  conversation_id: string;
  country: string;
  language: string;
  summary_text: string;
}

export interface SimilarSummary {
  conversation_id: string;
  country: string;
  language: string;
  topic_label: string;
  sentiment_label: string;
  summary_text: string;
  similarity_score: number;
}

export interface SimilarSummaryResponse {
  selected: Omit<SimilarSummary, "similarity_score">;
  similar: SimilarSummary[];
}

export interface CountryClusterCountry {
  country: string;
  iso3: string;
  cluster_id: number;
  dim1: number;
  dim2: number;
  conversations: number;
  top_topics: string;
  dominant_sentiment: string;
  positive_pct: number;
}

export interface CountryClusterPattern {
  cluster_id: number;
  country_count: number;
  countries: string[];
  dominant_topics: string[];
  dominant_sentiment: string;
  dominant_sentiment_pct: number;
  explanation: string;
}

export interface CountryClustersResponse {
  countries: CountryClusterCountry[];
  patterns: CountryClusterPattern[];
}

export interface TranslationResult {
  conversation_id: string;
  country: string;
  source_language: string;
  target_language: string;
  original_text: string;
  english_text: string;
  local_text: string;
  stored: boolean;
  stored_rows: number;
  provider: string;
}

export interface CountryTranslation {
  country: string;
  target_language: string;
  english_text: string;
  local_text: string;
  note: string | null;
}

export interface HeatmapCell {
  country: string;
  topic_label: string;
  conversations: number;
}

export interface LanguageTopicCell {
  language: string;
  topic_label: string;
  conversations: number;
}

export interface AskResponse {
  answer: string;
  table: Record<string, string | number>[];
  source?: "rules" | "ai";
}

export interface ExtractedTopic {
  topic: string;
  summary: string;
}

export interface ExtractionResult {
  top_topics: ExtractedTopic[];
  key_insights: string;
  emerging_trends: string;
  wow_factor_insights: string;
  story_angles: string;
}

export interface ExtractResponse {
  filter_description: string;
  conversations_analyzed: number;
  result: ExtractionResult;
  extraction_id: number | null;
}

export interface ExtractParams {
  country?: string;
  topic?: string;
  language?: string;
  limit?: number;
}

export interface VoiceScript {
  script: string;
  country: string | null;
  topic: string | null;
  chars: number;
}

export interface DeweyTopicMapping {
  prompt_topic: string;
  topic_label: string;
  topic_category: string;
  dewey_number: string;
  dewey_name: string;
}

export interface DeweyCategoryMapping {
  topic_category: string;
  dewey_number: string;
  dewey_name: string;
}

export interface LibraryTaxonomyResponse {
  topics: DeweyTopicMapping[];
  categories: DeweyCategoryMapping[];
}

export interface LibraryResource {
  id: string;
  title: string;
  authors: string[];
  published?: string | null;
  source: string;
  resource_type: "book" | "magazine" | "article";
  summary?: string | null;
  url?: string | null;
  journal?: string | null;
}

export interface LibrarySearchResponse {
  topic: string;
  dewey: {
    number: string;
    name: string;
    alternatives: { number: string; name: string }[];
  };
  catalog_matches: DeweyTopicMapping[];
  books: LibraryResource[];
  magazines: LibraryResource[];
  articles: LibraryResource[];
  warnings: string[];
}

export interface DeweyPromptRow {
  prompt_id: string;
  prompt_text: string;
  source_language?: string | null;
  topic_label?: string | null;
  topic_category?: string | null;
  dewey_number: string;
  dewey_name: string;
  confidence?: number | null;
}

export interface DeweyPromptSearchResponse {
  dewey?: string | null;
  query?: string | null;
  limit: number;
  offset: number;
  count: number;
  total_count: number;
  total_pages: number;
  rows: DeweyPromptRow[];
}

export interface DeweyIndexRunResponse {
  job_id: string;
  status: "queued";
  message: string;
}

export interface DeweyIndexJobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed" | "canceled";
  params: Record<string, unknown>;
  result?: Record<string, unknown> | null;
  error?: string | null;
  cancel_requested?: boolean;
  processed_rows?: number | null;
  indexed_rows?: number | null;
  total_rows_requested?: number | null;
  progress_percent?: number | null;
  created_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface DeweyIndexJobsResponse {
  count: number;
  jobs: DeweyIndexJobStatus[];
}

export interface DeweyTaxonomyOverview {
  [classId: string]: {
    name: string;
    divisions: Record<string, string>;
  };
}

export interface DeweyTaxonomyClass {
  number: string;
  name: string;
  divisions: Record<string, string>;
}

export interface DeweyTaxonomyDetailed {
  name: string;
  full_breakdown: Record<
    string,
    {
      title: string;
      sections: Record<string, string>;
    }
  >;
}

export interface DeweyTaxonomySearchResult {
  type: "class" | "division";
  dewey_number: string;
  name: string;
  match: "class_name" | "division_name";
}

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
}

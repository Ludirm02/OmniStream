export type Domain = "video" | "music" | "podcast" | "movie" | "news";

export interface ContentCard {
  id: string;
  title: string;
  domain: Domain;
  description: string;
  source: string;
  url: string;
  duration_minutes: number;
  tags: string[];
  mood_score: number;
  energy_score: number;
}

export interface RecommendationCard extends ContentCard {
  score: number;
  explanation: string;
  rank_reasons: string[];
}

export interface BundleCard {
  name: string;
  vibe: string;
  expected_minutes: number;
  explanation: string;
  items: RecommendationCard[];
}

export interface ContextSummary {
  vibe: string;
  time_segment: string;
  device: string;
  session_minutes: number;
  objective: string;
}

export interface UserInsights {
  top_tags: string[];
  dominant_domains: string[];
  curiosity_score: number;
  momentum_label: string;
}

export interface RecommendationResponse {
  recommendations: RecommendationCard[];
  bundles: BundleCard[];
  context: ContextSummary;
  insights: UserInsights;
  generated_at: string;
}

export interface VibeOption {
  id: string;
  label: string;
  objective: string;
}

export interface ResumeItem {
  content: ContentCard;
  completion_ratio: number;
  time_spent_seconds: number;
  last_seen_at: string;
}

export interface ResumeResponse {
  user_id: string;
  items: ResumeItem[];
}

export interface DailyFeedSlot {
  slot: string;
  vibe: string;
  items: RecommendationCard[];
}

export interface DailyFeedResponse {
  user_id: string;
  generated_at: string;
  slots: DailyFeedSlot[];
}

export interface RabbitHoleResponse {
  seed: RecommendationCard;
  journey: RecommendationCard[];
}

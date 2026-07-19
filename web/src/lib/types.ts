// TypeScript interfaces mirroring the FastAPI Pydantic schemas (core/schemas.py).
// Generated from backend introspection — keep in sync when backend schemas change.

export interface SourceSchema {
  id: number
  slug: string
  display_name: string
  site_url: string
  adapter_kind: string  // "dedicated" | "universal"
  is_active: boolean
  crawl_config: Record<string, unknown> | null
}

export interface RawListingBrief {
  id: number
  source_slug: string | null
  source_display_name: string | null
  url_source: string
  price_parsed: number | null
  currency: string | null
  review_status: string  // pending | auto_promoted | human_approved | rejected
  match_confidence: number | null
}

export interface ListingHistoryEvent {
  id: number
  event_type: string  // first_seen | price_change | availability_change | appeared | removed
  price_observed: number | null
  availability: string | null
  observed_at: string
  diff: { old_price?: number; new_price?: number; old_availability?: string; new_availability?: string } | null
}

export interface AnnonceBreve {
  id: number
  title: string
  property_type: string | null
  price: number | null
  currency: string
  city: string | null
  neighborhood: string | null
  location_slug: string | null
  lat: number | null
  lng: number | null
  bedrooms: number | null
  bathrooms: number | null
  area_sqm: number | null
  images: string[]
  best_source: string | null
}

export interface AnnonceDetaillee extends AnnonceBreve {
  description: string | null
  location_raw: string | null
  sources: RawListingBrief[]
  price_history: ListingHistoryEvent[]
  match_explanation: Record<string, unknown> | null
  match_confidence: number | null
  created_at: string | null
  last_seen_at: string | null
}

export type ListingCategory = 'Structure' | 'Land' | null
export type ComparisonMetric = 'total_price' | 'price_per_sqm'
export type FallbackLevel = 'neighborhood' | 'city' | null

export interface PriceAnalyse {
  listing_id: number
  price: number | null
  city: string | null
  property_type: string | null
  sample_size: number
  min_price: number | null
  max_price: number | null
  mean_price: number | null
  median_price: number | null
  percentile: number | null
  verdict: 'below_market' | 'around_market' | 'above_market' | 'insufficient_data'
  summary: string
  // Category-aware additions (all nullable for backwards compatibility)
  category: ListingCategory
  comparison_metric: ComparisonMetric | null
  avg_comparison: number | null
  listing_comparison: number | null
  savings: number | null
  fallback_level: FallbackLevel
  min_price_per_sqm: number | null
  max_price_per_sqm: number | null
  avg_price_per_sqm: number | null
}

export interface LocationSchema {
  id: number
  city: string
  neighborhood: string | null
  slug: string
  lat: number | null
  lng: number | null
}

export interface NeighborhoodAnalyticsSchema {
  location_id: number
  city: string
  neighborhood: string | null
  slug: string
  property_type: string | null
  listing_count: number
  average_price: number | null
  median_price: number | null
  min_price: number | null
  max_price: number | null
  price_per_sqm: number | null
  premium_score: number | null
  demand_score: number | null
  growth_score: number | null
  activity_score: number | null
  luxury_score: number | null
  trend_direction: 'up' | 'down' | 'flat' | null
  trend_pct: number | null
  // Category-aware additions (all nullable for backwards compatibility)
  category: ListingCategory
  min_price_per_sqm: number | null
  max_price_per_sqm: number | null
  avg_price_per_sqm: number | null
  fallback_level: FallbackLevel
}

export interface TrendingNeighborhood {
  slug: string
  city: string
  neighborhood: string
  growth_score: number
  trend_pct: number
  median_price: number
}

export interface ReviewAction {
  action: 'approve' | 'reject'
}

export interface SchedulerJobSchema {
  id: number
  job_type: string  // crawl_all | crawl_source | refresh | analytics
  source_id: number | null
  cron_expr: string | null
  last_run: string | null
  next_run: string | null
  status: string  // scheduled | running | succeeded | failed
  last_error: string | null
}

export interface CrawlResult {
  ok: boolean
  stats: Record<string, unknown> | null
  error: string | null
}

export interface CrawlSessionSummary {
  crawl_session_id: string
  source_slug: string
  started_at: string | null
  total_listings: number
  new_listings: number
  duplicates: number
  pending_count: number
  auto_promoted: number
  rejected: number
  status: string
}

export interface RawListingPayload {
  id: number
  url_source: string
  title_raw: string
  payload: Record<string, unknown> | null
}

export interface DashboardStats {
  counts: {
    total_raw_listings: number
    total_canonicals: number
    active_canonicals: number
    total_sources: number
    active_sources: number
    pending_review: number
    unique_cities: number
    unique_neighborhoods: number
    total_locations: number
  }
  price_stats: {
    min: number | null
    avg: number | null
    max: number | null
  }
  property_types: Array<{ type: string; count: number }>
  purpose_split: {
    rent: number
    sale: number
  }
  top_cities: Array<{ city: string; count: number }>
  jobs_summary: {
    running: number
    failed: number
  }
  recent_activity: {
    last_24h: number
    last_7d: number
  }
}

export interface HealthSchema {
  status: string
  version: string
  database: string
  scheduler_running: boolean
}

export interface CityProfileSchema {
  id: number
  city: string
  region: string | null
  security_rating: string | null
  security_summary: string | null
  current_threats: unknown[] | null
  safest_zones: string[] | null
  emergency_contacts: unknown[] | null
  travel_tips: string | null
  curfew_info: string | null
  population: number | null
  area_description: string | null
}

export interface NeighborhoodProfileSchema {
  id: number
  location_id: number | null
  city: string
  neighborhood: string | null
  security_rating: string | null
  security_notes: string | null
  amenities: unknown[] | null
  transport_info: string | null
  real_estate_context: string | null
  demographics: string | null
  landmarks: string[] | null
  risk_factors: string[] | null
  description: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatRequest {
  message: string
  history: ChatMessage[]
  language: 'fr' | 'en'
}

export interface ChatResponse {
  reply: string
  properties: AnnonceBreve[]
  tool_used: string | null
  tool_metadata: { type: string; data: Record<string, unknown> } | null
}

// Ad-hoc shape returned by GET /admin/review/pending
export interface PendingItem {
  id: number
  title_raw: string
  price_parsed: number | null
  currency: string | null
  location_raw: string | null
  url_source: string
  match_confidence: number | null
  match_explanation: Record<string, unknown> | null
  is_duplicate: boolean
  crawled_at: string
}
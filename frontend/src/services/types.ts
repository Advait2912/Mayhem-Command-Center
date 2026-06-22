/**
 * services/types.ts
 * Source of truth: migration/API_CONTRACT.md + migration/FRONTEND_ARCHITECTURE.md
 */

// ── META ──────────────────────────────────────────────────────────────
export interface ZoneCentroid {
  latitude: number;
  longitude: number;
}

export interface MetaResponse {
  causes: string[];
  zones: string[];
  veh_types: string[];
  event_count: number;
  zone_centroids: Record<string, ZoneCentroid>;
}

// ── EVENTS ────────────────────────────────────────────────────────────
export interface EventListItem {
  id: number;
  event_cause: string;
  zone_filled: string;
  start_ist?: string | null;
  model_track: string;
  closure_probability?: number | null;
  requires_road_closure: boolean;
  description?: string | null;
}

export interface EventListResponse {
  total: number;
  events: EventListItem[];
}

// ── ADVISORY ──────────────────────────────────────────────────────────
export interface DurationQuantile {
  type: "quantile";
  p10_hrs: number;
  p50_hrs: number;
  p90_hrs: number;
}

export interface DurationBand {
  type: "band";
  band: string;
  median_hrs_raw: number;
  confidence: string;
}

export interface DurationNone {
  type: "none";
  note: string;
}

export type DurationResult = DurationQuantile | DurationBand | DurationNone;

export interface PriorityResult {
  probability_high: number;
  label: "HIGH" | "LOW";
}

export interface RoutingResult {
  footprint_size: number;
  baseline_minutes: number;
  affected_minutes?: number | null;
  delay_minutes?: number | null;
  alt_route_exists: boolean;
  blocked_node_count: number;
  blocked_nodes: number[];
  /** [[lat, lng], ...], same order as blocked_nodes. */
  blocked_nodes_coordinates: [number, number][];
}

export interface DiversionRoute {
  rank: number;
  path_length: number;
  distance_km: number;
  travel_minutes: number;
  via: string;
  path_nodes: number[];
  /** [[lat, lng], ...] tracing path_nodes in order. */
  coordinates: [number, number][];
}

export interface SimilarEvent {
  event_cause: string;
  zone: string;
  duration_hrs?: number | null;
  requires_road_closure: boolean;
  recommended_officers?: number | null;
  similarity: number;
}

export interface SimilarEventsSummary {
  n: number;
  avg_resolution_hrs?: number | null;
  avg_officers?: number | null;
  closure_rate?: number | null;
}

export interface ConflictEvent {
  event_cause: string;
  closure_probability: number;
}

export interface ConflictsResult {
  count: number;
  events: ConflictEvent[];
}

export interface NetworkResilienceRoute {
  rank: number;
  path_length: number;
  distance_km: number;
  travel_minutes: number;
  via: string;
  compromised: boolean;
}

export interface NetworkResilienceResult {
  routes_checked: number;
  routes_compromised: number;
  warning?: string | null;
  route_status: NetworkResilienceRoute[];
}

export interface HikeContext {
  zone: string;
  predicted_window: string;
  trigger_reason: string;
  confidence: number;
  suggested_event_cause: string;
  source_snippet?: string | null;
}

export interface HistoricalPeakWindow {
  window: string;
  basis: string;
}

export interface Advisory {
  event_id?: string;
  event_cause: string;
  zone: string;
  closure_probability: number;
  recommended_officers: number;
  cascade_risk_score: number;
  spatial_confidence: boolean;
  spatial_warning?: string | null;
  recommended_tow_trucks?: number | null;
  signal_timing_suggestion?: string | null;
  historical_peak_window?: HistoricalPeakWindow | null;
  priority?: PriorityResult | null;
  duration?: DurationResult | null;
  predicted_hike_context?: HikeContext | null;
  conflicts?: ConflictsResult | null;
  latitude: number;
  longitude: number;
  footprint_radius_km: number;
  routing?: RoutingResult | null;
  recommended_barricade_node?: number | null;
  /** [lat, lng] for recommended_barricade_node, or null if none recommended. */
  recommended_barricade_coordinates?: [number, number] | null;
  barricade_candidates_considered: number[];
  diversion_routes: DiversionRoute[];
  network_resilience?: NetworkResilienceResult | null;
  similar_past_events: SimilarEvent[];
  similar_past_events_summary?: SimilarEventsSummary | null;
}

// ── OUTCOMES ──────────────────────────────────────────────────────────
export interface OutcomeRecord {
  logged_at: string;
  source_event_id?: string | null;
  event_cause: string;
  zone: string;
  predicted_officers?: number | null;
  predicted_closure_probability?: number | null;
  predicted_cascade_risk_score?: number | null;
  actual_officers_used?: number | null;
  actual_duration_hrs?: number | null;
  actual_required_closure?: "true" | "false" | null;
  actual_priority?: "HIGH" | "LOW" | null;
  notes?: string | null;
  used_for_training?: boolean | null;
}

export interface OutcomeListResponse {
  count: number;
  outcomes: OutcomeRecord[];
}

export interface OutcomeCreateRequest {
  source_event_id?: any;
  event_cause: string;
  zone: string;
  predicted_officers: number;
  predicted_closure_probability: number;
  predicted_cascade_risk_score?: number | null;
  actual_officers_used?: number | null;
  actual_duration_hrs?: number | null;
  actual_required_closure?: string | null;
  actual_priority?: string | null;
  notes?: string | null;
}

export interface OutcomeCreateResponse {
  status: string;
  record: OutcomeRecord;
}

// ── PREDICT ───────────────────────────────────────────────────────────
export interface PredictRequest {
  event_cause: string;
  zone_filled: string;
  latitude: number;
  longitude: number;
  start_datetime: string;
  description?: string;
  veh_type?: string;
  corridor?: string;
  gba_identifier?: string;
  endlatitude?: number | null;
  endlongitude?: number | null;
}

/**
 * services/api.ts
 * API Client for all 6 FastAPI endpoints.
 * Uses relative path '/api' which Vite proxies to localhost:8000 during dev.
 */

import {
  MetaResponse,
  EventListResponse,
  Advisory,
  OutcomeListResponse,
  OutcomeCreateRequest,
  OutcomeCreateResponse,
  PredictRequest,
} from './types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Endpoint 1: GET /api/meta
 */
export async function getMeta(): Promise<MetaResponse> {
  const res = await fetch(`${BASE_URL}/meta`);
  if (!res.ok) throw new Error(`Failed to fetch meta: ${res.statusText}`);
  return res.json();
}

/**
 * Endpoint 2: GET /api/events
 */
export async function getEvents(params: {
  search?: string;
  cause?: string;
  zone?: string;
  track?: string;
  limit?: number;
  offset?: number;
}): Promise<EventListResponse> {
  const url = new URL(`${BASE_URL}/events`, window.location.origin);
  if (params.search) url.searchParams.set('search', params.search);
  if (params.cause) url.searchParams.set('cause', params.cause);
  if (params.zone) url.searchParams.set('zone', params.zone);
  if (params.track) url.searchParams.set('track', params.track);
  if (params.limit) url.searchParams.set('limit', params.limit.toString());
  if (params.offset) url.searchParams.set('offset', params.offset.toString());

  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`Failed to fetch events: ${res.statusText}`);
  return res.json();
}

/**
 * Endpoint 3: GET /api/events/{id}/advisory
 */
export async function getAdvisory(id: number | string): Promise<Advisory> {
  const res = await fetch(`${BASE_URL}/events/${id}/advisory`);
  if (!res.ok) throw new Error(`Failed to fetch advisory for event ${id}: ${res.statusText}`);
  return res.json();
}

/**
 * Endpoint 4: POST /api/predict
 */
export async function predict(body: PredictRequest): Promise<Advisory> {
  const res = await fetch(`${BASE_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Prediction failed: ${err}`);
  }
  return res.json();
}

/**
 * Endpoint 5: GET /api/outcomes
 */
export async function getOutcomes(): Promise<OutcomeListResponse> {
  const res = await fetch(`${BASE_URL}/outcomes`);
  if (!res.ok) throw new Error(`Failed to fetch outcomes: ${res.statusText}`);
  return res.json();
}

/**
 * Endpoint 6: POST /api/outcomes
 */
export async function postOutcome(body: OutcomeCreateRequest): Promise<OutcomeCreateResponse> {
  const res = await fetch(`${BASE_URL}/outcomes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Outcome log failed: ${err}`);
  }
  return res.json();
}

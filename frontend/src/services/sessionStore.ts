/**
 * Typed sessionStorage helpers.
 * Data persists across refreshes and tab-switches within the same session.
 * Cleared automatically when the browser session ends.
 */

export const sessionStore = {
  get<T>(key: string): T | null {
    try {
      const raw = sessionStorage.getItem(key);
      return raw ? (JSON.parse(raw) as T) : null;
    } catch {
      return null;
    }
  },

  set<T>(key: string, value: T): void {
    try {
      sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Quota exceeded — silently skip
    }
  },

  remove(key: string): void {
    try {
      sessionStorage.removeItem(key);
    } catch {
      // ignore
    }
  },
};

// ── Session storage keys ──────────────────────────────────────────
export const SESSION_KEYS = {
  // Live Situation Room
  LIVE_EVENTS:       'gridlock:live:events',
  LIVE_FILTERS:      'gridlock:live:filters',
  LIVE_SELECTED_ID:  'gridlock:live:selectedId',

  // New Advisory
  NEW_FORM:          'gridlock:new:form',
  NEW_IS_STRETCH:    'gridlock:new:isStretch',
  NEW_ADVISORY:      'gridlock:new:advisory',

  // Outcomes Log
  OUTCOMES_LOG:      'gridlock:outcomes:log',
} as const;

import React, { useState, useEffect } from 'react';
import { useMeta } from '../hooks/useMeta';
import { PredictRequest, Advisory } from '../services/types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { LiveBoardMap } from '../features/advisory/LiveBoardMap';
import { LiveEventCard } from '../features/advisory/LiveEventCard';
import * as api from '../services/api';
import { sessionStore, SESSION_KEYS } from '../services/sessionStore';

interface LiveEvent {
  id: string;
  advisory: Advisory;
  addedAt: string; // ISO string (serializable for sessionStorage)
}

const haversineKm = (lat1: number, lon1: number, lat2: number, lon2: number) => {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
};

const DEFAULT_FORM: PredictRequest = {
  event_cause: '',
  zone_filled: '',
  latitude: 12.9716,
  longitude: 77.5946,
  start_datetime: new Date().toISOString().slice(0, 16),
  description: '',
  veh_type: '',
  corridor: '',
};

export const LivePredict: React.FC = () => {
  const { data: meta, loading: metaLoading } = useMeta();

  // ── Restore live events from session ──────────────────────────
  const [liveEvents, setLiveEvents] = useState<LiveEvent[]>(() => {
    return sessionStore.get<LiveEvent[]>(SESSION_KEYS.LIVE_EVENTS) ?? [];
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [form, setForm] = useState<PredictRequest>(DEFAULT_FORM);

  const [isStretch, setIsStretch] = useState(false);

  // ── Persist live events whenever they change ───────────────────
  useEffect(() => {
    sessionStore.set(SESSION_KEYS.LIVE_EVENTS, liveEvents);
  }, [liveEvents]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => {
      const updated = { ...prev, [name]: name.includes('lat') || name.includes('lon') ? parseFloat(value) : value };
      if (name === 'zone_filled' && meta?.zone_centroids?.[value]) {
        updated.latitude = meta.zone_centroids[value].latitude;
        updated.longitude = meta.zone_centroids[value].longitude;
      }
      return updated;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.event_cause || !form.zone_filled) return;
    
    setLoading(true);
    setError(null);
    try {
      const payload = { ...form };
      if (!payload.veh_type) payload.veh_type = 'MISSING';
      if (!payload.corridor) payload.corridor = 'MISSING';
      if (!isStretch) {
        delete payload.endlatitude;
        delete payload.endlongitude;
      }

      const advisory = await api.predict(payload);
      const newEvent: LiveEvent = {
        id: `live-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
        advisory,
        addedAt: new Date().toISOString(),
      };
      setLiveEvents(prev => [...prev, newEvent]);
      setForm(prev => ({ ...prev, description: '', start_datetime: new Date().toISOString().slice(0, 16) }));
    } catch (err: any) {
      setError(err.message || 'Failed to predict advisory');
    } finally {
      setLoading(false);
    }
  };

  const removeLiveEvent = (id: string) => {
    setLiveEvents(prev => prev.filter(ev => ev.id !== id));
  };

  const clearBoard = () => {
    setLiveEvents([]);
    sessionStore.remove(SESSION_KEYS.LIVE_EVENTS);
  };

  const handleMapFocus = () => {
    // LiveBoardMap handles bounds via its BoundsUpdater.
  };

  const findNearbyLiveEvents = (ev: { id: string; advisory: Advisory; addedAt: Date }, thresholdKm = 2) => {
    const a = ev.advisory;
    if (a.latitude == null || a.longitude == null) return [];
    const out = [];
    for (const other of eventsWithDate) {
      if (other.id === ev.id) continue;
      const b = other.advisory;
      if (b.latitude == null || b.longitude == null) continue;
      const d = haversineKm(a.latitude, a.longitude, b.latitude, b.longitude);
      if (d <= thresholdKm) out.push({ event: other, distanceKm: d });
    }
    return out.sort((x, y) => x.distanceKm - y.distanceKm);
  };

  // Convert back to a shape LiveEventCard expects (addedAt as Date)
  const sortedEvents = [...liveEvents]
    .sort((x, y) => {
      const xHigh = x.advisory.priority && x.advisory.priority.label === 'HIGH' ? 1 : 0;
      const yHigh = y.advisory.priority && y.advisory.priority.label === 'HIGH' ? 1 : 0;
      if (xHigh !== yHigh) return yHigh - xHigh;
      return new Date(y.addedAt).getTime() - new Date(x.addedAt).getTime();
    });

  // LiveBoardMap and LiveEventCard need Date objects for addedAt
  const eventsWithDate = sortedEvents.map(ev => ({
    ...ev,
    addedAt: new Date(ev.addedAt),
  }));

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%', overflow: 'hidden' }}>
      {/* Left Column: Form */}
      <div style={{ flex: '0 0 450px', display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto', paddingRight: '1rem' }}>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: '18px',
            letterSpacing: '-0.02em',
            background: 'linear-gradient(120deg, #fff 20%, var(--accent-cyan) 55%, var(--accent-blue) 80%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            backgroundSize: '200% auto',
            animation: 'shine 6s linear infinite',
            marginBottom: '4px',
          }}>
            Add event to the live board
          </div>
          <div className="eyebrow" style={{ color: 'var(--accent-cyan)' }}>
            Add events one at a time as reports come in. Each one runs through the full advisory pipeline and stays on the shared map.
          </div>
        </div>
        
        <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
          {metaLoading ? <LoadingSpinner message="Loading options..." /> : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Cause *</label>
                <select name="event_cause" value={form.event_cause} onChange={handleChange} required style={inputStyle}>
                  <option value="">-- Select Cause --</option>
                  {meta?.causes.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Zone *</label>
                <select name="zone_filled" value={form.zone_filled} onChange={handleChange} required style={inputStyle}>
                  <option value="">-- Select Zone --</option>
                  {meta?.zones.map(z => <option key={z} value={z}>{z}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Start Time (IST) *</label>
                <input type="datetime-local" name="start_datetime" value={form.start_datetime} onChange={handleChange} required style={inputStyle} />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Latitude *</label>
                  <input type="number" step="0.0001" name="latitude" value={form.latitude} onChange={handleChange} required style={inputStyle} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Longitude *</label>
                  <input type="number" step="0.0001" name="longitude" value={form.longitude} onChange={handleChange} required style={inputStyle} />
                </div>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '-0.5rem', marginBottom: '0.5rem' }}>
                Auto-filled from zone centroid. Edit to pinpoint exact location.
              </p>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Description</label>
                <textarea name="description" value={form.description} onChange={handleChange} rows={2} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Vehicle Type</label>
                  <select name="veh_type" value={form.veh_type} onChange={handleChange} style={inputStyle}>
                    <option value="">Unknown</option>
                    {meta?.veh_types.map(v => <option key={v} value={v}>{v.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
                  </select>
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Corridor</label>
                  <input type="text" name="corridor" value={form.corridor} onChange={handleChange} placeholder="e.g. ORR" style={inputStyle} />
                </div>
              </div>

              <div style={{ background: 'rgba(0,0,0,0.1)', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.85rem', cursor: 'pointer' }}>
                  <input type="checkbox" checked={isStretch} onChange={(e) => setIsStretch(e.target.checked)} />
                  Stretch event? (e.g. water-logging segment)
                </label>
                
                {isStretch && (
                  <div style={{ display: 'flex', gap: '1rem', marginTop: '0.75rem' }}>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '0.75rem', marginBottom: '0.25rem' }}>End Lat</label>
                      <input type="number" step="0.0001" name="endlatitude" value={form.endlatitude || ''} onChange={handleChange} style={inputStyle} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label style={{ display: 'block', fontSize: '0.75rem', marginBottom: '0.25rem' }}>End Lon</label>
                      <input type="number" step="0.0001" name="endlongitude" value={form.endlongitude || ''} onChange={handleChange} style={inputStyle} />
                    </div>
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '0.5rem' }}>
                <button type="submit" disabled={loading || !form.event_cause || !form.zone_filled} style={btnStyle(true)}>
                  {loading ? 'Predicting...' : '+ Add to live board'}
                </button>
              </div>
            </form>
          )}
        </div>
        
        {error && <ErrorBox error={error} />}
      </div>

      {/* Right Column: Map and Cards */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2 style={{ margin: 0, color: 'var(--text-primary)' }}>
            Live situation map <span style={{ color: 'var(--text-muted)' }}>{liveEvents.length ? `(${liveEvents.length} active)` : ''}</span>
          </h2>
          <button 
            onClick={clearBoard}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              background: 'transparent',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--radius-sm)',
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              fontFamily: 'var(--font-display)',
              fontSize: '12px',
              fontWeight: 600,
            }}
          >
            Clear board
          </button>
        </div>

        <LiveBoardMap events={eventsWithDate} onMarkerClick={(id) => {
          document.getElementById(`livecard-${id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }} />

        <div style={{ flex: '1', overflowY: 'auto', paddingRight: '0.5rem' }}>
          {eventsWithDate.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
              Add an event above — advisories will appear here and stack up as more events come in.
            </div>
          ) : (
            eventsWithDate.map(ev => (
              <LiveEventCard 
                key={ev.id} 
                event={ev} 
                nearbyEvents={findNearbyLiveEvents(ev)} 
                onRemove={removeLiveEvent}
                onMapFocus={handleMapFocus}
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
};

const inputStyle = {
  width: '100%', 
  padding: '0.6rem', 
  borderRadius: 'var(--radius-sm)', 
  border: '1px solid var(--glass-border)', 
  background: 'rgba(0,0,0,0.2)', 
  color: 'white',
  fontFamily: 'inherit'
};

const btnStyle = (primary: boolean) => ({
  flex: 1,
  padding: '0.75rem',
  background: primary ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)',
  color: 'white',
  border: 'none',
  borderRadius: 'var(--radius-sm)',
  fontWeight: 600,
  cursor: 'pointer'
});

import React, { useState, useEffect } from 'react';
import { useMeta } from '../hooks/useMeta';
import { usePredict } from '../hooks/usePredict';
import { PredictRequest, Advisory } from '../services/types';
import { AdvisoryPanel } from '../features/advisory/AdvisoryPanel';
import { EventMap } from '../features/advisory/EventMap';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { sessionStore, SESSION_KEYS } from '../services/sessionStore';

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

export const NewPredict: React.FC = () => {
  const { data: meta, loading: metaLoading } = useMeta();
  const { execute, loading: advLoading, error: advError, reset } = usePredict();

  // ── Restore form from session ──────────────────────────────────
  const [form, setForm] = useState<PredictRequest>(() => {
    const saved = sessionStore.get<PredictRequest>(SESSION_KEYS.NEW_FORM);
    return saved ?? DEFAULT_FORM;
  });

  const [isStretch, setIsStretch] = useState<boolean>(() => {
    return sessionStore.get<boolean>(SESSION_KEYS.NEW_IS_STRETCH) ?? false;
  });

  // ── Restore generated advisory from session ────────────────────
  const [advData, setAdvData] = useState<Advisory | null>(() => {
    return sessionStore.get<Advisory>(SESSION_KEYS.NEW_ADVISORY);
  });

  const [advError2, setAdvError2] = useState<string | null>(null);

  // ── Persist form changes ───────────────────────────────────────
  useEffect(() => {
    sessionStore.set(SESSION_KEYS.NEW_FORM, form);
  }, [form]);

  useEffect(() => {
    sessionStore.set(SESSION_KEYS.NEW_IS_STRETCH, isStretch);
  }, [isStretch]);

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
    
    const payload = { ...form };
    if (!payload.veh_type) payload.veh_type = 'MISSING';
    if (!payload.corridor) payload.corridor = 'MISSING';
    if (!isStretch) {
      delete payload.endlatitude;
      delete payload.endlongitude;
    }
    
    setAdvError2(null);
    try {
      const result = await execute(payload);
      if (result) {
        setAdvData(result);
        sessionStore.set(SESSION_KEYS.NEW_ADVISORY, result);
      }
    } catch (err: any) {
      setAdvError2(err?.message ?? 'Failed to generate advisory');
    }
  };

  const handleClear = () => {
    const freshForm = { ...DEFAULT_FORM, start_datetime: new Date().toISOString().slice(0, 16) };
    setForm(freshForm);
    setIsStretch(false);
    setAdvData(null);
    setAdvError2(null);
    sessionStore.remove(SESSION_KEYS.NEW_FORM);
    sessionStore.remove(SESSION_KEYS.NEW_IS_STRETCH);
    sessionStore.remove(SESSION_KEYS.NEW_ADVISORY);
    reset();
  };

  const displayError = advError2 ?? (advError ? String(advError) : null);

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%' }}>
      {/* Left Column: Form */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%' }}>
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
            Describe a new event
          </div>
          <div className="eyebrow" style={{ color: 'var(--accent-cyan)' }}>
            No event-feed integration here — fill in what a controller would know the moment a report comes in.
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '1.5rem', overflowY: 'auto' }}>
          {metaLoading ? <LoadingSpinner message="Loading options..." /> : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
              {/* ── Classification ── */}
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-3)' }}>Classification</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  <div>
                    <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Event cause *</label>
                    <select name="event_cause" value={form.event_cause} onChange={handleChange} required style={inputStyle}>
                      <option value="">Select...</option>
                      {meta?.causes.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                    <div style={{ flex: 1 }}>
                      <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Vehicle Type</label>
                      <select name="veh_type" value={form.veh_type} onChange={handleChange} style={inputStyle}>
                        <option value="">Unknown</option>
                        {meta?.veh_types.map(v => <option key={v} value={v}>{v.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</option>)}
                      </select>
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Corridor</label>
                      <input type="text" name="corridor" value={form.corridor} onChange={handleChange} placeholder="e.g. Outer Ring Road" style={inputStyle} />
                    </div>
                  </div>
                  <div>
                    <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Description</label>
                    <textarea name="description" value={form.description} onChange={handleChange} rows={2} style={{ ...inputStyle, resize: 'vertical' }} placeholder="Free text..."/>
                  </div>
                </div>
              </div>

              <hr className="divider" style={{ margin: 0 }} />

              {/* ── Location ── */}
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-3)' }}>Location</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  <div>
                    <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Zone *</label>
                    <select name="zone_filled" value={form.zone_filled} onChange={handleChange} required style={inputStyle}>
                      <option value="">Select...</option>
                      {meta?.zones.map(z => <option key={z} value={z}>{z}</option>)}
                    </select>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                    <div style={{ flex: 1 }}>
                      <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Latitude *</label>
                      <input type="number" step="0.0001" name="latitude" value={form.latitude} onChange={handleChange} required style={inputStyle} />
                    </div>
                    <div style={{ flex: 1 }}>
                      <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Longitude *</label>
                      <input type="number" step="0.0001" name="longitude" value={form.longitude} onChange={handleChange} required style={inputStyle} />
                    </div>
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                    Auto-filled from zone centroid — edit to pin exact location
                  </div>

                  {/* Stretch event — logically attached to location */}
                  <div style={{ background: 'rgba(255,255,255,0.03)', padding: 'var(--space-3)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: '13px', cursor: 'pointer', color: 'var(--text-secondary)' }}>
                      <input type="checkbox" checked={isStretch} onChange={(e) => setIsStretch(e.target.checked)} />
                      Stretch event (construction / water-logging segment)
                    </label>
                    {isStretch && (
                      <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-3)' }}>
                        <div style={{ flex: 1 }}>
                          <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>End latitude</label>
                          <input type="number" step="0.0001" name="endlatitude" value={form.endlatitude || ''} onChange={handleChange} style={inputStyle} />
                        </div>
                        <div style={{ flex: 1 }}>
                          <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>End longitude</label>
                          <input type="number" step="0.0001" name="endlongitude" value={form.endlongitude || ''} onChange={handleChange} style={inputStyle} />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <hr className="divider" style={{ margin: 0 }} />

              {/* ── Timing ── */}
              <div>
                <div className="eyebrow" style={{ marginBottom: 'var(--space-3)' }}>Timing</div>
                <div>
                  <label className="eyebrow" style={{ display: 'block', marginBottom: 'var(--space-1)' }}>Start date &amp; time (IST) *</label>
                  <input type="datetime-local" name="start_datetime" value={form.start_datetime} onChange={handleChange} required style={inputStyle} />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
                <button type="submit" disabled={advLoading || !form.event_cause || !form.zone_filled} style={btnStyle(true)}>
                  {advLoading ? 'Predicting...' : 'Run Advisory'}
                </button>
                <button type="button" onClick={handleClear} style={btnStyle(false)}>
                  Clear
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Right Column: Advisory Result */}
      <div style={{ flex: '1.5', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', padding: '2rem', overflowY: 'auto' }}>
        {!advData && !advLoading && !displayError ? (
          <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Submit the form to see an advisory here.
          </div>
        ) : advLoading ? (
          <LoadingSpinner message="Generating ML predictions..." fullPage />
        ) : displayError ? (
          <ErrorBox error={displayError} />
        ) : advData ? (
          <>
            <EventMap advisory={advData} />
            <AdvisoryPanel advisory={advData} />
          </>
        ) : null}
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

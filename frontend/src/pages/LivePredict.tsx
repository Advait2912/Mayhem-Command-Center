import React, { useState } from 'react';
import { useMeta } from '../hooks/useMeta';
import { usePredict } from '../hooks/usePredict';
import { PredictRequest } from '../services/types';
import { AdvisoryPanel } from '../features/advisory/AdvisoryPanel';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';

export const LivePredict: React.FC = () => {
  const { data: meta, loading: metaLoading } = useMeta();
  const { execute, data: advData, loading: advLoading, error: advError, reset } = usePredict();

  const [form, setForm] = useState<PredictRequest>({
    event_cause: '',
    zone_filled: '',
    latitude: 12.9716,
    longitude: 77.5946,
    start_datetime: new Date().toISOString().slice(0, 16),
    description: '',
    veh_type: 'car'
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({
      ...prev,
      [name]: name === 'latitude' || name === 'longitude' ? parseFloat(value) : value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.event_cause || !form.zone_filled) return;
    await execute(form);
  };

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%' }}>
      {/* Left Column: Form */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <h2 style={{ marginBottom: '0.25rem', color: 'var(--text-primary)' }}>New Event Advisory</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Featurizes a hypothetical event from scratch using only cached artifacts and runs the full pipeline.
        </p>
        <div className="glass-panel" style={{ padding: '1.5rem', overflowY: 'auto' }}>
          {metaLoading ? <LoadingSpinner message="Loading options..." /> : (
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Cause *</label>
                <select name="event_cause" value={form.event_cause} onChange={handleChange} required style={inputStyle}>
                  <option value="">-- Select Cause --</option>
                  {meta?.causes.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Zone *</label>
                <select name="zone_filled" value={form.zone_filled} onChange={handleChange} required style={inputStyle}>
                  <option value="">-- Select Zone --</option>
                  {meta?.zones.map(z => <option key={z} value={z}>{z}</option>)}
                </select>
              </div>

              <div style={{ display: 'flex', gap: '1rem' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Latitude</label>
                  <input type="number" step="0.0001" name="latitude" value={form.latitude} onChange={handleChange} style={inputStyle} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Longitude</label>
                  <input type="number" step="0.0001" name="longitude" value={form.longitude} onChange={handleChange} style={inputStyle} />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Start Time</label>
                <input type="datetime-local" name="start_datetime" value={form.start_datetime} onChange={handleChange} style={inputStyle} />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Vehicle Type</label>
                <select name="veh_type" value={form.veh_type} onChange={handleChange} style={inputStyle}>
                  {meta?.veh_types.map(v => <option key={v} value={v}>{v}</option>)}
                </select>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', marginBottom: '0.25rem' }}>Description</label>
                <textarea name="description" value={form.description} onChange={handleChange} rows={3} style={{ ...inputStyle, resize: 'vertical' }} />
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" disabled={advLoading || !form.event_cause || !form.zone_filled} style={btnStyle(true)}>
                  {advLoading ? 'Predicting...' : 'Generate Advisory'}
                </button>
                <button type="button" onClick={() => {
                  setForm({ ...form, event_cause: '', zone_filled: '', description: '' });
                  reset();
                }} style={btnStyle(false)}>
                  Clear
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Right Column: Advisory Result */}
      <div style={{ flex: '1.5', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', padding: '2rem', overflowY: 'auto' }}>
        {!advData && !advLoading && !advError ? (
          <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Fill the form and submit to see prediction
          </div>
        ) : advLoading ? (
          <LoadingSpinner message="Generating ML predictions..." fullPage />
        ) : advError ? (
          <ErrorBox error={advError} />
        ) : advData ? (
          <AdvisoryPanel advisory={advData} />
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

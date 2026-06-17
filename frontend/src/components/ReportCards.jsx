import React from 'react';

export const TriageCard = ({ data }) => (
  <div className="report-card">
    <div className="card-title" style={{ color: 'var(--danger)' }}>Triage</div>
    <div className="data-row">
      <span className="data-label">Priority</span>
      <span className={`data-value badge-${data.priority.toLowerCase()}`}>{data.priority}</span>
    </div>
    <div className="data-row">
      <span className="data-label">Cascade Risk</span>
      <span className="data-value">{data.cascade_risk}</span>
    </div>
    <div className="data-row">
      <span className="data-label">Closure Prob.</span>
      <span className="data-value">{Math.round(data.closure_probability * 100)}%</span>
    </div>
  </div>
);

export const DurationCard = ({ data }) => (
  <div className="report-card">
    <div className="card-title" style={{ color: 'var(--primary)' }}>Expected Duration</div>
    <div className="data-row">
      <span className="data-label">P50 (Median)</span>
      <span className="data-value">{data.p50} hrs</span>
    </div>
    <div className="data-row">
      <span className="data-label">P90 (Worst Case)</span>
      <span className="data-value">{data.p90} hrs</span>
    </div>
  </div>
);

export const SpatialCard = ({ data }) => (
  <div className="report-card">
    <div className="card-title" style={{ color: '#a855f7' }}>Spatial Impact</div>
    <div className="data-row">
      <span className="data-label">Impact Radius</span>
      <span className="data-value">{data.radius_km} km</span>
    </div>
    <div className="data-row">
      <span className="data-label">Est. Delay</span>
      <span className="data-value">{data.estimated_delay_minutes} mins</span>
    </div>
    <div style={{ marginTop: '8px', fontSize: '13px' }}>
      <span className="data-label">Alt Route: </span>
      <span className="data-value">{data.alternate_route}</span>
    </div>
  </div>
);

export const ResourceCard = ({ data }) => (
  <div className="report-card">
    <div className="card-title" style={{ color: 'var(--success)' }}>Resources</div>
    <div className="data-row">
      <span className="data-label">Officers Needed</span>
      <span className="data-value">{data.officers_needed}</span>
    </div>
    <div style={{ marginTop: '8px', fontSize: '13px' }}>
      <span className="data-label">Advisory: </span>
      <span className="data-value">{data.diversion_advisory}</span>
    </div>
  </div>
);

export const SimilarEventsCard = ({ events }) => (
  <div className="report-card">
    <div className="card-title" style={{ color: 'var(--text-muted)' }}>Historical Similarities</div>
    {events.map((e, i) => (
      <div key={i} style={{ fontSize: '13px', borderTop: '1px solid var(--border-color)', paddingTop: '8px', marginTop: '8px' }}>
        <div className="data-row">
          <span className="data-label">{e.summary}</span>
          <span className="data-value">{e.avg_resolution_hours}h</span>
        </div>
      </div>
    ))}
  </div>
);

export const ConflictCard = ({ data }) => (
  <div className={`report-card ${data.has_conflict ? 'conflict-active' : ''}`} style={{ borderLeft: data.has_conflict ? '4px solid var(--danger)' : '1px solid var(--border-color)' }}>
    <div className="card-title" style={{ color: data.has_conflict ? 'var(--danger)' : 'var(--text-muted)' }}>Conflict Analysis</div>
    <div style={{ fontSize: '13px', fontWeight: 500 }}>{data.message}</div>
  </div>
);

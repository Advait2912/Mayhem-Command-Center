import React from 'react';
import { SimilarEvent, SimilarEventsSummary } from '../../services/types';


interface SimilarEventsProps {
  events: SimilarEvent[];
  summary: SimilarEventsSummary | null;
}

export const SimilarEvents: React.FC<SimilarEventsProps> = ({ events, summary }) => {
  if (events.length === 0) return null;

  return (
    <div style={{ marginBottom: '8px' }}>
      {summary && (
        <div style={{ display: 'flex', gap: 'var(--space-5)', flexWrap: 'wrap', marginBottom: 'var(--space-3)', padding: 'var(--space-2) var(--space-3)', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-sm)' }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Matches</div>
            <div className="metric metric-sm">{summary.n}</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Closure Rate</div>
            <div className="metric metric-sm">{summary.closure_rate ? `${(summary.closure_rate * 100).toFixed(1)}%` : 'N/A'}</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Avg Resolution</div>
            <div className="metric metric-sm">{summary.avg_resolution_hrs ? `${summary.avg_resolution_hrs.toFixed(1)}h` : 'N/A'}</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Avg Officers</div>
            <div className="metric metric-sm">{summary.avg_officers ? summary.avg_officers.toFixed(1) : 'N/A'}</div>
          </div>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--text-muted)', textAlign: 'left' }}>
              <th style={{ padding: '4px 6px' }}>Cause</th>
              <th style={{ padding: '4px 6px' }}>Zone</th>
              <th style={{ padding: '4px 6px' }}>Closed?</th>
              <th style={{ padding: '4px 6px' }}>Dur.</th>
              <th style={{ padding: '4px 6px' }}>Off.</th>
              <th style={{ padding: '4px 6px', textAlign: 'right' }}>Sim.</th>
            </tr>
          </thead>
          <tbody>
            {events.map((evt, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                <td style={{ padding: '4px 6px', color: 'var(--text-primary)' }}>{evt.event_cause.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</td>
                <td style={{ padding: '4px 6px', color: 'var(--text-secondary)' }}>{evt.zone}</td>
                <td style={{ padding: '4px 6px', color: evt.requires_road_closure ? 'var(--status-danger)' : 'var(--text-muted)' }}>{evt.requires_road_closure ? 'Yes' : 'No'}</td>
                <td style={{ padding: '4px 6px', color: 'var(--text-secondary)' }}>{evt.duration_hrs ? `${evt.duration_hrs.toFixed(1)}h` : '—'}</td>
                <td style={{ padding: '4px 6px', color: 'var(--text-secondary)' }}>{evt.recommended_officers ?? '—'}</td>
                <td style={{ padding: '4px 6px', textAlign: 'right', fontWeight: 600, color: 'var(--accent-blue)' }}>{(evt.similarity * 100).toFixed(0)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

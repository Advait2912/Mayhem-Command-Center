import React from 'react';
import { SimilarEvent, SimilarEventsSummary } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';

interface SimilarEventsProps {
  events: SimilarEvent[];
  summary: SimilarEventsSummary | null;
}

export const SimilarEvents: React.FC<SimilarEventsProps> = ({ events, summary }) => {
  if (events.length === 0) return null;

  return (
    <SectionBlock title="Case-Based Reasoning (Similar Past Events)" icon="🔍">
      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '1rem', marginBottom: '1.5rem', padding: '1rem', background: 'rgba(255, 255, 255, 0.03)', borderRadius: 'var(--radius-md)' }}>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Matches Found</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{summary.n}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Historical Closure Rate</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{summary.closure_rate ? `${(summary.closure_rate * 100).toFixed(1)}%` : 'N/A'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Avg Resolution</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{summary.avg_resolution_hrs ? `${summary.avg_resolution_hrs.toFixed(1)} hrs` : 'N/A'}</div>
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Avg Officers Used</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 600 }}>{summary.avg_officers ? summary.avg_officers.toFixed(1) : 'N/A'}</div>
          </div>
        </div>
      )}

      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--text-secondary)', textAlign: 'left' }}>
              <th style={{ padding: '0.5rem' }}>Cause</th>
              <th style={{ padding: '0.5rem' }}>Zone</th>
              <th style={{ padding: '0.5rem' }}>Closed?</th>
              <th style={{ padding: '0.5rem' }}>Duration</th>
              <th style={{ padding: '0.5rem' }}>Officers</th>
              <th style={{ padding: '0.5rem', textAlign: 'right' }}>Similarity</th>
            </tr>
          </thead>
          <tbody>
            {events.map((evt, idx) => (
              <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                <td style={{ padding: '0.5rem' }}>{evt.event_cause}</td>
                <td style={{ padding: '0.5rem' }}>{evt.zone}</td>
                <td style={{ padding: '0.5rem' }}>{evt.requires_road_closure ? 'Yes' : 'No'}</td>
                <td style={{ padding: '0.5rem' }}>{evt.duration_hrs ? `${evt.duration_hrs.toFixed(1)}h` : '-'}</td>
                <td style={{ padding: '0.5rem' }}>{evt.recommended_officers ?? '-'}</td>
                <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: 600 }}>{(evt.similarity * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionBlock>
  );
};

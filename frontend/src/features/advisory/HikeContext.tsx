import React from 'react';
import { HikeContext as HikeContextType, HistoricalPeakWindow } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';

interface HikeContextProps {
  hike: HikeContextType | null;
  historical_peak: HistoricalPeakWindow | null;
}

export const HikeContext: React.FC<HikeContextProps> = ({ hike, historical_peak }) => {
  if (!hike && !historical_peak) return null;

  return (
    <SectionBlock title="Traffic Hike Risk" icon="📈">
      {hike && (
        <div style={{ marginBottom: '1rem', padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontWeight: 600, color: '#60a5fa', marginBottom: '0.5rem' }}>
            {hike.trigger_reason}
          </div>
          <div style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Window:</span> {hike.predicted_window}
          </div>
          <div style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Confidence:</span> {(hike.confidence * 100).toFixed(1)}%
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ color: 'var(--text-secondary)' }}>Suggested Match:</span> {hike.suggested_event_cause}
          </div>
          {hike.source_snippet && (
            <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
              "{hike.source_snippet}"
            </div>
          )}
        </div>
      )}

      {historical_peak && (
        <div style={{ padding: '0.75rem', background: 'rgba(255, 255, 255, 0.05)', borderRadius: 'var(--radius-md)', border: '1px solid var(--glass-border)' }}>
          <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Historical Peak Period Active</div>
          <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            <strong>{historical_peak.window}</strong> — {historical_peak.basis}
          </div>
        </div>
      )}
    </SectionBlock>
  );
};

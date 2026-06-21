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
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-4)', padding: 'var(--space-2) var(--space-3)', background: 'rgba(59, 130, 246, 0.08)', border: '1px solid rgba(59, 130, 246, 0.25)', borderRadius: 'var(--radius-sm)', marginBottom: historical_peak ? 'var(--space-2)' : 0 }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Trigger</div>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#60a5fa' }}>{hike.trigger_reason}</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Window</div>
            <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{hike.predicted_window}</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Confidence</div>
            <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{(hike.confidence * 100).toFixed(1)}%</div>
          </div>
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Match</div>
            <div style={{ fontSize: '12px', color: 'var(--text-primary)' }}>{hike.suggested_event_cause}</div>
          </div>
          {hike.source_snippet && (
            <div style={{ width: '100%', fontSize: '11px', fontStyle: 'italic', color: 'var(--text-muted)', paddingTop: '2px' }}>
              &ldquo;{hike.source_snippet}&rdquo;
            </div>
          )}
        </div>
      )}

      {historical_peak && (
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'baseline', padding: 'var(--space-2) var(--space-3)', background: 'rgba(255, 255, 255, 0.04)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)' }}>
          <span className="eyebrow">Historical peak:</span>
          <span style={{ fontSize: '12px', color: 'var(--text-primary)' }}>
            <strong>{historical_peak.window}</strong> — {historical_peak.basis}
          </span>
        </div>
      )}
    </SectionBlock>
  );
};

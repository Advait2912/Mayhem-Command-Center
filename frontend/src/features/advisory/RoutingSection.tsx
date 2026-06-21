import React from 'react';
import { RoutingResult } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';

interface RoutingSectionProps {
  routing: RoutingResult | null;
}

export const RoutingSection: React.FC<RoutingSectionProps> = ({ routing }) => {
  if (!routing) return null;

  return (
    <SectionBlock title="BPR Delay Impact" icon="⏱️">
      <div style={{ display: 'flex', gap: 'var(--space-5)', flexWrap: 'wrap', marginBottom: 'var(--space-2)' }}>
        <div>
          <div className="eyebrow" style={{ marginBottom: '2px' }}>Baseline</div>
          <div className="metric metric-sm" style={{ color: 'var(--text-primary)' }}>{routing.baseline_minutes.toFixed(1)} min</div>
        </div>
        {typeof routing.affected_minutes === 'number' && (
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Affected</div>
            <div className="metric metric-sm" style={{ color: 'var(--text-primary)' }}>{routing.affected_minutes.toFixed(1)} min</div>
          </div>
        )}
        {typeof routing.delay_minutes === 'number' && (
          <div>
            <div className="eyebrow" style={{ marginBottom: '2px' }}>Added Delay</div>
            <div className="metric metric-sm" style={{ color: 'var(--status-danger)' }}>+{routing.delay_minutes.toFixed(1)} min</div>
          </div>
        )}
        <div>
          <div className="eyebrow" style={{ marginBottom: '2px' }}>Footprint</div>
          <div className="metric metric-sm" style={{ color: 'var(--text-primary)' }}>{routing.footprint_size} nodes</div>
        </div>
        <div>
          <div className="eyebrow" style={{ marginBottom: '2px' }}>Alt Route</div>
          <div className="metric metric-sm" style={{ color: routing.alt_route_exists ? 'var(--status-success)' : 'var(--status-danger)' }}>
            {routing.alt_route_exists ? 'Yes' : 'No'}
          </div>
        </div>
      </div>
    </SectionBlock>
  );
};

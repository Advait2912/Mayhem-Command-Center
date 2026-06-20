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
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Baseline Time</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{routing.baseline_minutes.toFixed(1)} min</div>
        </div>
        {routing.affected_minutes !== null && (
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Affected Time</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{routing.affected_minutes.toFixed(1)} min</div>
          </div>
        )}
        {routing.delay_minutes !== null && (
          <div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Added Delay</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--status-danger)' }}>
              +{routing.delay_minutes.toFixed(1)} min
            </div>
          </div>
        )}
        <div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Footprint Nodes</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>{routing.footprint_size}</div>
        </div>
      </div>
      <div style={{ fontSize: '0.9rem' }}>
        <strong>Alt Route Exists:</strong> {routing.alt_route_exists ? 'Yes' : 'No'}
      </div>
    </SectionBlock>
  );
};

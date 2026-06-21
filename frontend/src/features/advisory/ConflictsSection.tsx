import React from 'react';
import { ConflictsResult } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';
import { getProbabilityBadge } from '../../components/Badge';

interface ConflictsSectionProps {
  conflicts: ConflictsResult | null;
}

export const ConflictsSection: React.FC<ConflictsSectionProps> = ({ conflicts }) => {
  if (!conflicts || conflicts.count === 0) return null;

  return (
    <SectionBlock title="Spatial Conflicts" icon="⚔️">
      <div style={{ marginBottom: 'var(--space-2)', fontSize: '12px', color: 'var(--status-warning)', fontWeight: 500 }}>
        {conflicts.count} concurrent event(s) in this zone.
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
        {conflicts.events.map((evt, idx) => (
          <div key={idx} style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 'var(--space-2)',
            padding: '3px 8px', 
            background: 'rgba(255, 255, 255, 0.05)', 
            borderRadius: '999px',
            border: '1px solid var(--glass-border)',
            fontSize: '12px'
          }}>
            <span style={{ fontWeight: 500 }}>{evt.event_cause}</span>
            {getProbabilityBadge(evt.closure_probability)}
          </div>
        ))}
      </div>
    </SectionBlock>
  );
};

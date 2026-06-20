import React from 'react';
import { NetworkResilienceResult } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';

interface NetworkResilienceProps {
  network_resilience: NetworkResilienceResult | null;
}

export const NetworkResilience: React.FC<NetworkResilienceProps> = ({ network_resilience }) => {
  if (!network_resilience) return null;

  const isCompromised = network_resilience.routes_compromised > 0;

  return (
    <SectionBlock title="Network Resilience" icon="🕸️">
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ fontSize: '1rem', fontWeight: 600, color: isCompromised ? 'var(--status-warning)' : 'var(--status-success)' }}>
          {network_resilience.routes_compromised} of {network_resilience.routes_checked} major routes compromised
        </div>
        {network_resilience.warning && (
          <div style={{ marginTop: '0.5rem', padding: '0.75rem', background: 'var(--status-warning-bg)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-sm)', color: 'var(--status-warning)' }}>
            ⚠️ {network_resilience.warning}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {network_resilience.route_status.map((rt) => (
          <div key={rt.rank} style={{ 
            display: 'flex', 
            justifyContent: 'space-between',
            padding: '0.5rem 0.75rem', 
            background: 'rgba(255, 255, 255, 0.03)', 
            borderRadius: 'var(--radius-sm)',
            borderLeft: `3px solid ${rt.compromised ? 'var(--status-warning)' : 'var(--status-success)'}`
          }}>
            <div>
              <div style={{ fontWeight: 500 }}>Via {rt.via}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {rt.distance_km.toFixed(1)} km • {rt.travel_minutes.toFixed(1)} min
              </div>
            </div>
            <div style={{ fontWeight: 600, color: rt.compromised ? 'var(--status-warning)' : 'var(--status-success)' }}>
              {rt.compromised ? 'Compromised' : 'Clear'}
            </div>
          </div>
        ))}
      </div>
    </SectionBlock>
  );
};

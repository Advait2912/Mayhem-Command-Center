import React from 'react';
import { NetworkResilienceResult } from '../../services/types';

interface NetworkResilienceProps {
  network_resilience: NetworkResilienceResult | null;
}

export const NetworkResilience: React.FC<NetworkResilienceProps> = ({ network_resilience }) => {
  if (!network_resilience) return null;

  const { routes_compromised, routes_checked, warning, route_status } = network_resilience;

  return (
    <div style={{ marginBottom: 'var(--space-3)' }}>
      {/* Headline metric */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-2)' }}>
        <span
          className="metric metric-sm"
          style={{ color: routes_compromised > 0 ? 'var(--status-danger)' : 'var(--status-success)' }}
        >
          {routes_compromised} / {routes_checked}
        </span>
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          routes compromised
        </span>
      </div>

      {/* Status strip */}
      <div className="status-strip" style={{ marginBottom: 'var(--space-3)' }}>
        {route_status.map((rt) => (
          <div
            key={rt.rank}
            className={`status-strip-segment${rt.compromised ? ' compromised' : ''}`}
            title={`#${rt.rank} via ${rt.via} — ${rt.compromised ? 'Compromised' : 'Clear'}`}
          />
        ))}
      </div>

      {/* Compact mono row list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {route_status.map((rt) => (
          <div key={rt.rank} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0 0' }}>
            <div style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-secondary)' }}>
              #{rt.rank} via {rt.via}
              <span style={{ color: 'var(--text-muted)', marginLeft: 'var(--space-2)' }}>
                · {rt.distance_km.toFixed(1)} km · {rt.travel_minutes.toFixed(0)} min
              </span>
            </div>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              fontWeight: 600,
              color: rt.compromised ? 'var(--status-danger)' : 'var(--status-success)',
            }}>
              {rt.compromised ? 'COMPROMISED' : 'CLEAR'}
            </span>
          </div>
        ))}
      </div>

      {/* Warning callout */}
      {warning && (
        <div style={{
          marginTop: 'var(--space-3)',
          padding: 'var(--space-2) var(--space-3)',
          background: 'var(--status-warning-bg)',
          borderLeft: '3px solid var(--status-warning)',
          borderRadius: 'var(--radius-sm)',
          fontSize: '13px',
          color: 'var(--status-warning)'
        }}>
          {warning}
        </div>
      )}
    </div>
  );
};

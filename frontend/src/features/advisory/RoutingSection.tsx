import React from 'react';
import { RoutingResult } from '../../services/types';


interface RoutingSectionProps {
  routing: RoutingResult | null;
}

export const RoutingSection: React.FC<RoutingSectionProps> = ({ routing }) => {
  if (!routing) return null;

    <div style={{ marginBottom: '8px' }}>
      <div className="eyebrow" style={{ color: 'var(--text-secondary)', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '4px' }}>
        <span>⏱️</span> BPR Delay Impact
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(70px, 1fr))', gap: '8px' }}>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 8px', borderRadius: '4px' }}>
          <div className="eyebrow" style={{ marginBottom: '2px', fontSize: '9px' }}>Baseline</div>
          <div className="metric metric-sm" style={{ color: 'var(--text-primary)', fontSize: '13px' }}>{routing.baseline_minutes.toFixed(1)}m</div>
        </div>
        {typeof routing.affected_minutes === 'number' && (
          <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 8px', borderRadius: '4px' }}>
            <div className="eyebrow" style={{ marginBottom: '2px', fontSize: '9px' }}>Affected</div>
            <div className="metric metric-sm" style={{ color: 'var(--text-primary)', fontSize: '13px' }}>{routing.affected_minutes.toFixed(1)}m</div>
          </div>
        )}
        {typeof routing.delay_minutes === 'number' && (
          <div style={{ background: 'rgba(255, 255, 255,0.1)', padding: '6px 8px', borderRadius: '4px', border: '1px solid rgba(255, 255, 255,0.2)' }}>
            <div className="eyebrow" style={{ marginBottom: '2px', fontSize: '9px', color: 'var(--status-danger)' }}>Added Delay</div>
            <div className="metric metric-sm" style={{ color: 'var(--status-danger)', fontSize: '13px' }}>+{routing.delay_minutes.toFixed(1)}m</div>
          </div>
        )}
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 8px', borderRadius: '4px' }}>
          <div className="eyebrow" style={{ marginBottom: '2px', fontSize: '9px' }}>Footprint</div>
          <div className="metric metric-sm" style={{ color: 'var(--text-primary)', fontSize: '13px' }}>{routing.footprint_size} <span style={{ fontSize: '10px' }}>nodes</span></div>
        </div>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px 8px', borderRadius: '4px' }}>
          <div className="eyebrow" style={{ marginBottom: '2px', fontSize: '9px' }}>Alt Route</div>
          <div className="metric metric-sm" style={{ color: routing.alt_route_exists ? 'var(--status-success)' : 'var(--status-danger)', fontSize: '13px' }}>
            {routing.alt_route_exists ? 'Yes' : 'No'}
          </div>
        </div>
      </div>
    </div>
};

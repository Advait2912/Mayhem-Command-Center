import React from 'react';
import { DiversionRoute } from '../../services/types';

interface BarricadeSectionProps {
  recommended_barricade_node: number | null;
  barricade_candidates_considered: number[];
  diversion_routes: DiversionRoute[];
}

export const BarricadeSection: React.FC<BarricadeSectionProps> = ({
  recommended_barricade_node,
  barricade_candidates_considered,
  diversion_routes
}) => {
  if (!recommended_barricade_node) return null;

  // Find max values for bar scaling
  const maxDist = diversion_routes.length > 0
    ? Math.max(...diversion_routes.map(r => r.distance_km))
    : 1;
  const maxTime = diversion_routes.length > 0
    ? Math.max(...diversion_routes.map(r => r.travel_minutes))
    : 1;

  return (
    <div style={{ marginBottom: 'var(--space-3)' }}>
      {/* Barricade node — single compact row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
        <div className="eyebrow">Barricade node</div>
        <span className="metric metric-sm" style={{ color: 'var(--status-warning)' }}>
          {recommended_barricade_node}
        </span>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          ({barricade_candidates_considered.length} candidates)
        </span>
      </div>

      {/* Diversion routes as compact compare-row bars */}
      {diversion_routes.length > 0 && (
        <div>
          <div className="eyebrow" style={{ marginBottom: 'var(--space-2)' }}>Diversion routes</div>
          {diversion_routes.map((rt, i) => (
            <div key={rt.rank} style={{ marginBottom: 'var(--space-3)' }}>
              {/* Route label */}
              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginBottom: 'var(--space-1)', fontFamily: 'var(--font-mono)' }}>
                <span style={{ color: i === 0 ? 'var(--accent-blue)' : 'var(--accent-purple)', fontWeight: 600 }}>
                  #{rt.rank}
                </span>
                {' '}via {rt.via}
                <span style={{ color: 'var(--text-muted)', marginLeft: 'var(--space-2)' }}>
                  · {rt.path_length} nodes
                </span>
              </div>
              {/* Distance bar */}
              <div className="compare-row">
                <span className="compare-label">Dist</span>
                <div className="compare-track">
                  <div
                    className={`compare-fill${i > 0 ? ' alt' : ''}`}
                    style={{ width: `${(rt.distance_km / maxDist) * 100}%` }}
                  />
                </div>
                <span className="compare-value" style={{ color: 'var(--text-primary)' }}>
                  {rt.distance_km.toFixed(1)} km
                </span>
              </div>
              {/* Time bar */}
              <div className="compare-row">
                <span className="compare-label">Time</span>
                <div className="compare-track">
                  <div
                    className={`compare-fill${i > 0 ? ' alt' : ''}`}
                    style={{ width: `${(rt.travel_minutes / maxTime) * 100}%` }}
                  />
                </div>
                <span className="compare-value" style={{ color: 'var(--text-primary)' }}>
                  {rt.travel_minutes.toFixed(1)} min
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

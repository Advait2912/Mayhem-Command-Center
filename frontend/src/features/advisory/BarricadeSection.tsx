import React from 'react';
import { DiversionRoute } from '../../services/types';
import { SectionBlock } from '../../components/SectionBlock';

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

  return (
    <SectionBlock title="Barricade & Diversion" icon="🚧">
      <div style={{ marginBottom: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Recommended Barricade Node</div>
        <div style={{ fontSize: '1.25rem', fontWeight: 600, color: 'var(--status-warning)' }}>
          {recommended_barricade_node}
        </div>
        <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          (Evaluated {barricade_candidates_considered.length} upstream candidates)
        </div>
      </div>

      {diversion_routes.length > 0 && (
        <div>
          <div style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '0.5rem' }}>Top Diversion Routes</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {diversion_routes.map((rt) => (
              <div key={rt.rank} style={{ 
                background: 'rgba(255, 255, 255, 0.05)', 
                padding: '0.75rem', 
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--glass-border)'
              }}>
                <div style={{ fontWeight: 600, marginBottom: '0.25rem' }}>
                  Rank #{rt.rank}: Via {rt.via}
                </div>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  {rt.distance_km.toFixed(1)} km • {rt.travel_minutes.toFixed(1)} min • {rt.path_length} nodes
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </SectionBlock>
  );
};

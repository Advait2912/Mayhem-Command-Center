import React from 'react';
import { Advisory } from '../../services/types';
import { StatGrid } from './StatGrid';
import { RoutingSection } from './RoutingSection';
import { BarricadeSection } from './BarricadeSection';
import { NetworkResilience } from './NetworkResilience';
import { ConflictsSection } from './ConflictsSection';
import { SimilarEvents } from './SimilarEvents';
import { HikeContext } from './HikeContext';
import { OutcomeForm } from './OutcomeForm';
import { EventMap } from './EventMap';
import { getProbabilityBadge } from '../../components/Badge';

interface AdvisoryPanelProps {
  advisory: Advisory;
  sourceEventId?: string | number;
}

export const AdvisoryPanel: React.FC<AdvisoryPanelProps> = ({ advisory, sourceEventId }) => {
  return (
    <div className="advisory-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <header style={{ marginBottom: '1rem' }}>
        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.25rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
          Advisory Details
          {getProbabilityBadge(advisory.closure_probability)}
        </h2>
        <div style={{ color: 'var(--text-muted)' }}>
          {advisory.event_cause} in {advisory.zone}
        </div>
      </header>

      {/* Map Visualization */}
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Location & Congestion Footprint
        </div>
        <EventMap advisory={advisory} />
      </div>

      {/* Primary Metrics */}
      <StatGrid advisory={advisory} />

      {/* Spatial Warnings */}
      {advisory.spatial_warning && (
        <div className="glass-panel" style={{ padding: '1rem', background: 'var(--status-warning-bg)', borderLeft: '4px solid var(--status-warning)', color: '#fcd34d', marginBottom: '1rem' }}>
          <strong>Spatial Warning:</strong> {advisory.spatial_warning}
        </div>
      )}

      {/* Traffic Hike Risk */}
      <HikeContext hike={advisory.predicted_hike_context || null} historical_peak={advisory.historical_peak_window || null} />

      {/* Signal Timing Suggestion */}
      {advisory.signal_timing_suggestion && (
        <div className="glass-panel" style={{ padding: '0.75rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: 'var(--radius-sm)', color: '#93c5fd', fontSize: '0.9rem', display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <span>🚥</span>
          <span>{advisory.signal_timing_suggestion} (centrality-weighted heuristic, not measured signal-cycle data).</span>
        </div>
      )}

      {/* Routing & Barricades */}
      <RoutingSection routing={advisory.routing || null} />
      <BarricadeSection 
        recommended_barricade_node={advisory.recommended_barricade_node || null}
        barricade_candidates_considered={advisory.barricade_candidates_considered}
        diversion_routes={advisory.diversion_routes}
      />

      {/* Network & Conflicts */}
      <NetworkResilience network_resilience={advisory.network_resilience || null} />
      <ConflictsSection conflicts={advisory.conflicts || null} />

      {/* Case Based Reasoning */}
      <SimilarEvents events={advisory.similar_past_events} summary={advisory.similar_past_events_summary || null} />

      {/* Outcome Logging Form */}
      <div style={{ marginTop: '2rem' }}>
        <OutcomeForm advisory={advisory} sourceEventId={sourceEventId} />
      </div>
    </div>
  );
};

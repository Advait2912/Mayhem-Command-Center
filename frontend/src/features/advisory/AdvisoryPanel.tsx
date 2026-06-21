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
import { RiskMeter } from './RiskMeter';

interface AdvisoryPanelProps {
  advisory: Advisory;
  sourceEventId?: string | number;
}

/* Thin divider with gradient fade */
const Div = () => (
  <div style={{
    height: '1px',
    margin: '8px 0',
    background: 'linear-gradient(90deg, rgba(255, 255, 255,0.35), rgba(201, 204, 209,0.2), transparent)',
  }} />
);

/* Section eyebrow */
const SectionLabel = ({ label, color }: { label: string; color?: string }) => (
  <div className="eyebrow" style={{
    marginBottom: '6px',
    color: color ?? 'var(--accent-cyan)',
    letterSpacing: '0.07em',
  }}>
    {label}
  </div>
);

export const AdvisoryPanel: React.FC<AdvisoryPanelProps> = ({ advisory, sourceEventId }) => {
  return (
    <div className="advisory-panel animate-fade-in" style={{ display: 'flex', flexDirection: 'column' }}>

      {/* ── HEADLINE ── */}
      <RiskMeter probability={advisory.closure_probability} />

      <div style={{ marginTop: '8px', marginBottom: '6px' }}>
        <div style={{
          fontSize: '13px',
          fontWeight: 700,
          fontFamily: 'var(--font-display)',
          color: 'var(--text-primary)',
          letterSpacing: '-0.01em',
        }}>
          {advisory.event_cause.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
        </div>
        <div className="eyebrow" style={{ marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {advisory.zone}
          {advisory.priority && (
            <span className={`status-tag ${advisory.priority.label === 'HIGH' ? 'status-tag-high' : 'status-tag-low'}`}>
              {advisory.priority.label} priority
            </span>
          )}
        </div>
      </div>

      {/* Spatial Warning */}
      {advisory.spatial_warning && (
        <div style={{
          padding: '5px 8px',
          background: 'var(--status-warning-bg)',
          borderLeft: '2px solid var(--status-warning)',
          borderRadius: 'var(--radius-sm)',
          color: 'var(--status-warning)',
          fontSize: '11px',
          marginBottom: '6px',
        }}>
          {advisory.spatial_warning}
        </div>
      )}

      <Div />

      {/* ── PRIMARY METRICS ── */}
      <SectionLabel label="Incident Metrics" />
      <StatGrid advisory={advisory} />

      <Div />

      {/* ── RECOMMENDED RESPONSE ── */}
      <SectionLabel label="Recommended Response" />
      <div style={{ display: 'flex', gap: '6px', marginBottom: '6px' }}>
        {/* Officers */}
        <div style={{
          flex: 1,
          padding: '6px 8px',
          background: 'rgba(255, 255, 255,0.07)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid rgba(255, 255, 255,0.2)',
          transition: 'box-shadow 0.2s ease',
          cursor: 'default',
        }}
          onMouseEnter={e => (e.currentTarget.style.boxShadow = 'var(--glow-blue)')}
          onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
        >
          <div className="eyebrow" style={{ color: 'var(--accent-blue)', marginBottom: '2px' }}>Officers</div>
          <div className="metric metric-sm" style={{ fontSize: '15px' }}>{advisory.recommended_officers}</div>
          <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '1px' }}>formula-based</div>
        </div>
        {/* Tow trucks */}
        {advisory.recommended_tow_trucks != null && (
          <div style={{
            flex: 1,
            padding: '6px 8px',
            background: 'rgba(201, 204, 209,0.07)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(201, 204, 209,0.2)',
            transition: 'box-shadow 0.2s ease',
            cursor: 'default',
          }}
            onMouseEnter={e => (e.currentTarget.style.boxShadow = 'var(--glow-cyan)')}
            onMouseLeave={e => (e.currentTarget.style.boxShadow = 'none')}
          >
            <div className="eyebrow" style={{ color: 'var(--accent-cyan)', marginBottom: '2px' }}>Tow Trucks</div>
            <div className="metric metric-sm" style={{ fontSize: '15px' }}>{advisory.recommended_tow_trucks}</div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '1px' }}>formula-based</div>
          </div>
        )}
      </div>

      {/* Signal timing */}
      {advisory.signal_timing_suggestion && (
        <div style={{
          padding: '5px 8px',
          background: 'rgba(255, 255, 255,0.06)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(255, 255, 255,0.15)',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          marginBottom: '6px',
        }}>
          <span className="eyebrow" style={{ color: 'var(--accent-cyan)', marginRight: '6px' }}>Signal timing:</span>
          {advisory.signal_timing_suggestion}
        </div>
      )}

      <Div />

      {/* ── ROUTE INTELLIGENCE ── */}
      <SectionLabel label="Route Intelligence" />
      <RoutingSection routing={advisory.routing ?? null} />
      <BarricadeSection
        recommended_barricade_node={advisory.recommended_barricade_node ?? null}
        barricade_candidates_considered={advisory.barricade_candidates_considered}
        diversion_routes={advisory.diversion_routes}
      />

      <Div />

      {/* ── NETWORK HEALTH ── */}
      <SectionLabel label="Network Health" />
      <NetworkResilience network_resilience={advisory.network_resilience ?? null} />

      <Div />

      {/* ── SUPPORTING EVIDENCE ── */}
      <SectionLabel label="Supporting Evidence" color="var(--text-muted)" />
      <div style={{ opacity: 0.88 }}>
        <HikeContext hike={advisory.predicted_hike_context ?? null} historical_peak={advisory.historical_peak_window ?? null} />
        <ConflictsSection conflicts={advisory.conflicts ?? null} />
        <SimilarEvents events={advisory.similar_past_events} summary={advisory.similar_past_events_summary ?? null} />
      </div>

      <Div />

      {/* ── OUTCOME FORM ── */}
      <SectionLabel label="Log Actual Outcome" color="var(--text-muted)" />
      <OutcomeForm advisory={advisory} sourceEventId={sourceEventId} />
    </div>
  );
};

import React from 'react';
import { Advisory } from '../../services/types';
import { StatBox } from '../../components/StatBox';

interface StatGridProps {
  advisory: Advisory;
}

export const StatGrid: React.FC<StatGridProps> = ({ advisory }) => {
  const formatDuration = () => {
    const dur = advisory.duration;
    if (!dur) return 'N/A';
    
    if (dur.type === 'quantile') {
      return `${dur.p50_hrs.toFixed(1)} hrs`;
    }
    if (dur.type === 'band') {
      return dur.band;
    }
    return 'None';
  };

  const formatDurationSubtext = () => {
    const dur = advisory.duration;
    if (!dur) return '';
    if (dur.type === 'quantile') {
      return `80% CI: ${dur.p10_hrs.toFixed(1)}-${dur.p90_hrs.toFixed(1)}h`;
    }
    if (dur.type === 'band') {
      return 'explicit low-confidence note (concordance ≈0.566)';
    }
    return '';
  };

  const getClosureColor = (prob: number) => {
    if (prob >= 0.7) return 'red';
    if (prob >= 0.4) return 'amber';
    return 'green';
  };

  const getRiskColor = (risk: number) => {
    if (risk >= 7) return 'red';
    if (risk >= 4) return 'amber';
    return 'green';
  };

  return (
    <div className="stat-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
      <StatBox 
        label="Closure Probability" 
        value={`${(advisory.closure_probability * 100).toFixed(1)}%`}
        color={getClosureColor(advisory.closure_probability)}
        subtext="calibrated, not raw model score"
        highlight
      />
      <StatBox 
        label="Congestion Score" 
        value={`${advisory.cascade_risk_score}/10`}
        color={getRiskColor(advisory.cascade_risk_score)}
        subtext="measures clustering with nearby events, not standalone severity — 0 means no concurrent nearby events were found, even for high-closure-probability"
        highlight
      />
      <StatBox 
        label="Duration (P50)" 
        value={formatDuration()}
        color={advisory.duration?.type === 'none' ? 'blue' : 'purple'}
        subtext={formatDurationSubtext()}
      />
      <StatBox 
        label="Recommended Officers" 
        value={advisory.recommended_officers}
        color="blue"
        subtext="formula-based heuristic"
      />
      <StatBox 
        label="Tow Trucks" 
        value={advisory.recommended_tow_trucks ?? '-'}
        color="blue"
        subtext="formula-based heuristic"
      />
    </div>
  );
};

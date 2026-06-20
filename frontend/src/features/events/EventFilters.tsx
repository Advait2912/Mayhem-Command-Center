import React from 'react';
import { useMeta } from '../../hooks/useMeta';

interface EventFiltersProps {
  filters: {
    cause?: string;
    zone?: string;
  };
  onChange: (key: string, value: string) => void;
}

export const EventFilters: React.FC<EventFiltersProps> = ({ filters, onChange }) => {
  const { data: meta, loading } = useMeta();

  return (
    <div className="glass-panel" style={{ padding: '1rem', display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
      <div style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Filters</div>
      
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <label style={{ fontSize: '0.85rem' }}>Cause</label>
        <select 
          value={filters.cause || ''} 
          onChange={(e) => onChange('cause', e.target.value)}
          style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
          disabled={loading}
        >
          <option value="">All Causes</option>
          {meta?.causes.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <label style={{ fontSize: '0.85rem' }}>Zone</label>
        <select 
          value={filters.zone || ''} 
          onChange={(e) => onChange('zone', e.target.value)}
          style={{ padding: '0.4rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
          disabled={loading}
        >
          <option value="">All Zones</option>
          {meta?.zones.map(z => <option key={z} value={z}>{z}</option>)}
        </select>
      </div>
    </div>
  );
};

import React from 'react';
import { EventListItem } from '../../services/types';
import { getProbabilityBadge } from '../../components/Badge';

interface EventListProps {
  events: EventListItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

export const EventList: React.FC<EventListProps> = ({ events, selectedId, onSelect }) => {
  if (events.length === 0) {
    return <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>No events found.</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
      {events.map((evt) => {
        const isSelected = evt.id === selectedId;
        return (
          <div 
            key={evt.id} 
            onClick={() => onSelect(evt.id)}
            style={{ 
              padding: '1rem', 
              background: isSelected ? 'rgba(59, 130, 246, 0.15)' : 'var(--bg-panel)',
              border: `1px solid ${isSelected ? 'var(--accent-blue)' : 'var(--glass-border)'}`,
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}
          >
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                {evt.event_cause} in {evt.zone_filled}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                ID: {evt.id} | {evt.start_ist ? new Date(evt.start_ist).toLocaleString() : 'Unknown Time'}
              </div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
              {getProbabilityBadge(evt.closure_probability || 0)}
              {evt.requires_road_closure && (
                <span style={{ fontSize: '0.75rem', color: '#fca5a5', border: '1px solid #fca5a5', padding: '0.1rem 0.4rem', borderRadius: '4px' }}>
                  Closed
                </span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

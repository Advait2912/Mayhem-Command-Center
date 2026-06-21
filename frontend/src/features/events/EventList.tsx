import React from 'react';
import { EventListItem } from '../../services/types';

interface EventListProps {
  events: EventListItem[];
  selectedId: number | null;
  onSelect: (id: number) => void;
}

// Human-readable cause string
const formatCause = (cause: string) =>
  cause.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

// Relative time from ISO string
const relativeTime = (isoStr?: string | null): string => {
  if (!isoStr) return '—';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hrs = Math.floor(mins / 60);
  const days = Math.floor(hrs / 24);
  if (days > 0) return `${days}d ago`;
  if (hrs > 0) return `${hrs}h ago`;
  if (mins > 0) return `${mins}m ago`;
  return 'just now';
};

// Rail color for risk level
const railColor = (prob?: number | null) => {
  if (prob == null) return 'var(--text-muted)';
  if (prob >= 0.7) return 'var(--status-danger)';
  if (prob >= 0.4) return 'var(--status-warning)';
  return 'var(--status-success)';
};

// Status tag variant
const riskTagClass = (prob?: number | null) => {
  if (prob == null) return '';
  if (prob >= 0.7) return 'status-tag-high';
  if (prob >= 0.4) return 'status-tag-medium';
  return 'status-tag-low';
};

const riskLabel = (prob?: number | null) => {
  if (prob == null) return 'Unknown';
  if (prob >= 0.7) return 'High';
  if (prob >= 0.4) return 'Medium';
  return 'Low';
};

const severityClass = (prob?: number | null) => {
  if (prob == null) return '';
  if (prob >= 0.7) return 'risk-high';
  if (prob >= 0.4) return 'risk-medium';
  return 'risk-low';
};

export const EventList: React.FC<EventListProps> = ({ events, selectedId, onSelect }) => {
  if (events.length === 0) {
    return (
      <div className="eyebrow" style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
        No events found
      </div>
    );
  }

  return (
    <div>
      {events.map((evt) => {
        const isSelected = evt.id === selectedId;
        return (
            <div
              key={evt.id}
              className={`feed-row${isSelected ? ` selected panel-live ${severityClass(evt.closure_probability)}` : ''}`}
              onClick={() => onSelect(evt.id)}
            >

            {/* Left risk color rail */}
            <div
              className="feed-row-rail"
              style={{ background: railColor(evt.closure_probability) }}
            />

            {/* Title block */}
            <div style={{ flex: 1, minWidth: 0 }}>
              <div className="feed-row-title" style={{ marginBottom: '2px', fontSize: '13px', overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }}>
                {formatCause(evt.event_cause)} — {evt.zone_filled}
              </div>
              <div className="feed-row-meta">
                {evt.id} · {relativeTime(evt.start_ist)}
                {evt.requires_road_closure && (
                  <span style={{ marginLeft: '6px', color: 'var(--status-danger)' }}>· closed</span>
                )}
              </div>
            </div>

            {/* Risk status tag */}
            <span className={`status-tag ${riskTagClass(evt.closure_probability)}`} style={{ flexShrink: 0, fontSize: '10px' }}>
              {riskLabel(evt.closure_probability)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

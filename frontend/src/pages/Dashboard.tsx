import React, { useState } from 'react';
import { useEvents } from '../hooks/useEvents';
import { useAdvisory } from '../hooks/useAdvisory';
import { EventFilters } from '../features/events/EventFilters';
import { EventList } from '../features/events/EventList';
import { AdvisoryPanel } from '../features/advisory/AdvisoryPanel';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { Pagination } from '../components/Pagination';

export const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<{ cause?: string; zone?: string; limit: number; offset: number }>({
    limit: 10,
    offset: 0,
  });

  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  const { data: eventsData, loading: eventsLoading, error: eventsError } = useEvents(filters);
  const { data: advisoryData, loading: advLoading, error: advError } = useAdvisory(selectedEventId);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [key]: value || undefined,
      offset: 0 // Reset to page 1 on filter change
    }));
    setSelectedEventId(null); // Clear selection
  };

  const handlePageChange = (newOffset: number) => {
    setFilters(prev => ({ ...prev, offset: newOffset }));
    setSelectedEventId(null);
  };

  return (
    <div style={{ display: 'flex', gap: '2rem', height: '100%' }}>
      {/* Left Column: Events */}
      <div style={{ flex: '1', display: 'flex', flexDirection: 'column', height: '100%' }}>
        <h2 style={{ marginBottom: '0.25rem', color: 'var(--text-primary)' }}>Search historical events</h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
          Pick a real event from the Astram log (Nov 2023 - Apr 2024) and replay it through the full advisory pipeline.
        </p>
        <EventFilters filters={filters} onChange={handleFilterChange} />
        
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '0.5rem' }}>
          {eventsLoading ? (
            <LoadingSpinner message="Loading events..." />
          ) : eventsError ? (
            <ErrorBox error={eventsError} />
          ) : eventsData ? (
            <>
              <EventList 
                events={eventsData.events} 
                selectedId={selectedEventId} 
                onSelect={setSelectedEventId} 
              />
              <Pagination 
                total={eventsData.total} 
                limit={filters.limit} 
                offset={filters.offset} 
                onPageChange={handlePageChange} 
              />
            </>
          ) : null}
        </div>
      </div>

      {/* Right Column: Advisory */}
      <div style={{ flex: '1.5', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)', padding: '2rem', overflowY: 'auto' }}>
        {!selectedEventId ? (
          <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            Select an event to view its advisory
          </div>
        ) : advLoading ? (
          <LoadingSpinner message="Generating advisory..." fullPage />
        ) : advError ? (
          <ErrorBox error={advError} />
        ) : advisoryData ? (
          <AdvisoryPanel advisory={advisoryData} sourceEventId={selectedEventId} />
        ) : null}
      </div>
    </div>
  );
};

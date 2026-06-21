import React, { useEffect, useState } from 'react';
import { useEvents } from '../hooks/useEvents';
import { useAdvisory } from '../hooks/useAdvisory';
import { EventFilters } from '../features/events/EventFilters';
import { EventList } from '../features/events/EventList';
import { AdvisoryPanel } from '../features/advisory/AdvisoryPanel';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorBox } from '../components/ErrorBox';
import { Pagination } from '../components/Pagination';
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from 'react-leaflet';
import { Advisory } from '../services/types';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Pulse CSS injected once
const PULSE_CSS = `
.db-pulse-wrapper { background: transparent !important; border: none !important; }
.db-pulse {
  position: relative; width: 24px; height: 24px;
}
.db-pulse-core {
  position: absolute; inset: 0; margin: auto;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--db-color, #E5484D);
  box-shadow: 0 0 0 2px rgba(255,255,255,0.2), 0 0 12px var(--db-color, #E5484D);
  z-index: 3;
}
.db-pulse-ring {
  position: absolute; inset: 0; margin: auto;
  width: 24px; height: 24px; border-radius: 50%;
  border: 2px solid var(--db-color, #E5484D);
  animation: db-pulse-anim 2.4s ease-out infinite; opacity: 0;
}
.db-pulse-ring.d2 { animation-delay: 1.2s; }
@keyframes db-pulse-anim {
  0%   { transform: scale(0.5); opacity: 0.8; }
  100% { transform: scale(2.6); opacity: 0; }
}
`;
let dbPulseCSS = false;
const injectDBCSS = () => {
  if (dbPulseCSS) return;
  const s = document.createElement('style');
  s.textContent = PULSE_CSS;
  document.head.appendChild(s);
  dbPulseCSS = true;
};

const createDBPulseIcon = (color: string) => {
  injectDBCSS();
  return L.divIcon({
    className: 'db-pulse-wrapper',
    html: `<div class="db-pulse" style="--db-color:${color}">
      <span class="db-pulse-ring"></span>
      <span class="db-pulse-ring d2"></span>
      <span class="db-pulse-core"></span>
    </div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
};


const BENGALURU_CENTER: [number, number] = [12.9716, 77.5946];

const MapController: React.FC<{ advisory: Advisory | null }> = ({ advisory }) => {
  const map = useMap();
  useEffect(() => {
    if (advisory?.latitude && advisory?.longitude) {
      map.flyTo([advisory.latitude, advisory.longitude], 14, { duration: 0.7 });
    } else {
      map.flyTo(BENGALURU_CENTER, 11, { duration: 0.7 });
    }
  }, [advisory, map]);
  return null;
};

export const Dashboard: React.FC = () => {
  const [filters, setFilters] = useState<{ cause?: string; zone?: string; limit: number; offset: number }>({
    limit: 10,
    offset: 0,
  });

  const [selectedEventId, setSelectedEventId] = useState<number | null>(null);

  const { data: eventsData, loading: eventsLoading, error: eventsError } = useEvents(filters);
  const { data: advisoryData, loading: advLoading, error: advError } = useAdvisory(selectedEventId);

  const handleFilterChange = (key: string, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value || undefined, offset: 0 }));
    setSelectedEventId(null);
  };

  const handlePageChange = (newOffset: number) => {
    setFilters(prev => ({ ...prev, offset: newOffset }));
    setSelectedEventId(null);
  };

  const riskColorRaw = advisoryData
    ? (advisoryData.closure_probability >= 0.7 ? '#E5484D'
      : advisoryData.closure_probability >= 0.4 ? '#E0A526'
      : '#2BAE76')
    : '#5468FF';

  const riskColorVar = advisoryData
    ? (advisoryData.closure_probability >= 0.7 ? 'var(--status-danger)'
      : advisoryData.closure_probability >= 0.4 ? 'var(--status-warning)'
      : 'var(--status-success)')
    : 'var(--accent-cyan)';

  const trackingLabel = advisoryData
    ? (advisoryData.closure_probability >= 0.7 ? 'CRITICAL'
      : advisoryData.closure_probability >= 0.4 ? 'ELEVATED'
      : 'MONITORING')
    : 'OVERVIEW';

  const trackingClass = advisoryData
    ? (advisoryData.closure_probability >= 0.7 ? 'status-tag-high'
      : advisoryData.closure_probability >= 0.4 ? 'status-tag-medium'
      : 'status-tag-low')
    : 'status-tag-low';

  const baseRadiusM = advisoryData?.footprint_radius_km
    ? Math.min(advisoryData.footprint_radius_km * 1000, 800)
    : 0;

  return (
    <div style={{ display: 'flex', gap: 'var(--space-4)', height: '100%', overflow: 'hidden' }}>
      {/* Feed Pane */}
      <div style={{ width: '320px', flexShrink: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div style={{ marginBottom: 'var(--space-3)' }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: '16px',
            letterSpacing: '-0.02em',
            background: 'linear-gradient(120deg, #fff 20%, var(--accent-cyan) 55%, var(--accent-blue) 80%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
            backgroundSize: '200% auto',
            animation: 'shine 6s linear infinite',
            marginBottom: '2px',
          }}>
            Historical Events
          </div>
          <div className="eyebrow" style={{ marginBottom: 'var(--space-2)', color: 'var(--accent-cyan)' }}>
            Nov 2023 – Apr 2024 · Astram log
          </div>
          <EventFilters filters={filters} onChange={handleFilterChange} />
        </div>

        <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }}>
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

      {/* Map Pane */}
      <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
        <div className="eyebrow" style={{ marginBottom: 'var(--space-2)', color: advisoryData ? riskColorVar : undefined }}>
          {advisoryData
            ? `${advisoryData.event_cause.replace(/_/g, ' ')} — ${advisoryData.zone}`
            : 'Bengaluru Overview'}
        </div>
        <div style={{
          flex: 1,
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          border: '1px solid rgba(84,104,255,0.2)',
          position: 'relative',
          boxShadow: advisoryData ? `0 0 20px ${riskColorRaw}22` : 'none',
          transition: 'box-shadow 0.4s ease',
        }}>
          <MapContainer
            center={BENGALURU_CENTER}
            zoom={11}
            style={{ height: '100%', width: '100%' }}
            zoomControl={true}
            attributionControl={false}
          >
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <MapController advisory={advisoryData ?? null} />
            {advisoryData && (
              <>
                {/* Pulsing incident marker */}
                <Marker
                  position={[advisoryData.latitude, advisoryData.longitude]}
                  icon={createDBPulseIcon(riskColorRaw)}
                >
                  <Popup>
                    <strong>{advisoryData.event_cause.replace(/_/g, ' ')}</strong><br />
                    {advisoryData.zone} — {(advisoryData.closure_probability * 100).toFixed(0)}% closure prob
                  </Popup>
                </Marker>

                {/* Two tight threat rings */}
                {baseRadiusM > 0 && [0, 1].map(i => (
                  <Circle
                    key={i}
                    center={[advisoryData.latitude, advisoryData.longitude]}
                    radius={baseRadiusM * (1 + i * 0.55)}
                    pathOptions={{
                      color: riskColorRaw,
                      fillColor: riskColorRaw,
                      fillOpacity: i === 0 ? 0.06 : 0,
                      weight: i === 0 ? 1.5 : 1,
                      dashArray: '5, 5',
                      opacity: i === 0 ? 0.7 : 0.35,
                    }}
                  />
                ))}
              </>
            )}
          </MapContainer>

          {/* Vignette */}
          <div className="map-vignette" />

          {/* HUD overlays */}
          <div className="map-hud-overlay">
            <div className="map-hud-corner tl">
              <span className="eyebrow">Zone</span>
              <span className="metric metric-sm">{advisoryData?.zone ?? 'All Zones'}</span>
            </div>
            <div className="map-hud-corner tr">
              <span className={`status-tag ${trackingClass}`}>{trackingLabel}</span>
            </div>
            {advisoryData && (
              <>
                <div className="map-hud-corner bl">
                  <span className="eyebrow">Coord</span>
                  <span className="metric metric-sm" style={{ color: riskColorVar }}>
                    {advisoryData.latitude.toFixed(4)}, {advisoryData.longitude.toFixed(4)}
                  </span>
                </div>
                <div className="map-hud-corner br">
                  <span className="eyebrow">Footprint</span>
                  <span className="metric metric-sm">{advisoryData.footprint_radius_km?.toFixed(1) ?? '—'} km</span>
                </div>
              </>
            )}
          </div>
        </div>

        {!selectedEventId && (
          <div className="eyebrow" style={{ marginTop: 'var(--space-2)', textAlign: 'center' }}>
            Select an event to zoom into incident location
          </div>
        )}
      </div>

      {/* Report Pane */}
      {selectedEventId && (
        <div style={{
          width: '400px',
          flexShrink: 0,
          height: '100%',
          overflowY: 'auto',
          background: 'rgba(15,17,22,0.95)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid rgba(84,104,255,0.15)',
          padding: 'var(--space-4)',
          backdropFilter: 'blur(8px)',
        }}>
          {advLoading ? (
            <LoadingSpinner message="Generating advisory..." fullPage />
          ) : advError ? (
            <ErrorBox error={advError} />
          ) : advisoryData ? (
            <AdvisoryPanel advisory={advisoryData} sourceEventId={selectedEventId} />
          ) : null}
        </div>
      )}
    </div>
  );
};

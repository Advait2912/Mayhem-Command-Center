import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { Advisory } from '../../services/types';

// Fix for default Leaflet marker icon issues in React
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

// CSS for the pulsing incident marker — injected once
const PULSE_CSS = `
.pulse-marker-wrapper { background: transparent !important; border: none !important; }
.pulse-marker {
  position: relative;
  width: 24px; height: 24px;
}
.pulse-core {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 12px; height: 12px;
  border-radius: 50%;
  background: var(--marker-color, #E5484D);
  box-shadow: 0 0 0 2px rgba(255,255,255,0.25), 0 0 10px var(--marker-color, #E5484D);
  z-index: 3;
}
.pulse-ring {
  position: absolute;
  inset: 0;
  margin: auto;
  width: 24px; height: 24px;
  border-radius: 50%;
  border: 2px solid var(--marker-color, #E5484D);
  animation: pulse-expand 2.4s ease-out infinite;
  opacity: 0;
}
.pulse-ring.delay { animation-delay: 1.2s; }
@keyframes pulse-expand {
  0%   { transform: scale(0.6); opacity: 0.9; }
  100% { transform: scale(2.8); opacity: 0; }
}
`;

let pulseCSSInjected = false;
const injectPulseCSS = () => {
  if (pulseCSSInjected) return;
  const style = document.createElement('style');
  style.textContent = PULSE_CSS;
  document.head.appendChild(style);
  pulseCSSInjected = true;
};

const createPulseIcon = (color: string) => {
  injectPulseCSS();
  return L.divIcon({
    className: 'pulse-marker-wrapper',
    html: `
      <div class="pulse-marker" style="--marker-color: ${color}">
        <span class="pulse-ring"></span>
        <span class="pulse-ring delay"></span>
        <span class="pulse-core"></span>
      </div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -14],
  });
};

// Keeps the map centered on position whenever advisory changes
const MapFocus: React.FC<{ position: [number, number] }> = ({ position }) => {
  const map = useMap();
  useEffect(() => {
    map.setView(position, 15, { animate: true, duration: 0.6 });
  }, [position[0], position[1]]); // eslint-disable-line react-hooks/exhaustive-deps
  return null;
};

interface EventMapProps {
  advisory: Advisory;
}

export const EventMap: React.FC<EventMapProps> = ({ advisory }) => {
  if (!advisory.latitude || !advisory.longitude) return null;

  const position: [number, number] = [advisory.latitude, advisory.longitude];

  // Radius in meters — capped to keep rings local
  const baseRadiusM = advisory.footprint_radius_km
    ? Math.min(advisory.footprint_radius_km * 1000, 800)
    : 350;

  const riskColorRaw =
    advisory.closure_probability >= 0.7 ? '#E5484D' :
    advisory.closure_probability >= 0.4 ? '#E0A526' :
    '#2BAE76';

  const riskColorVar =
    advisory.closure_probability >= 0.7 ? 'var(--status-danger)' :
    advisory.closure_probability >= 0.4 ? 'var(--status-warning)' :
    'var(--status-success)';

  const trackingLabel =
    advisory.closure_probability >= 0.7 ? 'CRITICAL' :
    advisory.closure_probability >= 0.4 ? 'ELEVATED' :
    'MONITORING';

  const trackingClass =
    advisory.closure_probability >= 0.7 ? 'status-tag-high' :
    advisory.closure_probability >= 0.4 ? 'status-tag-medium' :
    'status-tag-low';

  return (
    <div
      className="glass-panel"
      style={{
        height: '240px',
        width: '100%',
        marginBottom: '1rem',
        overflow: 'hidden',
        borderRadius: 'var(--radius-lg)',
        position: 'relative',
      }}
    >
      <MapContainer
        center={position}
        zoom={15}
        style={{ height: '100%', width: '100%' }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <MapFocus position={position} />

        {/* Pulsing incident marker — most prominent element */}
        <Marker position={position} icon={createPulseIcon(riskColorRaw)}>
          <Popup>
            <strong>{advisory.event_cause.replace(/_/g, ' ')}</strong><br />
            <span style={{ color: '#888' }}>{advisory.zone}</span>
          </Popup>
        </Marker>

        {/* Threat rings — tight, local impact only */}
        {[0, 1].map(i => (
          <Circle
            key={i}
            center={position}
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
      </MapContainer>

      {/* Dark edge vignette */}
      <div className="map-vignette" />

      {/* HUD corner overlays */}
      <div className="map-hud-overlay">
        {/* TL: Zone */}
        <div className="map-hud-corner tl">
          <span className="eyebrow">Zone</span>
          <span className="metric metric-sm">{advisory.zone}</span>
        </div>
        {/* TR: Tracking status */}
        <div className="map-hud-corner tr">
          <span className={`status-tag ${trackingClass}`}>{trackingLabel}</span>
        </div>
        {/* BL: Coordinates */}
        <div className="map-hud-corner bl">
          <span className="eyebrow">Coord</span>
          <span className="metric metric-sm" style={{ color: riskColorVar }}>
            {advisory.latitude.toFixed(4)}, {advisory.longitude.toFixed(4)}
          </span>
        </div>
        {/* BR: Footprint radius */}
        <div className="map-hud-corner br">
          <span className="eyebrow">Footprint</span>
          <span className="metric metric-sm">{advisory.footprint_radius_km?.toFixed(1) || '0.5'} km</span>
        </div>
      </div>
    </div>
  );
};

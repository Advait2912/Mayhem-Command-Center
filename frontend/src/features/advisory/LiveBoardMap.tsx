import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Circle, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { Advisory } from '../../services/types';

// Pulse CSS injected once
const PULSE_CSS = `
.lbm-pulse-wrapper { background: transparent !important; border: none !important; }
.lbm-pulse { position: relative; width: 20px; height: 20px; }
.lbm-core {
  position: absolute; inset: 0; margin: auto;
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--lbm-color, #FFFFFF);
  box-shadow: 0 0 0 2px rgba(255,255,255,0.15), 0 0 10px var(--lbm-color, #FFFFFF);
  z-index: 3;
}
.lbm-ring {
  position: absolute; inset: 0; margin: auto;
  width: 20px; height: 20px; border-radius: 50%;
  border: 2px solid var(--lbm-color, #FFFFFF);
  animation: lbm-anim 2.4s ease-out infinite; opacity: 0;
}
.lbm-ring.d2 { animation-delay: 1.2s; }
@keyframes lbm-anim {
  0%   { transform: scale(0.5); opacity: 0.85; }
  100% { transform: scale(2.5); opacity: 0; }
}
.lbm-core {
  transition: transform .15s ease, background .15s ease, box-shadow .15s ease;
}
.lbm-pulse:hover .lbm-core {
  background: var(--accent-live);
  box-shadow: 0 0 0 2px rgba(63, 214, 198, 0.3), 0 0 10px var(--accent-live);
  transform: scale(1.25);
}
.lbm-pulse:active .lbm-core {
  background: var(--accent-live);
  transform: scale(0.9);
}
`;
let lbmCSS = false;
const injectLBMCSS = () => {
  if (lbmCSS) return;
  const s = document.createElement('style');
  s.textContent = PULSE_CSS;
  document.head.appendChild(s);
  lbmCSS = true;
};

const createLBMIcon = (color: string) => {
  injectLBMCSS();
  return L.divIcon({
    className: 'lbm-pulse-wrapper',
    html: `<div class="lbm-pulse" style="--lbm-color:${color}">
      <span class="lbm-ring"></span>
      <span class="lbm-ring d2"></span>
      <span class="lbm-core"></span>
    </div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    popupAnchor: [0, -12],
  });
};


interface LiveEvent {
  id: string;
  advisory: Advisory;
  addedAt: Date;
}

interface LiveBoardMapProps {
  events: LiveEvent[];
  onMarkerClick: (id: string) => void;
}

const BoundsUpdater: React.FC<{ events: LiveEvent[] }> = ({ events }) => {
  const map = useMap();
  useEffect(() => {
    if (events.length === 0) return;
    const bounds: [number, number][] = events
      .filter(ev => ev.advisory.latitude != null && ev.advisory.longitude != null)
      .map(ev => [ev.advisory.latitude, ev.advisory.longitude]);
    if (bounds.length > 0) {
      map.fitBounds(bounds, { maxZoom: 14, padding: [50, 50] });
    }
  }, [events, map]);
  return null;
};

const getColors = () => {
  const root = getComputedStyle(document.documentElement);
  return {
    danger: root.getPropertyValue('--status-danger').trim(),
    warning: root.getPropertyValue('--status-warning').trim(),
    success: root.getPropertyValue('--status-success').trim(),
  };
};

export const LiveBoardMap: React.FC<LiveBoardMapProps> = ({ events, onMarkerClick }) => {
  const COLORS = React.useMemo(() => getColors(), []);
  
  const riskColor = (prob: number) =>
    prob >= 0.7 ? COLORS.danger : prob >= 0.4 ? COLORS.warning : COLORS.success;

const riskTagClass = (prob: number) =>
  prob >= 0.7 ? 'status-tag-high' : prob >= 0.4 ? 'status-tag-medium' : 'status-tag-low';

const riskLabel = (prob: number) =>
  prob >= 0.7 ? 'CRITICAL' : prob >= 0.4 ? 'ELEVATED' : 'MONITORING';


  const highestRiskEvent = events.length > 0
    ? [...events].sort((a, b) => b.advisory.closure_probability - a.advisory.closure_probability)[0]
    : null;

  const totalActive = events.length;
  const criticalCount = events.filter(e => e.advisory.closure_probability >= 0.7).length;

  return (
    <div
      className="map-card"
      style={{
        height: '340px',
        width: '100%',
        borderRadius: 'var(--radius-lg)',
        overflow: 'hidden',
        marginBottom: '0.75rem',
        border: criticalCount > 0 ? '1px solid var(--accent-live)' : '1px solid var(--border)',
        position: 'relative',
        boxShadow: highestRiskEvent ? `0 0 0 1px ${riskColor(highestRiskEvent.advisory.closure_probability)}33, 0 0 14px ${riskColor(highestRiskEvent.advisory.closure_probability)}22` : 'none',
      }}
    >
      <MapContainer
        center={[12.9716, 77.5946]}
        zoom={12}
        style={{ height: '100%', width: '100%', zIndex: 1 }}
        zoomControl={false}
        attributionControl={false}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          maxZoom={19}
        />
        <BoundsUpdater events={events} />

        {events.map((ev) => {
          const a = ev.advisory;
          if (a.latitude == null || a.longitude == null) return null;
          const color = riskColor(a.closure_probability);
          const baseRadius = Math.min((a.footprint_radius_km ?? 0.5) * 1000, 700);

          return (
            <React.Fragment key={ev.id}>
              <Marker
                position={[a.latitude, a.longitude]}
                icon={createLBMIcon(color)}
                eventHandlers={{ click: () => onMarkerClick(ev.id) }}
              >
                <Popup>
                  <strong>{a.event_cause.replace(/_/g, ' ')}</strong><br />
                  {a.zone} · {(a.closure_probability * 100).toFixed(0)}% closure<br />
                  Officers: {a.recommended_officers}
                </Popup>
              </Marker>

              {baseRadius > 0 && (
                <Circle
                  center={[a.latitude, a.longitude]}
                  radius={baseRadius}
                  pathOptions={{
                    color,
                    fillColor: color,
                    fillOpacity: 0.06,
                    weight: 1,
                    dashArray: '4, 4',
                    opacity: 0.5,
                  }}
                />
              )}
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Vignette */}
      <div className="map-vignette" />

      {/* HUD overlay */}
      <div className="map-hud-overlay">
        {/* TL: Active count */}
        <div className="map-hud-corner tl">
          <span className="eyebrow">Active</span>
          <span className="metric metric-sm">{totalActive} event{totalActive !== 1 ? 's' : ''}</span>
        </div>

        {/* TR: Critical count or CLEAR */}
        <div className="map-hud-corner tr">
          {criticalCount > 0
            ? <span className="status-tag status-tag-high">{criticalCount} CRITICAL</span>
            : <span className="status-tag status-tag-low">ALL CLEAR</span>
          }
        </div>

        {/* BL: Highest risk zone */}
        {highestRiskEvent && (
          <div className="map-hud-corner bl">
            <span className="eyebrow">Top Risk Zone</span>
            <span className="metric metric-sm" style={{ color: riskColor(highestRiskEvent.advisory.closure_probability) }}>
              {highestRiskEvent.advisory.zone}
            </span>
          </div>
        )}

        {/* BR: Tracking */}
        {highestRiskEvent && (
          <div className="map-hud-corner br">
            <span className="eyebrow">Max Threat</span>
            <span className={`status-tag ${riskTagClass(highestRiskEvent.advisory.closure_probability)}`}>
              {riskLabel(highestRiskEvent.advisory.closure_probability)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

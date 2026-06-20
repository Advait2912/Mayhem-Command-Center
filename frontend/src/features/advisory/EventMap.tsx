import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
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

interface EventMapProps {
  advisory: Advisory;
}

export const EventMap: React.FC<EventMapProps> = ({ advisory }) => {
  if (!advisory.latitude || !advisory.longitude) return null;

  const position: [number, number] = [advisory.latitude, advisory.longitude];
  
  // Radius is in km, leaflet Circle radius is in meters
  const radiusMeters = advisory.footprint_radius_km ? advisory.footprint_radius_km * 1000 : 500;

  return (
    <div className="glass-panel" style={{ height: '300px', width: '100%', marginBottom: '1.5rem', overflow: 'hidden', borderRadius: 'var(--radius-lg)' }}>
      <MapContainer 
        center={position} 
        zoom={14} 
        style={{ height: '100%', width: '100%' }}
      >
        {/* Dark mode friendly map tiles (CartoDB Dark Matter) */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
        />
        
        <Marker position={position}>
          <Popup>
            <strong>{advisory.event_cause}</strong><br />
            {advisory.zone}
          </Popup>
        </Marker>

        <Circle 
          center={position} 
          radius={radiusMeters} 
          pathOptions={{ 
            color: 'var(--status-danger)', 
            fillColor: 'var(--status-danger)', 
            fillOpacity: 0.2 
          }} 
        />
      </MapContainer>
    </div>
  );
};

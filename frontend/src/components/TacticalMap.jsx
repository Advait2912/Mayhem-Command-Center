import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Circle, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const BENGALURU_CENTER = [12.9716, 77.5946];

function ChangeView({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, 13);
    }
  }, [center, map]);
  return null;
}

export const TacticalMap = ({ impactData, center }) => {
  return (
    <div className="map-container">
      <MapContainer center={center || BENGALURU_CENTER} zoom={12} style={{ height: '100%', width: '100%' }}>
        <ChangeView center={center} />
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; CARTO'
        />
        {impactData && (
          <>
            <Marker position={center || BENGALURU_CENTER} />
            <Circle 
              center={center || BENGALURU_CENTER} 
              radius={impactData.radius_km * 1000} 
              pathOptions={{ color: 'var(--danger)', fillColor: 'var(--danger)', fillOpacity: 0.3 }} 
            />
          </>
        )}
      </MapContainer>
    </div>
  );
};

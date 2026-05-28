import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import { useEffect } from "react";

const riskColor = (risk: string) => risk === "High" ? "#dc2626" : risk === "Medium" ? "#d97706" : "#16a34a";

function FlyTo({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lon], 5);
  }, [lat, lon, map]);
  return null;
}

export default function FloodMap({ regions, selected, onSelect }: { regions: any[]; selected: { lat: number; lon: number }; onSelect: (region: any) => void }) {
  return (
    <MapContainer center={[selected.lat, selected.lon]} zoom={4} scrollWheelZoom className="h-full min-h-[420px]">
      <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FlyTo lat={selected.lat} lon={selected.lon} />
      {regions.map((region) => (
        <CircleMarker
          key={region.country}
          center={[region.lat, region.lon]}
          radius={18}
          pathOptions={{ color: riskColor(region.risk_level), fillColor: riskColor(region.risk_level), fillOpacity: 0.45 }}
          eventHandlers={{ click: () => onSelect(region) }}
        >
          <Popup>{region.country}: {region.risk_level} risk</Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}

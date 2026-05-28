import { GeoJSON, MapContainer, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { useEffect, useMemo, useState } from "react";
import type { LatLngExpression } from "leaflet";

import { api, type Prediction, type Region } from "../api/client";

type SelectedPlace = { country: string; lat: number; lon: number };
type CountryResult = Prediction & SelectedPlace;

const GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson";

const riskColor = (risk: string) => (risk === "High" ? "#dc2626" : risk === "Medium" ? "#d97706" : "#16a34a");
const baselineColor = (risk: number) => (risk > 0.6 ? "#dc2626" : risk >= 0.3 ? "#d97706" : "#16a34a");

function riskFromProbability(probability: number) {
  if (probability < 0.3) return "Low";
  if (probability <= 0.6) return "Medium";
  return "High";
}

function FlyTo({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lon], 4);
  }, [lat, lon, map]);
  return null;
}

function ClickPoint({ enabled, onPointSelect }: { enabled?: boolean; onPointSelect?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(event) {
      if (enabled && onPointSelect) onPointSelect(event.latlng.lat, event.latlng.lng);
    },
  });
  return null;
}

function centroid(geometry: any): { lat: number; lon: number } {
  const coords: number[][] = [];
  const visit = (node: any) => {
    if (!Array.isArray(node)) return;
    if (typeof node[0] === "number" && typeof node[1] === "number") coords.push(node as number[]);
    else node.forEach(visit);
  };
  visit(geometry.coordinates);
  if (!coords.length) return { lat: 0, lon: 0 };
  const lon = coords.reduce((sum, item) => sum + item[0], 0) / coords.length;
  const lat = coords.reduce((sum, item) => sum + item[1], 0) / coords.length;
  return { lat, lon };
}

function countryName(feature: any) {
  return feature?.properties?.ADMIN ?? feature?.properties?.name ?? feature?.properties?.NAME ?? "Unknown";
}

export default function FloodMap({
  regions,
  selected,
  onSelect,
  onPrediction,
  allowPointSelect = false,
}: {
  regions: Region[];
  selected: SelectedPlace;
  onSelect: (region: SelectedPlace) => void;
  onPrediction?: (result: CountryResult) => void;
  allowPointSelect?: boolean;
}) {
  const [geoJson, setGeoJson] = useState<any | null>(null);
  const [loadingCountry, setLoadingCountry] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, CountryResult>>({});
  const regionByName = useMemo(() => new Map(regions.map((region) => [region.country.toLowerCase(), region])), [regions]);

  useEffect(() => {
    fetch(GEOJSON_URL).then((response) => response.json()).then(setGeoJson).catch(() => setGeoJson(null));
  }, []);

  const center: LatLngExpression = [selected.lat, selected.lon];

  return (
    <MapContainer center={center} zoom={3} scrollWheelZoom className="h-full min-h-[420px]">
      <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <FlyTo lat={selected.lat} lon={selected.lon} />
      <ClickPoint enabled={allowPointSelect} onPointSelect={(lat, lon) => onSelect({ country: "Custom point", lat, lon })} />
      {geoJson && (
        <GeoJSON
          key={`${Object.keys(results).length}-${loadingCountry ?? "idle"}`}
          data={geoJson}
          style={(feature) => {
            const name = countryName(feature);
            const result = results[name];
            const region = regionByName.get(name.toLowerCase());
            const fillColor = result ? riskColor(result.risk_level) : region ? baselineColor(region.risk_baseline) : "#94a3b8";
            return {
              color: loadingCountry === name ? "#111827" : "#475569",
              weight: loadingCountry === name ? 2 : 0.7,
              fillColor,
              fillOpacity: result || region ? 0.48 : 0.12,
            };
          }}
          onEachFeature={(feature, layer) => {
            const name = countryName(feature);
            layer.on("click", async () => {
              const point = centroid(feature.geometry);
              const selectedCountry = { country: name, lat: point.lat, lon: point.lon };
              onSelect(selectedCountry);
              setLoadingCountry(name);
              layer.bindPopup(`${name}: loading prediction...`).openPopup();
              try {
                const prediction = await api.predict({ country: name, lat: point.lat, lon: point.lon, date: new Date().toISOString().slice(0, 10) });
                const result = { ...selectedCountry, ...prediction };
                setResults((previous) => ({ ...previous, [name]: result }));
                onPrediction?.(result);
                layer
                  .bindPopup(
                    `<strong>${name}</strong><br/>Flood probability: ${Math.round(prediction.flood_probability * 100)}%<br/>Risk: ${prediction.risk_level}<br/>Confidence: ${Math.round(prediction.confidence * 100)}%<br/>Data source: ${prediction.data_source}`
                  )
                  .openPopup();
              } finally {
                setLoadingCountry(null);
              }
            });
          }}
        />
      )}
      {!geoJson && (
        <Popup position={center}>
          World country layer is loading. Click the map or use the controls to run a prediction.
        </Popup>
      )}
    </MapContainer>
  );
}

export type { CountryResult, SelectedPlace };

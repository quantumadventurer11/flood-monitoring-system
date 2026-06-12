import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer, useMap, useMapEvents } from "react-leaflet";
import { useEffect, useMemo, useState } from "react";
import type { LatLngExpression } from "leaflet";

import { api, type Hotspot, type Prediction, type Region } from "../api/client";

type SelectedPlace = { country: string; lat: number; lon: number };
type CountryResult = Prediction & SelectedPlace;
type MapHotspot = Hotspot & { label: string; kind: "model" | "ground_truth" };

const GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson";

const riskColor = (risk: string) => (risk === "High" ? "#dc2626" : risk === "Medium" ? "#d97706" : "#16a34a");
const baselineColor = (risk: number) => (risk > 0.6 ? "#94a3b8" : risk >= 0.3 ? "#cbd5e1" : "#e2e8f0");

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

function DetailRows({ values }: { values?: Record<string, string | number | null> }) {
  const entries = Object.entries(values ?? {}).filter(([, value]) => value !== null && value !== undefined);
  if (!entries.length) return null;
  return (
    <dl className="mt-2 max-h-44 overflow-auto border-t border-slate-200 pt-2 text-xs">
      {entries.map(([key, value]) => (
        <div key={key} className="grid grid-cols-[112px_1fr] gap-2 rounded px-1 py-0.5">
          <dt className="font-semibold capitalize text-slate-600">{key.replace(/_/g, " ")}</dt>
          <dd className="text-slate-800">{String(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

export default function FloodMap({
  regions,
  selected,
  onSelect,
  onPrediction,
  allowPointSelect = false,
  externalResults = {},
  hotspots = [],
}: {
  regions: Region[];
  selected: SelectedPlace;
  onSelect: (region: SelectedPlace) => void;
  onPrediction?: (result: CountryResult) => void;
  allowPointSelect?: boolean;
  externalResults?: Record<string, CountryResult>;
  hotspots?: MapHotspot[];
}) {
  const [geoJson, setGeoJson] = useState<any | null>(null);
  const [loadingCountry, setLoadingCountry] = useState<string | null>(null);
  const [results, setResults] = useState<Record<string, CountryResult>>({});
  const displayedResults = useMemo(() => ({ ...results, ...externalResults }), [externalResults, results]);
  const regionByName = useMemo(() => new Map(regions.map((region) => [region.country.toLowerCase(), region])), [regions]);

  useEffect(() => {
    fetch(GEOJSON_URL).then((response) => response.json()).then(setGeoJson).catch(() => setGeoJson(null));
  }, []);

  const center: LatLngExpression = [selected.lat, selected.lon];

  return (
    <MapContainer center={center} zoom={3} scrollWheelZoom className="h-full min-h-[420px]">
      <TileLayer
        attribution="Tiles &copy; Esri, Maxar, Earthstar Geographics, and the GIS User Community"
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
      />
      <FlyTo lat={selected.lat} lon={selected.lon} />
      <ClickPoint enabled={allowPointSelect} onPointSelect={(lat, lon) => onSelect({ country: "Custom point", lat, lon })} />
      {geoJson && (
        <GeoJSON
          key={`${Object.keys(displayedResults).length}-${loadingCountry ?? "idle"}`}
          data={geoJson}
          style={(feature) => {
            const name = countryName(feature);
            const result = displayedResults[name];
            const region = regionByName.get(name.toLowerCase());
            const fillColor = result ? riskColor(result.risk_level) : region ? baselineColor(region.risk_baseline) : "#94a3b8";
            const isSelected = selected.country === name;
            return {
              color: loadingCountry === name || isSelected ? "#111827" : "#64748b",
              weight: loadingCountry === name || isSelected ? 2 : 0.7,
              fillColor,
              fillOpacity: result ? 0.54 : region ? 0.18 : 0.1,
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
                    `<strong>${name}</strong><br/>Flood probability: ${Math.round(prediction.flood_probability * 100)}%<br/>Risk: ${prediction.risk_level}<br/>Confidence: ${Math.round(prediction.confidence * 100)}%<br/>Data source: ${prediction.data_source}<br/>Validation: ${prediction.validation_status}`
                  )
                  .openPopup();
              } finally {
                setLoadingCountry(null);
              }
            });
          }}
        />
      )}
      {hotspots.map((hotspot, index) => (
        <CircleMarker
          key={`${hotspot.kind}-${hotspot.lat}-${hotspot.lon}-${index}`}
          center={[hotspot.lat, hotspot.lon]}
          radius={hotspot.kind === "ground_truth" ? 8 : 6}
          pathOptions={{
            color: hotspot.kind === "ground_truth" ? "#38bdf8" : riskColor(hotspot.risk_level),
            fillColor: hotspot.kind === "ground_truth" ? "#0ea5e9" : riskColor(hotspot.risk_level),
            fillOpacity: hotspot.kind === "ground_truth" ? 0.82 : 0.72,
            weight: 2,
            className: "hotspot-pulse",
          }}
        >
          <Popup>
            <div className="min-w-64 space-y-2">
              <div>
                <strong className="block text-sm text-slate-900">{hotspot.label}</strong>
                <span className="text-xs text-slate-500">{hotspot.source}</span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="rounded bg-slate-50 p-2">
                  <span className="block text-slate-500">Coordinates</span>
                  <strong className="text-slate-900">{hotspot.lat.toFixed(4)}, {hotspot.lon.toFixed(4)}</strong>
                </div>
                <div className="rounded bg-slate-50 p-2">
                  <span className="block text-slate-500">Score</span>
                  <strong className="text-slate-900">{Math.round(hotspot.probability * 100)}%</strong>
                </div>
              </div>
              <div className="rounded border border-slate-200 bg-white p-2 text-xs">
                <span className="block text-slate-500">Class</span>
                <strong className="text-slate-900">{hotspot.flood_class ?? hotspot.risk_level}</strong>
              </div>
              <DetailRows values={hotspot.details} />
              <DetailRows values={hotspot.data} />
            </div>
          </Popup>
        </CircleMarker>
      ))}
      {!geoJson && (
        <Popup position={center}>
          World country layer is loading. Click the map or use the controls to run a prediction.
        </Popup>
      )}
    </MapContainer>
  );
}

export type { CountryResult, SelectedPlace };

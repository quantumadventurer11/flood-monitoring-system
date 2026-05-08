import { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Rectangle, useMapEvents } from 'react-leaflet'
import { LatLng } from 'leaflet'
import { geoApi, eventsApi, ingestionApi } from '../api/client'
import type { GeographicArea, FloodEvent } from '../types'
import toast from 'react-hot-toast'

// Click handler component
function MapClickHandler({ onSelect }: { onSelect: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) { onSelect(e.latlng.lat, e.latlng.lng) }
  })
  return null
}

export function MapPage() {
  const [areas, setAreas] = useState<GeographicArea[]>([])
  const [selected, setSelected] = useState<GeographicArea | null>(null)
  const [events, setEvents] = useState<FloodEvent[]>([])
  const [startDate, setStartDate] = useState('2024-06-01')
  const [endDate, setEndDate] = useState('2024-06-30')
  const [satellite, setSatellite] = useState('S1')
  const [jobId, setJobId] = useState<number | null>(null)
  const [fetching, setFetching] = useState(false)

  useEffect(() => {
    geoApi.listAreas().then(r => setAreas(r.data)).catch(console.error)
  }, [])

  const handleMapClick = useCallback(async (lat: number, lng: number) => {
    try {
      const { data } = await geoApi.searchByBbox(lat - 1, lng - 1, lat + 1, lng + 1)
      if (data.length > 0) {
        const area = data[0] as GeographicArea
        setSelected(area)
        const evtRes = await eventsApi.areaRecent(area.area_id)
        setEvents(evtRes.data)
      } else {
        setSelected(null)
        toast('No monitored area found at that location', { icon: '📍' })
      }
    } catch {
      console.error('Area lookup failed')
    }
  }, [])

  const handleFetchData = async () => {
    if (!selected) return toast.error('Select a region on the map first')
    setFetching(true)
    try {
      const { data } = await ingestionApi.triggerSentinel(selected.area_id, startDate, endDate, satellite)
      setJobId(data.job_id)
      toast.success(`Satellite fetch job #${data.job_id} started!`)
    } catch {
      toast.error('Failed to trigger satellite data fetch')
    } finally {
      setFetching(false)
    }
  }

  return (
    <div className="flex h-full flex-col lg:flex-row">
      {/* Map */}
      <div className="flex-1 relative" style={{ minHeight: '60vh' }}>
        <MapContainer
          center={[20, 0]}
          zoom={2}
          style={{ width: '100%', height: '100%' }}
          className="absolute inset-0"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onSelect={handleMapClick} />

          {/* Draw area bounding boxes */}
          {areas.map(area =>
            area.min_lat && area.min_lon && area.max_lat && area.max_lon ? (
              <Rectangle
                key={area.area_id}
                bounds={[[area.min_lat, area.min_lon], [area.max_lat, area.max_lon]]}
                pathOptions={{
                  color: selected?.area_id === area.area_id ? '#3b82f6' : '#64748b',
                  weight: selected?.area_id === area.area_id ? 2 : 1,
                  fillOpacity: selected?.area_id === area.area_id ? 0.25 : 0.1,
                }}
                eventHandlers={{
                  click: () => {
                    setSelected(area)
                    eventsApi.areaRecent(area.area_id).then(r => setEvents(r.data))
                  }
                }}
              >
                <Popup>
                  <div className="text-sm">
                    <strong>{area.area_name}</strong><br />
                    Type: {area.area_type}
                  </div>
                </Popup>
              </Rectangle>
            ) : null
          )}
        </MapContainer>

        {/* Click hint */}
        <div className="absolute top-3 left-1/2 -translate-x-1/2 z-[1000] bg-slate-900/90 text-white text-xs px-3 py-1.5 rounded-full">
          Click on the map or a highlighted region to select it
        </div>
      </div>

      {/* Right panel */}
      <aside className="w-full lg:w-80 bg-slate-800 border-l border-slate-700 overflow-y-auto p-4 space-y-4 shrink-0">
        {selected ? (
          <>
            <div>
              <h2 className="text-white font-semibold text-sm">{selected.area_name}</h2>
              <p className="text-slate-400 text-xs capitalize">{selected.area_type}</p>
            </div>

            {/* Fetch satellite data */}
            <div className="bg-slate-700 rounded-lg p-3 space-y-2">
              <p className="text-xs font-medium text-slate-300">Fetch Satellite Data</p>
              <select value={satellite} onChange={e => setSatellite(e.target.value)}
                className="w-full bg-slate-600 text-white text-xs rounded px-2 py-1.5 border border-slate-500">
                <option value="S1">Sentinel-1 (SAR – radar)</option>
                <option value="S2">Sentinel-2 (Optical)</option>
              </select>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)}
                className="w-full bg-slate-600 text-white text-xs rounded px-2 py-1.5 border border-slate-500" />
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)}
                className="w-full bg-slate-600 text-white text-xs rounded px-2 py-1.5 border border-slate-500" />
              <button onClick={handleFetchData} disabled={fetching}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold py-1.5 rounded transition-colors">
                {fetching ? 'Submitting…' : '🛰️ Fetch Data'}
              </button>
              {jobId && <p className="text-xs text-green-400">Job #{jobId} running</p>}
            </div>

            {/* Recent flood events */}
            <div>
              <p className="text-xs font-medium text-slate-300 mb-2">Recent Flood Events</p>
              {events.length === 0
                ? <p className="text-xs text-slate-500">No events recorded for this area.</p>
                : events.map((e) => (
                  <div key={e.flood_event_id} className="bg-slate-700 rounded p-2 mb-1.5 text-xs">
                    <p className="text-white">Detected: {new Date(e.detected_at).toLocaleDateString()}</p>
                    <p className="text-slate-400">Confidence: {e.confidence ?? 'N/A'}</p>
                    {e.summary && <p className="text-slate-300 mt-0.5">{e.summary}</p>}
                  </div>
                ))
              }
            </div>
          </>
        ) : (
          <div className="space-y-3">
            <p className="text-white text-sm font-semibold">World Map</p>
            <p className="text-slate-400 text-xs">Click on a highlighted region or anywhere on the map to select a monitoring area.</p>
            <p className="text-xs font-medium text-slate-300 mt-4">All Monitored Areas ({areas.length})</p>
            {areas.map(area => (
              <button key={area.area_id}
                onClick={() => {
                  setSelected(area)
                  eventsApi.areaRecent(area.area_id).then(r => setEvents(r.data))
                }}
                className="w-full text-left bg-slate-700 hover:bg-slate-600 rounded-lg px-3 py-2 text-xs text-white transition-colors">
                {area.area_name}
                <span className="block text-slate-400 capitalize">{area.area_type}</span>
              </button>
            ))}
          </div>
        )}
      </aside>
    </div>
  )
}

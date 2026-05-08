import { useEffect, useState } from 'react'
import { eventsApi } from '../api/client'
import type { FloodEvent } from '../types'
import { format } from 'date-fns'

function Badge({ value, map }: { value: string; map: Record<string, string> }) {
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${map[value] ?? 'bg-slate-500'}`}>
      {value}
    </span>
  )
}

const confidenceColors: Record<string, string> = {
  HIGH: 'bg-red-600', MEDIUM: 'bg-yellow-500', LOW: 'bg-green-600'
}

export function EventsPage() {
  const [events, setEvents] = useState<FloodEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [filterConf, setFilterConf] = useState('')

  useEffect(() => {
    eventsApi.list({ confidence: filterConf || undefined, limit: 100 })
      .then(r => setEvents(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [filterConf])

  return (
    <div className="p-6 space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Flood Events</h1>
          <p className="text-slate-400 text-sm mt-1">AI-detected flood events from satellite data</p>
        </div>
        <select value={filterConf} onChange={e => setFilterConf(e.target.value)}
          className="bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2">
          <option value="">All Confidence</option>
          <option value="HIGH">High</option>
          <option value="MEDIUM">Medium</option>
          <option value="LOW">Low</option>
        </select>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">ID</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Area</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Detected</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Confidence</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Summary</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {loading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">Loading…</td></tr>
            ) : events.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">
                No flood events recorded yet. Trigger a satellite data fetch to begin.
              </td></tr>
            ) : events.map(evt => (
              <tr key={evt.flood_event_id} className="hover:bg-slate-700/50 transition-colors">
                <td className="px-5 py-3 text-slate-300">#{evt.flood_event_id}</td>
                <td className="px-5 py-3 text-white font-medium">Area #{evt.area_id}</td>
                <td className="px-5 py-3 text-slate-300">{format(new Date(evt.detected_at), 'dd MMM yyyy')}</td>
                <td className="px-5 py-3">
                  {evt.confidence
                    ? <Badge value={evt.confidence} map={confidenceColors} />
                    : <span className="text-slate-500 text-xs">N/A</span>}
                </td>
                <td className="px-5 py-3 text-slate-400 max-w-xs truncate">{evt.summary ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

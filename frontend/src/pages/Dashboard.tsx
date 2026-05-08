import { useEffect, useState } from 'react'
import { Waves, Bell, AlertTriangle, Map } from 'lucide-react'
import { Link } from 'react-router-dom'
import { eventsApi, alertsApi } from '../api/client'
import type { FloodEvent, Alert } from '../types'
import { format } from 'date-fns'

function StatCard({ icon: Icon, label, value, color }: {
  icon: React.ElementType
  label: string
  value: string | number
  color: string
}) {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-5 h-5 text-white" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <p className="text-sm text-slate-400">{label}</p>
      </div>
    </div>
  )
}

function SeverityBadge({ severity }: { severity: string }) {
  const cls: Record<string, string> = {
    CRITICAL: 'bg-red-600',
    HIGH: 'bg-orange-500',
    MEDIUM: 'bg-yellow-500 text-gray-900',
    LOW: 'bg-green-500',
  }
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold text-white ${cls[severity] ?? 'bg-slate-500'}`}>
      {severity}
    </span>
  )
}

export function Dashboard() {
  const [summary, setSummary] = useState<{ total_events: number; high_confidence_events: number; recent_events: FloodEvent[] } | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      eventsApi.summary(),
      alertsApi.list({ limit: 5 })
    ]).then(([sumRes, alertRes]) => {
      setSummary(sumRes.data)
      setAlerts(alertRes.data)
    }).catch(console.error).finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Dashboard</h1>
        <p className="text-slate-400 text-sm mt-1">Global flood monitoring overview</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Waves}         label="Total Events"      value={summary?.total_events ?? '–'}           color="bg-blue-600" />
        <StatCard icon={AlertTriangle} label="High Confidence"   value={summary?.high_confidence_events ?? '–'} color="bg-red-600" />
        <StatCard icon={Bell}          label="Active Alerts"     value={alerts.filter(a => a.status === 'TRIGGERED').length} color="bg-orange-500" />
        <StatCard icon={Map}           label="Monitored Regions" value={15}                                      color="bg-emerald-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Flood Events */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
            <h2 className="font-semibold text-white">Recent Flood Events</h2>
            <Link to="/events" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
          </div>
          <div className="divide-y divide-slate-700">
            {loading ? (
              <p className="p-5 text-slate-400 text-sm">Loading…</p>
            ) : summary?.recent_events.length === 0 ? (
              <p className="p-5 text-slate-400 text-sm">No flood events recorded yet.</p>
            ) : (
              summary?.recent_events.map(evt => (
                <div key={evt.flood_event_id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-white font-medium">Area #{evt.area_id}</p>
                    <p className="text-xs text-slate-400">{format(new Date(evt.detected_at), 'dd MMM yyyy HH:mm')}</p>
                  </div>
                  {evt.confidence && <SeverityBadge severity={evt.confidence} />}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-700">
            <h2 className="font-semibold text-white">Recent Alerts</h2>
            <Link to="/alerts" className="text-xs text-blue-400 hover:text-blue-300">View all →</Link>
          </div>
          <div className="divide-y divide-slate-700">
            {loading ? (
              <p className="p-5 text-slate-400 text-sm">Loading…</p>
            ) : alerts.length === 0 ? (
              <p className="p-5 text-slate-400 text-sm">No alerts yet.</p>
            ) : (
              alerts.map(alert => (
                <div key={alert.alert_id} className="px-5 py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-white font-medium">{alert.summary ?? `Alert #${alert.alert_id}`}</p>
                    <p className="text-xs text-slate-400">{format(new Date(alert.triggered_at), 'dd MMM yyyy HH:mm')}</p>
                  </div>
                  <SeverityBadge severity={alert.severity} />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Links */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
        <h2 className="font-semibold text-white mb-3">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Link to="/map" className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            🗺️ Open World Map
          </Link>
          <Link to="/ingest" className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            🛰️ Fetch Satellite Data
          </Link>
          <Link to="/alerts" className="bg-slate-700 hover:bg-slate-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
            🔔 Manage Alerts
          </Link>
        </div>
      </div>
    </div>
  )
}

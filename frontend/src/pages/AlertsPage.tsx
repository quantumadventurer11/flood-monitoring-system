import { useEffect, useState } from 'react'
import { alertsApi } from '../api/client'
import type { Alert } from '../types'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const severityColors: Record<string, string> = {
  CRITICAL: 'bg-red-600', HIGH: 'bg-orange-500', MEDIUM: 'bg-yellow-500 text-gray-900', LOW: 'bg-green-600'
}
const statusColors: Record<string, string> = {
  TRIGGERED: 'bg-red-800 text-red-200', ACKNOWLEDGED: 'bg-blue-800 text-blue-200',
  RESOLVED: 'bg-green-900 text-green-300', FALSE_POSITIVE: 'bg-slate-600 text-slate-300'
}

export function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)

  const load = () => {
    alertsApi.list({ limit: 100 }).then(r => setAlerts(r.data))
      .catch(console.error).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const acknowledge = async (id: number) => {
    await alertsApi.updateStatus(id, 'ACKNOWLEDGED')
    toast.success('Alert acknowledged')
    load()
  }

  const resolve = async (id: number) => {
    await alertsApi.updateStatus(id, 'RESOLVED')
    toast.success('Alert resolved')
    load()
  }

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-white">Alerts</h1>
        <p className="text-slate-400 text-sm mt-1">Monitor and manage flood threshold alerts</p>
      </div>

      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Triggered</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Severity</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Status</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Summary</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {loading ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">Loading…</td></tr>
            ) : alerts.length === 0 ? (
              <tr><td colSpan={5} className="px-5 py-8 text-center text-slate-400">No alerts yet.</td></tr>
            ) : alerts.map(alert => (
              <tr key={alert.alert_id} className="hover:bg-slate-700/50">
                <td className="px-5 py-3 text-slate-300">{format(new Date(alert.triggered_at), 'dd MMM HH:mm')}</td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold text-white ${severityColors[alert.severity] ?? 'bg-slate-500'}`}>
                    {alert.severity}
                  </span>
                </td>
                <td className="px-5 py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusColors[alert.status] ?? 'bg-slate-600 text-white'}`}>
                    {alert.status}
                  </span>
                </td>
                <td className="px-5 py-3 text-slate-400 max-w-xs truncate">{alert.summary ?? '—'}</td>
                <td className="px-5 py-3">
                  <div className="flex gap-2">
                    {alert.status === 'TRIGGERED' && (
                      <button onClick={() => acknowledge(alert.alert_id)}
                        className="text-xs text-blue-400 hover:text-blue-300">Acknowledge</button>
                    )}
                    {(alert.status === 'TRIGGERED' || alert.status === 'ACKNOWLEDGED') && (
                      <button onClick={() => resolve(alert.alert_id)}
                        className="text-xs text-green-400 hover:text-green-300">Resolve</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

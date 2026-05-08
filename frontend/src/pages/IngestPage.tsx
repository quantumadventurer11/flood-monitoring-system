import { useEffect, useState } from 'react'
import { ingestionApi, geoApi } from '../api/client'
import type { GeographicArea } from '../types'
import toast from 'react-hot-toast'

export function IngestPage() {
  const [areas, setAreas] = useState<GeographicArea[]>([])
  const [areaId, setAreaId] = useState('')
  const [satellite, setSatellite] = useState('S1')
  const [startDate, setStartDate] = useState('2024-06-01')
  const [endDate, setEndDate] = useState('2024-07-01')
  const [jobs, setJobs] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    geoApi.listAreas().then(r => { setAreas(r.data); if (r.data[0]) setAreaId(String(r.data[0].area_id)) })
    ingestionApi.listJobs().then(r => setJobs(r.data))
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!areaId) return
    setLoading(true)
    try {
      const { data } = await ingestionApi.triggerSentinel(Number(areaId), startDate, endDate, satellite)
      toast.success(`Job #${data.job_id} started`)
      ingestionApi.listJobs().then(r => setJobs(r.data))
    } catch {
      toast.error('Failed to start ingestion job')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Data Ingestion</h1>
        <p className="text-slate-400 text-sm mt-1">Fetch Sentinel-1/2 satellite data via the free Copernicus STAC API</p>
      </div>

      {/* Form */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5">
        <h2 className="font-semibold text-white mb-4">Trigger Satellite Data Fetch</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Monitoring Area</label>
              <select value={areaId} onChange={e => setAreaId(e.target.value)} required
                className="w-full bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2">
                {areas.map(a => <option key={a.area_id} value={a.area_id}>{a.area_name}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Satellite</label>
              <select value={satellite} onChange={e => setSatellite(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2">
                <option value="S1">Sentinel-1 (SAR / Radar)</option>
                <option value="S2">Sentinel-2 (Optical)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Start Date</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} required
                className="w-full bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">End Date</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} required
                className="w-full bg-slate-700 border border-slate-600 text-white text-sm rounded-lg px-3 py-2" />
            </div>
          </div>
          <button type="submit" disabled={loading || !areaId}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-semibold px-5 py-2.5 rounded-lg text-sm transition-colors">
            {loading ? 'Submitting…' : '🛰️ Fetch Satellite Data'}
          </button>
        </form>
      </div>

      {/* Jobs table */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-700">
          <h2 className="font-semibold text-white">Recent Ingestion Jobs</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Job #</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Type</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Status</th>
              <th className="px-5 py-3 text-left text-xs font-semibold text-slate-400">Started</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700">
            {jobs.length === 0
              ? <tr><td colSpan={4} className="px-5 py-6 text-center text-slate-400 text-sm">No jobs yet</td></tr>
              : jobs.map((j: any) => (
                <tr key={j.ingest_job_id} className="hover:bg-slate-700/40">
                  <td className="px-5 py-3 text-slate-300">#{j.ingest_job_id}</td>
                  <td className="px-5 py-3 text-white">{j.job_type}</td>
                  <td className="px-5 py-3">
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                      j.status === 'COMPLETED' ? 'bg-green-700 text-white' :
                      j.status === 'FAILED'    ? 'bg-red-700 text-white' :
                      j.status === 'RUNNING'   ? 'bg-blue-700 text-white' :
                                                 'bg-slate-600 text-white'
                    }`}>{j.status}</span>
                  </td>
                  <td className="px-5 py-3 text-slate-400 text-xs">{new Date(j.started_at).toLocaleString()}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

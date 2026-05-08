import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, Map, Bell, Download,
  LogOut, Waves
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/',        icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/map',     icon: Map,             label: 'World Map'  },
  { to: '/events',  icon: Waves,           label: 'Flood Events' },
  { to: '/alerts',  icon: Bell,            label: 'Alerts'    },
  { to: '/ingest',  icon: Download,        label: 'Data Ingestion' },
]

export function Layout() {
  const navigate = useNavigate()

  const handleLogout = () => {
    localStorage.removeItem('fms_token')
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-slate-900 text-white overflow-hidden">
      {/* ── Sidebar ───────────────────────────────────────────────── */}
      <aside className="w-64 bg-slate-800 flex flex-col border-r border-slate-700 shrink-0">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-700">
          <Waves className="text-blue-400 w-8 h-8" />
          <div>
            <p className="font-bold text-sm leading-tight">Flood Monitoring</p>
            <p className="text-xs text-slate-400">System</p>
          </div>
        </div>

        {/* Nav links */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                )
              }
            >
              <Icon className="w-4 h-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-slate-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full px-4 py-2.5 rounded-lg text-sm text-slate-300 hover:bg-red-600 hover:text-white transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* ── Main content ─────────────────────────────────────────── */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}

import { Activity, BarChart3, CloudRain, History, MapPinned, Microscope } from "lucide-react";
import { useMemo, useState } from "react";
import Dashboard from "./pages/Dashboard";
import Forecast from "./pages/Forecast";
import HistoryPage from "./pages/History";
import Methodology from "./pages/Methodology";
import Predictor from "./pages/Predictor";

const pages = [
  { id: "dashboard", label: "Dashboard", icon: MapPinned, component: Dashboard },
  { id: "predictor", label: "Predictor", icon: Activity, component: Predictor },
  { id: "forecast", label: "Forecast", icon: CloudRain, component: Forecast },
  { id: "history", label: "History", icon: History, component: HistoryPage },
  { id: "methodology", label: "Methodology", icon: Microscope, component: Methodology },
];

export default function App() {
  const [active, setActive] = useState("dashboard");
  const Page = useMemo(() => pages.find((page) => page.id === active)?.component ?? Dashboard, [active]);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-bold text-ink">Flood Monitoring System</h1>
            <p className="text-sm text-slate-600">Sentinel SAR/optical classification with paper-faithful methodology visuals.</p>
          </div>
          <nav className="flex flex-wrap gap-2">
            {pages.map((page) => {
              const Icon = page.icon;
              return (
                <button
                  key={page.id}
                  onClick={() => setActive(page.id)}
                  className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                    active === page.id ? "bg-flood text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
                  }`}
                >
                  <Icon size={16} />
                  {page.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        <Page />
      </main>
    </div>
  );
}

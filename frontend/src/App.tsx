import { Activity, CloudRain, History, MapPinned, Microscope, Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";
import SpacexAILogo from "./components/SpacexAILogo";
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

function pageFromPath() {
  const pageId = window.location.pathname.replace("/", "");
  return pages.some((page) => page.id === pageId) ? pageId : "dashboard";
}

export default function App() {
  const [active, setActive] = useState(pageFromPath);
  const [forecastPlace, setForecastPlace] = useState<{ country: string; lat: number; lon: number } | null>(null);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const stored = window.localStorage.getItem("theme");
    if (stored === "light" || stored === "dark") return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("theme", theme);
  }, [theme]);

  const openPage = (pageId: string) => {
    setActive(pageId);
    window.history.replaceState(null, "", pageId === "dashboard" ? "/" : `/${pageId}`);
  };
  const openForecast = (place: { country: string; lat: number; lon: number }) => {
    setForecastPlace(place);
    setActive("forecast");
    window.history.replaceState(null, "", `?country=${encodeURIComponent(place.country)}&lat=${place.lat}&lon=${place.lon}`);
  };

  return (
    <div className="min-h-screen bg-slate-50 transition-colors duration-300 dark:bg-slate-950">
      <header className="border-b border-slate-200 bg-white/95 backdrop-blur transition-colors duration-300 dark:border-slate-800 dark:bg-slate-950/95">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-lg bg-blue-600 text-white shadow-sm">
              <MapPinned size={22} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-ink dark:text-white">Flood Monitoring System</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">Satellite, rainfall, and validation signals for flood-risk monitoring.</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-900">
              <SpacexAILogo />
            </div>
            <button
              aria-label="Toggle color theme"
              onClick={() => setTheme((current) => (current === "dark" ? "light" : "dark"))}
              className="interactive-button grid h-10 w-10 place-items-center rounded-lg border border-slate-200 bg-white text-slate-700 transition hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:hover:bg-slate-800"
            >
              {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <nav className="flex flex-wrap gap-2">
              {pages.map((page) => {
                const Icon = page.icon;
                return (
                  <button
                    key={page.id}
                    onClick={() => openPage(page.id)}
                    className={`interactive-button flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${
                      active === page.id ? "bg-flood text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                    }`}
                  >
                    <Icon size={16} />
                    {page.label}
                  </button>
                );
              })}
            </nav>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6">
        {active === "dashboard" && <Dashboard onOpenForecast={openForecast} />}
        {active === "predictor" && <Predictor onOpenForecast={openForecast} />}
        {active === "forecast" && <Forecast initialPlace={forecastPlace} />}
        {active === "history" && <HistoryPage />}
        {active === "methodology" && <Methodology />}
      </main>
    </div>
  );
}

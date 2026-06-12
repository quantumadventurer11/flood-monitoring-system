export default function FloodGauge({ probability }: { probability: number }) {
  const pct = Math.round(probability * 100);
  const color = probability > 0.7 ? "#dc2626" : probability >= 0.35 ? "#d97706" : "#16a34a";
  return (
    <div className="card soft-panel p-4 text-center">
      <div className="mx-auto grid h-36 w-36 place-items-center rounded-full transition-all duration-700" style={{ background: `conic-gradient(${color} ${pct}%, #e2e8f0 0)` }}>
        <div className="grid h-24 w-24 place-items-center rounded-full bg-white dark:bg-slate-950">
          <span className="text-3xl font-bold" style={{ color }}>{pct}%</span>
        </div>
      </div>
      <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">Flood likelihood</p>
    </div>
  );
}

export default function FloodGauge({ probability, compact = false, framed = true }: { probability: number; compact?: boolean; framed?: boolean }) {
  const pct = Math.round(probability * 100);
  const color = probability > 0.7 ? "#dc2626" : probability >= 0.35 ? "#d97706" : "#16a34a";
  const size = compact ? "h-24 w-24" : "h-36 w-36";
  const innerSize = compact ? "h-16 w-16" : "h-24 w-24";
  const textSize = compact ? "text-xl" : "text-3xl";
  const content = (
    <>
      <div className={`mx-auto grid ${size} place-items-center rounded-full transition-all duration-700`} style={{ background: `conic-gradient(${color} ${pct}%, #e2e8f0 0)` }}>
        <div className={`grid ${innerSize} place-items-center rounded-full bg-white dark:bg-slate-950`}>
          <span className={`${textSize} font-bold`} style={{ color }}>{pct}%</span>
        </div>
      </div>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Flood likelihood</p>
    </>
  );
  if (!framed) {
    return <div className="text-center">{content}</div>;
  }
  return (
    <div className="card soft-panel p-4 text-center">
      {content}
    </div>
  );
}

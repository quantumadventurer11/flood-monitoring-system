export default function SpacexAILogo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-2">
      <svg className="h-9 w-9 shrink-0" viewBox="0 0 48 48" role="img" aria-label="SpacexAI original logo">
        <defs>
          <linearGradient id="spacexai-wave" x1="8" x2="40" y1="35" y2="13" gradientUnits="userSpaceOnUse">
            <stop stopColor="#0077b6" />
            <stop offset="1" stopColor="#00a6a6" />
          </linearGradient>
        </defs>
        <circle cx="24" cy="24" r="18" fill="none" stroke="currentColor" className="text-slate-300 dark:text-slate-700" strokeWidth="2" />
        <ellipse className="orbit-spin text-blue-500 dark:text-cyan-300" cx="24" cy="24" rx="21" ry="8" fill="none" stroke="currentColor" strokeWidth="1.8" />
        <path d="M10 29c4.6-5.4 9-6.8 13.2-4.1 4.8 3.1 9.8 1.8 14.8-4" fill="none" stroke="url(#spacexai-wave)" strokeLinecap="round" strokeWidth="4" />
        <circle className="gentle-pulse" cx="36" cy="15" r="3" fill="#22d3ee" />
      </svg>
      {!compact && (
        <div className="leading-tight">
          <p className="text-sm font-bold tracking-wide text-slate-900 dark:text-white">SpacexAI</p>
          <p className="text-[11px] font-medium uppercase text-slate-500 dark:text-slate-400">Member</p>
        </div>
      )}
    </div>
  );
}

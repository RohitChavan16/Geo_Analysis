import { Moon, RefreshCcw, Sun, Zap } from 'lucide-react'

export default function TopBar({ onSync, onRealtime, busy, statusText, theme, onToggleTheme }) {
  return (
    <div className="glass-card mb-6 border-slate-200/70 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-100">GeoShop Command Center</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Singapore place-change intelligence across OSM, data.gov.sg, OneMap, and digital signals.</p>
          <p className="mt-2 text-xs font-medium text-slate-500 dark:text-slate-400">{statusText}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={onToggleTheme}
            className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
          >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />} {theme === 'dark' ? 'Light' : 'Dark'}
          </button>
          <button disabled={busy} onClick={onSync} className="inline-flex items-center gap-2 rounded-xl bg-slateblue px-4 py-2 text-sm font-medium text-white disabled:opacity-60">
            <RefreshCcw size={16} /> Trigger Sync
          </button>
          <button disabled={busy} onClick={onRealtime} className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60 dark:bg-slate-100 dark:text-slate-900">
            <Zap size={16} /> Real-time Update
          </button>
        </div>
      </div>
    </div>
  )
}

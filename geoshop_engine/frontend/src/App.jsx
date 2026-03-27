import { useEffect, useMemo, useState } from 'react'
import { Activity, Building2, CircleCheckBig, CircleX, Database } from 'lucide-react'
import { api } from './lib/api'
import TopBar from './components/TopBar'
import StatCard from './components/StatCard'
import SyncSection from './sections/SyncSection'
import TrendSection from './sections/TrendSection'
import MapSection from './sections/MapSection'
import ChangeFeedSection from './sections/ChangeFeedSection'

function hasAnyChangeRows(payload) {
  if (!payload) return false
  return (payload.new_shops?.length || 0) + (payload.closed_shops?.length || 0) + (payload.updated_shops?.length || 0) > 0
}

export default function App() {
  const [stats, setStats] = useState({})
  const [syncStatus, setSyncStatus] = useState({})
  const [progress, setProgress] = useState({})
  const [history, setHistory] = useState([])
  const [shops, setShops] = useState([])
  const [changes, setChanges] = useState({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [theme, setTheme] = useState(() => {
    const saved = (localStorage.getItem('theme') || 'light').toLowerCase().trim()
    return saved === 'dark' ? 'dark' : 'light'
  })

  const loadDashboard = async () => {
    try {
      const [shopStats, status, pg, hist, shopData] = await Promise.all([
        api.getShopStats(),
        api.getSyncStatus(),
        api.getSyncProgress(),
        api.getSyncHistory(20),
        api.getShops('limit=1000'),
      ])
      setStats(shopStats || {})
      setSyncStatus(status || {})
      setProgress(pg || {})
      setHistory(hist?.history || [])
      setShops(Array.isArray(shopData) ? shopData : [])

      const activeRun = pg?.active_run_id
      const latestSuccessfulRun = (hist?.history || []).find((h) => h.status === 'success')?.run_id

      let changeData = activeRun ? await api.getSyncChanges(activeRun) : null
      if (!hasAnyChangeRows(changeData) && latestSuccessfulRun) {
        changeData = await api.getSyncChanges(latestSuccessfulRun)
      }
      if (!changeData) {
        changeData = await api.getSyncChanges()
      }

      setChanges(changeData || {})
      setError('')
    } catch (e) {
      setError(e.message || 'Failed to load dashboard')
    }
  }

  useEffect(() => {
    const next = theme === 'dark' ? 'dark' : 'light'
    const root = document.documentElement
    const body = document.body

    // Hard-set classes to avoid stale state when toggling repeatedly.
    root.classList.remove('dark', 'light')
    body.classList.remove('dark', 'light')
    root.classList.add(next)
    body.classList.add(next)

    localStorage.setItem('theme', next)
  }, [theme])

  useEffect(() => {
    loadDashboard()
    const t = setInterval(loadDashboard, 5000)
    return () => clearInterval(t)
  }, [])

  const statusText = useMemo(() => {
    const s = progress?.status || 'idle'
    const stage = progress?.stage || 'idle'
    const msg = progress?.message || 'No sync running'
    return `[${String(s).toUpperCase()} | ${stage}] ${msg}`
  }, [progress])

  const trigger = async (mode = 'sync') => {
    try {
      setBusy(true)
      if (mode === 'sync') await api.triggerSync()
      else await api.triggerRealtime()
      await loadDashboard()
    } catch (e) {
      setError(e.message || 'Failed to trigger update')
    } finally {
      setBusy(false)
    }
  }

  const liveChanges = progress?.live_change_summary || {}

  return (
    <main className="mx-auto max-w-[1600px] p-4 md:p-6">
      <TopBar
        onSync={() => trigger('sync')}
        onRealtime={() => trigger('realtime')}
        busy={busy}
        statusText={statusText}
        theme={theme}
        onToggleTheme={() => setTheme((t) => ((String(t).toLowerCase().trim() === 'dark') ? 'light' : 'dark'))}
      />

      {error ? <div className="mb-4 rounded-xl border border-rose/30 bg-rose/10 px-4 py-3 text-sm text-rose dark:border-rose-900 dark:bg-rose-950/40">{error}</div> : null}

      <section className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-6">
        <StatCard label="Active Shops" value={stats.total_active_shops || 0} hint="Current active records" tone="blue" />
        <StatCard label="High Confidence" value={stats.high_confidence_shops || 0} hint="confidence >= threshold" tone="green" />
        <StatCard label="Live New" value={liveChanges.new_count || 0} hint="during current sync" tone="green" />
        <StatCard label="Live Closed" value={liveChanges.closed_count || 0} hint="during current sync" tone="red" />
        <StatCard label="Sync Status" value={syncStatus.latest_sync_status || 'never'} hint="latest backend state" tone="amber" />
        <StatCard label="Last Sync" value={syncStatus.last_sync ? 'Done' : 'Never'} hint={syncStatus.last_sync ? new Date(syncStatus.last_sync).toLocaleString() : 'No completed sync'} tone="blue" />
      </section>

      <section className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <SyncSection progress={progress} history={history} />
        <TrendSection history={history} theme={theme} />
      </section>

      <section className="mb-6 grid grid-cols-1 gap-6 xl:grid-cols-2">
        <MapSection shops={shops} changes={changes} />
        <ChangeFeedSection changes={changes} />
      </section>

      <footer className="grid grid-cols-2 gap-2 rounded-2xl border border-slate-200 bg-white p-4 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 md:grid-cols-5">
        <div className="flex items-center gap-2"><Activity size={14} /> FastAPI</div>
        <div className="flex items-center gap-2"><Database size={14} /> MongoDB</div>
        <div className="flex items-center gap-2"><Building2 size={14} /> OSM + DataGov + OneMap</div>
        <div className="flex items-center gap-2"><CircleCheckBig size={14} /> Open Detection Engine</div>
        <div className="flex items-center gap-2"><CircleX size={14} /> Closure Detection Engine</div>
      </footer>
    </main>
  )
}

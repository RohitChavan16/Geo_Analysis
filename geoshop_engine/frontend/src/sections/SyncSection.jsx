import SectionCard from '../components/SectionCard'

function SourcePill({ name, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800/70">
      <div className="text-[11px] uppercase tracking-wide text-slate-500 dark:text-slate-400">{name}</div>
      <div className="text-lg font-semibold text-slate-800 dark:text-slate-100">{value}</div>
    </div>
  )
}

export default function SyncSection({ progress, history }) {
  const counts = progress?.source_counts || {}
  const live = progress?.live_change_summary || {}
  const pct = Math.max(0, Math.min(100, Number(progress?.progress_percent || 0)))

  return (
    <SectionCard title="Sync Monitor" subtitle="Parallel source ingestion with live progress and change counters.">
      <div className="mb-4">
        <div className="mb-2 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>{progress?.message || 'No sync running'}</span>
          <span>{pct}%</span>
        </div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-700">
          <div className="h-3 rounded-full bg-gradient-to-r from-slateblue to-mint transition-all" style={{ width: `${pct}%` }} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <SourcePill name="OSM" value={counts.osm || 0} />
        <SourcePill name="DataGov" value={counts.datagov || 0} />
        <SourcePill name="OneMap" value={counts.onemap || 0} />
        <SourcePill name="Digital" value={counts.digital || 0} />
        <SourcePill name="Total" value={counts.total || 0} />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3">
        <SourcePill name="Live New" value={live.new_count || 0} />
        <SourcePill name="Live Updated" value={live.updated_count || 0} />
        <SourcePill name="Live Closed" value={live.closed_count || 0} />
      </div>

      <div className="mt-5 overflow-x-auto">
        <table className="w-full min-w-[760px] border-separate border-spacing-y-1 text-sm">
          <thead className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
            <tr>
              <th className="px-2 py-1 text-left">Run</th>
              <th className="px-2 py-1 text-left">Status</th>
              <th className="px-2 py-1 text-right">New</th>
              <th className="px-2 py-1 text-right">Updated</th>
              <th className="px-2 py-1 text-right">Closed</th>
              <th className="px-2 py-1 text-right">Total Source</th>
            </tr>
          </thead>
          <tbody>
            {(history || []).slice(0, 8).map((row) => (
              <tr key={row.run_id} className="rounded-xl bg-slate-50 text-slate-700 dark:bg-slate-800/60 dark:text-slate-200">
                <td className="rounded-l-xl px-2 py-2">{row.run_id?.slice(0, 10) || '-'}</td>
                <td className="px-2 py-2">{row.status || '-'}</td>
                <td className="px-2 py-2 text-right">{row.new_count || 0}</td>
                <td className="px-2 py-2 text-right">{row.updated_count || 0}</td>
                <td className="px-2 py-2 text-right">{row.closed_count || 0}</td>
                <td className="rounded-r-xl px-2 py-2 text-right">{row.source_counts?.total || 0}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  )
}

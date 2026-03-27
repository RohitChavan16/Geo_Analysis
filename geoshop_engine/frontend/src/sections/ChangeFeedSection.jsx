import SectionCard from '../components/SectionCard'

function DetailLine({ label, value }) {
  if (value === undefined || value === null || value === '') return null
  return <div className="text-xs text-slate-600 dark:text-slate-300"><span className="font-semibold">{label}:</span> {String(value)}</div>
}

function Row({ item }) {
  const status = item.predicted_status || 'Change'
  const color = status === 'Closed Place' ? 'text-rose-600' : status === 'New Place' ? 'text-emerald-600' : 'text-amber-600'
  const coords = item.coordinates || {}

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="font-medium text-slate-900 dark:text-slate-100">{item.place_name || item.name || 'Unknown'}</div>
          <div className="text-xs text-slate-500 dark:text-slate-400">{item.address || 'No address'}</div>
        </div>
        <div className={`text-xs font-semibold ${color}`}>{status}</div>
      </div>

      <div className="mt-2 space-y-1">
        <DetailLine label="Category" value={item.category || item.shop_type} />
        <DetailLine label="Coordinates" value={Number.isFinite(Number(coords.lat)) && Number.isFinite(Number(coords.lng)) ? `${Number(coords.lat).toFixed(6)}, ${Number(coords.lng).toFixed(6)}` : ''} />
        <DetailLine label="Match In DB" value={item.match_in_database} />
        <DetailLine label="Confidence" value={item.confidence} />
        <DetailLine label="Decision Score" value={item.decision_score} />
        <DetailLine label="Digital Score" value={item.digital_footprint_score} />
        <DetailLine label="Sources" value={(item.sources || []).join(', ')} />
        <DetailLine label="Reason" value={item.reason} />
        <DetailLine label="Closure Type" value={item.closure_type} />
        <DetailLine label="Phone" value={item.phone} />
        <DetailLine label="Website" value={item.website} />
        <DetailLine label="Opening Hours" value={item.opening_hours} />
        <DetailLine label="Postal" value={item.postal_code} />
      </div>
    </div>
  )
}

export default function ChangeFeedSection({ changes }) {
  const newShops = changes?.new_shops || []
  const closedShops = changes?.closed_shops || []
  const updatedShops = changes?.updated_shops || []
  const all = [...newShops, ...closedShops, ...updatedShops]

  return (
    <SectionCard
      title="Live Changes"
      subtitle={`Openings: ${newShops.length} | Closures: ${closedShops.length} | Updates: ${updatedShops.length}`}
    >
      <div className="grid max-h-[520px] grid-cols-1 gap-3 overflow-auto lg:grid-cols-1">
        {all.length ? all.map((item, idx) => <Row key={`${item.place_name || 'shop'}-${idx}`} item={item} />) : <div className="text-sm text-slate-500 dark:text-slate-400">No change entries yet. Waiting for a completed sync run with detected changes.</div>}
      </div>
    </SectionCard>
  )
}

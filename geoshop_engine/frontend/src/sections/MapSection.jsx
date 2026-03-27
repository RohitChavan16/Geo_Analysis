import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { CircleMarker, MapContainer, Popup, TileLayer } from 'react-leaflet'
import SectionCard from '../components/SectionCard'

delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const SG_CENTER = [1.3521, 103.8198]

function parseCoordinates(item) {
  const c = item?.coordinates
  const lat = Number(c?.lat ?? item?.lat)
  const lng = Number(c?.lng ?? item?.lng)
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null
  return [lat, lng]
}

function toChangePoints(items, status) {
  return (items || [])
    .map((item) => {
      const coords = parseCoordinates(item)
      if (!coords) return null
      return {
        ...item,
        coords,
        markerStatus: status,
      }
    })
    .filter(Boolean)
}

export default function MapSection({ shops, changes }) {
  const basePoints = (shops || [])
    .map((shop) => {
      const lat = Number(shop.lat)
      const lng = Number(shop.lng)
      if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null
      return { ...shop, coords: [lat, lng], markerStatus: 'existing' }
    })
    .filter(Boolean)
    .slice(0, 900)

  const newPoints = toChangePoints(changes?.new_shops, 'new')
  const updatedPoints = toChangePoints(changes?.updated_shops, 'updated')
  const closedPoints = toChangePoints(changes?.closed_shops, 'closed')

  const allPoints = [...basePoints, ...updatedPoints, ...newPoints, ...closedPoints]

  const styleMap = {
    existing: { color: '#3b82f6', fill: '#3b82f6', radius: 3 },
    updated: { color: '#f59e0b', fill: '#f59e0b', radius: 5 },
    new: { color: '#10b981', fill: '#10b981', radius: 6 },
    closed: { color: '#ef4444', fill: '#ef4444', radius: 6 },
  }

  return (
    <SectionCard title="Singapore Map View" subtitle="Live geospatial view with status colors for new/updated/closed.">
      <div className="mb-3 flex flex-wrap gap-2 text-xs">
        <span className="rounded-full bg-blue-100 px-3 py-1 text-blue-700 dark:bg-blue-900/50 dark:text-blue-200">Existing</span>
        <span className="rounded-full bg-amber-100 px-3 py-1 text-amber-700 dark:bg-amber-900/50 dark:text-amber-200">Updated</span>
        <span className="rounded-full bg-emerald-100 px-3 py-1 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-200">New</span>
        <span className="rounded-full bg-rose-100 px-3 py-1 text-rose-700 dark:bg-rose-900/50 dark:text-rose-200">Closed</span>
      </div>

      <div className="h-[480px] overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
        <MapContainer center={SG_CENTER} zoom={11} className="h-full w-full">
          <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
          {allPoints.map((point, idx) => {
            const style = styleMap[point.markerStatus] || styleMap.existing
            return (
              <CircleMarker
                key={`${point.id || point.place_name || point.name}-${point.markerStatus}-${idx}`}
                center={point.coords}
                radius={style.radius}
                pathOptions={{ color: style.color, fillColor: style.fill, fillOpacity: 0.7, weight: 1.5 }}
              >
                <Popup>
                  <div className="min-w-[210px]">
                    <div className="font-semibold">{point.place_name || point.name || 'Unknown Shop'}</div>
                    <div className="text-xs text-slate-600">{point.address || 'No address'}</div>
                    <div className="mt-1 text-xs">Status: {point.predicted_status || point.markerStatus}</div>
                    <div className="text-xs">Confidence: {point.confidence ?? point.confidence_score ?? 0}</div>
                    {point.reason ? <div className="mt-1 text-xs text-slate-500">Reason: {point.reason}</div> : null}
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}
        </MapContainer>
      </div>
    </SectionCard>
  )
}

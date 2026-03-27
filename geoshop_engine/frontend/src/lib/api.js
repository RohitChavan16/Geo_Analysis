const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api'

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`)
  const data = await res.json()
  if (!res.ok) throw new Error(data?.detail || `HTTP ${res.status}`)
  return data
}

export const api = {
  getShops: (params = '') => getJson(`/shops${params ? `?${params}` : ''}`),
  getShopStats: () => getJson('/shops/stats'),
  getSyncStatus: () => getJson('/sync/status'),
  getSyncProgress: () => getJson('/sync/progress'),
  getSyncHistory: (limit = 20) => getJson(`/sync/history?limit=${limit}`),
  getSyncChanges: (runId) => getJson(`/sync/changes${runId ? `?run_id=${encodeURIComponent(runId)}` : ''}`),
  triggerSync: () => fetch(`${API_BASE}/sync/trigger`, { method: 'POST' }).then((r) => r.json()),
  triggerRealtime: () => fetch(`${API_BASE}/update/realtime`, { method: 'POST' }).then((r) => r.json()),
  getPipeline: (refresh = false) => getJson(`/debug/pipeline-data${refresh ? '?refresh=true' : ''}`),
}

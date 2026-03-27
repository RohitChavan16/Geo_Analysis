import { ResponsiveContainer, ComposedChart, Line, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts'
import SectionCard from '../components/SectionCard'

export default function TrendSection({ history, theme = 'light' }) {
  const axis = theme === 'dark' ? '#94a3b8' : '#64748b'
  const grid = theme === 'dark' ? '#334155' : '#e2e8f0'

  const data = (history || [])
    .filter((h) => h.status === 'success')
    .slice(0, 20)
    .reverse()
    .reduce((acc, h, i) => {
      const prev = acc[i - 1]
      const net = (prev?.net || 0) + (h.new_count || 0) - (h.closed_count || 0)
      acc.push({
        run: `Run ${i + 1}`,
        new: h.new_count || 0,
        closed: h.closed_count || 0,
        updated: h.updated_count || 0,
        net,
      })
      return acc
    }, [])

  return (
    <SectionCard title="Open vs Closed Trend" subtitle="Per-sync counts plus cumulative net growth trend.">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke={grid} />
            <XAxis dataKey="run" stroke={axis} />
            <YAxis stroke={axis} />
            <Tooltip />
            <Legend />
            <Bar dataKey="new" fill="#10b981" name="New" />
            <Bar dataKey="closed" fill="#ef4444" name="Closed" />
            <Bar dataKey="updated" fill="#f59e0b" name="Updated" />
            <Line type="monotone" dataKey="net" stroke="#3957ff" strokeWidth={3} dot={false} name="Net Growth" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  )
}

import { useEffect, useRef, useState } from 'react'
import gsap from 'gsap'

export default function StatCard({ label, value, hint, tone = 'blue' }) {
  const toneMap = {
    blue: 'text-slateblue dark:text-blue-300',
    green: 'text-mint dark:text-emerald-300',
    red: 'text-rose dark:text-rose-300',
    amber: 'text-amber dark:text-amber-300',
  }

  const isNumber = typeof value === 'number' && Number.isFinite(value)
  const [displayValue, setDisplayValue] = useState(isNumber ? value : value)
  const valueRef = useRef(isNumber ? value : 0)

  useEffect(() => {
    if (!isNumber) {
      setDisplayValue(value)
      return
    }

    const counter = { val: valueRef.current }
    gsap.to(counter, {
      val: value,
      duration: 0.5,
      ease: 'power2.out',
      onUpdate: () => setDisplayValue(Math.round(counter.val)),
    })
    valueRef.current = value
  }, [isNumber, value])

  return (
    <div className="glass-card p-4 transition-colors">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
      <div className={`mt-2 text-2xl font-semibold ${toneMap[tone] || toneMap.blue}`}>{displayValue}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{hint}</div> : null}
    </div>
  )
}

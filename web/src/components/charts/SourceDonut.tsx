/**
 * SourceDonut — Recharts PieChart donut with center total label.
 * Legend on the right. Animate sectors on mount.
 */
import { useMemo } from 'react'
import type { ReactNode } from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface DonutDatum {
  label: string
  value: number
  color: string
}

interface SourceDonutProps {
  data: DonutDatum[]
  height?: number
}

function CustomTooltip({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: DonutDatum }>
}) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-strong rounded-xl px-3 py-2 text-xs">
      <p className="font-semibold text-fg">{d.label}</p>
      <p className="text-fg/60">{d.value}</p>
    </div>
  )
}

function renderLegendContent(props: unknown): ReactNode {
  const { payload = [] } = props as { payload?: Array<{ payload: DonutDatum }> }
  return (
    <div className="flex flex-col gap-2 pl-4">
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-xs">
          <div
            className="h-3 w-3 rounded-sm shrink-0"
            style={{ backgroundColor: entry.payload.color }}
          />
          <span className="text-fg/60">{entry.payload.label}</span>
          <span className="text-fg/40">{entry.payload.value}</span>
        </div>
      ))}
    </div>
  )
}

export default function SourceDonut({ data, height = 260 }: SourceDonutProps) {
  const total = useMemo(() => data.reduce((s, d) => s + d.value, 0), [data])

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-white/40">
        Aucune donnée disponible
      </div>
    )
  }

  return (
    <div className="flex items-center justify-center gap-4">
      <div className="relative" style={{ width: height, height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              innerRadius="60%"
              outerRadius="90%"
              paddingAngle={2}
              animationDuration={800}
              animationBegin={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} stroke="rgba(255,255,255,0.5)" strokeWidth={2} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
          </PieChart>
        </ResponsiveContainer>
        {/* Center total */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className="text-2xl font-bold tracking-tight text-fg">{total}</span>
          <span className="text-xs text-fg/40">Total</span>
        </div>
      </div>
      <Legend content={renderLegendContent} />
    </div>
  )
}
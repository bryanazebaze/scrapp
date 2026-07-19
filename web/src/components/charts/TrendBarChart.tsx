/**
 * TrendBarChart — horizontal Recharts BarChart of growth_score per neighborhood.
 * Bars use prism-violet→fuchsia gradient. Animate on mount.
 */
import { useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { TrendingNeighborhood } from '@/lib/types'
import { formatXAF, percent } from '@/lib/utils'

interface TrendBarChartProps {
  data: TrendingNeighborhood[]
  height?: number
}

interface ChartDatum {
  name: string
  growth_score: number
  trend_pct: number
  median_price: number
  city: string
}

function CustomTooltip({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: ChartDatum }>
}) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-strong rounded-xl px-3 py-2 text-xs space-y-1">
      <p className="font-semibold text-fg">{d.name}</p>
      <p className="text-fg/60">{d.city}</p>
      <p className="text-prism-violet">Croissance: {d.growth_score.toFixed(1)}/10</p>
      <p className="text-fg/60">Tendance: {percent(d.trend_pct)}</p>
      <p className="text-fg/60">Prix médian: {formatXAF(d.median_price)}</p>
    </div>
  )
}

export default function TrendBarChart({ data, height = 300 }: TrendBarChartProps) {
  const chartData = useMemo<ChartDatum[]>(() => {
    return data.map((d) => ({
      name: d.neighborhood,
      growth_score: d.growth_score,
      trend_pct: d.trend_pct,
      median_price: d.median_price,
      city: d.city,
    }))
  }, [data])

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-white/40">
        Aucune donnée de tendance disponible
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={chartData}
        layout="vertical"
        margin={{ top: 10, right: 20, bottom: 10, left: 10 }}
      >
        <defs>
          <linearGradient id="bar-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#E94E1B" />
            <stop offset="100%" stopColor="#6B2D5C" />
          </linearGradient>
        </defs>
        <XAxis
          type="number"
          domain={[0, 10]}
          tick={{ fill: 'rgb(var(--wi) / 0.45)', fontSize: 11 }}
          axisLine={{ stroke: 'rgb(var(--wi) / 0.10)' }}
          tickLine={false}
        />
        <YAxis
          type="category"
          dataKey="name"
          tick={{ fill: 'rgb(var(--wi) / 0.68)', fontSize: 12 }}
          axisLine={{ stroke: 'rgb(var(--wi) / 0.10)' }}
          tickLine={false}
          width={120}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgb(var(--wi) / 0.04)' }} />
        <Bar
          dataKey="growth_score"
          radius={[0, 6, 6, 0]}
          animationDuration={800}
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill="url(#bar-gradient)" />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
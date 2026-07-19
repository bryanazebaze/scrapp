/**
 * PriceHistoryChart — Recharts LineChart of price over time.
 * X axis: observed_at, Y axis: price_observed. Gradient stroke violet→cyan.
 */
import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import type { ListingHistoryEvent } from '@/lib/types'
import { formatDate, formatXAF } from '@/lib/utils'
import EmptyState from '@/components/ui/EmptyState'
import { TrendingDown } from 'lucide-react'

interface PriceHistoryChartProps {
  events: ListingHistoryEvent[]
  height?: number
}

interface ChartDatum {
  date: string
  price: number
  label: string
}

function CustomTooltip({ active, payload }: {
  active?: boolean
  payload?: Array<{ payload: ChartDatum }>
}) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <div className="glass-strong rounded-xl px-3 py-2 text-xs">
      <p className="text-fg/60">{d.label}</p>
      <p className="font-semibold text-fg">{formatXAF(d.price)}</p>
    </div>
  )
}

export default function PriceHistoryChart({
  events,
  height = 260,
}: PriceHistoryChartProps) {
  const data = useMemo<ChartDatum[]>(() => {
    return events
      .filter((e) => e.price_observed != null)
      .map((e) => ({
        date: e.observed_at,
        price: e.price_observed!,
        label: formatDate(e.observed_at),
      }))
      .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
  }, [events])

  if (data.length === 0) {
    return (
      <EmptyState
        icon={TrendingDown}
        title="Aucun historique de prix"
        description="Il n'y a pas encore d'événements de prix enregistrés pour cette annonce."
      />
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 10, right: 10, bottom: 10, left: 10 }}>
        <defs>
          <linearGradient id="price-stroke" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#E94E1B" />
            <stop offset="100%" stopColor="#D97706" />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgb(var(--wi) / 0.06)" />
        <XAxis
          dataKey="label"
          tick={{ fill: 'rgb(var(--wi) / 0.45)', fontSize: 11 }}
          axisLine={{ stroke: 'rgb(var(--wi) / 0.10)' }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: 'rgb(var(--wi) / 0.45)', fontSize: 11 }}
          axisLine={{ stroke: 'rgb(var(--wi) / 0.10)' }}
          tickLine={false}
          tickFormatter={(v: number) => formatXAF(v)}
          width={90}
        />
        <Tooltip content={<CustomTooltip />} />
        <Line
          type="monotone"
          dataKey="price"
          stroke="url(#price-stroke)"
          strokeWidth={2.5}
          dot={{ fill: '#E94E1B', r: 4 }}
          activeDot={{ r: 6, fill: '#D97706' }}
          animationDuration={800}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
/**
 * ScoreHeatmap — grid/table of neighborhoods and their 5 scores.
 * Color intensity mapped to score (0=transparent, 10=saturated).
 * Sorts by premium_score desc by default.
 */
import { useMemo } from 'react'
import type { NeighborhoodAnalyticsSchema } from '@/lib/types'
import { cn } from '@/lib/utils'

interface ScoreHeatmapProps {
  rows: NeighborhoodAnalyticsSchema[]
  height?: number
}

const scoreColumns: {
  key: keyof NeighborhoodAnalyticsSchema
  label: string
  color: string
}[] = [
  { key: 'premium_score', label: 'Premium', color: '#E94E1B' },
  { key: 'demand_score', label: 'Demande', color: '#D97706' },
  { key: 'growth_score', label: 'Croissance', color: '#6B2D5C' },
  { key: 'activity_score', label: 'Activité', color: '#E8A53A' },
  { key: 'luxury_score', label: 'Luxueux', color: '#1F8A4C' },
]

function cellStyle(score: number | null, baseColor: string): React.CSSProperties {
  if (score == null) return { backgroundColor: 'rgb(var(--wi) / 0.03)' }
  const alpha = Math.max(0.12, Math.min(0.9, score / 10))
  return { backgroundColor: `${baseColor}${Math.round(alpha * 255).toString(16).padStart(2, '0')}` }
}

export default function ScoreHeatmap({ rows, height }: ScoreHeatmapProps) {
  const sorted = useMemo(() => {
    return [...rows].sort(
      (a, b) => (b.premium_score ?? 0) - (a.premium_score ?? 0),
    )
  }, [rows])

  if (sorted.length === 0) {
    return (
      <div className="flex items-center justify-center py-12 text-sm text-white/40">
        Aucune donnée de scoring disponible
      </div>
    )
  }

  return (
    <div className="w-full overflow-x-auto no-scrollbar">
      <div
        className="min-w-[640px]"
        style={height ? { maxHeight: height, overflowY: 'auto' } : undefined}
      >
        {/* Header */}
        <div
          className="grid gap-2 px-3 py-2"
          style={{ gridTemplateColumns: 'minmax(160px, 1fr) repeat(5, 1fr)' }}
        >
          <div className="text-xs font-medium uppercase tracking-wider text-white/40">
            Quartier
          </div>
          {scoreColumns.map((col) => (
            <div
              key={col.key}
              className="text-center text-xs font-medium uppercase tracking-wider text-white/40"
            >
              {col.label}
            </div>
          ))}
        </div>

        {/* Rows */}
        <div className="space-y-1">
          {sorted.map((row) => (
            <div
              key={row.location_id}
              className="grid gap-2 items-center rounded-lg px-3 py-2 transition hover:bg-white/5"
              style={{ gridTemplateColumns: 'minmax(160px, 1fr) repeat(5, 1fr)' }}
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-white/80">
                  {row.neighborhood ?? row.slug}
                </p>
                <p className="truncate text-xs text-white/30">{row.city}</p>
              </div>
              {scoreColumns.map((col) => {
                const score = row[col.key] as number | null
                return (
                  <div
                    key={col.key}
                    className={cn(
                      'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition',
                    )}
                    style={cellStyle(score, col.color)}
                    title={`${col.label}: ${score ?? 'N/A'}`}
                  >
                    <span className={score != null ? 'text-white' : 'text-fg/30'}>
                      {score != null ? score.toFixed(1) : '—'}
                    </span>
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-3 px-3 text-xs text-white/30">
        <span>0</span>
        <div className="h-2 flex-1 max-w-[200px] rounded-full bg-gradient-to-r from-transparent via-brand-500/50 to-brand-500" />
        <span>10</span>
        <span className="ml-2">Intensité du score</span>
      </div>
    </div>
  )
}
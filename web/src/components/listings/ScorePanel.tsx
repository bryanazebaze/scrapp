import { motion } from 'framer-motion'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import type { NeighborhoodAnalyticsSchema } from '@/lib/types'
import { formatXAF, formatXAFPerSqm, percent, cn } from '@/lib/utils'
import ScoreRing from '@/components/ui/ScoreRing'
import EmptyState from '@/components/ui/EmptyState'

interface ScorePanelProps {
  analytics: NeighborhoodAnalyticsSchema | null | undefined
}

export default function ScorePanel({ analytics }: ScorePanelProps) {
  if (analytics == null) {
    return (
      <EmptyState
        title="Données d'analyse non disponibles"
        description="Les scores de ce quartier ne sont pas encore calculés."
      />
    )
  }

  const trendIcon =
    analytics.trend_direction === 'up' ? (
      <TrendingUp className="h-4 w-4 text-emerald-400" />
    ) : analytics.trend_direction === 'down' ? (
      <TrendingDown className="h-4 w-4 text-rose-400" />
    ) : (
      <Minus className="h-4 w-4 text-white/40" />
    )

  const trendColor =
    analytics.trend_direction === 'up'
      ? 'text-emerald-400'
      : analytics.trend_direction === 'down'
        ? 'text-rose-400'
        : 'text-white/40'

  const rings = [
    { label: 'Premium', score: analytics.premium_score },
    { label: 'Demande', score: analytics.demand_score },
    { label: 'Croissance', score: analytics.growth_score },
    { label: 'Activité', score: analytics.activity_score },
    { label: 'Luxe', score: analytics.luxury_score },
  ]

  // Category-aware header + price stats
  const isLand = analytics.category === 'Land'
  const isStructure = analytics.category === 'Structure'

  const headerLabel = isLand
    ? 'Prix moyen/m²'
    : isStructure
      ? 'Prix moyen'
      : 'Prix médian'

  const headerValue = isLand
    ? formatXAFPerSqm(analytics.avg_price_per_sqm)
    : isStructure
      ? formatXAF(analytics.average_price)
      : formatXAF(analytics.median_price)

  const priceStats = isLand
    ? [
        { label: 'Min/m²', value: formatXAFPerSqm(analytics.min_price_per_sqm) },
        { label: 'Moyen/m²', value: formatXAFPerSqm(analytics.avg_price_per_sqm) },
        { label: 'Max/m²', value: formatXAFPerSqm(analytics.max_price_per_sqm) },
      ]
    : isStructure
      ? [
          { label: 'Min', value: formatXAF(analytics.min_price) },
          { label: 'Moyen', value: formatXAF(analytics.average_price) },
          { label: 'Max', value: formatXAF(analytics.max_price) },
        ]
      : [
          { label: 'Min', value: formatXAF(analytics.min_price) },
          { label: 'Médian', value: formatXAF(analytics.median_price) },
          { label: 'Max', value: formatXAF(analytics.max_price) },
        ]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="glass space-y-5 rounded-2xl p-6"
    >
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-fg">
            {analytics.neighborhood || analytics.city}
          </h3>
          <p className="text-sm text-white/50">{analytics.city}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <span className="text-xs text-white/40">{headerLabel}</span>
          <span className="text-base font-semibold text-fg">{headerValue}</span>
        </div>
      </div>

      {/* Trend */}
      <div className="flex items-center gap-2 rounded-xl bg-white/5 px-3 py-2">
        {trendIcon}
        <span className={cn('text-sm font-medium', trendColor)}>
          {percent(analytics.trend_pct)}
        </span>
        <span className="text-xs text-white/40">
          ({analytics.listing_count} bien(s))
        </span>
      </div>

      {/* Score rings */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        {rings.map((r) => (
          <div
            key={r.label}
            className="flex flex-col items-center justify-center rounded-xl bg-white/[0.03] py-4"
          >
            <ScoreRing score={r.score} size={90} label={r.label} />
          </div>
        ))}
      </div>

      {/* Price stats */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {priceStats.map((s) => (
          <div key={s.label} className="rounded-xl bg-white/[0.03] py-2">
            <p className="text-xs text-white/40">{s.label}</p>
            <p className="text-sm font-medium text-fg">{s.value}</p>
          </div>
        ))}
      </div>

      {/* Fallback caption */}
      {analytics.fallback_level === 'city' && (
        <p className="text-center text-xs text-white/30">
          Basé sur la ville — données insuffisantes au quartier
        </p>
      )}
    </motion.div>
  )
}
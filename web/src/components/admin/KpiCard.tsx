/**
 * KpiCard — big glass stat tile for admin dashboard KPIs.
 * Shows icon in a colored glass chip, big value, label, optional trend, optional sub-text.
 * Renders shimmer placeholder when loading.
 */
import { motion } from 'framer-motion'
import { ArrowDownRight, ArrowUpRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn, formatNumber, percent } from '@/lib/utils'

type Accent = 'violet' | 'cyan' | 'fuchsia' | 'amber' | 'emerald' | 'brand'

interface KpiCardProps {
  label: string
  value: string | number
  sub?: string
  icon: LucideIcon
  trend?: number
  accent?: Accent
  loading?: boolean
}

const accentMap: Record<Accent, { text: string; iconBg: string }> = {
  violet: { text: 'text-prism-violet', iconBg: 'bg-prism-violet/15' },
  cyan: { text: 'text-prism-cyan', iconBg: 'bg-prism-cyan/15' },
  fuchsia: { text: 'text-prism-fuchsia', iconBg: 'bg-prism-fuchsia/15' },
  amber: { text: 'text-prism-amber', iconBg: 'bg-prism-amber/15' },
  emerald: { text: 'text-prism-emerald', iconBg: 'bg-prism-emerald/15' },
  brand: { text: 'text-brand-400', iconBg: 'bg-brand-500/15' },
}

export default function KpiCard({
  label,
  value,
  sub,
  icon: Icon,
  trend,
  accent = 'violet',
  loading = false,
}: KpiCardProps) {
  const a = accentMap[accent]
  const displayValue = typeof value === 'number' ? formatNumber(value) : value
  const trendUp = (trend ?? 0) >= 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="glass rounded-2xl p-5 transition hover:border-white/20 hover:shadow-glass-lg hover:-translate-y-0.5"
    >
      <div className="flex items-start justify-between">
        {loading ? (
          <div className="h-11 w-11 rounded-xl shimmer" />
        ) : (
          <div className={cn('flex h-11 w-11 items-center justify-center rounded-xl', a.iconBg)}>
            <Icon className={cn('h-5 w-5', a.text)} />
          </div>
        )}
        {trend != null && !loading && (
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
              trendUp ? 'bg-emerald-400/15 text-emerald-600 dark:text-emerald-300' : 'bg-rose-400/15 text-rose-600 dark:text-rose-300',
            )}
          >
            {trendUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {percent(trend)}
          </span>
        )}
      </div>
      <div className="mt-4">
        {loading ? (
          <>
            <div className="h-8 w-24 rounded-lg shimmer" />
            <div className="mt-2 h-4 w-16 rounded shimmer" />
          </>
        ) : (
          <>
            <p className="text-2xl font-bold tracking-tight text-fg">{displayValue}</p>
            <p className="mt-1 text-sm text-white/50">{label}</p>
            {sub && <p className="mt-0.5 text-xs text-white/30">{sub}</p>}
          </>
        )}
      </div>
    </motion.div>
  )
}
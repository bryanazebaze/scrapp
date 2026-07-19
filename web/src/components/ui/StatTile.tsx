/**
 * StatTile — glass card showing a single KPI with icon, value, label, and optional trend.
 */
import { motion } from 'framer-motion'
import type { LucideIcon } from 'lucide-react'
import { cn, formatNumber, percent } from '@/lib/utils'

type Accent = 'violet' | 'cyan' | 'fuchsia' | 'amber' | 'emerald' | 'brand'

interface StatTileProps {
  label: string
  value: string | number
  sub?: string
  icon?: LucideIcon
  trend?: number
  accent?: Accent
}

const accentMap: Record<Accent, { text: string; bg: string; iconBg: string }> = {
  violet: { text: 'text-prism-violet', bg: 'bg-prism-violet/10', iconBg: 'bg-prism-violet/15' },
  cyan: { text: 'text-prism-cyan', bg: 'bg-prism-cyan/10', iconBg: 'bg-prism-cyan/15' },
  fuchsia: { text: 'text-prism-fuchsia', bg: 'bg-prism-fuchsia/10', iconBg: 'bg-prism-fuchsia/15' },
  amber: { text: 'text-prism-amber', bg: 'bg-prism-amber/10', iconBg: 'bg-prism-amber/15' },
  emerald: { text: 'text-prism-emerald', bg: 'bg-prism-emerald/10', iconBg: 'bg-prism-emerald/15' },
  brand: { text: 'text-brand-400', bg: 'bg-brand-500/10', iconBg: 'bg-brand-500/15' },
}

export default function StatTile({
  label,
  value,
  sub,
  icon: Icon,
  trend,
  accent = 'violet',
}: StatTileProps) {
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
        {Icon && (
          <div className={cn('flex h-11 w-11 items-center justify-center rounded-xl', a.iconBg)}>
            <Icon className={cn('h-5 w-5', a.text)} />
          </div>
        )}
        {trend != null && (
          <span
            className={cn(
              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
              trendUp ? 'bg-prism-emerald/12 text-emerald-600 dark:text-emerald-300' : 'bg-rose-500/10 text-rose-600 dark:text-rose-300',
            )}
          >
            {percent(trend)}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold tracking-tight text-fg">
          {displayValue}
        </p>
        <p className="mt-1 text-sm text-white/50">{label}</p>
        {sub && <p className="mt-0.5 text-xs text-white/30">{sub}</p>}
      </div>
    </motion.div>
  )
}
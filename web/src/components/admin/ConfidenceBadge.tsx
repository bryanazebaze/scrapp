/**
 * ConfidenceBadge — pill badge showing match confidence value.
 * Color thresholds: >=0.75 emerald, 0.40-0.74 amber, <0.40 rose, null white/40.
 */
import { cn } from '@/lib/utils'

interface ConfidenceBadgeProps {
  confidence: number | null | undefined
}

export default function ConfidenceBadge({ confidence }: ConfidenceBadgeProps) {
  const isNull = confidence == null
  const v = confidence ?? 0

  const { colorClass, label } = isNull
    ? { colorClass: 'bg-white/10 text-fg/40', label: 'N/A' }
    : v >= 0.75
      ? { colorClass: 'bg-emerald-400/15 text-emerald-600 dark:text-emerald-300', label: 'Élevée' }
      : v >= 0.40
        ? { colorClass: 'bg-amber-400/15 text-amber-600 dark:text-amber-300', label: 'Moyenne' }
        : { colorClass: 'bg-rose-400/15 text-rose-600 dark:text-rose-300', label: 'Faible' }

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        colorClass,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-70" />
      {isNull ? 'N/A' : `${label} · ${v.toFixed(2)}`}
    </span>
  )
}
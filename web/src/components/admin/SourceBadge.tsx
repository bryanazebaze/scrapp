/**
 * SourceBadge — pill badge for source adapter kind + active state.
 * dedicated = prism-cyan, universal = prism-fuchsia.
 * If !active, dim with opacity-50 and add "désactivé" sub-label.
 */
import { cn } from '@/lib/utils'

interface SourceBadgeProps {
  kind: 'dedicated' | 'universal'
  active: boolean
}

export default function SourceBadge({ kind, active }: SourceBadgeProps) {
  const colorClass =
    kind === 'dedicated'
      ? 'bg-prism-cyan/15 text-prism-cyan'
      : 'bg-prism-fuchsia/15 text-prism-fuchsia'

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        colorClass,
        !active && 'opacity-50',
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {kind === 'dedicated' ? 'Dédié' : 'Universel'}
      {!active && <span className="text-white/40">· désactivé</span>}
    </span>
  )
}
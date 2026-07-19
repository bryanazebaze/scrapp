/**
 * Badge — small pill-shaped label in various prism colors.
 * Variants: solid (filled), soft (translucent bg), outline (border only).
 */
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type BadgeColor = 'violet' | 'cyan' | 'fuchsia' | 'amber' | 'emerald' | 'rose' | 'white'
type BadgeVariant = 'solid' | 'soft' | 'outline'

interface BadgeProps {
  children: ReactNode
  color?: BadgeColor
  variant?: BadgeVariant
  className?: string
}

const softClasses: Record<BadgeColor, string> = {
  violet:  'bg-prism-violet/12 text-prism-violet',
  cyan:    'bg-prism-cyan/12 text-prism-cyan',
  fuchsia: 'bg-prism-fuchsia/12 text-prism-fuchsia',
  amber:   'bg-prism-amber/15 text-prism-amber',
  emerald: 'bg-prism-emerald/12 text-prism-emerald',
  rose:    'bg-rose-500/10 text-rose-700 dark:text-rose-300',
  white:   'bg-ink-900/5 text-ink-900 dark:bg-white/10 dark:text-white',
}

const outlineClasses: Record<BadgeColor, string> = {
  violet:  'border border-prism-violet/40 text-prism-violet',
  cyan:    'border border-prism-cyan/40 text-prism-cyan',
  fuchsia: 'border border-prism-fuchsia/40 text-prism-fuchsia',
  amber:   'border border-prism-amber/50 text-prism-amber',
  emerald: 'border border-prism-emerald/40 text-prism-emerald',
  rose:    'border border-rose-500/40 text-rose-700 dark:text-rose-300',
  white:   'border border-ink-900/15 text-ink-900',
}

const solidClasses: Record<BadgeColor, string> = {
  violet:  'bg-prism-violet text-white',
  cyan:    'bg-prism-cyan text-white',
  fuchsia: 'bg-prism-fuchsia text-white',
  amber:   'bg-prism-amber text-white',
  emerald: 'bg-prism-emerald text-white',
  rose:    'bg-rose-500 text-white',
  white:   'bg-white text-ink-900 border border-ink-900/10',
}

const variantMap: Record<BadgeVariant, Record<BadgeColor, string>> = {
  soft: softClasses,
  outline: outlineClasses,
  solid: solidClasses,
}

export default function Badge({
  children,
  color = 'violet',
  variant = 'soft',
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        variantMap[variant][color],
        className,
      )}
    >
      {children}
    </span>
  )
}
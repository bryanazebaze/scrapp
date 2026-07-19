/**
 * EmptyState — centered placeholder for empty/no-data states.
 * Shows a large faded icon, title, description, and optional action.
 */
import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: LucideIcon
  title: string
  description?: string
  action?: ReactNode
  className?: string
}

export default function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center py-16 px-6 text-center',
        className,
      )}
    >
      {Icon && (
        <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-white/5 border border-white/10">
          <Icon className="h-10 w-10 text-fg/30" strokeWidth={1.5} />
        </div>
      )}
      <h3 className="text-lg font-semibold text-fg tracking-tight">
        {title}
      </h3>
      {description && (
        <p className="mt-2 max-w-md text-sm text-fg/50">
          {description}
        </p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
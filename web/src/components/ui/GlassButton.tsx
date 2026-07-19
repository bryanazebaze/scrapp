/**
 * GlassButton — styled button with variants (primary, ghost, outline, danger).
 * Forwards ref, uses Framer Motion for tap animation.
 */
import { forwardRef } from 'react'
import { motion } from 'framer-motion'
import type { ReactNode, MouseEvent } from 'react'
import { cn } from '@/lib/utils'

type Variant = 'primary' | 'ghost' | 'outline' | 'danger'
type Size = 'sm' | 'md' | 'lg'

interface GlassButtonProps {
  children: ReactNode
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void
  type?: 'button' | 'submit' | 'reset'
  variant?: Variant
  size?: Size
  className?: string
  disabled?: boolean
  title?: string
  id?: string
  'aria-label'?: string
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-brand-500 to-brand-400 text-white shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40',
  ghost: 'bg-white/5 hover:bg-white/10 text-fg',
  outline: 'border border-white/15 hover:border-white/30 bg-transparent text-fg',
  danger:
    'bg-rose-500/10 text-rose-700 dark:text-rose-300 hover:bg-rose-500/20 border border-rose-500/30',
}

const sizeClasses: Record<Size, string> = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
}

const GlassButton = forwardRef<HTMLButtonElement, GlassButtonProps>(
  (
    { children, onClick, type = 'button', variant = 'primary', size = 'md', className, disabled, title, id, ...ariaProps },
    ref,
  ) => {
    return (
      <motion.button
        ref={ref}
        id={id}
        type={type}
        onClick={onClick}
        disabled={disabled}
        title={title}
        whileTap={{ scale: 0.97 }}
        aria-label={ariaProps['aria-label']}
        className={cn(
          'inline-flex items-center justify-center gap-2 rounded-xl font-medium transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed',
          variantClasses[variant],
          sizeClasses[size],
          className,
        )}
      >
        {children}
      </motion.button>
    )
  },
)

GlassButton.displayName = 'GlassButton'

export default GlassButton
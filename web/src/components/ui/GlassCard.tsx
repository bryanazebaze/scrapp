/**
 * GlassCard — reusable glassmorphic panel.
 * Renders a div with glass/glass-strong styling, rounded corners, and optional hover lift.
 */
import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface GlassCardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  strong?: boolean
  as?: keyof JSX.IntrinsicElements
}

export default function GlassCard({
  children,
  className,
  hover = false,
  strong = false,
}: GlassCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={cn(
        strong ? 'glass-strong' : 'glass',
        'rounded-2xl p-6',
        hover &&
          'transition hover:border-white/20 hover:shadow-glass-lg hover:-translate-y-0.5',
        className,
      )}
    >
      {children}
    </motion.div>
  )
}
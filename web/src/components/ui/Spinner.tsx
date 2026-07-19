/**
 * Spinner — loading indicator using the .spinner CSS utility.
 * Scales the spinner by the `size` prop (default 32px).
 */
import { cn } from '@/lib/utils'

interface SpinnerProps {
  size?: number
  className?: string
  label?: string
}

export default function Spinner({ size = 32, className, label }: SpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <div
        className="spinner"
        style={{
          width: `${size}px`,
          height: `${size}px`,
          borderWidth: `${Math.max(2, Math.round(size / 10))}px`,
        }}
        role="status"
        aria-label="Chargement"
      />
      {label && (
        <p className="text-sm text-white/50">{label}</p>
      )}
    </div>
  )
}
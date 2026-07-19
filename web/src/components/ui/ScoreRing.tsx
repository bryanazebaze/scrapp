/**
 * ScoreRing — circular SVG progress ring (0-10 scale).
 * Animated stroke-dashoffset, gradient stroke, centered value.
 */
import { motion } from 'framer-motion'
import { scoreColor } from '@/lib/utils'

interface ScoreRingProps {
  score: number | null
  size?: number
  label?: string
  showValue?: boolean
}

export default function ScoreRing({
  score,
  size = 120,
  label,
  showValue = true,
}: ScoreRingProps) {
  const stroke = Math.max(4, size * 0.06)
  const radius = (size - stroke) / 2
  const circumference = 2 * Math.PI * radius
  const isNull = score == null
  const pct = isNull ? 0 : Math.max(0, Math.min(10, score)) / 10
  const offset = circumference * (1 - pct)

  const gradientId = `score-ring-grad-${size}`

  return (
    <div
      className="flex flex-col items-center justify-center gap-2"
      style={{ width: size, height: size + (label ? 24 : 0) }}
    >
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          <defs>
            <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#E94E1B" />
              <stop offset="100%" stopColor="#D97706" />
            </linearGradient>
          </defs>
          {/* Background ring */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgb(var(--wi) / 0.08)"
            strokeWidth={stroke}
            strokeDasharray={isNull ? `${circumference / 20} ${circumference / 20}` : undefined}
            strokeDashoffset={isNull ? 0 : undefined}
          />
          {/* Progress ring */}
          {!isNull && (
            <motion.circle
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={`url(#${gradientId})`}
              strokeWidth={stroke}
              strokeLinecap="round"
              strokeDasharray={circumference}
              initial={{ strokeDashoffset: circumference }}
              animate={{ strokeDashoffset: offset }}
              transition={{ duration: 0.8, ease: 'easeOut' }}
            />
          )}
        </svg>
        {/* Center value */}
        {showValue && (
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-2xl font-bold tracking-tight ${scoreColor(score)}`}>
              {isNull ? 'N/A' : score.toFixed(1)}
            </span>
            <span className="text-[10px] uppercase tracking-wider text-white/40">
              {isNull ? '' : '/ 10'}
            </span>
          </div>
        )}
      </div>
      {label && (
        <span className="text-xs text-white/50">{label}</span>
      )}
    </div>
  )
}
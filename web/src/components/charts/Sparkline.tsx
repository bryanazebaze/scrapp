/**
 * Sparkline — tiny inline line chart (no axes, no tooltip).
 * SVG path with gradient stroke. Used in KPI tiles for trend hints.
 */
import { useId, useMemo } from 'react'

interface SparklineProps {
  values: number[]
  width?: number
  height?: number
  stroke?: string
}

export default function Sparkline({
  values,
  width = 80,
  height = 28,
  stroke = '#E94E1B',
}: SparklineProps) {
  const reactId = useId()
  const gradId = `spark-grad-${reactId.replace(/[:]/g, '')}`

  const path = useMemo(() => {
    if (values.length < 2) return ''
    const min = Math.min(...values)
    const max = Math.max(...values)
    const range = max - min || 1
    const stepX = width / (values.length - 1)
    const points = values.map((v, i) => {
      const x = i * stepX
      const y = height - ((v - min) / range) * (height - 4) - 2
      return `${x},${y}`
    })
    return `M ${points.join(' L ')}`
  }, [values, width, height])

  if (values.length < 2) return null

  return (
    <svg width={width} height={height} className="inline-block">
      <defs>
        <linearGradient id={gradId} x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={stroke} />
          <stop offset="100%" stopColor="#D97706" />
        </linearGradient>
      </defs>
      <path
        d={path}
        fill="none"
        stroke={`url(#${gradId})`}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
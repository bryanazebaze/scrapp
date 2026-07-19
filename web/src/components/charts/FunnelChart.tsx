/**
 * FunnelChart — horizontal stacked bars representing funnel stages.
 * Each stage has width proportional to count, colored, with labels.
 */
import { motion } from 'framer-motion'

interface FunnelStage {
  label: string
  count: number
  color: string
}

interface FunnelChartProps {
  stages: FunnelStage[]
}

export default function FunnelChart({ stages }: FunnelChartProps) {
  const maxCount = Math.max(...stages.map((s) => s.count), 1)
  const total = stages.reduce((s, st) => s + st.count, 0)

  return (
    <div className="space-y-3">
      {stages.map((stage, i) => {
        const widthPct = (stage.count / maxCount) * 100
        const sharePct = total > 0 ? (stage.count / total) * 100 : 0
        return (
          <div key={stage.label} className="flex items-center gap-3">
            {/* Label */}
            <div className="w-28 shrink-0 text-right">
              <span className="text-xs font-medium text-fg/60">{stage.label}</span>
            </div>
            {/* Bar */}
            <div className="flex-1 h-8 bg-white/5 rounded-lg overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${widthPct}%` }}
                transition={{ duration: 0.6, delay: i * 0.1, ease: 'easeOut' }}
                className="h-full flex items-center justify-end pr-3 rounded-lg"
                style={{ backgroundColor: stage.color }}
              >
                <span className="text-xs font-semibold text-white whitespace-nowrap">
                  {stage.count} ({sharePct.toFixed(1)}%)
                </span>
              </motion.div>
            </div>
          </div>
        )
      })}
      {stages.length === 0 && (
        <div className="flex items-center justify-center py-12 text-sm text-white/40">
          Aucune donnée disponible
        </div>
      )}
    </div>
  )
}
/**
 * PendingReviewTable — glass table for pending review items.
 * Columns: Title, Price, Location, Confidence, Crawled, Actions.
 * Row hover highlight. Framer Motion stagger on entrance.
 * While an action is pending on a row, shows a small spinner instead of buttons.
 */
import { motion } from 'framer-motion'
import { AlertCircle, Check, Clock3, ExternalLink, X } from 'lucide-react'
import type { PendingItem } from '@/lib/types'
import { cn, formatXAF, relativeTime } from '@/lib/utils'
import ConfidenceBadge from '@/components/admin/ConfidenceBadge'
import EmptyState from '@/components/ui/EmptyState'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'

interface PendingReviewTableProps {
  items: PendingItem[]
  onApprove: (id: number) => void
  onReject: (id: number) => void
  loadingAction?: number | null
}

export default function PendingReviewTable({
  items,
  onApprove,
  onReject,
  loadingAction = null,
}: PendingReviewTableProps) {
  if (items.length === 0) {
    return (
      <EmptyState
        icon={Check}
        title="File d'attente vide"
        description="Aucune annonce en attente de révision. Les nouvelles annonces apparaîtront ici."
      />
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse">
        <thead>
          <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-white/40">
            <th className="px-4 py-3 font-medium">Titre</th>
            <th className="px-4 py-3 font-medium">Prix</th>
            <th className="px-4 py-3 font-medium">Localisation</th>
            <th className="px-4 py-3 font-medium">Confiance</th>
            <th className="px-4 py-3 font-medium">Doublon</th>
            <th className="px-4 py-3 font-medium">Crawlé</th>
            <th className="px-4 py-3 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item, i) => {
            const isLoading = loadingAction === item.id
            return (
              <motion.tr
                key={item.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: Math.min(i * 0.03, 0.3) }}
                className="border-b border-white/5 transition hover:bg-white/[0.03]"
              >
                <td className="px-4 py-3">
                  <a
                    href={item.url_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 text-sm text-white/80 hover:text-fg"
                  >
                    <span className="max-w-[220px] truncate">{item.title_raw || 'Sans titre'}</span>
                    <ExternalLink className="h-3.5 w-3.5 shrink-0 text-white/30" />
                  </a>
                </td>
                <td className="px-4 py-3 text-sm text-white/70">
                  {formatXAF(item.price_parsed)}
                </td>
                <td className="px-4 py-3 text-sm text-white/60">
                  <span className="max-w-[180px] truncate inline-block">
                    {item.location_raw || '—'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <ConfidenceBadge confidence={item.match_confidence} />
                </td>
                <td className="px-4 py-3">
                  {item.is_duplicate ? (
                    <span className="inline-flex items-center gap-1 rounded-full bg-amber-400/15 px-2.5 py-1 text-xs font-medium text-amber-600 dark:text-amber-300">
                      <AlertCircle className="h-3 w-3" />
                      Possible doublon
                    </span>
                  ) : (
                    <span className="text-xs text-white/30">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-sm text-white/50">
                  <span className="inline-flex items-center gap-1">
                    <Clock3 className="h-3.5 w-3.5 text-white/30" />
                    {relativeTime(item.crawled_at)}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center justify-end gap-2">
                    {isLoading ? (
                      <Spinner size={20} />
                    ) : (
                      <>
                        <GlassButton
                          size="sm"
                          variant="ghost"
                          className={cn('text-emerald-600 dark:text-emerald-300 hover:bg-emerald-500/15')}
                          onClick={() => onApprove(item.id)}
                          aria-label="Approuver"
                        >
                          <Check className="h-4 w-4" />
                          Approuver
                        </GlassButton>
                        <GlassButton
                          size="sm"
                          variant="ghost"
                          className={cn('text-rose-600 dark:text-rose-300 hover:bg-rose-500/15')}
                          onClick={() => onReject(item.id)}
                          aria-label="Rejeter"
                        >
                          <X className="h-4 w-4" />
                          Rejeter
                        </GlassButton>
                      </>
                    )}
                  </div>
                </td>
              </motion.tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
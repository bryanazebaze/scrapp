/**
 * CrawlHistoryTable — displays recent crawl sessions for a source.
 */
import { CheckCircle2, Clock3, Globe, Search, Timer, XCircle } from 'lucide-react'
import type { CrawlSessionSummary } from '@/lib/types'
import { useCrawlSessions } from '@/hooks/useAdmin'
import { relativeTime } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'

interface CrawlHistoryTableProps {
  sourceSlug: string | null
}

export default function CrawlHistoryTable({ sourceSlug }: CrawlHistoryTableProps) {
  const sessionsQ = useCrawlSessions(sourceSlug)

  if (!sourceSlug) {
    return (
      <GlassCard>
        <div className="py-8 text-center text-sm text-white/40">
          Sélectionnez une source pour voir l'historique des crawls.
        </div>
      </GlassCard>
    )
  }

  if (sessionsQ.isLoading) {
    return (
      <GlassCard>
        <div className="flex justify-center py-12">
          <Spinner size={28} />
        </div>
      </GlassCard>
    )
  }

  if (sessionsQ.isError) {
    return (
      <GlassCard>
        <EmptyState
          icon={XCircle}
          title="Erreur"
          description="Impossible de charger l'historique des crawls."
        />
      </GlassCard>
    )
  }

  const sessions = sessionsQ.data ?? []

  if (sessions.length === 0) {
    return (
      <GlassCard>
        <EmptyState
          icon={Clock3}
          title="Aucun historique"
          description={`Aucune session de crawl trouvée pour ${sourceSlug}. Lancez un crawl.`}
        />
      </GlassCard>
    )
  }

  return (
    <GlassCard>
      <div className="mb-4 flex items-center gap-2">
        <Clock3 className="h-5 w-5 text-white/50" />
        <h2 className="text-lg font-semibold text-fg">
          Historique des crawls — {sourceSlug}
        </h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[700px] border-collapse">
          <thead>
            <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-white/40">
              <th className="px-3 py-3 font-medium">Date</th>
              <th className="px-3 py-3 text-right font-medium">Total</th>
              <th className="px-3 py-3 text-right font-medium">Nouveaux</th>
              <th className="px-3 py-3 text-right font-medium">Doublons</th>
              <th className="px-3 py-3 text-right font-medium">En attente</th>
              <th className="px-3 py-3 text-right font-medium">Promus</th>
              <th className="px-3 py-3 text-right font-medium">Rejetés</th>
              <th className="px-3 py-3 text-center font-medium">Statut</th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((session) => (
              <tr
                key={session.crawl_session_id}
                className="border-b border-white/5 transition hover:bg-white/[0.03]"
              >
                <td className="px-3 py-3 text-sm text-white/70">
                  {session.started_at
                    ? relativeTime(session.started_at)
                    : '—'}
                </td>
                <td className="px-3 py-3 text-right text-sm text-white/70">
                  {session.total_listings}
                </td>
                <td className="px-3 py-3 text-right text-sm text-emerald-400">
                  {session.new_listings}
                </td>
                <td className="px-3 py-3 text-right text-sm text-amber-400">
                  {session.duplicates}
                </td>
                <td className="px-3 py-3 text-right text-sm text-fuchsia-400">
                  {session.pending_count}
                </td>
                <td className="px-3 py-3 text-right text-sm text-cyan-400">
                  {session.auto_promoted}
                </td>
                <td className="px-3 py-3 text-right text-sm text-white/40">
                  {session.rejected}
                </td>
                <td className="px-3 py-3 text-center">
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-400/10 px-2 py-0.5 text-xs font-medium text-emerald-400">
                    <CheckCircle2 className="h-3 w-3" />
                    {session.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </GlassCard>
  )
}

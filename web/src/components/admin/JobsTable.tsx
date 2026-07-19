/**
 * JobsTable — glass table for scheduled jobs.
 * Columns: Type (with icon), Cron, Dernière exécution, Prochaine, Statut, Erreur.
 * Status badges: running = amber pulsing, succeeded = emerald, failed = rose, scheduled = cyan.
 */
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  Clock4,
  RefreshCw,
  Search,
  Timer,
  XCircle,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { SchedulerJobSchema } from '@/lib/types'
import { cn, formatDateTime } from '@/lib/utils'
import EmptyState from '@/components/ui/EmptyState'

interface JobsTableProps {
  jobs: SchedulerJobSchema[]
}

function jobIcon(type: string): LucideIcon {
  if (type.startsWith('crawl')) return Search
  if (type === 'refresh') return RefreshCw
  if (type === 'analytics') return BarChart3
  return Clock4
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { icon: LucideIcon; cls: string; pulse?: boolean }> = {
    running: { icon: Timer, cls: 'bg-amber-400/15 text-amber-600 dark:text-amber-300', pulse: true },
    succeeded: { icon: CheckCircle2, cls: 'bg-emerald-400/15 text-emerald-600 dark:text-emerald-300' },
    failed: { icon: XCircle, cls: 'bg-rose-400/15 text-rose-600 dark:text-rose-300' },
    scheduled: { icon: Clock4, cls: 'bg-prism-cyan/15 text-prism-cyan' },
  }
  const s = map[status] ?? map['scheduled']
  const Icon = s.icon
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
        s.cls,
        s.pulse && 'animate-pulse',
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {status}
    </span>
  )
}

export default function JobsTable({ jobs }: JobsTableProps) {
  if (jobs.length === 0) {
    return (
      <EmptyState
        icon={Clock4}
        title="Aucun job planifié"
        description="Les jobs planifiés apparaîtront ici. Ils sont gérés par le scheduler backend."
      />
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[800px] border-collapse">
        <thead>
          <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-white/40">
            <th className="px-4 py-3 font-medium">Type</th>
            <th className="px-4 py-3 font-medium">Cron</th>
            <th className="px-4 py-3 font-medium">Dernière exécution</th>
            <th className="px-4 py-3 font-medium">Prochaine</th>
            <th className="px-4 py-3 font-medium">Statut</th>
            <th className="px-4 py-3 font-medium">Erreur</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => {
            const Icon = jobIcon(job.job_type)
            return (
              <tr
                key={job.id}
                className="border-b border-white/5 transition hover:bg-white/[0.03]"
              >
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-2 text-sm text-white/80">
                    <Icon className="h-4 w-4 text-white/40" />
                    {job.job_type}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-white/60 font-mono">
                  {job.cron_expr || '—'}
                </td>
                <td className="px-4 py-3 text-sm text-white/60">
                  {formatDateTime(job.last_run)}
                </td>
                <td className="px-4 py-3 text-sm text-white/60">
                  {formatDateTime(job.next_run)}
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={job.status} />
                </td>
                <td className="px-4 py-3 text-sm">
                  {job.last_error ? (
                    <span
                      className="inline-flex items-center gap-1.5 text-rose-600 dark:text-rose-300"
                      title={job.last_error}
                    >
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                      <span className="max-w-[200px] truncate">{job.last_error}</span>
                    </span>
                  ) : (
                    <span className="text-white/30">—</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
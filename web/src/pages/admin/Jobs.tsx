/**
 * Jobs — crawl command center.
 * Source selector + live SSE crawl progress, results visualization,
 * crawl history, and scheduled jobs table.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { CalendarClock, RefreshCw } from 'lucide-react'
import { useJobs, useSources } from '@/hooks/useAdmin'
import { relativeTime } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import JobsTable from '@/components/admin/JobsTable'
import CrawlProgressPanel from '@/components/admin/CrawlProgressPanel'
import CrawlHistoryTable from '@/components/admin/CrawlHistoryTable'

export default function Jobs() {
  const jobsQ = useJobs()
  const sourcesQ = useSources()
  const [selectedSource, setSelectedSource] = useState<string | null>(null)

  const jobs = jobsQ.data ?? []
  const sources = sourcesQ.data ?? []

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-fg lg:text-3xl">
            <CalendarClock className="h-7 w-7 text-prism-violet" />
            Command Center
          </h1>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-white/40">
            <RefreshCw className="h-3.5 w-3.5" />
            Actualisé toutes les 30s · dernière sync {relativeTime(new Date(jobsQ.dataUpdatedAt).toISOString())}
          </p>
        </div>
      </motion.div>

      {/* Crawl Progress Panel — source selector + live SSE + results */}
      {sourcesQ.isLoading ? (
        <GlassCard>
          <div className="flex justify-center py-8">
            <Spinner size={28} />
          </div>
        </GlassCard>
      ) : (
        <CrawlProgressPanel
          sources={sources}
          onSourceChange={setSelectedSource}
        />
      )}

      {/* Crawl history for selected source */}
      <CrawlHistoryTable sourceSlug={selectedSource} />

      {/* Scheduled jobs table */}
      <GlassCard>
        <div className="mb-4 flex items-center gap-2">
          <CalendarClock className="h-5 w-5 text-white/50" />
          <h2 className="text-lg font-semibold text-fg">Jobs planifiés</h2>
          {!jobsQ.isLoading && (
            <span className="text-sm text-white/40">
              · {jobs.length} job{jobs.length !== 1 ? 's' : ''}
            </span>
          )}
        </div>
        {jobsQ.isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : jobsQ.isError ? (
          <EmptyState
            icon={CalendarClock}
            title="Erreur"
            description="Impossible de charger les jobs."
          />
        ) : jobs.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title="Aucun job"
            description="Les jobs planifiés apparaîtront ici."
          />
        ) : (
          <JobsTable jobs={jobs} />
        )}
      </GlassCard>
    </div>
  )
}

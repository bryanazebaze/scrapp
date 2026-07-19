/**
 * Pending — the review queue page.
 * usePendingReviews with pagination (limit 20).
 * PendingReviewTable in the middle.
 * On approve/reject → useReviewAction.mutateAsync.
 * Success toast (inline glass banner, auto-fades).
 * KPI row at top + "Voir sources" link.
 */
import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Check, ChevronLeft, ChevronRight, Clock, Globe, Inbox } from 'lucide-react'
import { usePendingReviews, useReviewAction } from '@/hooks/useAdmin'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'
import KpiCard from '@/components/admin/KpiCard'
import PendingReviewTable from '@/components/admin/PendingReviewTable'

const LIMIT = 20

export default function Pending() {
  const [skip, setSkip] = useState(0)
  const pendingQ = usePendingReviews(skip, LIMIT)
  const reviewAction = useReviewAction()

  const [toast, setToast] = useState<{ type: 'success' | 'error'; msg: string } | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const showToast = (type: 'success' | 'error', msg: string) => {
    setToast({ type, msg })
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }

  useEffect(() => {
    return () => {
      if (toastTimer.current) clearTimeout(toastTimer.current)
    }
  }, [])

  const handleApprove = async (id: number) => {
    try {
      await reviewAction.mutateAsync({ id, action: 'approve' })
      showToast('success', `Annonce #${id} approuvée.`)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Échec de l\'approbation')
    }
  }

  const handleReject = async (id: number) => {
    try {
      await reviewAction.mutateAsync({ id, action: 'reject' })
      showToast('success', `Annonce #${id} rejetée.`)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Échec du rejet')
    }
  }

  const items = pendingQ.data ?? []
  const loadingAction = reviewAction.isPending ? reviewAction.variables?.id ?? null : null

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
            <Clock className="h-7 w-7 text-prism-amber" />
            File d'attente
          </h1>
          <p className="mt-1 text-sm text-white/40">
            Annonces en attente de révision manuelle
          </p>
        </div>
        <Link to="/admin/sources">
          <GlassButton variant="outline" size="sm">
            <Globe className="h-4 w-4" />
            Voir sources
          </GlassButton>
        </Link>
      </motion.div>

      {/* KPI row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <KpiCard
          label="En attente (page)"
          value={items.length}
          sub={`skip ${skip} · limit ${LIMIT}`}
          icon={Inbox}
          accent="amber"
          loading={pendingQ.isLoading}
        />
        <KpiCard
          label="Actions effectuées"
          value={reviewAction.isSuccess ? 1 : 0}
          sub="cette session"
          icon={Check}
          accent="emerald"
          loading={false}
        />
        <KpiCard
          label="File totale (approx.)"
          value={skip + items.length}
          sub="estimation"
          icon={Clock}
          accent="violet"
          loading={pendingQ.isLoading}
        />
      </div>

      {/* Toast */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`rounded-xl border px-4 py-3 text-sm ${
              toast.type === 'success'
                ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-600 dark:text-emerald-300'
                : 'border-rose-400/20 bg-rose-400/10 text-rose-600 dark:text-rose-300'
            }`}
          >
            {toast.msg}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Table */}
      <GlassCard>
        {pendingQ.isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : pendingQ.isError ? (
          <div className="py-8 text-center text-sm text-rose-300">
            Erreur : {pendingQ.error instanceof Error ? pendingQ.error.message : 'inconnue'}
          </div>
        ) : (
          <PendingReviewTable
            items={items}
            onApprove={handleApprove}
            onReject={handleReject}
            loadingAction={loadingAction}
          />
        )}

        {/* Pagination */}
        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-white/40">
            {skip > 0 ? `À partir de ${skip}` : 'Première page'} · {items.length} affichés
          </span>
          <div className="flex gap-2">
            <GlassButton
              size="sm"
              variant="ghost"
              onClick={() => setSkip((s) => Math.max(0, s - LIMIT))}
              disabled={skip === 0 || pendingQ.isLoading}
            >
              <ChevronLeft className="h-4 w-4" />
              Précédent
            </GlassButton>
            <GlassButton
              size="sm"
              variant="ghost"
              onClick={() => setSkip((s) => s + LIMIT)}
              disabled={items.length < LIMIT || pendingQ.isLoading}
            >
              Suivant
              <ChevronRight className="h-4 w-4" />
            </GlassButton>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
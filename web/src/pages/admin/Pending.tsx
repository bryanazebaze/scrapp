/**
 * Pending — the review queue page.
 * Shows pending listings AND detected duplicates with side-by-side comparison.
 */
import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertCircle, Check, ChevronLeft, ChevronRight, Clock, Globe, Inbox } from 'lucide-react'
import { usePendingReviews, useReviewAction, useDuplicates, useValidateDuplicate } from '@/hooks/useAdmin'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'
import KpiCard from '@/components/admin/KpiCard'
import PendingReviewTable from '@/components/admin/PendingReviewTable'
import DuplicateReviewCard from '@/components/admin/DuplicateReviewCard'

const LIMIT = 20

export default function Pending() {
  const [skip, setSkip] = useState(0)
  const [dupSkip, setDupSkip] = useState(0)
  const pendingQ = usePendingReviews(skip, LIMIT)
  const reviewAction = useReviewAction()
  const duplicatesQ = useDuplicates(dupSkip, LIMIT)
  const validateDup = useValidateDuplicate()

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

  const handleConfirmDuplicate = async (id: number) => {
    try {
      await validateDup.mutateAsync({ id, action: 'confirm_duplicate' })
      showToast('success', `Doublon #${id} confirmé.`)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Échec de la validation')
    }
  }

  const handleNotDuplicate = async (id: number) => {
    try {
      await validateDup.mutateAsync({ id, action: 'not_duplicate' })
      showToast('success', `Annonce #${id} séparée — nouveau bien créé.`)
    } catch (err) {
      showToast('error', err instanceof Error ? err.message : 'Échec de la séparation')
    }
  }

  const items = pendingQ.data ?? []
  const dupItems = duplicatesQ.data ?? []
  const loadingAction = reviewAction.isPending ? reviewAction.variables?.id ?? null : null
  const dupLoadingAction = validateDup.isPending ? validateDup.variables?.id ?? null : null

  const pendingCount = items.length
  const dupCount = dupItems.length

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
            Annonces en attente de révision manuelle et doublons à valider
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
      <div className="grid gap-4 sm:grid-cols-4">
        <KpiCard
          label="En attente"
          value={pendingCount}
          sub={`page ${skip / LIMIT + 1}`}
          icon={Inbox}
          accent="amber"
          loading={pendingQ.isLoading}
        />
        <KpiCard
          label="Doublons détectés"
          value={dupCount}
          sub={`page ${dupSkip / LIMIT + 1}`}
          icon={AlertCircle}
          accent="amber"
          loading={duplicatesQ.isLoading}
        />
        <KpiCard
          label="Actions effectuées"
          value={(reviewAction.isSuccess ? 1 : 0) + (validateDup.isSuccess ? 1 : 0)}
          sub="cette session"
          icon={Check}
          accent="emerald"
          loading={false}
        />
        <KpiCard
          label="Total à traiter"
          value={pendingCount + dupCount}
          sub="en attente + doublons"
          icon={Clock}
          accent="violet"
          loading={pendingQ.isLoading || duplicatesQ.isLoading}
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

      {/* Pending listings table */}
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

      {/* Duplicates section */}
      {duplicatesQ.isLoading ? (
        <GlassCard>
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        </GlassCard>
      ) : duplicatesQ.isError ? null : dupItems.length > 0 ? (
        <div className="space-y-4">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h2 className="flex items-center gap-3 text-xl font-bold tracking-tight text-fg">
              <AlertCircle className="h-6 w-6 text-amber-400" />
              Doublons détectés
            </h2>
            <p className="mt-1 text-sm text-white/40">
              Comparez chaque annonce avec la propriété existante et confirmez ou infirmez le doublon.
            </p>
          </motion.div>

          {dupItems.map((item) => (
            <DuplicateReviewCard
              key={item.id}
              item={item}
              onConfirm={handleConfirmDuplicate}
              onNotDuplicate={handleNotDuplicate}
              loadingAction={dupLoadingAction}
            />
          ))}

          <div className="flex items-center justify-between">
            <span className="text-xs text-white/40">
              {dupSkip > 0 ? `À partir de ${dupSkip}` : 'Première page'} · {dupItems.length} affichés
            </span>
            <div className="flex gap-2">
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={() => setDupSkip((s) => Math.max(0, s - LIMIT))}
                disabled={dupSkip === 0 || duplicatesQ.isLoading}
              >
                <ChevronLeft className="h-4 w-4" />
                Précédent
              </GlassButton>
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={() => setDupSkip((s) => s + LIMIT)}
                disabled={dupItems.length < LIMIT || duplicatesQ.isLoading}
              >
                Suivant
                <ChevronRight className="h-4 w-4" />
              </GlassButton>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

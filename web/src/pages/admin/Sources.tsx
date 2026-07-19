/**
 * Sources — admin sources management.
 * useSources() → SourcesPanel.
 * "Créer une source" button opens Modal with form (slug, display_name, site_url, adapter_kind).
 * POST via api.post('/admin/sources', body) with try/catch.
 * "Recompute analytics" button.
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useQueryClient } from '@tanstack/react-query'
import { Check, Globe, Link2, Plus, Sparkles } from 'lucide-react'
import { useRecomputeAnalytics, useSources, useToggleSource } from '@/hooks/useAdmin'
import { useCrawlContext } from '@/contexts/CrawlContext'
import { api } from '@/lib/api'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Modal from '@/components/ui/Modal'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import SourcesPanel from '@/components/admin/SourcesPanel'

interface CreateSourceForm {
  slug: string
  display_name: string
  site_url: string
  adapter_kind: 'dedicated' | 'universal'
}

const EMPTY_FORM: CreateSourceForm = {
  slug: '',
  display_name: '',
  site_url: '',
  adapter_kind: 'dedicated',
}

export default function Sources() {
  const sourcesQ = useSources()
  const toggleMut = useToggleSource()
  const crawlCtx = useCrawlContext()
  const recompute = useRecomputeAnalytics()
  const qc = useQueryClient()

  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<CreateSourceForm>(EMPTY_FORM)
  const [creating, setCreating] = useState(false)
  const [createMsg, setCreateMsg] = useState<{ ok: boolean; msg: string } | null>(null)

  // Quick URL add state
  const [quickUrlOpen, setQuickUrlOpen] = useState(false)
  const [quickUrl, setQuickUrl] = useState('')
  const [quickAdding, setQuickAdding] = useState(false)
  const [quickMsg, setQuickMsg] = useState<{ ok: boolean; msg: string } | null>(null)

  const handleToggle = (slug: string) => {
    toggleMut.mutate(slug)
  }

  const handleCrawl = (slug: string) => {
    crawlCtx.startCrawl(slug)
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    setCreateMsg(null)
    try {
      await api.post('/admin/sources', form)
      setCreateMsg({ ok: true, msg: `Source « ${form.display_name} » créée avec succès.` })
      setForm(EMPTY_FORM)
      qc.invalidateQueries({ queryKey: ['sources'] })
      setTimeout(() => {
        setModalOpen(false)
        setCreateMsg(null)
      }, 1500)
    } catch (err) {
      setCreateMsg({
        ok: false,
        msg: err instanceof Error ? err.message : 'Échec de la création',
      })
    } finally {
      setCreating(false)
    }
  }

  const handleQuickUrl = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!quickUrl) return
    setQuickAdding(true)
    setQuickMsg(null)
    try {
      const parsed = new URL(quickUrl)
      const hostname = parsed.hostname.replace(/^www\./, '')
      const slug = hostname
        .replace(/[^a-z0-9]/g, '-')
        .replace(/-+/g, '-')
        .replace(/^-|-$/g, '')
        .slice(0, 60) || 'nouvelle-source'
      const displayName = hostname

      await api.post('/admin/sources', {
        slug,
        display_name: displayName,
        site_url: quickUrl,
        adapter_kind: 'universal',
        is_active: true,
        crawl_config: {},
      })
      setQuickMsg({ ok: true, msg: `Source universelle « ${displayName} » ajoutée.` })
      qc.invalidateQueries({ queryKey: ['sources'] })
      setTimeout(() => {
        setQuickUrlOpen(false)
        setQuickUrl('')
        setQuickMsg(null)
      }, 1500)
    } catch (err) {
      setQuickMsg({
        ok: false,
        msg: err instanceof Error ? err.message : 'Échec de l\'ajout',
      })
    } finally {
      setQuickAdding(false)
    }
  }

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
            <Globe className="h-7 w-7 text-prism-cyan" />
            Sources
          </h1>
          <p className="mt-1 text-sm text-white/40">
            Gérez les sources de crawl · {sourcesQ.data?.length ?? 0} source(s)
          </p>
        </div>
        <div className="flex gap-2">
          <GlassButton
            variant="outline"
            onClick={() => recompute.mutate()}
            disabled={recompute.isPending}
          >
            {recompute.isPending ? <Spinner size={16} /> : <Sparkles className="h-4 w-4" />}
            Recalculer analytics
          </GlassButton>
          <GlassButton variant="ghost" onClick={() => setQuickUrlOpen(true)}>
            <Link2 className="h-4 w-4" />
            Ajouter via URL
          </GlassButton>
          <GlassButton variant="primary" onClick={() => setModalOpen(true)}>
            <Plus className="h-4 w-4" />
            Créer une source
          </GlassButton>
        </div>
      </motion.div>

      {recompute.isSuccess && (
        <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-600 dark:text-emerald-300">
          Analytics recalculés.
        </div>
      )}

      {/* Sources panel */}
      {sourcesQ.isLoading ? (
        <div className="flex justify-center py-16"><Spinner size={32} /></div>
      ) : sourcesQ.isError ? (
        <GlassCard>
          <EmptyState
            icon={Globe}
            title="Erreur de chargement"
            description="Impossible de charger les sources."
          />
        </GlassCard>
      ) : sourcesQ.data && sourcesQ.data.length > 0 ? (
        <SourcesPanel
          sources={sourcesQ.data}
          onToggle={handleToggle}
          onCrawl={handleCrawl}
          pendingSlug={(crawlCtx.state.status === 'streaming' || crawlCtx.state.status === 'connecting') && crawlCtx.state.sourceSlug ? crawlCtx.state.sourceSlug : undefined}
        />
      ) : (
        <GlassCard>
          <EmptyState
            icon={Globe}
            title="Aucune source"
            description="Créez votre première source de crawl."
            action={
              <GlassButton variant="primary" onClick={() => setModalOpen(true)}>
                <Plus className="h-4 w-4" />
                Créer une source
              </GlassButton>
            }
          />
        </GlassCard>
      )}

      {/* Create source modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Créer une source" size="md">
        <form onSubmit={handleCreate} className="space-y-4">
          <FormField label="Slug" required>
            <input
              type="text"
              value={form.slug}
              onChange={(e) => setForm({ ...form, slug: e.target.value })}
              placeholder="ex: mapiole"
              required
              className="glass-input w-full"
            />
          </FormField>
          <FormField label="Nom d'affichage" required>
            <input
              type="text"
              value={form.display_name}
              onChange={(e) => setForm({ ...form, display_name: e.target.value })}
              placeholder="Mapiole"
              required
              className="glass-input w-full"
            />
          </FormField>
          <FormField label="URL du site" required>
            <input
              type="url"
              value={form.site_url}
              onChange={(e) => setForm({ ...form, site_url: e.target.value })}
              placeholder="https://exemple.com"
              required
              className="glass-input w-full"
            />
          </FormField>
          <FormField label="Type d'adaptateur" required>
            <select
              value={form.adapter_kind}
              onChange={(e) =>
                setForm({ ...form, adapter_kind: e.target.value as 'dedicated' | 'universal' })
              }
              className="glass-input w-full cursor-pointer"
            >
              <option value="dedicated" className="bg-ink-900">Dédié</option>
              <option value="universal" className="bg-ink-900">Universel</option>
            </select>
          </FormField>

          <AnimatePresence>
            {createMsg && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`rounded-xl border px-4 py-3 text-sm ${
                  createMsg.ok
                    ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-600 dark:text-emerald-300'
                    : 'border-rose-400/20 bg-rose-400/10 text-rose-600 dark:text-rose-300'
                }`}
              >
                {createMsg.ok && <Check className="mr-1 inline h-4 w-4" />}
                {createMsg.msg}
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex justify-end gap-2 pt-2">
            <GlassButton
              type="button"
              variant="ghost"
              onClick={() => setModalOpen(false)}
              disabled={creating}
            >
              Annuler
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={creating}>
              {creating ? <Spinner size={16} /> : <Plus className="h-4 w-4" />}
              Créer
            </GlassButton>
          </div>
        </form>
      </Modal>

      {/* Quick URL add modal */}
      <Modal open={quickUrlOpen} onClose={() => { setQuickUrlOpen(false); setQuickUrl(''); setQuickMsg(null) }} title="Ajouter une source via URL" size="md">
        <form onSubmit={handleQuickUrl} className="space-y-4">
          <FormField label="URL du site" required>
            <input
              type="url"
              value={quickUrl}
              onChange={(e) => setQuickUrl(e.target.value)}
              placeholder="https://exemple.com"
              required
              className="glass-input w-full"
            />
          </FormField>
          <p className="text-xs text-white/40">
            Le type d'adaptateur sera défini sur <strong>universel</strong>.
            Le slug et le nom seront générés automatiquement à partir du domaine.
          </p>

          <AnimatePresence>
            {quickMsg && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`rounded-xl border px-4 py-3 text-sm ${
                  quickMsg.ok
                    ? 'border-emerald-400/20 bg-emerald-400/10 text-emerald-600 dark:text-emerald-300'
                    : 'border-rose-400/20 bg-rose-400/10 text-rose-600 dark:text-rose-300'
                }`}
              >
                {quickMsg.ok && <Check className="mr-1 inline h-4 w-4" />}
                {quickMsg.msg}
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex justify-end gap-2 pt-2">
            <GlassButton
              type="button"
              variant="ghost"
              onClick={() => { setQuickUrlOpen(false); setQuickUrl(''); setQuickMsg(null) }}
              disabled={quickAdding}
            >
              Annuler
            </GlassButton>
            <GlassButton type="submit" variant="primary" disabled={quickAdding || !quickUrl}>
              {quickAdding ? <Spinner size={16} /> : <Link2 className="h-4 w-4" />}
              Ajouter
            </GlassButton>
          </div>
        </form>
      </Modal>
    </div>
  )
}

function FormField({
  label,
  required,
  children,
}: {
  label: string
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div>
      <label className="mb-1.5 block text-xs uppercase tracking-wider text-white/40">
        {label}{required && <span className="ml-0.5 text-rose-400">*</span>}
      </label>
      {children}
    </div>
  )
}
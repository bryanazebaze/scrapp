/**
 * CrawlProgressPanel — live crawl view using global CrawlContext.
 * Shows source selector, SSE progress, inline listing cards with
 * raw payload/HTML, and post-crawl results summary.
 * Shared state means Sources and Jobs pages stay in sync.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Code2,
  ExternalLink,
  Globe,
  Image,
  MapPin,
  Play,
  RefreshCw,
  Search,
  Square,
  Timer,
  Trash2,
  XCircle,
} from 'lucide-react'
import type { SourceSchema } from '@/lib/types'
import { useCrawlContext, CrawlListing } from '@/contexts/CrawlContext'
import { cn, formatXAF, relativeTime } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'

interface CrawlProgressPanelProps {
  sources: SourceSchema[]
  onSourceChange?: (slug: string | null) => void
}

export default function CrawlProgressPanel({ sources, onSourceChange }: CrawlProgressPanelProps) {
  const activeSources = sources.filter((s) => s.is_active)
  const { state, startCrawl, stopCrawl } = useCrawlContext()

  const [selectedSlug, setSelectedSlug] = useState<string>(
    activeSources[0]?.slug ?? ''
  )
  const [maxPages, setMaxPages] = useState(1)
  const [elapsed, setElapsed] = useState(0)
  const [showListings, setShowListings] = useState(true)
  const [expandedListing, setExpandedListing] = useState<number | null>(null)
  const [viewMode, setViewMode] = useState<'cards' | 'raw' | 'rendered'>('cards')

  useEffect(() => {
    if (activeSources[0]?.slug) {
      onSourceChange?.(activeSources[0].slug)
    }
  }, [])

  // Elapsed timer
  useEffect(() => {
    if (state.status !== 'streaming' && state.status !== 'connecting') {
      setElapsed(0)
      return
    }
    const start = Date.now()
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000))
    }, 1000)
    return () => clearInterval(interval)
  }, [state.status])

  const handleStartCrawl = (testMode = true) => {
    if (!selectedSlug) return
    onSourceChange?.(selectedSlug)
    setExpandedListing(null)
    startCrawl(selectedSlug, testMode, maxPages)
  }

  const isRunning = state.status === 'connecting' || state.status === 'streaming'

  return (
    <div className="space-y-4">
      {/* Source selector + buttons */}
      <GlassCard>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="mb-1.5 block text-xs uppercase tracking-wider text-white/40">
              Source
            </label>
            <select
              value={selectedSlug}
              onChange={(e) => {
                setSelectedSlug(e.target.value)
                onSourceChange?.(e.target.value)
              }}
              disabled={isRunning}
              className="glass-input w-full cursor-pointer"
            >
              {activeSources.length === 0 && (
                <option value="" className="bg-ink-900">Aucune source active</option>
              )}
              {activeSources.map((s) => (
                <option key={s.slug} value={s.slug} className="bg-ink-900">
                  {s.display_name} ({s.adapter_kind === 'dedicated' ? 'Dédié' : 'Universel'})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="mb-1.5 block text-xs uppercase tracking-wider text-white/40">
              Pages
            </label>
            <input
              type="number"
              min={1}
              max={50}
              value={maxPages}
              onChange={(e) => setMaxPages(Math.max(1, parseInt(e.target.value) || 1))}
              disabled={isRunning}
              className="glass-input w-20 text-center"
            />
          </div>
          <div className="flex gap-2">
            {isRunning ? (
              <GlassButton variant="ghost" onClick={stopCrawl}>
                <Square className="h-4 w-4 text-rose-400" />
                Arrêter
              </GlassButton>
            ) : (
              <>
                <GlassButton
                  variant="primary"
                  onClick={() => handleStartCrawl(true)}
                  disabled={!selectedSlug || activeSources.length === 0}
                >
                  <Play className="h-4 w-4" />
                  Test crawl
                </GlassButton>
                <GlassButton
                  variant="outline"
                  onClick={() => handleStartCrawl(false)}
                  disabled={!selectedSlug || activeSources.length === 0}
                  title="Crawl avec persistence DB"
                >
                  <Play className="h-4 w-4" />
                  Crawl réel
                </GlassButton>
              </>
            )}
          </div>
        </div>
      </GlassCard>

      {/* Live progress */}
      <AnimatePresence>
        {state.status !== 'idle' && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
            <GlassCard>
              {/* Connecting */}
              {state.status === 'connecting' && (
                <div className="flex items-center gap-3 py-4">
                  <Spinner size={24} />
                  <div>
                    <p className="text-sm font-medium text-fg">Connexion au flux SSE...</p>
                    <p className="text-xs text-white/40">Démarrage du crawl pour {state.sourceSlug}</p>
                  </div>
                </div>
              )}

              {/* Streaming / Done */}
              {(state.status === 'streaming' || state.status === 'done') && (
                <div className="space-y-4">
                  {/* Header */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {state.status === 'done' ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                      ) : (
                        <Spinner size={20} />
                      )}
                      <span className="text-sm font-medium text-fg">
                        {state.status === 'done' ? 'Crawl terminé' : `Crawl en cours — ${state.sourceSlug}`}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-white/40">
                      <span className="flex items-center gap-1">
                        <Timer className="h-3.5 w-3.5" />
                        {Math.floor(elapsed / 60)}m {elapsed % 60}s
                      </span>
                      <span>Page {state.currentPage || '—'}</span>
                      <span>{state.listingsFound} annonces</span>
                    </div>
                  </div>

                  {/* Progress bar */}
                  {state.status === 'streaming' && (
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-brand-500 to-prism-amber"
                        animate={{ width: ['0%', '60%', '80%', '95%'] }}
                        transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
                      />
                    </div>
                  )}
                  {state.status === 'done' && (
                    <div className="h-1.5 overflow-hidden rounded-full bg-emerald-400/20">
                      <div className="h-full w-full rounded-full bg-emerald-400" />
                    </div>
                  )}

                  {state.message && <p className="text-sm text-white/60">{state.message}</p>}

                  {/* Results summary */}
                  {state.status === 'done' && (
                    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                      <ResultCard label="Annonces" value={state.listingsFound} icon={Globe} accent="cyan" />
                      <ResultCard label="Nouveaux" value={state.newListings} icon={CheckCircle2} accent="emerald" />
                      <ResultCard label="Re-crawls" value={state.recrawl} icon={RefreshCw} accent="violet" />
                      <ResultCard label="Doublons" value={state.duplicates} icon={Search} accent="amber" />
                      <ResultCard label="En attente" value={state.pendingCount} icon={Timer} accent="fuchsia"
                        linkTo={state.pendingCount > 0 ? '/admin/file-attente' : undefined} />
                      <ResultCard label="Retirés" value={state.removed} icon={Trash2} accent="rose" />
                    </div>
                  )}

                  {/* Listing data display */}
                  {state.listings.length > 0 && (
                    <div className="border-t border-white/5 pt-4">
                      <div className="mb-3 flex items-center justify-between">
                        <button
                          onClick={() => setShowListings(!showListings)}
                          className="flex items-center gap-2 text-sm font-medium text-fg hover:text-white/80"
                        >
                          {showListings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                          Données du crawl ({state.listings.length} annonces)
                        </button>
                        <div className="flex gap-1 rounded-lg bg-white/5 p-0.5">
                          {(['cards', 'raw', 'rendered'] as const).map((mode) => (
                            <button
                              key={mode}
                              onClick={() => setViewMode(mode)}
                              className={cn(
                                'rounded-md px-3 py-1 text-xs font-medium transition',
                                viewMode === mode ? 'bg-white/10 text-fg' : 'text-white/40 hover:text-white/70'
                              )}
                            >
                              {mode === 'cards' ? 'Résumé' : mode === 'raw' ? 'Brut' : 'Rendu'}
                            </button>
                          ))}
                        </div>
                      </div>

                      <AnimatePresence>
                        {showListings && (
                          <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="overflow-hidden"
                          >
                            {/* Cards view */}
                            {viewMode === 'cards' && (
                              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                                {state.listings.map((listing) => (
                                  <ListingCard
                                    key={listing.index}
                                    listing={listing}
                                    expanded={expandedListing === listing.index}
                                    onToggle={() =>
                                      setExpandedListing(expandedListing === listing.index ? null : listing.index)
                                    }
                                  />
                                ))}
                              </div>
                            )}

                            {/* Raw JSON view */}
                            {viewMode === 'raw' && (
                              <div className="max-h-[600px] overflow-auto rounded-xl bg-ink-900/60">
                                <pre className="p-4 text-xs text-white/60 font-mono whitespace-pre-wrap">
                                  {JSON.stringify(state.listings, null, 2)}
                                </pre>
                              </div>
                            )}

                            {/* Rendered HTML view */}
                            {viewMode === 'rendered' && (
                              <div className="max-h-[600px] overflow-auto rounded-xl bg-ink-900/60 p-4">
                                {state.listings.map((listing) => (
                                  <div key={listing.index} className="mb-6 border-b border-white/10 pb-6 last:border-0">
                                    <div className="mb-2 flex items-start justify-between">
                                      <h4 className="text-sm font-semibold text-fg">
                                        #{listing.index} — {listing.title_raw || 'Sans titre'}
                                      </h4>
                                      <span className="text-sm font-bold text-emerald-400">
                                        {formatXAF(listing.price_parsed)}
                                      </span>
                                    </div>
                                    <div className="space-y-2 text-sm text-white/60">
                                      <p className="flex items-center gap-1">
                                        <MapPin className="h-3.5 w-3.5 text-white/30" />
                                        {listing.location_raw || '—'}
                                      </p>
                                      <p>{listing.description_raw || 'Pas de description'}</p>
                                      <p className="text-xs text-white/40">
                                        Type: {listing.property_type_raw || '—'} · Source: {listing.url_source}
                                      </p>
                                      {listing.images_raw && listing.images_raw.length > 0 && (
                                        <div className="flex gap-2 overflow-x-auto pt-2">
                                          {listing.images_raw.slice(0, 5).map((img, i) => (
                                            <img
                                              key={i}
                                              src={img}
                                              alt={`Photo ${i + 1}`}
                                              className="h-16 w-16 rounded-lg object-cover"
                                              onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                                            />
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            )}
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  )}
                </div>
              )}

              {/* Error */}
              {state.status === 'error' && (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <XCircle className="h-5 w-5 text-rose-400" />
                    <span className="text-sm font-medium text-rose-300">Erreur de crawl</span>
                  </div>
                  <p className="text-sm text-rose-400/80">{state.error}</p>
                  <GlassButton size="sm" variant="ghost" onClick={stopCrawl}>Réessayer</GlassButton>
                </div>
              )}
            </GlassCard>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ---------- Listing card ---------- */
function ListingCard({
  listing,
  expanded,
  onToggle,
}: {
  listing: CrawlListing
  expanded: boolean
  onToggle: () => void
}) {
  return (
    <div className={cn('rounded-xl border border-white/10 bg-white/[0.02] p-3 transition', expanded && 'border-white/20 bg-white/[0.04]')}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <button onClick={onToggle} className="text-left hover:text-fg">
            <p className="truncate text-xs font-medium text-white/80">
              #{listing.index} — {listing.title_raw || 'Sans titre'}
            </p>
          </button>
          <p className="mt-0.5 text-xs text-white/40 truncate">{listing.location_raw || '—'}</p>
        </div>
        <span className="shrink-0 text-xs font-semibold text-emerald-400">
          {formatXAF(listing.price_parsed)}
        </span>
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 overflow-hidden space-y-3"
          >
            {/* Images */}
            {listing.images_raw && listing.images_raw.length > 0 && (
              <div className="flex gap-1.5 overflow-x-auto pb-1">
                {listing.images_raw.slice(0, 6).map((img, i) => (
                  <img
                    key={i}
                    src={img}
                    alt={`Photo ${i + 1}`}
                    className="h-14 w-14 shrink-0 rounded-lg object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }}
                  />
                ))}
              </div>
            )}

            {/* Details */}
            <div className="space-y-1 text-xs text-white/50">
              <p><span className="text-white/30">Type:</span> {listing.property_type_raw || '—'}</p>
              <p><span className="text-white/30">Prix brut:</span> {listing.price_raw || '—'}</p>
              <p className="truncate">
                <span className="text-white/30">URL:</span>{' '}
                <a href={listing.url_source || '#'} target="_blank" rel="noopener noreferrer"
                   className="text-prism-cyan hover:underline">
                  {listing.url_source} <ExternalLink className="inline h-3 w-3" />
                </a>
              </p>
            </div>

            {/* Description */}
            {listing.description_raw && (
              <p className="text-xs text-white/60 line-clamp-3">{listing.description_raw}</p>
            )}

            {/* Raw payload toggle */}
            {listing.payload && Object.keys(listing.payload).length > 0 && (
              <details className="text-xs">
                <summary className="cursor-pointer text-white/40 hover:text-white/70 flex items-center gap-1">
                  <Code2 className="h-3.5 w-3.5" />
                  Payload brut ({Object.keys(listing.payload).length} champs)
                </summary>
                <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-ink-900/80 p-2 text-xs text-white/50 font-mono">
                  {JSON.stringify(listing.payload, null, 2)}
                </pre>
              </details>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      <button
        onClick={onToggle}
        className="mt-2 flex w-full items-center justify-center gap-1 text-xs text-white/30 hover:text-white/60"
      >
        {expanded ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
        {expanded ? 'Moins' : 'Détails'}
      </button>
    </div>
  )
}

/* ---------- Result card ---------- */
function ResultCard({
  label, value, icon: Icon, accent, linkTo,
}: {
  label: string; value: number; icon: typeof Globe
  accent: 'emerald' | 'amber' | 'fuchsia' | 'cyan' | 'violet' | 'rose'
  linkTo?: string
}) {
  const accentMap: Record<string, string> = {
    emerald: 'text-emerald-400 bg-emerald-400/10 border-emerald-400/20',
    amber: 'text-amber-400 bg-amber-400/10 border-amber-400/20',
    fuchsia: 'text-fuchsia-400 bg-fuchsia-400/10 border-fuchsia-400/20',
    cyan: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/20',
    violet: 'text-violet-400 bg-violet-400/10 border-violet-400/20',
    rose: 'text-rose-400 bg-rose-400/10 border-rose-400/20',
  }

  const content = (
    <div className={cn('rounded-xl border p-4', accentMap[accent])}>
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider opacity-70">{label}</span>
        <Icon className="h-4 w-4 opacity-60" />
      </div>
      <p className="mt-1 text-2xl font-bold">{value}</p>
    </div>
  )

  if (linkTo) {
    return <Link to={linkTo} className="block transition hover:opacity-80">{content}</Link>
  }
  return content
}

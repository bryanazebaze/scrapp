import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { motion } from 'framer-motion'
import {
  Bed, Bath, Maximize, MapPin, Globe, Shield,
  TrendingUp, ArrowLeft,
} from 'lucide-react'
import { api } from '@/lib/api'
import type {
  AnnonceDetaillee, ListingHistoryEvent, AnnonceBreve, PriceAnalyse,
} from '@/lib/types'
import { formatXAF, formatNumber, formatDate, verdictLabel, verdictColor, cn } from '@/lib/utils'
import { useNeighborhoodAnalytics } from '@/hooks/useNeighborhoods'
import ListingGallery from '@/components/listings/ListingGallery'
import ListingGrid from '@/components/listings/ListingGrid'
import ScorePanel from '@/components/listings/ScorePanel'
import NeighborhoodProfilePanel from '@/components/listings/NeighborhoodProfilePanel'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Badge from '@/components/ui/Badge'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import PriceHistoryChart from '@/components/charts/PriceHistoryChart'
import Footer from '@/components/layout/Footer'

// --- Inline hooks (these endpoints don't have dedicated hook files yet) ---
function useListing(id: string | undefined) {
  return useQuery<AnnonceDetaillee>({
    enabled: !!id,
    queryKey: ['listing', id],
    queryFn: () => api.get(`/annonces/${id}`),
  })
}

function useListingHistory(id: string | undefined) {
  return useQuery<ListingHistoryEvent[]>({
    enabled: !!id,
    queryKey: ['listing-history', id],
    queryFn: () => api.get(`/annonces/${id}/history`),
  })
}

function useSimilarListings(id: string | undefined) {
  return useQuery<AnnonceBreve[]>({
    enabled: !!id,
    queryKey: ['similar', id],
    queryFn: () => api.get(`/annonces/${id}/similar`),
  })
}

function usePriceAnalysis(id: string | undefined) {
  return useQuery<PriceAnalyse>({
    enabled: !!id,
    queryKey: ['price-analysis', id],
    queryFn: () => api.get(`/annonces/${id}/analyse`),
  })
}

export default function ListingDetail() {
  const { id } = useParams<{ id: string }>()
  const listing = useListing(id)
  const history = useListingHistory(id)
  const similar = useSimilarListings(id)
  const analysis = usePriceAnalysis(id)
  const analytics = useNeighborhoodAnalytics(listing.data?.location_slug ?? undefined)

  if (listing.isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-4">
        <Spinner size={40} label="Chargement de l'annonce..." />
      </div>
    )
  }

  if (listing.isError || !listing.data) {
    return (
      <div className="px-4 pb-20">
        <EmptyState
          title="Annonce introuvable"
          description="Cette annonce n'existe pas ou a été supprimée."
        />
        <div className="mt-4 text-center">
          <Link to="/recherche" className="text-sm text-brand-500 hover:underline">
            ← Retour à la recherche
          </Link>
        </div>
      </div>
    )
  }

  const l = listing.data

  return (
    <div className="px-4 pb-6">
      <div className="mx-auto max-w-7xl">
        {/* Back link */}
        <Link
          to="/recherche"
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-white/50 transition hover:text-fg"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden="true" />
          Retour
        </Link>

        <div className="grid gap-6 lg:grid-cols-[1fr_400px]">
          {/* Left column */}
          <div className="space-y-6 min-w-0">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <ListingGallery images={l.images} />
            </motion.div>

            <GlassCard className="space-y-3">
              <h1 className="text-xl font-bold text-fg sm:text-2xl break-words">{l.title}</h1>
              {l.description ? (
                <div className="prose prose-sm dark:prose-invert max-w-none text-sm text-fg/80">
                  <p className="whitespace-pre-wrap break-words">{l.description}</p>
                </div>
              ) : (
                <p className="text-sm text-white/40">Aucune description disponible.</p>
              )}
            </GlassCard>

            {/* Price history */}
            <GlassCard className="space-y-4">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-fg">
                <TrendingUp className="h-5 w-5 text-brand-500" aria-hidden="true" />
                Historique des prix
              </h2>
              {history.isLoading ? (
                <Spinner label="Chargement..." />
              ) : history.isError || !history.data || history.data.length === 0 ? (
                <p className="text-sm text-white/40">Aucun historique disponible.</p>
              ) : (
                <PriceHistoryChart events={history.data} />
              )}
            </GlassCard>

            {/* Neighborhood Profile */}
            {analytics.data?.location_id && (
              <NeighborhoodProfilePanel locationId={analytics.data.location_id} />
            )}
          </div>

          {/* Right column - sticky */}
          <div className="space-y-6 min-w-0">
            <div className="sticky top-6 space-y-4">
              <GlassCard className="space-y-4">
                {/* Price */}
                <div>
                  <p className="text-xs uppercase tracking-wider text-white/40">Prix</p>
                  <p className="text-3xl font-bold text-fg">{formatXAF(l.price)}</p>
                </div>

                {/* Verdict */}
                {analysis.data && (
                  <div className="rounded-xl bg-white/5 p-3">
                    <p className="text-xs text-white/40">Analyse du marché</p>
                    <p className={cn('text-sm font-medium', verdictColor(analysis.data.verdict))}>
                      {verdictLabel(analysis.data.verdict)}
                    </p>
                    {analysis.data.savings != null &&
                      (analysis.data.verdict === 'below_market' ||
                        analysis.data.verdict === 'above_market') && (
                        <p
                          className={cn(
                            'mt-1 text-sm font-semibold',
                            analysis.data.verdict === 'below_market'
                              ? 'text-emerald-400'
                              : 'text-rose-400',
                          )}
                        >
                          {analysis.data.verdict === 'below_market'
                            ? `Vous économisez ${formatXAF(Math.abs(analysis.data.savings))}${
                                analysis.data.comparison_metric === 'price_per_sqm' ? '/m²' : ''
                              }`
                            : `Vous payez ${formatXAF(Math.abs(analysis.data.savings))}${
                                analysis.data.comparison_metric === 'price_per_sqm' ? '/m²' : ''
                              } de plus`}
                        </p>
                      )}
                    {analysis.data.summary && (
                      <p className="mt-1 text-xs text-white/50">{analysis.data.summary}</p>
                    )}
                    {analysis.data.fallback_level === 'city' && (
                      <p className="mt-1 text-xs text-white/30">
                        Comparaison basée sur la ville
                      </p>
                    )}
                  </div>
                )}

                {/* Chips */}
                <div className="flex flex-wrap gap-2">
                  {l.bedrooms != null && (
                    <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-sm text-white/70">
                      <Bed className="h-4 w-4" aria-hidden="true" />
                      {formatNumber(l.bedrooms)} ch.
                    </span>
                  )}
                  {l.bathrooms != null && (
                    <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-sm text-white/70">
                      <Bath className="h-4 w-4" aria-hidden="true" />
                      {formatNumber(l.bathrooms)} sdb.
                    </span>
                  )}
                  {l.area_sqm != null && (
                    <span className="inline-flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-sm text-white/70">
                      <Maximize className="h-4 w-4" aria-hidden="true" />
                      {formatNumber(l.area_sqm)} m²
                    </span>
                  )}
                </div>

                {/* Location */}
                {(l.city || l.neighborhood) && (
                  <div className="flex items-start gap-2 rounded-xl bg-white/5 p-3">
                    <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" aria-hidden="true" />
                    <div>
                      <p className="text-sm text-fg">{l.neighborhood || '—'}</p>
                      <p className="text-xs text-white/50">{l.city || '—'}</p>
                      {l.lat != null && l.lng != null && (
                        <p className="mt-1 text-xs text-white/30">
                          {l.lat.toFixed(4)}, {l.lng.toFixed(4)}
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* Voir offre — link to original source */}
                {l.sources.length > 0 && (
                  <a
                    href={l.sources[0].url_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <GlassButton
                      variant="primary"
                      size="lg"
                      className="w-full"
                      type="button"
                    >
                      <Globe className="h-4 w-4" aria-hidden="true" />
                      Voir offre
                    </GlassButton>
                  </a>
                )}

                {/* Match confidence */}
                {l.match_confidence != null && (
                  <div className="flex items-center gap-2">
                    <Shield className="h-4 w-4 text-white/40" aria-hidden="true" />
                    <span className="text-xs text-white/40">Confiance: </span>
                    <Badge
                      color={l.match_confidence >= 0.75 ? 'emerald' : l.match_confidence >= 0.4 ? 'amber' : 'rose'}
                      variant="soft"
                    >
                      {(l.match_confidence * 100).toFixed(0)}%
                    </Badge>
                  </div>
                )}

                {/* Dates */}
                {l.created_at && (
                  <p className="text-xs text-white/30">
                    Vu le {formatDate(l.created_at)}
                  </p>
                )}
              </GlassCard>

              {/* Score panel */}
              {analytics.data && <ScorePanel analytics={analytics.data} />}
            </div>
          </div>
        </div>

        {/* Similar listings */}
        <section className="mt-10">
          <h2 className="mb-4 text-xl font-semibold text-fg">Biens similaires</h2>
          {similar.isLoading ? (
            <Spinner label="Chargement..." />
          ) : similar.isError || !similar.data || similar.data.length === 0 ? (
            <p className="text-sm text-white/40">Aucun bien similaire trouvé.</p>
          ) : (
            <ListingGrid listings={similar.data.slice(0, 4)} />
          )}
        </section>
      </div>

      <Footer />
    </div>
  )
}
import { useSearchParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MapPin, Search, ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { useNeighborhoods, useNeighborhoodAnalytics, useCityNeighborhoods } from '@/hooks/useNeighborhoods'
import { formatXAF, percent, cn } from '@/lib/utils'
import ScorePanel from '@/components/listings/ScorePanel'
import NeighborhoodProfilePanel from '@/components/listings/NeighborhoodProfilePanel'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import Footer from '@/components/layout/Footer'

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  visible: { opacity: 1, y: 0 },
}

export default function NeighborhoodsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const slug = searchParams.get('slug') ?? undefined
  const city = searchParams.get('city') ?? undefined

  const allNeighborhoods = useNeighborhoods()
  const analytics = useNeighborhoodAnalytics(slug)
  const cityNeighborhoods = useCityNeighborhoods(city)

  // --- Detail view (slug present) ---
  if (slug) {
    return (
      <div className="px-4 pb-6">
        <div className="mx-auto max-w-5xl">
          <Link
            to="/quartiers"
            className="mb-4 inline-flex items-center gap-1.5 text-sm text-white/50 transition hover:text-fg"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Tous les quartiers
          </Link>

          {analytics.isLoading ? (
            <div className="flex justify-center py-20">
              <Spinner size={40} label="Chargement..." />
            </div>
          ) : analytics.isError || !analytics.data ? (
            <EmptyState
              title="Quartier introuvable"
              description="Les données pour ce quartier ne sont pas disponibles."
            />
          ) : (
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              transition={{ duration: 0.4 }}
              className="space-y-6"
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-bold text-fg">
                    {analytics.data.neighborhood || analytics.data.city}
                  </h1>
                  <p className="flex items-center gap-1 text-sm text-white/50">
                    <MapPin className="h-4 w-4" aria-hidden="true" />
                    {analytics.data.city}
                  </p>
                </div>
                <Link to={`/recherche?city=${encodeURIComponent(analytics.data.neighborhood || analytics.data.city)}`}>
                  <GlassButton variant="primary" size="sm">
                    Biens dans ce quartier
                  </GlassButton>
                </Link>
              </div>

              <ScorePanel analytics={analytics.data} />
              
              <NeighborhoodProfilePanel locationId={analytics.data.location_id} />
            </motion.div>
          )}
        </div>
        <Footer />
      </div>
    )
  }

  // --- City view (city param present) ---
  if (city) {
    return (
      <div className="px-4 pb-6">
        <div className="mx-auto max-w-7xl">
          <Link
            to="/quartiers"
            className="mb-4 inline-flex items-center gap-1.5 text-sm text-white/50 transition hover:text-fg"
          >
            <ArrowLeft className="h-4 w-4" aria-hidden="true" />
            Tous les quartiers
          </Link>

          <h1 className="mb-5 text-2xl font-bold text-fg">
            Quartiers de {city}
          </h1>

          {cityNeighborhoods.isLoading ? (
            <div className="flex justify-center py-20">
              <Spinner size={40} label="Chargement..." />
            </div>
          ) : cityNeighborhoods.isError ? (
            <EmptyState
              title="Erreur"
              description="Impossible de charger les quartiers de cette ville."
            />
          ) : !cityNeighborhoods.data || cityNeighborhoods.data.length === 0 ? (
            <EmptyState
              title="Aucun quartier"
              description={`Aucune donnée disponible pour ${city}.`}
            />
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {cityNeighborhoods.data.map((n, i) => (
                <motion.div
                  key={n.slug}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                >
                  <Link to={`/quartiers?slug=${n.slug}`}>
                    <GlassCard hover className="space-y-3">
                      <h3 className="font-semibold text-fg">
                        {n.neighborhood || n.city}
                      </h3>
                      <p className="text-xs text-white/50">{n.city}</p>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white/40">Prix médian</span>
                        <span className="font-medium text-fg">
                          {formatXAF(n.median_price)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white/40">Tendance</span>
                        <span
                          className={cn(
                            'font-medium',
                            n.trend_direction === 'up'
                              ? 'text-emerald-500'
                              : n.trend_direction === 'down'
                                ? 'text-rose-500'
                                : 'text-fg/50',
                          )}
                        >
                          {percent(n.trend_pct)}
                        </span>
                      </div>
                      <p className="text-xs text-white/40">{n.listing_count} bien(s)</p>
                    </GlassCard>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
        <Footer />
      </div>
    )
  }

  // --- Default: all neighborhoods ---
  const filtered = (allNeighborhoods.data ?? []).filter((n) => {
    if (!search) return true
    const q = search.toLowerCase()
    return (
      n.city.toLowerCase().includes(q) ||
      (n.neighborhood?.toLowerCase().includes(q) ?? false)
    )
  })

  return (
    <div className="px-4 py-6">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          transition={{ duration: 0.4 }}
        >
          <h1 className="mb-5 text-2xl font-bold text-fg">Quartiers</h1>
        </motion.div>

        {/* Search */}
        <div className="mb-6">
          <div className="glass flex items-center gap-2 rounded-2xl p-2">
            <Search className="ml-2 h-5 w-5 text-white/40" aria-hidden="true" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher un quartier ou une ville..."
              className="flex-1 bg-transparent px-2 py-2 text-sm text-fg placeholder-white/40 outline-none"
              aria-label="Rechercher un quartier"
            />
          </div>
        </div>

        {allNeighborhoods.isLoading ? (
          <div className="flex justify-center py-20">
            <Spinner size={40} label="Chargement des quartiers..." />
          </div>
        ) : allNeighborhoods.isError ? (
          <EmptyState
            title="Erreur"
            description="Impossible de charger les quartiers."
          />
        ) : filtered.length === 0 ? (
          <EmptyState
            title="Aucun quartier trouvé"
            description="Essayez un autre terme de recherche."
          />
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filtered.map((n, i) => (
              <motion.div
                key={n.id}
                initial="hidden"
                animate="visible"
                variants={fadeUp}
                transition={{ duration: 0.3, delay: i * 0.03 }}
              >
                <Link to={`/quartiers?slug=${n.slug}`}>
                  <GlassCard hover className="space-y-3">
                    <div className="flex items-start gap-2">
                      <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-brand-500" aria-hidden="true" />
                      <div>
                        <h3 className="font-semibold text-fg">
                          {n.neighborhood || n.city}
                        </h3>
                        <p className="text-xs text-white/50">{n.city}</p>
                      </div>
                    </div>
                    <p className="text-sm text-brand-500">Voir l'analyse →</p>
                  </GlassCard>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  )
}
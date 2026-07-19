import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Search, TrendingUp, MapPin, ArrowRight, Building2 } from 'lucide-react'
import { useListings } from '@/hooks/useListings'
import { useTrendingNeighborhoods } from '@/hooks/useNeighborhoods'
import { useCities } from '@/hooks/useProfiles'
import { formatXAF, percent, cn } from '@/lib/utils'
import ListingGrid from '@/components/listings/ListingGrid'
import Spinner from '@/components/ui/Spinner'
import GlassCard from '@/components/ui/GlassCard'
import Footer from '@/components/layout/Footer'

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

export default function Home() {
  const navigate = useNavigate()
  const [searchValue, setSearchValue] = useState('')

  const trending = useTrendingNeighborhoods(6)
  const listings = useListings({ limit: 8 })
  const cities = useCities()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchValue.trim()) {
      navigate(`/recherche?q=${encodeURIComponent(searchValue.trim())}`)
    }
  }

  return (
    <div>
      {/* Hero */}
      <section className="relative px-4 pt-4 pb-12 sm:pt-10">
        <div className="mx-auto max-w-4xl text-center">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-balance text-4xl font-bold tracking-tight text-fg sm:text-5xl lg:text-6xl">
              Trouvez le{' '}
              <span className="prism-text italic">bon</span> logement au Cameroun
            </h1>
          </motion.div>

          <motion.p
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mx-auto mt-4 max-w-2xl text-balance text-base text-white/60 sm:text-lg"
          >
            Agrégez toutes les annonces immobilières en un seul lieu. Comparez les
            prix, explorez les quartiers, prenez des décisions éclairées.
          </motion.p>

          {/* Search bar */}
          <motion.form
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            transition={{ duration: 0.5, delay: 0.2 }}
            onSubmit={handleSearch}
            className="mx-auto mt-8 max-w-2xl"
          >
            <div className="glass-strong flex items-center gap-2 rounded-2xl p-2">
              <Search className="ml-2 h-5 w-5 shrink-0 text-white/40" aria-hidden="true" />
              <input
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                placeholder="Ex: 3 chambres à Bonamoussadi moins de 100k..."
                className="flex-1 bg-transparent px-2 py-2 text-sm text-fg placeholder-white/40 outline-none"
                aria-label="Rechercher un bien immobilier"
              />
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-brand-400 px-5 py-2.5 text-sm font-medium text-white transition hover:shadow-lg hover:shadow-brand-500/40"
              >
                Rechercher
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </motion.form>
        </div>
      </section>

      {/* Trending neighborhoods */}
      <section className="px-4 py-10">
        <div className="mx-auto max-w-7xl">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-xl font-semibold text-fg">
              <TrendingUp className="h-5 w-5 text-brand-500" aria-hidden="true" />
              Quartiers en tendance
            </h2>
            <Link
              to="/quartiers"
              className="text-sm text-white/50 transition hover:text-fg"
            >
              Tout voir →
            </Link>
          </div>

          {trending.isLoading ? (
            <div className="flex justify-center py-10">
              <Spinner label="Chargement des quartiers..." />
            </div>
          ) : trending.isError ? (
            <p className="py-8 text-center text-sm text-rose-400">
              Erreur lors du chargement des quartiers.
            </p>
          ) : !trending.data || trending.data.length === 0 ? (
            <p className="py-8 text-center text-sm text-white/40">
              Aucune donnée de tendance disponible pour le moment.
            </p>
          ) : (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {trending.data.map((t, i) => (
                <motion.div
                  key={t.slug}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                  transition={{ duration: 0.35, delay: i * 0.05 }}
                >
                  <Link to={`/quartiers?slug=${t.slug}`}>
                    <GlassCard hover className="space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h3 className="font-semibold text-fg">
                            {t.neighborhood}
                          </h3>
                          <p className="flex items-center gap-1 text-xs text-white/50">
                            <MapPin className="h-3 w-3" aria-hidden="true" />
                            {t.city}
                          </p>
                        </div>
                        <span
                          className={cn(
                            'inline-flex items-center gap-1 rounded-lg px-2 py-1 text-xs font-medium',
                            t.trend_pct >= 0
                              ? 'bg-emerald-400/15 text-emerald-400'
                              : 'bg-rose-400/15 text-rose-400',
                          )}
                        >
                          {t.trend_pct >= 0 ? (
                            <TrendingUp className="h-3 w-3" />
                          ) : (
                            <TrendingUp className="h-3 w-3 rotate-180" />
                          )}
                          {percent(t.trend_pct)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-white/40">Prix médian</span>
                        <span className="font-medium text-fg">
                          {formatXAF(t.median_price)}
                        </span>
                      </div>
                    </GlassCard>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Featured listings */}
      <section className="px-4 py-10">
        <div className="mx-auto max-w-7xl">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="text-xl font-semibold text-fg">Biens en vedette</h2>
            <Link
              to="/recherche"
              className="text-sm text-white/50 transition hover:text-fg"
            >
              Tout voir →
            </Link>
          </div>
          <ListingGrid
            listings={listings.data ?? []}
            loading={listings.isLoading}
            error={listings.error ?? null}
          />
        </div>
      </section>

      {/* Cities */}
      <section className="px-4 py-10">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-5 flex items-center gap-2 text-xl font-semibold text-fg">
            <Building2 className="h-5 w-5 text-brand-500" aria-hidden="true" />
            Villes
          </h2>

          {cities.isLoading ? (
            <div className="flex justify-center py-10">
              <Spinner label="Chargement des villes..." />
            </div>
          ) : cities.isError ? (
            <p className="py-8 text-center text-sm text-rose-400">
              Erreur lors du chargement des villes.
            </p>
          ) : !cities.data || cities.data.length === 0 ? (
            <p className="py-8 text-center text-sm text-white/40">
              Aucune ville disponible.
            </p>
          ) : (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
              {cities.data.map((city, i) => (
                <motion.div
                  key={city.id}
                  initial="hidden"
                  animate="visible"
                  variants={fadeUp}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                >
                  <Link to={`/quartiers?city=${encodeURIComponent(city.city)}`}>
                    <GlassCard hover className="text-center">
                      <Building2
                        className="mx-auto h-8 w-8 text-brand-500"
                        aria-hidden="true"
                      />
                      <h3 className="mt-2 font-semibold text-fg">{city.city}</h3>
                      {city.region && (
                        <p className="text-xs text-white/40">{city.region}</p>
                      )}
                    </GlassCard>
                  </Link>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      <Footer />
    </div>
  )
}
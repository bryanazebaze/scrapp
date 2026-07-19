import { useState, useEffect, useCallback, useId } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Heart, Trash2, Info } from 'lucide-react'
import { useListings } from '@/hooks/useListings'
import ListingGrid from '@/components/listings/ListingGrid'
import GlassButton from '@/components/ui/GlassButton'
import EmptyState from '@/components/ui/EmptyState'
import Footer from '@/components/layout/Footer'

// --- Inline favorites hook (exported for reuse in ListingCard/Detail) ---
const STORAGE_KEY = 'centralimmo:favorites'

export function useFavorites() {
  const [favorites, setFavorites] = useState<number[]>([])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) setFavorites(JSON.parse(raw))
    } catch {
      /* ignore */
    }
  }, [])

  const persist = (arr: number[]) => {
    setFavorites(arr)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(arr))
    } catch {
      /* ignore */
    }
  }

  const toggle = useCallback((id: number) => {
    setFavorites((prev) => {
      const next = prev.includes(id)
        ? prev.filter((x) => x !== id)
        : [...prev, id]
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      } catch {
        /* ignore */
      }
      return next
    })
  }, [])

  const clear = useCallback(() => {
    persist([])
  }, [])

  const has = (id: number) => favorites.includes(id)

  return { favorites, toggle, clear, has }
}

export default function Favorites() {
  const fid = useId()
  const { favorites, clear: clearFavorites } = useFavorites()
  const listings = useListings({ limit: 200 })

  const favorited = (listings.data ?? []).filter((l) =>
    favorites.includes(l.id),
  )

  return (
    <div className="px-4 pb-6">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-6 flex items-center justify-between"
        >
          <div>
            <h1 className="flex items-center gap-2 text-2xl font-bold text-fg">
              <Heart className="h-6 w-6 text-brand-500" aria-hidden="true" />
              Mes favoris
            </h1>
            <p className="text-sm text-white/50">
              {favorited.length} bien(s) enregistré(s)
            </p>
          </div>
          {favorited.length > 0 && (
            <GlassButton
              variant="danger"
              size="sm"
              onClick={clearFavorites}
              aria-label="Tout effacer"
            >
              <Trash2 className="h-4 w-4" aria-hidden="true" />
              Tout effacer
            </GlassButton>
          )}
        </motion.div>

        {listings.isLoading ? (
          <ListingGrid listings={[]} loading />
        ) : favorited.length === 0 ? (
          <EmptyState
            title="Aucun favori"
            description="Explorez les biens et cliquez sur le cœur pour les enregistrer."
          />
        ) : (
          <ListingGrid listings={favorited} />
        )}

        {/* Note */}
        <div className="mt-6 flex items-start gap-2 rounded-xl bg-white/5 p-4">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-white/40" aria-hidden="true" />
          <p className="text-xs text-white/40">
            Bientôt synchronisé avec votre compte. Pour l'instant, vos favoris
            sont stockés localement sur cet appareil.
          </p>
        </div>

        <div className="mt-4 text-center">
          <Link to="/recherche" className="text-sm text-brand-500 hover:underline">
            ← Explorer les biens
          </Link>
        </div>
      </div>
      <Footer />
    </div>
  )
}
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SlidersHorizontal } from 'lucide-react'
import { useListings, type ListingsParams } from '@/hooks/useListings'
import { useSearch } from '@/hooks/useSearch'
import ListingGrid from '@/components/listings/ListingGrid'
import FilterPanel from '@/components/listings/FilterPanel'
import GlassButton from '@/components/ui/GlassButton'
import Modal from '@/components/ui/Modal'

type SortKey = 'newest' | 'price_asc' | 'price_desc'

function parseFilters(params: URLSearchParams): ListingsParams {
  const num = (k: string) => {
    const v = params.get(k)
    return v ? Number(v) : undefined
  }
  return {
    q: params.get('q') || undefined,
    city: params.get('city') || undefined,
    property_type: params.get('property_type') || undefined,
    min_price: num('min_price'),
    max_price: num('max_price'),
    min_bedrooms: num('min_bedrooms'),
    max_bedrooms: num('max_bedrooms'),
    min_bathrooms: num('min_bathrooms'),
    min_area: num('min_area'),
    max_area: num('max_area'),
  }
}

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [showFilters, setShowFilters] = useState(false)
  const [sort, setSort] = useState<SortKey>('newest')

  const q = searchParams.get('q') || ''
  const filters = useMemo(() => parseFilters(searchParams), [searchParams])

  const hasQuery = !!q.trim()
  const searchResults = useSearch({ q, ...filters })
  const listingResults = useListings({ limit: 100, ...filters })

  const results = hasQuery ? searchResults.data : listingResults.data
  const loading = hasQuery ? searchResults.isLoading : listingResults.isLoading
  const error = hasQuery ? searchResults.error : listingResults.error

  const sorted = useMemo(() => {
    if (!results) return []
    const arr = [...results]
    if (sort === 'price_asc') {
      arr.sort((a, b) => (a.price ?? 0) - (b.price ?? 0))
    } else if (sort === 'price_desc') {
      arr.sort((a, b) => (b.price ?? 0) - (a.price ?? 0))
    }
    return arr
  }, [results, sort])

  const updateFilters = (next: ListingsParams) => {
    const params: Record<string, string> = {}
    if (next.q) params.q = next.q
    if (next.city) params.city = next.city
    if (next.property_type) params.property_type = next.property_type
    if (next.min_price != null) params.min_price = String(next.min_price)
    if (next.max_price != null) params.max_price = String(next.max_price)
    if (next.min_bedrooms != null) params.min_bedrooms = String(next.min_bedrooms)
    if (next.max_bedrooms != null) params.max_bedrooms = String(next.max_bedrooms)
    if (next.min_bathrooms != null) params.min_bathrooms = String(next.min_bathrooms)
    if (next.min_area != null) params.min_area = String(next.min_area)
    if (next.max_area != null) params.max_area = String(next.max_area)
    setSearchParams(params)
  }

  const resetFilters = () => {
    const params: Record<string, string> = {}
    if (q) params.q = q
    setSearchParams(params)
  }

  return (
    <div className="px-4 pb-6">
      <div className="mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="mb-1 text-2xl font-bold text-fg">
            {q ? `Résultats pour « ${q} »` : 'Recherche'}
          </h1>
          <p className="mb-5 text-sm text-white/50">
            {sorted.length} bien(s) trouvé(s)
          </p>
        </motion.div>

        {/* Sort + mobile filter button */}
        <div className="mb-4 flex items-center justify-between gap-3">
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value as SortKey)}
            className="glass-input"
            aria-label="Trier par"
          >
            <option value="newest" className="bg-ink-900">Plus récents</option>
            <option value="price_asc" className="bg-ink-900">Prix croissant</option>
            <option value="price_desc" className="bg-ink-900">Prix décroissant</option>
          </select>

          <GlassButton
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(true)}
            className="lg:hidden"
          >
            <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
            Filtres
          </GlassButton>
        </div>

        <div className="flex gap-6">
          {/* Sidebar filters - desktop */}
          <aside className="hidden lg:block lg:w-72 shrink-0">
            <div className="sticky top-6">
              <FilterPanel
                value={filters}
                onChange={updateFilters}
                onReset={resetFilters}
              />
            </div>
          </aside>

          {/* Results grid */}
          <div className="min-w-0 flex-1">
            <ListingGrid
              listings={sorted}
              loading={loading}
              error={error ?? null}
              itemsPerPage={8}
            />
          </div>
        </div>

        {/* Mobile filter modal */}
        <Modal
          open={showFilters}
          onClose={() => setShowFilters(false)}
          title="Filtres"
        >
            <FilterPanel
              value={filters}
              onChange={(next) => {
                updateFilters(next)
              }}
              onReset={() => {
                resetFilters()
                setShowFilters(false)
              }}
            />
        </Modal>
      </div>
    </div>
  )
}
import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import type { AnnonceBreve } from '@/lib/types'
import ListingCard from './ListingCard'
import EmptyState from '@/components/ui/EmptyState'
import GlassButton from '@/components/ui/GlassButton'

interface ListingGridProps {
  listings: AnnonceBreve[]
  loading?: boolean
  error?: Error | null
  itemsPerPage?: number
}

function SkeletonCard() {
  return (
    <div className="glass overflow-hidden rounded-2xl">
      <div className="shimmer h-48 w-full" />
      <div className="space-y-3 p-4">
        <div className="shimmer h-4 w-3/4 rounded-lg" />
        <div className="shimmer h-3 w-1/2 rounded-lg" />
        <div className="flex gap-2">
          <div className="shimmer h-6 w-14 rounded-lg" />
          <div className="shimmer h-6 w-14 rounded-lg" />
          <div className="shimmer h-6 w-14 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

export default function ListingGrid({
  listings,
  loading = false,
  error = null,
  itemsPerPage,
}: ListingGridProps) {
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    setCurrentPage(1)
  }, [listings])

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <EmptyState
        title="Une erreur est survenue"
        description={error.message || 'Impossible de charger les annonces.'}
      />
    )
  }

  if (!listings || listings.length === 0) {
    return (
      <EmptyState
        title="Aucune annonce trouvée"
        description="Essayez de modifier vos critères de recherche."
      />
    )
  }

  const hasPagination = itemsPerPage && listings.length > itemsPerPage
  const totalPages = itemsPerPage ? Math.ceil(listings.length / itemsPerPage) : 1
  const displayedListings = hasPagination
    ? listings.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
    : listings

  return (
    <div className="space-y-8">
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.05 } },
        }}
        className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4"
      >
        {displayedListings.map((listing) => (
          <motion.div
            key={listing.id}
            variants={{
              hidden: { opacity: 0, y: 16 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            <ListingCard listing={listing} />
          </motion.div>
        ))}
      </motion.div>

      {hasPagination && (
        <div className="flex justify-center items-center gap-2 mt-8">
          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            Précédent
          </GlassButton>
          
          <div className="flex items-center gap-1 overflow-x-auto max-w-full pb-2 sm:pb-0 px-2 scrollbar-none">
            {Array.from({ length: totalPages }).map((_, i) => {
              const page = i + 1;
              return (
                <GlassButton
                  key={page}
                  variant={page === currentPage ? 'primary' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentPage(page)}
                  className="w-8 h-8 p-0 shrink-0"
                  aria-label={`Aller à la page ${page}`}
                >
                  {page}
                </GlassButton>
              )
            })}
          </div>

          <GlassButton
            variant="ghost"
            size="sm"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
          >
            Suivant
          </GlassButton>
        </div>
      )}
    </div>
  )
}
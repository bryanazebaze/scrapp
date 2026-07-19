import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import { Bed, Bath, Maximize, MapPin } from 'lucide-react'
import type { AnnonceBreve } from '@/lib/types'
import { cn, formatXAF, formatNumber } from '@/lib/utils'

interface ListingCardProps {
  listing: AnnonceBreve
}

export default function ListingCard({ listing }: ListingCardProps) {
  const navigate = useNavigate()
  const img = listing.images?.[0]
  const placeholderGradient =
    'linear-gradient(135deg, rgba(167,139,250,0.25) 0%, rgba(34,211,238,0.18) 50%, rgba(233,78,27,0.22) 100%)'

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      whileHover={{ y: -4 }}
      onClick={() => navigate(`/annonces/${listing.id}`)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          navigate(`/annonces/${listing.id}`)
        }
      }}
      className={cn(
        'glass group cursor-pointer overflow-hidden rounded-2xl',
        'transition-all duration-300 hover:border-white/20 hover:shadow-glass-lg',
      )}
    >
      {/* Image */}
      <div className="relative h-32 sm:h-48 overflow-hidden">
        {img ? (
          <img
            src={img}
            alt={listing.title}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        ) : (
          <div
            className="flex h-full w-full items-center justify-center"
            style={{ background: placeholderGradient }}
          >
            <MapPin className="h-10 w-10 text-white/30" aria-hidden="true" />
          </div>
        )}
        {/* Price badge */}
        <div className="absolute bottom-2 left-2 sm:bottom-3 sm:left-3 rounded-xl bg-ink-900/70 px-2 sm:px-3 py-1 sm:py-1.5 backdrop-blur-md">
          <span className="text-xs sm:text-sm font-bold text-white">
            {formatXAF(listing.price)}
          </span>
        </div>
        {listing.property_type && (
          <div className="absolute top-2 right-2 sm:top-3 sm:right-3 rounded-lg bg-brand-500/80 px-2 sm:px-2.5 py-0.5 sm:py-1 backdrop-blur-md">
            <span className="text-[10px] sm:text-xs font-medium text-white">
              {listing.property_type}
            </span>
          </div>
        )}
      </div>

      {/* Body */}
      <div className="p-3 sm:p-4">
        <h3 className="line-clamp-2 text-xs sm:text-sm font-semibold text-fg">
          {listing.title}
        </h3>
        {(listing.city || listing.neighborhood) && (
          <div className="mt-2 flex items-center gap-1 text-xs text-white/50">
            <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">
              {[listing.neighborhood, listing.city].filter(Boolean).join(', ')}
            </span>
          </div>
        )}

        {/* Chips */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {listing.bedrooms != null && (
            <span className="inline-flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1 text-xs text-white/70">
              <Bed className="h-3.5 w-3.5" aria-hidden="true" />
              {formatNumber(listing.bedrooms)}
            </span>
          )}
          {listing.bathrooms != null && (
            <span className="inline-flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1 text-xs text-white/70">
              <Bath className="h-3.5 w-3.5" aria-hidden="true" />
              {formatNumber(listing.bathrooms)}
            </span>
          )}
          {listing.area_sqm != null && (
            <span className="inline-flex items-center gap-1 rounded-lg bg-white/5 px-2 py-1 text-xs text-white/70">
              <Maximize className="h-3.5 w-3.5" aria-hidden="true" />
              {formatNumber(listing.area_sqm)} m²
            </span>
          )}
        </div>
      </div>
    </motion.div>
  )
}
/**
 * DuplicateReviewCard — side-by-side comparison for duplicate validation.
 * Shows the new listing on the left, matched canonical on the right,
 * with main images and key details. Oui (confirm) / Non (not duplicate) actions.
 */
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Check, ExternalLink, Images, X, AlertCircle, History, Eye } from 'lucide-react'
import type { DuplicateItem } from '@/lib/types'
import { cn, formatXAF, relativeTime } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'

interface DuplicateReviewCardProps {
  item: DuplicateItem
  onConfirm: (id: number) => void
  onNotDuplicate: (id: number) => void
  loadingAction?: number | null
}

export default function DuplicateReviewCard({
  item,
  onConfirm,
  onNotDuplicate,
  loadingAction = null,
}: DuplicateReviewCardProps) {
  const isLoading = loadingAction === item.id

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <GlassCard className="overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 px-5 py-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-amber-400" />
            <span className="text-sm font-medium text-white/80">
              Doublon potentiel #{item.id}
            </span>
            <span className="text-xs text-white/40">
              Crawlé {relativeTime(item.crawled_at)}
            </span>
            {Boolean((item.match_explanation as Record<string, unknown> | null)?.human_validated) ? (
              <span className="inline-flex items-center gap-1 rounded-full bg-purple-400/15 px-2 py-0.5 text-xs font-medium text-purple-400">
                <History className="h-3 w-3" />
                {(item.match_explanation as Record<string, unknown>).human_decision === 'not_duplicate'
                  ? 'Séparé'
                  : 'Confirmé'}
              </span>
            ) : null}
          </div>
          <div className="flex items-center gap-2">
            {item.canonical && (
              <Link
                to={`/annonces/${item.canonical.id}`}
                className="inline-flex items-center gap-1 text-xs text-white/40 hover:text-white/80 transition"
              >
                <Eye className="h-3.5 w-3.5" />
                Voir le bien
              </Link>
            )}
            <a
              href={item.url_source}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-white/40 hover:text-white/70 transition"
            >
              <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>

        {/* Side-by-side comparison */}
        <div className="grid grid-cols-2 divide-x divide-white/10">
          {/* Left: New listing */}
          <div className="p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-emerald-400">
              Nouvelle annonce
            </p>
            <div className="mb-3 aspect-[4/3] overflow-hidden rounded-lg bg-white/5">
              {item.image_main ? (
                <img
                  src={item.image_main}
                  alt={item.title_raw}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-white/20">
                  <Images className="h-10 w-10" />
                </div>
              )}
            </div>
            <h3 className="mb-1 text-sm font-medium text-white/90 line-clamp-2">
              {item.title_raw || 'Sans titre'}
            </h3>
            <p className="mb-1 text-lg font-semibold text-fg">
              {formatXAF(item.price_parsed)}
            </p>
            <p className="text-xs text-white/50">
              {item.location_raw || 'Localisation inconnue'}
            </p>
            <a
              href={item.url_source}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition"
            >
              <ExternalLink className="h-3 w-3" />
              Source originale
            </a>
          </div>

          {/* Right: Matched canonical */}
          <div className="p-4">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-amber-400">
              Propriété existante
            </p>
            <div className="mb-3 aspect-[4/3] overflow-hidden rounded-lg bg-white/5">
              {item.canonical?.image_main ? (
                <img
                  src={item.canonical.image_main}
                  alt={item.canonical.title}
                  className="h-full w-full object-cover"
                  loading="lazy"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-white/20">
                  <Images className="h-10 w-10" />
                </div>
              )}
            </div>
            <h3 className="mb-1 text-sm font-medium text-white/90 line-clamp-2">
              {item.canonical?.title || 'Propriété sans titre'}
            </h3>
            <p className="mb-1 text-lg font-semibold text-fg">
              {formatXAF(item.canonical?.price ?? null)}
            </p>
            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-white/50">
              {item.canonical?.bedrooms != null && (
                <span>{item.canonical.bedrooms} chambre{item.canonical.bedrooms > 1 ? 's' : ''}</span>
              )}
              {item.canonical?.bathrooms != null && (
                <span>{item.canonical.bathrooms} SDB</span>
              )}
              {item.canonical?.area_sqm != null && (
                <span>{item.canonical.area_sqm} m²</span>
              )}
            </div>
            {item.canonical && (
              <Link
                to={`/annonces/${item.canonical.id}`}
                className="mt-2 inline-flex items-center gap-1 text-xs text-white/30 hover:text-white/60 transition"
              >
                <Eye className="h-3 w-3" />
                Voir la fiche
              </Link>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-center gap-3 border-t border-white/10 px-5 py-3">
          {isLoading ? (
            <Spinner size={24} />
          ) : (
            <>
              <GlassButton
                size="sm"
                variant="ghost"
                className={cn(
                  'text-emerald-600 dark:text-emerald-300 hover:bg-emerald-500/15',
                )}
                onClick={() => onConfirm(item.id)}
                aria-label="Confirmer le doublon"
              >
                <Check className="h-4 w-4" />
                Oui — c'est un doublon
              </GlassButton>
              <GlassButton
                size="sm"
                variant="ghost"
                className={cn(
                  'text-rose-600 dark:text-rose-300 hover:bg-rose-500/15',
                )}
                onClick={() => onNotDuplicate(item.id)}
                aria-label="Pas un doublon"
              >
                <X className="h-4 w-4" />
                Non — pas un doublon
              </GlassButton>
            </>
          )}
        </div>
      </GlassCard>
    </motion.div>
  )
}

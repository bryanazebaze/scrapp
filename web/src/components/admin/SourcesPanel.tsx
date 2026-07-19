/**
 * SourcesPanel — grid of source cards with toggle/crawl actions.
 * Each card shows display_name, slug, site_url, SourceBadge, and two buttons.
 * Confirm before crawl with inline "Crawl en cours..." state.
 * Framer Motion stagger on entrance.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { ExternalLink, Globe, Play, Power } from 'lucide-react'
import type { SourceSchema } from '@/lib/types'
import { cn } from '@/lib/utils'
import SourceBadge from '@/components/admin/SourceBadge'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'

interface SourcesPanelProps {
  sources: SourceSchema[]
  onToggle: (slug: string) => void
  onCrawl: (slug: string) => void
  pendingSlug?: string
}

export default function SourcesPanel({
  sources,
  onToggle,
  onCrawl,
  pendingSlug,
}: SourcesPanelProps) {
  const [confirmSlug, setConfirmSlug] = useState<string | null>(null)

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {sources.map((src, i) => {
        const isCrawling = pendingSlug === src.slug
        const isConfirming = confirmSlug === src.slug
        return (
          <motion.div
            key={src.slug}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: Math.min(i * 0.06, 0.4), ease: 'easeOut' }}
            className="glass rounded-2xl p-5 transition hover:border-white/20"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/5">
                  <Globe className="h-5 w-5 text-white/60" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-fg">{src.display_name}</h3>
                  <p className="text-xs text-white/40">{src.slug}</p>
                </div>
              </div>
              <SourceBadge
                kind={src.adapter_kind === 'dedicated' ? 'dedicated' : 'universal'}
                active={src.is_active}
              />
            </div>

            <a
              href={src.site_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 text-xs text-white/50 hover:text-white/80"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              <span className="max-w-[200px] truncate">{src.site_url}</span>
            </a>

            <div className="mt-4 flex items-center gap-2">
              <GlassButton
                size="sm"
                variant="outline"
                className={cn('flex-1', !src.is_active && 'text-emerald-600 dark:text-emerald-300')}
                onClick={() => onToggle(src.slug)}
                disabled={isCrawling}
              >
                <Power className="h-4 w-4" />
                {src.is_active ? 'Désactiver' : 'Activer'}
              </GlassButton>
              {isCrawling ? (
                <div className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-white/60">
                  <Spinner size={16} />
                  Crawl en cours...
                </div>
              ) : isConfirming ? (
                <div className="flex flex-1 items-center gap-1">
                  <GlassButton
                    size="sm"
                    variant="ghost"
                    className="flex-1 text-amber-600 dark:text-amber-300 hover:bg-amber-500/15"
                    onClick={() => {
                      setConfirmSlug(null)
                      onCrawl(src.slug)
                    }}
                  >
                    Confirmer
                  </GlassButton>
                  <GlassButton
                    size="sm"
                    variant="ghost"
                    className="text-white/50"
                    onClick={() => setConfirmSlug(null)}
                    aria-label="Annuler"
                  >
                    Annuler
                  </GlassButton>
                </div>
              ) : (
                <GlassButton
                  size="sm"
                  variant="ghost"
                  className="flex-1"
                  onClick={() => setConfirmSlug(src.slug)}
                  disabled={!src.is_active}
                >
                  <Play className="h-4 w-4" />
                  Crawler
                </GlassButton>
              )}
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}
/**
 * Listings — admin browse-all-listings with server-side filters.
 * Filter bar (city, type, price, bedrooms, q) syncs to URL searchParams.
 * Glass table with client-side pagination (50/page).
 * Row click → /annonces/:id (link out).
 */
import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Building2,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Eye,
  Home,
  Search,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useListings } from '@/hooks/useListings'
import { cn, formatXAF, formatCompact } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import ConfidenceBadge from '@/components/admin/ConfidenceBadge'

const PAGE_SIZE = 50

const PROPERTY_TYPES = ['', 'apartment', 'house', 'land', 'commercial', 'office']

export default function Listings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [page, setPage] = useState(0)

  const city = searchParams.get('city') || ''
  const propertyType = searchParams.get('property_type') || ''
  const minPrice = searchParams.get('min_price') || ''
  const maxPrice = searchParams.get('max_price') || ''
  const minBedrooms = searchParams.get('min_bedrooms') || ''
  const q = searchParams.get('q') || ''

  const params = useMemo(
    () => ({
      city: city || undefined,
      property_type: propertyType || undefined,
      min_price: minPrice ? Number(minPrice) : undefined,
      max_price: maxPrice ? Number(maxPrice) : undefined,
      min_bedrooms: minBedrooms ? Number(minBedrooms) : undefined,
      q: q || undefined,
      limit: 200,
    }),
    [city, propertyType, minPrice, maxPrice, minBedrooms, q],
  )

  const listingsQ = useListings(params)

  const all = listingsQ.data ?? []
  const totalPages = Math.max(1, Math.ceil(all.length / PAGE_SIZE))
  const paged = all.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  const setParam = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams)
    if (value) next.set(key, value)
    else next.delete(key)
    setSearchParams(next, { replace: true })
    setPage(0)
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-fg lg:text-3xl">
          <Building2 className="h-7 w-7 text-prism-cyan" />
          Annonces
        </h1>
        <p className="mt-1 text-sm text-white/40">
          Parcourez les annonces canoniques · {listingsQ.data?.length ?? 0} résultats
        </p>
      </motion.div>

      {/* Filter bar */}
      <GlassCard>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
          <FilterInput
            label="Ville"
            value={city}
            onChange={(v) => setParam('city', v)}
            placeholder="Douala"
          />
          <FilterSelect
            label="Type"
            value={propertyType}
            onChange={(v) => setParam('property_type', v)}
            options={PROPERTY_TYPES.map((t) => ({ value: t, label: t || 'Tous' }))}
          />
          <FilterInput
            label="Prix min"
            value={minPrice}
            onChange={(v) => setParam('min_price', v)}
            placeholder="500000"
            type="number"
          />
          <FilterInput
            label="Prix max"
            value={maxPrice}
            onChange={(v) => setParam('max_price', v)}
            placeholder="50000000"
            type="number"
          />
          <FilterInput
            label="Chambres min"
            value={minBedrooms}
            onChange={(v) => setParam('min_bedrooms', v)}
            placeholder="2"
            type="number"
          />
          <FilterInput
            label="Recherche"
            value={q}
            onChange={(v) => setParam('q', v)}
            placeholder="Mot-clé..."
            icon={Search}
          />
        </div>
      </GlassCard>

      {/* Table */}
      <GlassCard>
        {listingsQ.isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : listingsQ.isError ? (
          <EmptyState icon={Building2} title="Erreur" description="Impossible de charger les annonces." />
        ) : paged.length === 0 ? (
          <EmptyState
            icon={Home}
            title="Aucune annonce"
            description="Ajustez les filtres ou attendez de nouvelles annonces."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[1000px] border-collapse">
              <thead>
                <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-white/40">
                  <th className="px-3 py-3 font-medium">Titre</th>
                  <th className="px-3 py-3 font-medium">Prix</th>
                  <th className="px-3 py-3 font-medium">Ville</th>
                  <th className="px-3 py-3 font-medium">Quartier</th>
                  <th className="px-3 py-3 font-medium">Type</th>
                  <th className="px-3 py-3 font-medium">Ch.</th>
                  <th className="px-3 py-3 font-medium">Surface</th>
                  <th className="px-3 py-3 font-medium">Source</th>
                  <th className="px-3 py-3 font-medium">Confiance</th>
                  <th className="px-3 py-3 text-right font-medium">Voir</th>
                </tr>
              </thead>
              <tbody>
                {paged.map((item, i) => (
                  <motion.tr
                    key={item.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2, delay: Math.min(i * 0.02, 0.3) }}
                    className="border-b border-white/5 transition hover:bg-white/[0.03]"
                  >
                    <td className="px-3 py-3">
                      <Link
                        to={`/annonces/${item.id}`}
                        className="block max-w-[200px] truncate text-sm text-white/80 hover:text-fg"
                      >
                        {item.title || 'Sans titre'}
                      </Link>
                    </td>
                    <td className="px-3 py-3 text-sm text-white/70">{formatXAF(item.price)}</td>
                    <td className="px-3 py-3 text-sm text-white/60">{item.city ?? '—'}</td>
                    <td className="px-3 py-3 text-sm text-white/60">
                      <span className="max-w-[140px] truncate inline-block">
                        {item.neighborhood ?? '—'}
                      </span>
                    </td>
                    <td className="px-3 py-3 text-sm text-white/50">{item.property_type ?? '—'}</td>
                    <td className="px-3 py-3 text-sm text-white/50">{item.bedrooms ?? '—'}</td>
                    <td className="px-3 py-3 text-sm text-white/50">
                      {item.area_sqm ? `${formatCompact(item.area_sqm)} m²` : '—'}
                    </td>
                    <td className="px-3 py-3 text-sm text-white/50">
                      {item.best_source ?? '—'}
                    </td>
                    <td className="px-3 py-3">
                      <ConfidenceBadge confidence={null} />
                    </td>
                    <td className="px-3 py-3 text-right">
                      <Link
                        to={`/annonces/${item.id}`}
                        className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 text-white/50 transition hover:bg-white/10 hover:text-fg"
                        aria-label="Voir l'annonce"
                      >
                        <Eye className="h-4 w-4" />
                      </Link>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {all.length > PAGE_SIZE && (
          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-white/40">
              Page {page + 1} sur {totalPages} · {all.length} annonces
            </span>
            <div className="flex gap-2">
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
              >
                <ChevronLeft className="h-4 w-4" />
                Précédent
              </GlassButton>
              <GlassButton
                size="sm"
                variant="ghost"
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
              >
                Suivant
                <ChevronRight className="h-4 w-4" />
              </GlassButton>
            </div>
          </div>
        )}

        <div className="mt-4 flex justify-end">
          <Link
            to="/recherche"
            className="inline-flex items-center gap-1.5 text-sm text-white/40 hover:text-white/70"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Voir sur le site
          </Link>
        </div>
      </GlassCard>
    </div>
  )
}

/* ---------- filter inputs ---------- */

function FilterInput({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  icon: Icon,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  placeholder?: string
  type?: string
  icon?: LucideIcon
}) {
  return (
    <div>
      <label className="mb-1 block text-xs uppercase tracking-wider text-white/40">{label}</label>
      <div className="relative">
        {Icon && <Icon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={cn('glass-input w-full', Icon && 'pl-9')}
        />
      </div>
    </div>
  )
}

function FilterSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string
  value: string
  onChange: (v: string) => void
  options: { value: string; label: string }[]
}) {
  return (
    <div>
      <label className="mb-1 block text-xs uppercase tracking-wider text-white/40">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="glass-input w-full cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value} className="bg-ink-900 text-white">
            {opt.label}
          </option>
        ))}
      </select>
    </div>
  )
}
/**
 * NeighborhoodAnalyticsTable — sortable glass table of neighborhood analytics.
 * Columns: Quartier, Ville, Listings, Prix médian, Prix/m², Premium, Demande,
 * Croissance, Activité, Luxe, Tendance.
 * Score cells use scoreBg + scoreColor. Trend column: arrow + percent.
 * Click headers to sort. Default sort: premium_score desc.
 */
import { useMemo, useState } from 'react'
import {
  ArrowDown,
  ArrowUpDown,
  ArrowUp,
} from 'lucide-react'
import type { NeighborhoodAnalyticsSchema } from '@/lib/types'
import {
  cn,
  categoryLabel,
  formatCompact,
  formatXAF,
  formatXAFPerSqm,
  scoreBg,
  scoreColor,
} from '@/lib/utils'
import EmptyState from '@/components/ui/EmptyState'
import type { LucideIcon } from 'lucide-react'

interface NeighborhoodAnalyticsTableProps {
  rows: NeighborhoodAnalyticsSchema[]
  onRowClick?: (row: NeighborhoodAnalyticsSchema) => void
}

type SortKey =
  | 'neighborhood'
  | 'city'
  | 'category'
  | 'listing_count'
  | 'median_price'
  | 'price_per_sqm'
  | 'avg_price_per_sqm'
  | 'premium_score'
  | 'activity_score'
  | 'luxury_score'

type SortDir = 'asc' | 'desc'

interface Column {
  key: SortKey
  label: string
  numeric: boolean
}

const columns: Column[] = [
  { key: 'neighborhood', label: 'Quartier', numeric: false },
  { key: 'city', label: 'Ville', numeric: false },
  { key: 'category', label: 'Catégorie', numeric: false },
  { key: 'listing_count', label: 'Listings', numeric: true },
  { key: 'median_price', label: 'Prix médian', numeric: true },
  { key: 'price_per_sqm', label: 'Prix/m²', numeric: true },
  { key: 'avg_price_per_sqm', label: 'Prix moy./m²', numeric: true },
  { key: 'premium_score', label: 'Premium', numeric: true },
  { key: 'activity_score', label: 'Activité', numeric: true },
  { key: 'luxury_score', label: 'Luxe', numeric: true },
]

function getVal(row: NeighborhoodAnalyticsSchema, key: SortKey): number | string {
  const map: Record<SortKey, number | string | null> = {
    neighborhood: row.neighborhood ?? row.city,
    city: row.city,
    category: row.category,
    listing_count: row.listing_count,
    median_price: row.median_price,
    price_per_sqm: row.price_per_sqm,
    avg_price_per_sqm: row.avg_price_per_sqm,
    premium_score: row.premium_score,
    activity_score: row.activity_score,
    luxury_score: row.luxury_score,
  }
  const v = map[key]
  return v ?? -Infinity
}

function ScoreCell({ score }: { score: number | null }) {
  return (
    <span
      className={cn(
        'inline-flex min-w-[2.5rem] justify-center rounded-md px-2 py-1 text-xs font-semibold',
        scoreBg(score),
        scoreColor(score),
      )}
    >
      {score == null ? '—' : score.toFixed(1)}
    </span>
  )
}

export default function NeighborhoodAnalyticsTable({
  rows,
  onRowClick,
}: NeighborhoodAnalyticsTableProps) {
  const [sortKey, setSortKey] = useState<SortKey>('listing_count')
  const [sortDir, setSortDir] = useState<SortDir>('desc')

  const sorted = useMemo(() => {
    const arr = [...rows]
    arr.sort((a, b) => {
      const va = getVal(a, sortKey)
      const vb = getVal(b, sortKey)
      let cmp: number
      if (typeof va === 'number' && typeof vb === 'number') {
        cmp = va - vb
      } else {
        cmp = String(va).localeCompare(String(vb), 'fr')
      }
      return sortDir === 'asc' ? cmp : -cmp
    })
    return arr
  }, [rows, sortKey, sortDir])

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir(key === 'neighborhood' || key === 'city' ? 'asc' : 'desc')
    }
  }

  const SortIcon = ({ col }: { col: Column }) => {
    if (col.key !== sortKey) return <ArrowUpDown className="h-3 w-3 text-white/20" />
    return sortDir === 'asc'
      ? <ArrowUp className="h-3 w-3 text-prism-cyan" />
      : <ArrowDown className="h-3 w-3 text-prism-cyan" />
  }

  if (rows.length === 0) {
    return (
      <EmptyState
        icon={ArrowUpDown}
        title="Aucune donnée analytique"
        description="Lancez un recompute analytics pour générer les scores par quartier."
      />
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[960px] border-collapse">
        <thead>
          <tr className="border-b border-white/10 text-left text-xs uppercase tracking-wider text-white/40">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'px-3 py-3 font-medium select-none cursor-pointer transition hover:text-white/70',
                  col.numeric && 'text-right',
                )}
                onClick={() => handleSort(col.key)}
              >
                <span className={cn('inline-flex items-center gap-1', col.numeric && 'justify-end')}>
                  {col.label}
                  <SortIcon col={col} />
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row) => (
            <tr
              key={`${row.location_id}-${row.property_type ?? 'all'}`}
              className={cn(
                'border-b border-white/5 transition hover:bg-white/[0.03]',
                onRowClick && 'cursor-pointer',
              )}
              onClick={() => onRowClick?.(row)}
            >
              <td className="px-3 py-3 text-sm text-white/80">
                {row.neighborhood ?? row.city}
              </td>
              <td className="px-3 py-3 text-sm text-white/60">{row.city}</td>
              <td className="px-3 py-3 text-sm text-white/60">
                {categoryLabel(row.category)}
              </td>
              <td className="px-3 py-3 text-right text-sm text-white/70">{row.listing_count}</td>
              <td className="px-3 py-3 text-right text-sm text-white/70">
                {formatXAF(row.median_price)}
              </td>
              <td className="px-3 py-3 text-right text-sm text-white/60">
                {formatCompact(row.price_per_sqm)}
              </td>
              <td className="px-3 py-3 text-right text-sm text-white/60">
                {formatXAFPerSqm(row.avg_price_per_sqm)}
              </td>
              <td className="px-3 py-3 text-right">
                <ScoreCell score={row.premium_score} />
              </td>
              <td className="px-3 py-3 text-right">
                <ScoreCell score={row.activity_score} />
              </td>
              <td className="px-3 py-3 text-right">
                <ScoreCell score={row.luxury_score} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
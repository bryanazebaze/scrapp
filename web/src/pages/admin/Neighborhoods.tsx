/**
 * Neighborhoods — analytics explorer with city tabs and drill-down.
 * City selector (tab bar). Selected city → useCityNeighborhoods → NeighborhoodAnalyticsTable.
 * Recompute analytics button on the right.
 * Click row → Modal with useNeighborhoodAnalytics(slug) full detail: ScoreRings + price stats + trend.
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { MapPin, Sparkles } from 'lucide-react'
import type { NeighborhoodAnalyticsSchema } from '@/lib/types'
import { useCityNeighborhoods, useNeighborhoodAnalytics } from '@/hooks/useNeighborhoods'
import { useRecomputeAnalytics } from '@/hooks/useAdmin'
import { cn, formatXAF, formatCompact } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Modal from '@/components/ui/Modal'
import Spinner from '@/components/ui/Spinner'
import ScoreRing from '@/components/ui/ScoreRing'
import EmptyState from '@/components/ui/EmptyState'
import NeighborhoodAnalyticsTable from '@/components/admin/NeighborhoodAnalyticsTable'

const MAJOR_CITIES = [
  'Douala',
  'Yaoundé',
  'Bafoussam',
  'Bamenda',
  'Garoua',
  'Maroua',
  'Ngaoundéré',
  'Kribi',
  'Limbe',
  'Buéa',
]

export default function Neighborhoods() {
  const [city, setCity] = useState(MAJOR_CITIES[0])
  const [selectedSlug, setSelectedSlug] = useState<string | null>(null)

  const cityQ = useCityNeighborhoods(city)
  const detailQ = useNeighborhoodAnalytics(selectedSlug ?? undefined)
  const recompute = useRecomputeAnalytics()

  const rows = cityQ.data ?? []

  const handleRowClick = (row: NeighborhoodAnalyticsSchema) => {
    setSelectedSlug(row.slug)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
      >
        <div>
          <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-fg lg:text-3xl">
            <MapPin className="h-7 w-7 text-prism-violet" />
            Quartiers
          </h1>
          <p className="mt-1 text-sm text-white/40">
            Analytics par quartier · {rows.length} quartiers pour {city}
          </p>
        </div>
        <GlassButton
          variant="outline"
          onClick={() => recompute.mutate()}
          disabled={recompute.isPending}
        >
          {recompute.isPending ? <Spinner size={16} /> : <Sparkles className="h-4 w-4" />}
          Recalculer analytics
        </GlassButton>
      </motion.div>

      {recompute.isSuccess && (
        <div className="rounded-xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-600 dark:text-emerald-300">
          Analytics recalculés.
        </div>
      )}

      {/* City tabs */}
      <div className="flex flex-wrap gap-1 rounded-2xl bg-white/[0.03] p-1.5">
        {MAJOR_CITIES.map((c) => (
          <button
            key={c}
            onClick={() => setCity(c)}
            className={cn(
              'rounded-xl px-3 py-2 text-sm font-medium transition',
              city === c
                ? 'bg-white/10 text-fg shadow-sm'
                : 'text-white/40 hover:text-white/70',
            )}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Table */}
      <GlassCard>
        {cityQ.isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : cityQ.isError ? (
          <EmptyState
            icon={MapPin}
            title="Erreur"
            description="Impossible de charger les analytics pour cette ville."
          />
        ) : rows.length === 0 ? (
          <EmptyState
            icon={MapPin}
            title={`Aucune donnée pour ${city}`}
            description="Lancez un recompute analytics pour générer les scores."
          />
        ) : (
          <NeighborhoodAnalyticsTable rows={rows} onRowClick={handleRowClick} />
        )}
      </GlassCard>

      {/* Drill-down modal */}
      <Modal
        open={!!selectedSlug}
        onClose={() => setSelectedSlug(null)}
        title="Détail du quartier"
        size="lg"
      >
        {detailQ.isLoading ? (
          <div className="flex justify-center py-12"><Spinner size={32} /></div>
        ) : detailQ.data ? (
          <NeighborhoodDetail data={detailQ.data} />
        ) : (
          <EmptyState icon={MapPin} title="Quartier introuvable" />
        )}
      </Modal>
    </div>
  )
}

function NeighborhoodDetail({ data }: { data: NeighborhoodAnalyticsSchema }) {
  const scores = [
    { label: 'Premium', value: data.premium_score },
    { label: 'Activité', value: data.activity_score },
    { label: 'Luxe', value: data.luxury_score },
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-semibold text-fg">
          {data.neighborhood ?? data.city}
        </h3>
        <p className="text-sm text-white/40">
          {data.city}
          {data.property_type && ` · ${data.property_type}`}
        </p>
      </div>

      {/* Score rings */}
      <div className="flex flex-wrap justify-center gap-4">
        {scores.map((s) => (
          <ScoreRing key={s.label} score={s.value} size={90} label={s.label} />
        ))}
      </div>

      {/* Price stats */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatBox label="Listings" value={String(data.listing_count)} />
        <StatBox label="Prix médian" value={formatXAF(data.median_price)} />
        <StatBox label="Prix min" value={formatXAF(data.min_price)} />
        <StatBox label="Prix max" value={formatXAF(data.max_price)} />
        <StatBox label="Prix/m²" value={formatCompact(data.price_per_sqm)} />
        <StatBox label="Prix moyen" value={formatXAF(data.average_price)} />
      </div>
    </div>
  )
}

function StatBox({
  label,
  value,
  icon,
}: {
  label: string
  value: string
  icon?: React.ReactNode
}) {
  return (
    <div className="rounded-xl bg-white/[0.03] px-3 py-2.5">
      <p className="text-xs uppercase tracking-wider text-white/40">{label}</p>
      <p className="mt-1 flex items-center gap-1.5 text-sm font-medium text-white/80">
        {icon}
        {value}
      </p>
    </div>
  )
}
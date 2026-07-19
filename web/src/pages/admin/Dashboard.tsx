/**
 * Dashboard — system overview with KPIs, price stats, type distribution,
 * city breakdown, and recent activity. Refreshes every 60s.
 */
import { motion } from 'framer-motion'
import {
  Activity,
  BarChart3,
  Building2,
  CalendarClock,
  Clock,
  Globe,
  Home,
  MapPin,
  TrendingUp,
  AlertTriangle,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { useDashboard } from '@/hooks/useAdmin'
import { formatXAF, formatCompact } from '@/lib/utils'
import GlassCard from '@/components/ui/GlassCard'
import Spinner from '@/components/ui/Spinner'

export default function Dashboard() {
  const { user } = useAuth()
  const dashQ = useDashboard()
  const d = dashQ.data

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <h1 className="text-2xl font-bold tracking-tight text-fg lg:text-3xl">
          Tableau de bord
        </h1>
        <p className="mt-1 text-sm text-white/40">
          Bienvenue, <span className="text-white/70">{user?.email}</span>
        </p>
      </motion.div>

      {dashQ.isLoading ? (
        <div className="flex justify-center py-20"><Spinner size={40} /></div>
      ) : dashQ.isError ? (
        <GlassCard>
          <div className="py-12 text-center text-rose-400">
            Impossible de charger les statistiques.
          </div>
        </GlassCard>
      ) : d ? (
        <>
          {/* KPI row 1 — core counts */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Annonces actives" value={formatCompact(d.counts.active_canonicals)} icon={Home} accent="emerald" sub={`${formatCompact(d.counts.total_raw_listings)} brutes`} />
            <StatCard label="Sources actives" value={d.counts.active_sources} icon={Globe} accent="cyan" sub={`sur ${d.counts.total_sources} configurées`} />
            <StatCard label="En attente" value={d.counts.pending_review} icon={Clock} accent="amber" sub="à réviser" />
            <StatCard label="Villes suivies" value={d.counts.unique_cities} icon={MapPin} accent="violet" sub={`${d.counts.unique_neighborhoods} quartiers`} />
          </div>

          {/* KPI row 2 — activity + jobs */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Ajouts 24h" value={d.recent_activity.last_24h} icon={Activity} accent="fuchsia" sub={`${d.recent_activity.last_7d} sur 7 jours`} />
            <StatCard label="Total canoniques" value={formatCompact(d.counts.total_canonicals)} icon={Building2} accent="brand" sub={`${d.counts.active_canonicals} actifs`} />
            <StatCard label="Jobs en cours" value={d.jobs_summary.running} icon={CalendarClock} accent={d.jobs_summary.running > 0 ? 'amber' : 'emerald'} sub={`${d.jobs_summary.failed} échoués`} />
            <StatCard label="Location / Vente" value={`${d.purpose_split.rent} / ${d.purpose_split.sale}`} icon={TrendingUp} accent="cyan" sub={d.purpose_split.rent > d.purpose_split.sale ? 'Majorité location' : 'Majorité vente'} />
          </div>

          {/* Price overview + type distribution */}
          <div className="grid gap-6 lg:grid-cols-2">
            <GlassCard>
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-fg">
                <BarChart3 className="h-4 w-4 text-prism-cyan" />
                Aperçu des prix
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <PriceBadge label="Minimum" value={d.price_stats.min} />
                <PriceBadge label="Moyen" value={d.price_stats.avg} />
                <PriceBadge label="Maximum" value={d.price_stats.max} />
              </div>
            </GlassCard>

            <GlassCard>
              <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-fg">
                <Home className="h-4 w-4 text-prism-fuchsia" />
                Types de biens
              </h3>
              <div className="space-y-2">
                {d.property_types.slice(0, 6).map((pt) => {
                  const pct = d.counts.active_canonicals > 0
                    ? Math.round((pt.count / d.counts.active_canonicals) * 100)
                    : 0
                  return (
                    <div key={pt.type} className="flex items-center gap-3">
                      <span className="w-20 shrink-0 text-xs text-white/60">{pt.type}</span>
                      <div className="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-brand-500 to-prism-amber"
                          style={{ width: `${Math.max(pct, 1)}%` }}
                        />
                      </div>
                      <span className="w-12 text-right text-xs text-white/40">{pt.count}</span>
                    </div>
                  )
                })}
              </div>
            </GlassCard>
          </div>

          {/* Top cities */}
          <GlassCard>
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-fg">
              <MapPin className="h-4 w-4 text-prism-violet" />
              Top villes par annonces
            </h3>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {d.top_cities.map((city, i) => {
                const maxCount = d.top_cities[0]?.count ?? 1
                const pct = Math.round((city.count / maxCount) * 100)
                return (
                  <div key={city.city} className="rounded-xl bg-white/[0.03] p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-white/60">{i + 1}. {city.city}</span>
                      <span className="text-xs font-semibold text-white/80">{city.count}</span>
                    </div>
                    <div className="mt-2 h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-prism-violet to-prism-fuchsia"
                        style={{ width: `${Math.max(pct, 3)}%` }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </GlassCard>

          {/* Alerts row */}
          {d.counts.pending_review > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 flex items-center gap-3"
            >
              <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
              <p className="text-sm text-amber-600 dark:text-amber-300">
                {d.counts.pending_review} annonce{d.counts.pending_review > 1 ? 's' : ''} en attente de révision manuelle.{' '}
                <a href="/admin/file-attente" className="underline font-medium">Voir la file d'attente →</a>
              </p>
            </motion.div>
          )}
        </>
      ) : null}
    </div>
  )
}

/* ---------- Helpers ---------- */

function StatCard({
  label, value, icon: Icon, accent, sub,
}: {
  label: string
  value: string | number
  icon: typeof Home
  accent: 'emerald' | 'cyan' | 'amber' | 'violet' | 'fuchsia' | 'brand'
  sub?: string
}) {
  const accentMap: Record<string, string> = {
    emerald: 'bg-emerald-400/10 text-emerald-400',
    cyan: 'bg-cyan-400/10 text-cyan-400',
    amber: 'bg-amber-400/10 text-amber-400',
    violet: 'bg-violet-400/10 text-violet-400',
    fuchsia: 'bg-fuchsia-400/10 text-fuchsia-400',
    brand: 'bg-brand-500/10 text-brand-400',
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="glass rounded-2xl p-4"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-white/40">{label}</span>
        <div className={`flex h-8 w-8 items-center justify-center rounded-xl ${accentMap[accent]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-2 text-2xl font-bold text-fg">{value}</p>
      {sub && <p className="mt-0.5 text-xs text-white/30">{sub}</p>}
    </motion.div>
  )
}

function PriceBadge({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="rounded-xl bg-white/[0.03] p-3 text-center">
      <p className="text-xs uppercase tracking-wider text-white/40">{label}</p>
      <p className="mt-1 text-lg font-bold text-fg">
        {value ? formatXAF(value) : '—'}
      </p>
    </div>
  )
}

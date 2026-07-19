import { useState, useEffect, useId } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, Trash2, Plus, Info, Search } from 'lucide-react'
import type { ListingsParams } from '@/hooks/useListings'
import { buildQuery } from '@/lib/api'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import EmptyState from '@/components/ui/EmptyState'
import Footer from '@/components/layout/Footer'

interface SavedAlert {
  id: string
  name: string
  query: ListingsParams
  created_at: string
}

const STORAGE_KEY = 'centralimmo:alerts'

const PROPERTY_TYPES = [
  { value: '', label: 'Tous' },
  { value: 'Appartement', label: 'Appartement' },
  { value: 'Maison', label: 'Maison' },
  { value: 'Studio', label: 'Studio' },
  { value: 'Terrain', label: 'Terrain' },
  { value: 'Bureau', label: 'Bureau' },
  { value: 'Magasin', label: 'Magasin' },
]

function loadAlerts(): SavedAlert[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw)
  } catch {
    /* ignore */
  }
  return []
}

function saveAlerts(alerts: SavedAlert[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(alerts))
  } catch {
    /* ignore */
  }
}

function querySummary(q: ListingsParams): string[] {
  const parts: string[] = []
  if (q.city) parts.push(q.city)
  if (q.property_type) parts.push(q.property_type)
  if (q.max_price != null) parts.push(`≤ ${q.max_price} FCFA`)
  if (q.min_bedrooms != null) parts.push(`≥ ${q.min_bedrooms} ch.`)
  return parts
}

export default function Alerts() {
  const fid = useId()
  const [alerts, setAlerts] = useState<SavedAlert[]>([])

  // Form state
  const [name, setName] = useState('')
  const [city, setCity] = useState('')
  const [propertyType, setPropertyType] = useState('')
  const [maxPrice, setMaxPrice] = useState('')

  useEffect(() => {
    setAlerts(loadAlerts())
  }, [])

  const createAlert = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    const query: ListingsParams = {}
    if (city.trim()) query.city = city.trim()
    if (propertyType) query.property_type = propertyType
    if (maxPrice) query.max_price = Number(maxPrice)
    const alert: SavedAlert = {
      id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6),
      name: name.trim(),
      query,
      created_at: new Date().toISOString(),
    }
    const next = [alert, ...alerts]
    setAlerts(next)
    saveAlerts(next)
    setName('')
    setCity('')
    setPropertyType('')
    setMaxPrice('')
  }

  const deleteAlert = (id: string) => {
    const next = alerts.filter((a) => a.id !== id)
    setAlerts(next)
    saveAlerts(next)
  }

  const alertToUrl = (alert: SavedAlert) =>
    `/recherche${buildQuery(alert.query as Record<string, unknown>)}`

  return (
    <div className="px-4 pb-6">
      <div className="mx-auto max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          <h1 className="flex items-center gap-2 text-2xl font-bold text-fg">
            <Bell className="h-6 w-6 text-brand-500" aria-hidden="true" />
            Mes alertes
          </h1>
          <p className="text-sm text-white/50">
            Soyez notifié des nouveaux biens correspondant à vos critères.
          </p>
        </motion.div>

        {/* Create alert form */}
        <GlassCard className="mt-6 space-y-4">
          <h2 className="flex items-center gap-2 text-lg font-semibold text-fg">
            <Plus className="h-5 w-5 text-brand-500" aria-hidden="true" />
            Créer une alerte
          </h2>
          <form onSubmit={createAlert} className="space-y-4">
            <div>
              <label htmlFor={`${fid}-name`} className="mb-1 block text-xs font-medium text-white/50">
                Nom de l'alerte
              </label>
              <input
                id={`${fid}-name`}
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Studios à Akwa"
                required
                className="glass-input w-full"
              />
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              <div>
                <label htmlFor={`${fid}-city`} className="mb-1 block text-xs font-medium text-white/50">
                  Ville
                </label>
                <input
                  id={`${fid}-city`}
                  type="text"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="Douala..."
                  className="glass-input w-full"
                />
              </div>
              <div>
                <label htmlFor={`${fid}-type`} className="mb-1 block text-xs font-medium text-white/50">
                  Type
                </label>
                <select
                  id={`${fid}-type`}
                  value={propertyType}
                  onChange={(e) => setPropertyType(e.target.value)}
                  className="glass-input w-full"
                >
                  {PROPERTY_TYPES.map((t) => (
                    <option key={t.value} value={t.value} className="bg-ink-900">
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor={`${fid}-price`} className="mb-1 block text-xs font-medium text-white/50">
                  Prix max (FCFA)
                </label>
                <input
                  id={`${fid}-price`}
                  type="number"
                  min={0}
                  value={maxPrice}
                  onChange={(e) => setMaxPrice(e.target.value)}
                  placeholder="500000"
                  className="glass-input w-full"
                />
              </div>
            </div>
            <GlassButton type="submit" variant="primary" size="md">
              <Plus className="h-4 w-4" aria-hidden="true" />
              Créer l'alerte
            </GlassButton>
          </form>
        </GlassCard>

        {/* Alert list */}
        <div className="mt-6 space-y-3">
          {alerts.length === 0 ? (
            <EmptyState
              title="Aucune alerte"
              description="Créez-en une pour être notifié des nouveaux biens."
            />
          ) : (
            <AnimatePresence>
              {alerts.map((alert, i) => (
                <motion.div
                  key={alert.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 12 }}
                  transition={{ duration: 0.25, delay: i * 0.03 }}
                >
                  <GlassCard hover className="flex items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-fg">{alert.name}</h3>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {querySummary(alert.query).map((chip, idx) => (
                          <span
                            key={idx}
                            className="rounded-lg bg-white/5 px-2 py-0.5 text-xs text-white/60"
                          >
                            {chip}
                          </span>
                        ))}
                      </div>
                      <p className="mt-1 text-xs text-white/30">
                        Créée le {new Date(alert.created_at).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-2">
                      <Link to={alertToUrl(alert)}>
                        <GlassButton variant="outline" size="sm" aria-label="Voir les résultats">
                          <Search className="h-4 w-4" aria-hidden="true" />
                          Résultats
                        </GlassButton>
                      </Link>
                      <GlassButton
                        variant="danger"
                        size="sm"
                        onClick={() => deleteAlert(alert.id)}
                        aria-label={`Supprimer l'alerte ${alert.name}`}
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </GlassButton>
                    </div>
                  </GlassCard>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {/* Note */}
        <div className="mt-6 flex items-start gap-2 rounded-xl bg-white/5 p-4">
          <Info className="mt-0.5 h-4 w-4 shrink-0 text-white/40" aria-hidden="true" />
          <p className="text-xs text-white/40">
            Bientôt notifié par email/SMS — fonctionnalité en attente d'intégration backend.
          </p>
        </div>
      </div>
      <Footer />
    </div>
  )
}
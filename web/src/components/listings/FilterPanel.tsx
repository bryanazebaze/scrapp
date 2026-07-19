import { useId } from 'react'
import { RotateCcw } from 'lucide-react'
import type { ListingsParams } from '@/hooks/useListings'
import GlassButton from '@/components/ui/GlassButton'

interface FilterPanelProps {
  value: ListingsParams
  onChange: (next: ListingsParams) => void
  onReset?: () => void
}

const PROPERTY_TYPES = [
  { value: '', label: 'Tous les types' },
  { value: 'Appartement', label: 'Appartement' },
  { value: 'Maison', label: 'Maison' },
  { value: 'Studio', label: 'Studio' },
  { value: 'Terrain', label: 'Terrain' },
  { value: 'Bureau', label: 'Bureau' },
  { value: 'Magasin', label: 'Magasin' },
]

export default function FilterPanel({ value, onChange, onReset }: FilterPanelProps) {
  const id = useId()

  const update = (patch: Partial<ListingsParams>) => {
    onChange({ ...value, ...patch })
  }

  const numField = (key: keyof ListingsParams, label: string) => (
    <div>
      <label
        htmlFor={`${id}-${key}`}
        className="mb-1 block text-xs font-medium text-white/50"
      >
        {label}
      </label>
      <input
        id={`${id}-${key}`}
        type="number"
        min={0}
        value={(value[key] as number | undefined) ?? ''}
        onChange={(e) => {
          const v = e.target.value
          update({ [key]: v === '' ? undefined : Number(v) } as Partial<ListingsParams>)
        }}
        placeholder="—"
        className="glass-input w-full"
      />
    </div>
  )

  return (
    <div className="glass space-y-4 rounded-2xl p-5">
      <h2 className="text-sm font-semibold text-fg">Filtres</h2>

      {/* Free text search */}
      <div>
        <label
          htmlFor={`${id}-q`}
          className="mb-1 block text-xs font-medium text-white/50"
        >
          Recherche
        </label>
        <input
          id={`${id}-q`}
          type="text"
          value={value.q ?? ''}
          onChange={(e) => update({ q: e.target.value || undefined })}
          placeholder="Mots-clés..."
          className="glass-input w-full"
        />
      </div>

      {/* City */}
      <div>
        <label
          htmlFor={`${id}-city`}
          className="mb-1 block text-xs font-medium text-white/50"
        >
          Ville ou Quartier
        </label>
        <input
          id={`${id}-city`}
          type="text"
          value={value.city ?? ''}
          onChange={(e) => update({ city: e.target.value || undefined })}
          placeholder="Ex: Douala, Bastos..."
          className="glass-input w-full"
        />
      </div>

      {/* Property type */}
      <div>
        <label
          htmlFor={`${id}-type`}
          className="mb-1 block text-xs font-medium text-white/50"
        >
          Type de bien
        </label>
        <select
          id={`${id}-type`}
          value={value.property_type ?? ''}
          onChange={(e) =>
            update({ property_type: e.target.value || undefined })
          }
          className="glass-input w-full"
        >
          {PROPERTY_TYPES.map((t) => (
            <option key={t.value} value={t.value} className="bg-ink-900">
              {t.label}
            </option>
          ))}
        </select>
      </div>

      {/* Price range */}
      <div>
        <span className="mb-2 block text-xs font-medium text-white/50">
          Prix (FCFA)
        </span>
        <div className="grid grid-cols-2 gap-2">
          {numField('min_price', 'Min')}
          {numField('max_price', 'Max')}
        </div>
      </div>

      {/* Bedrooms */}
      <div>
        <span className="mb-2 block text-xs font-medium text-white/50">
          Chambres
        </span>
        <div className="grid grid-cols-2 gap-2">
          {numField('min_bedrooms', 'Min')}
          {numField('max_bedrooms', 'Max')}
        </div>
      </div>

      {/* Bathrooms + Area */}
      <div className="grid grid-cols-2 gap-3">
        {numField('min_bathrooms', 'Salles de bain min')}
        {numField('min_area', 'Surface min (m²)')}
      </div>
      <div className="grid grid-cols-2 gap-3">
        {numField('max_area', 'Surface max (m²)')}
      </div>

      {onReset && (
        <GlassButton
          variant="outline"
          size="sm"
          onClick={onReset}
          className="w-full"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Réinitialiser
        </GlassButton>
      )}
    </div>
  )
}
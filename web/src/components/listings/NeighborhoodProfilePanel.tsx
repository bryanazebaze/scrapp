import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { Shield, Train, Trees, AlertTriangle, Building2, MapPin, ChevronDown, ChevronUp, Volume2, VolumeX, Loader2 } from 'lucide-react'
import { useNeighborhoodProfileByLocation } from '@/hooks/useProfiles'
import GlassCard from '@/components/ui/GlassCard'
import Spinner from '@/components/ui/Spinner'

function ExpandableText({ text, maxLength = 150 }: { text: string; maxLength?: number }) {
  const [expanded, setExpanded] = useState(false)
  if (!text) return null
  if (text.length <= maxLength) return <p className="text-xs text-white/60 leading-relaxed whitespace-pre-wrap">{text}</p>
  
  return (
    <div>
      <p className="text-xs text-white/60 leading-relaxed whitespace-pre-wrap">
        {expanded ? text : `${text.slice(0, maxLength)}...`}
      </p>
      <button 
        onClick={() => setExpanded(!expanded)}
        className="mt-1 text-[10px] font-semibold text-brand-500 hover:text-brand-400 flex items-center gap-1 transition"
      >
        {expanded ? (
          <><ChevronUp className="h-3 w-3" /> Voir moins</>
        ) : (
          <><ChevronDown className="h-3 w-3" /> Voir plus</>
        )}
      </button>
    </div>
  )
}

function TTSButton({ text }: { text: string }) {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  const handlePlay = async () => {
    if (isPlaying && audioRef.current) {
      audioRef.current.pause()
      setIsPlaying(false)
      return
    }

    if (!text) return

    setIsLoading(true)
    try {
      const response = await fetch('https://api.elevenlabs.io/v1/text-to-speech/EXAVITQu4vr4xnSDxMaL', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': 'sk_6e55aeb3ec3d68bb1f28fa1c34ee5fe0220213caa32f812a'
        },
        body: JSON.stringify({
          text,
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75
          }
        })
      })
      
      if (!response.ok) {
        throw new Error('TTS Failed')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const audio = new Audio(url)
      audioRef.current = audio
      
      audio.onended = () => setIsPlaying(false)
      audio.onerror = () => setIsPlaying(false)
      
      await audio.play()
      setIsPlaying(true)
    } catch (err) {
      console.error(err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <button 
      onClick={handlePlay}
      disabled={isLoading}
      className="p-1.5 rounded-full bg-brand-500/10 text-brand-500 hover:bg-brand-500/20 transition disabled:opacity-50"
      title="Écouter"
    >
      {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : isPlaying ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
    </button>
  )
}

interface NeighborhoodProfilePanelProps {
  locationId?: number
}

export default function NeighborhoodProfilePanel({ locationId }: NeighborhoodProfilePanelProps) {
  const profileQuery = useNeighborhoodProfileByLocation(locationId)

  if (!locationId) return null
  if (profileQuery.isLoading) {
    return (
      <GlassCard className="flex items-center justify-center p-6">
        <Spinner label="Chargement du profil du quartier..." />
      </GlassCard>
    )
  }

  const profile = profileQuery.data
  if (!profile) return null

  // Don't show if almost completely empty
  if (!profile.description && !profile.security_rating && !profile.transport_info && (!profile.amenities || profile.amenities.length === 0)) {
    return null
  }

  return (
    <GlassCard className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <h2 className="flex items-center gap-2 text-lg font-semibold text-fg">
          <MapPin className="h-5 w-5 text-brand-500" aria-hidden="true" />
          Profil du quartier : {profile.neighborhood || profile.city}
        </h2>
        {profile.description && <TTSButton text={profile.description} />}
      </div>

      {profile.description && (
        <div className="text-sm text-fg/80 leading-relaxed whitespace-pre-wrap">
          <ExpandableText text={profile.description} maxLength={200} />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {/* Security */}
        {(profile.security_rating || profile.security_notes) && (
          <div className="rounded-xl bg-white/5 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <h3 className="font-medium text-fg">Sécurité</h3>
              {profile.security_rating && (
                <span className="ml-auto text-xs font-bold px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400">
                  {profile.security_rating}
                </span>
              )}
              {profile.security_notes && <TTSButton text={profile.security_notes} />}
            </div>
            {profile.security_notes && (
              <ExpandableText text={profile.security_notes} maxLength={120} />
            )}
          </div>
        )}

        {/* Transport & Infrastructure */}
        {profile.transport_info && (
          <div className="rounded-xl bg-white/5 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Train className="h-4 w-4 text-blue-400" />
              <h3 className="font-medium text-fg">Transport & Accès</h3>
            </div>
            <ExpandableText text={profile.transport_info} maxLength={120} />
          </div>
        )}

        {/* Real Estate Context */}
        {profile.real_estate_context && (
          <div className="rounded-xl bg-white/5 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-purple-400" />
              <h3 className="font-medium text-fg">Immobilier</h3>
            </div>
            <ExpandableText text={profile.real_estate_context} maxLength={120} />
          </div>
        )}

        {/* Amenities */}
        {profile.amenities && profile.amenities.length > 0 && (
          <div className="rounded-xl bg-white/5 p-4 space-y-2">
            <div className="flex items-center gap-2">
              <Trees className="h-4 w-4 text-emerald-500" />
              <h3 className="font-medium text-fg">Commodités</h3>
            </div>
            <ul className="text-xs text-white/60 leading-relaxed list-disc list-inside">
              {profile.amenities.slice(0, 4).map((amenity, i) => (
                <li key={i} className="truncate">{String(amenity)}</li>
              ))}
              {profile.amenities.length > 4 && <li>...</li>}
            </ul>
          </div>
        )}
      </div>

      {/* Risk Factors */}
      {profile.risk_factors && profile.risk_factors.length > 0 && (
        <div className="rounded-xl bg-rose-500/10 p-4 border border-rose-500/20">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-rose-400" />
            <h3 className="font-medium text-rose-400 text-sm">Facteurs de risque</h3>
          </div>
          <ul className="text-xs text-rose-300/80 leading-relaxed list-disc list-inside space-y-1">
            {profile.risk_factors.map((risk, i) => (
              <li key={i}>{risk}</li>
            ))}
          </ul>
        </div>
      )}
    </GlassCard>
  )
}

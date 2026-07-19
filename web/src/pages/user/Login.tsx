import { useState, useEffect, useId } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ShieldCheck } from 'lucide-react'
import {
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth'
import { auth } from '@/firebase'
import { useAuth } from '@/contexts/AuthContext'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import { cn } from '@/lib/utils'

function firebaseErrorToFrench(err: unknown): string {
  const code = (err as { code?: string })?.code || ''
  const map: Record<string, string> = {
    'auth/invalid-phone-number': 'Numéro de téléphone invalide.',
    'auth/too-many-requests': 'Trop de tentatives. Réessayez plus tard.',
    'auth/invalid-verification-code': 'Code de vérification invalide.',
    'auth/code-expired': 'Le code a expiré. Demandez un nouveau code.',
    'auth/popup-closed-by-user': 'Fenêtre fermée avant la connexion.',
    'auth/popup-blocked': 'Pop-up bloqué. Autorisez les pop-ups pour ce site.',
    'auth/cancelled-popup-request': 'Connexion annulée.',
    'auth/operation-not-allowed': 'Cette méthode de connexion n\'est pas activée.',
    'auth/network-request-failed': 'Erreur réseau. Vérifiez votre connexion.',
  }
  return map[code] || 'Une erreur est survenue. Réessayez.'
}

export default function Login() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const { user } = useAuth()
  const fid = useId()
  const redirect = searchParams.get('redirect') || '/profil'

  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (user) navigate(redirect, { replace: true })
  }, [user, navigate, redirect])

  const googleSignIn = async () => {
    setError('')
    setLoading(true)
    try {
      await signInWithPopup(auth, new GoogleAuthProvider())
      navigate(redirect, { replace: true })
    } catch (err) {
      setError(firebaseErrorToFrench(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 pb-10">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md"
      >
        <GlassCard strong className="space-y-5">
          {/* Header */}
          <div className="text-center">
            <h1 className="text-2xl font-bold text-fg">Connexion</h1>
            <p className="mt-1 text-sm text-white/50">
              Accédez à vos favoris et alertes
            </p>
          </div>

          {/* Error */}
          {error && (
            <p className="rounded-lg bg-rose-500/15 px-3 py-2 text-sm text-rose-600 dark:text-rose-300" role="alert">
              {error}
            </p>
          )}

          {/* Google Sign In */}
          <div className="space-y-4 pt-4">
            <GlassButton
              variant="outline"
              size="lg"
              className="w-full flex items-center gap-3 bg-white/5 hover:bg-white/10"
              onClick={googleSignIn}
              disabled={loading}
            >
              <img src="/Google_Favicon_2025.svg" alt="Google" className="h-5 w-5" />
              {loading ? 'Connexion...' : 'Continuer avec Google'}
            </GlassButton>
          </div>

          {/* Note */}
          <div className="mt-6 flex items-start gap-2 rounded-xl bg-white/5 p-3">
            <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-white/40" aria-hidden="true" />
            <p className="text-xs text-white/40">
              Assurez-vous que Google est activé dans la console Firebase,
              et que ce domaine est autorisé.
            </p>
          </div>
        </GlassCard>
      </motion.div>
    </div>
  )
}
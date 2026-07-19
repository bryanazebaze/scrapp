/**
 * AdminLogin — admin email/password login via the FastAPI JWT backend
 * (POST /admin/login -> {access_token, admin}). Also exposes Google
 * sign-in as a fallback (Firebase + ADMIN_EMAILS allowlist).
 */
import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  GoogleAuthProvider,
  signInWithPopup,
} from 'firebase/auth'
import { ArrowLeft, Lock, Mail, ShieldAlert } from 'lucide-react'
import { auth, ADMIN_EMAILS, isAdminEmail } from '@/firebase'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import GlassButton from '@/components/ui/GlassButton'
import Spinner from '@/components/ui/Spinner'
import { api, ADMIN_EMAIL_KEY, ADMIN_TOKEN_KEY } from '@/lib/api'

interface AdminLoginResponse {
  access_token: string
  token_type: string
  admin: { id: number; username: string | null; email: string | null }
}

export default function AdminLogin() {
  const { user, isAdmin } = useAuth()
  const navigate = useNavigate()

  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Redirect if already admin
  useEffect(() => {
    if (isAdmin) navigate('/admin', { replace: true })
  }, [isAdmin, navigate])

  // If signed in via Firebase but not admin, show the not-authorized state
  const signedInNotAdmin = !!user && !isAdmin && !localStorage.getItem(ADMIN_TOKEN_KEY)

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const res = await api.post<AdminLoginResponse>('/admin/login', {
        identifier,
        password,
      })
      localStorage.setItem(ADMIN_TOKEN_KEY, res.access_token)
      localStorage.setItem(
        ADMIN_EMAIL_KEY,
        res.admin.email || res.admin.username || identifier,
      )
      // Force a re-render of AuthContext by reloading; the JWT path does
      // not trigger Firebase's onAuthStateChanged.
      navigate('/admin', { replace: true })
      window.location.reload()
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? 'Identifiants admin invalides'
          : 'Échec de connexion admin',
      )
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    setError(null)
    setLoading(true)
    try {
      const provider = new GoogleAuthProvider()
      await signInWithPopup(auth, provider)
      // onAuthStateChanged in AuthContext will pick this up; isAdmin is
      // derived from the ADMIN_EMAILS allowlist for the Firebase path.
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Échec de connexion Google')
    } finally {
      setLoading(false)
    }
  }

  if (signedInNotAdmin) {
    return (
      <div className="flex min-h-screen items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
          className="glass-strong w-full max-w-md rounded-3xl p-8"
        >
          <div className="mb-6 flex flex-col items-center text-center">
            <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-rose-500/15">
              <ShieldAlert className="h-8 w-8 text-rose-400" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-fg">
              Accès non autorisé
            </h1>
            <p className="mt-3 text-sm text-white/50">
              Votre email <span className="text-white/80">{user?.email}</span> n'est pas
              autorisé pour l'administration. Contactez l'administrateur.
            </p>
            <p className="mt-4 text-xs text-white/30">
              Emails autorisés : {Array.from(ADMIN_EMAILS).join(', ')}
            </p>
          </div>
          <Link to="/">
            <GlassButton variant="ghost" className="w-full">
              <ArrowLeft className="h-4 w-4" />
              Retour au site
            </GlassButton>
          </Link>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="glass-strong w-full max-w-md rounded-3xl p-8"
      >
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-prism-violet via-prism-fuchsia to-prism-cyan shadow-lg shadow-prism-violet/30">
            <Lock className="h-7 w-7 text-white" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            <span className="prism-text">Administration CentralImmo</span>
          </h1>
          <p className="mt-2 text-sm text-white/40">
            Accès réservé aux administrateurs autorisés
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-xl border border-rose-400/20 bg-rose-400/10 px-4 py-3 text-sm text-rose-600 dark:text-rose-300">
            {error}
          </div>
        )}

        <form onSubmit={handleEmailLogin} className="space-y-4">
          <div>
            <label htmlFor="admin-email" className="mb-1.5 block text-xs uppercase tracking-wider text-white/40">
              Email ou identifiant
            </label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-white/30" />
              <input
                id="admin-email"
                type="text"
                value={identifier}
                onChange={(e) => setIdentifier(e.target.value)}
                placeholder="azebazeaurel@gmail.com"
                required
                autoComplete="username"
                className={cn('glass-input w-full pl-11')}
              />
            </div>
          </div>
          <div>
            <label htmlFor="admin-password" className="mb-1.5 block text-xs uppercase tracking-wider text-white/40">
              Mot de passe
            </label>
            <input
              id="admin-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
              className="glass-input w-full"
            />
          </div>
          <GlassButton type="submit" variant="primary" className="w-full" disabled={loading}>
            {loading ? <Spinner size={18} /> : <Lock className="h-4 w-4" />}
            Se connecter
          </GlassButton>
        </form>

        <div className="my-5 flex items-center gap-3">
          <div className="h-px flex-1 bg-white/10" />
          <span className="text-xs text-white/30">ou</span>
          <div className="h-px flex-1 bg-white/10" />
        </div>

        <GlassButton variant="outline" className="w-full" onClick={handleGoogleLogin} disabled={loading}>
          <svg className="h-4 w-4" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Continuer avec Google
        </GlassButton>

        <Link
          to="/"
          className="mt-6 flex items-center justify-center gap-2 text-sm text-white/40 transition hover:text-white/70"
        >
          <ArrowLeft className="h-4 w-4" />
          Retour au site
        </Link>
      </motion.div>
    </div>
  )
}
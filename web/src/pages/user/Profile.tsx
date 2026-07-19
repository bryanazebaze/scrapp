import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Heart, Bell, LogOut, Shield, Mail, Phone } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import GlassCard from '@/components/ui/GlassCard'
import GlassButton from '@/components/ui/GlassButton'
import Badge from '@/components/ui/Badge'
import Footer from '@/components/layout/Footer'

export default function Profile() {
  const { user, loading, isAdmin, signOut } = useAuth()
  const navigate = useNavigate()

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="spinner" />
      </div>
    )
  }

  if (!user) {
    navigate('/login?redirect=/profil', { replace: true })
    return null
  }

  const displayName = user.displayName || user.email || 'Utilisateur'
  const initial = (user.email || user.displayName || 'U')[0].toUpperCase()
  const handleSignOut = async () => {
    await signOut()
    navigate('/', { replace: true })
  }

  return (
    <div className="px-4 pb-6">
      <div className="mx-auto max-w-3xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="space-y-6"
        >
          {/* Profile header */}
          <GlassCard className="flex items-center gap-4">
            {user.photoURL ? (
              <img
                src={user.photoURL}
                alt={displayName}
                className="h-20 w-20 rounded-full border-2 border-white/20"
              />
            ) : (
              <div className="flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-prism-violet text-2xl font-bold text-white">
                {initial}
              </div>
            )}
            <div className="space-y-1">
              <h1 className="text-xl font-bold text-fg">{displayName}</h1>
              {user.email && (
                <p className="flex items-center gap-1.5 text-sm text-white/50">
                  <Mail className="h-3.5 w-3.5" aria-hidden="true" />
                  {user.email}
                </p>
              )}
              {user.phoneNumber && (
                <p className="flex items-center gap-1.5 text-sm text-white/50">
                  <Phone className="h-3.5 w-3.5" aria-hidden="true" />
                  {user.phoneNumber}
                </p>
              )}
              {isAdmin && (
                <Badge color="amber" variant="soft">
                  <Shield className="h-3 w-3" aria-hidden="true" />
                  Admin
                </Badge>
              )}
            </div>
          </GlassCard>

          {/* Actions */}
          <div className="grid gap-4 sm:grid-cols-2">
            <GlassCard hover className="space-y-3">
              <Heart className="h-6 w-6 text-brand-500" aria-hidden="true" />
              <h2 className="font-semibold text-fg">Mes favoris</h2>
              <p className="text-sm text-white/50">
                Consultez les biens que vous avez enregistrés.
              </p>
              <GlassButton variant="outline" size="sm" onClick={() => navigate('/favoris')}>
                Voir mes favoris
              </GlassButton>
            </GlassCard>

            <GlassCard hover className="space-y-3">
              <Bell className="h-6 w-6 text-brand-500" aria-hidden="true" />
              <h2 className="font-semibold text-fg">Mes alertes</h2>
              <p className="text-sm text-white/50">
                Gérez vos alertes de recherche.
              </p>
              <GlassButton variant="outline" size="sm" onClick={() => navigate('/alertes')}>
                Voir mes alertes
              </GlassButton>
            </GlassCard>
          </div>

          {/* Admin panel */}
          {isAdmin && (
            <GlassCard hover className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <Shield className="h-6 w-6 text-prism-amber" aria-hidden="true" />
                <div>
                  <h2 className="font-semibold text-fg">Panneau d'administration</h2>
                  <p className="text-sm text-white/50">
                    Gérer les sources, file d'attente, analytics.
                  </p>
                </div>
              </div>
              <GlassButton
                variant="primary"
                size="sm"
                onClick={() => navigate('/admin')}
              >
                Accéder
              </GlassButton>
            </GlassCard>
          )}

          {/* Sign out */}
          <GlassButton
            variant="danger"
            size="md"
            onClick={handleSignOut}
            className="w-full"
          >
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Se déconnecter
          </GlassButton>
        </motion.div>
      </div>
      <Footer />
    </div>
  )
}
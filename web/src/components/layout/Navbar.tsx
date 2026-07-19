/**
 * Navbar — top navigation for user-facing pages.
 * Fixed top, glass background. Includes logo, nav links, language toggle,
 * favorites/alerts icons, and auth-aware right side (Connexion or avatar dropdown).
 */
import { useState, useEffect, useRef } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Heart,
  Bell,
  Menu,
  X,
  Globe,
  User as UserIcon,
  LogOut,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import ThemeToggle from '@/components/ui/ThemeToggle'

const navLinks = [
  { label: 'Accueil', to: '/' },
  { label: 'Rechercher', to: '/recherche' },
  { label: 'Quartiers', to: '/quartiers' },
  { label: 'Assistant', to: '/chat' },
]

function PrismLogo() {
  return (
    <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-xl shadow-lg shadow-brand-500/20">
      <img src="/logo.png" alt="Logo" className="h-full w-full object-cover" />
    </div>
  )
}

export default function Navbar() {
  const { user, signOut } = useAuth()
  const location = useLocation()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [lang, setLang] = useState<'fr' | 'en'>('fr')
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const stored = (localStorage.getItem('lang') as 'fr' | 'en' | null)
    if (stored) setLang(stored)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
    setDropdownOpen(false)
  }, [location.pathname])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const toggleLang = () => {
    const next = lang === 'fr' ? 'en' : 'fr'
    setLang(next)
    localStorage.setItem('lang', next)
  }

  const isActive = (to: string) =>
    to === '/' ? location.pathname === '/' : location.pathname.startsWith(to)

  return (
    <nav className="fixed top-0 left-0 right-0 z-40 glass border-b border-white/10">
      <div className="mx-auto max-w-7xl px-4 md:px-6">
        <div className="flex h-16 items-center justify-between gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <PrismLogo />
            <span className="text-lg font-semibold tracking-tight text-fg hidden sm:block">
              Central<span className="brand-text">Immo</span>
            </span>
          </Link>

          {/* Center nav links — desktop */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={cn(
                  'rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200',
                  isActive(link.to)
                    ? 'bg-white/10 text-fg'
                    : 'text-white/50 hover:bg-white/5 hover:text-white/80',
                )}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-2 shrink-0">
            {/* Language toggle */}
            <button
              onClick={toggleLang}
              className="flex items-center gap-1.5 rounded-lg px-2.5 py-2 text-sm font-medium text-white/50 transition hover:bg-white/5 hover:text-white/80"
              aria-label="Changer de langue"
              title="Changer de langue"
            >
              <Globe className="h-4 w-4" />
              <span className="hidden sm:inline">{lang.toUpperCase()}</span>
            </button>

            {/* Theme toggle */}
            <ThemeToggle />

            {/* Favorites */}
            <Link
              to="/favoris"
              className="flex h-9 w-9 items-center justify-center rounded-lg text-white/50 transition hover:bg-white/5 hover:text-fg"
              aria-label="Favoris"
            >
              <Heart className="h-5 w-5" />
            </Link>

            {/* Alerts */}
            <Link
              to="/alertes"
              className="flex h-9 w-9 items-center justify-center rounded-lg text-white/50 transition hover:bg-white/5 hover:text-fg"
              aria-label="Alertes"
            >
              <Bell className="h-5 w-5" />
            </Link>

            {/* Auth */}
            {user ? (
              <div ref={dropdownRef} className="relative">
                <button
                  onClick={() => setDropdownOpen((v) => !v)}
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-prism-violet to-prism-cyan text-sm font-semibold text-white transition hover:shadow-lg hover:shadow-prism-violet/30"
                  aria-label="Menu du profil"
                  aria-expanded={dropdownOpen}
                >
                  {(user.email ?? '?')[0].toUpperCase()}
                </button>
                <AnimatePresence>
                  {dropdownOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 8 }}
                      transition={{ duration: 0.15 }}
                      className="absolute right-0 top-12 w-48 glass-strong rounded-xl p-2"
                    >
                      <div className="px-3 py-2 border-b border-white/10">
                        <p className="text-xs text-white/40 truncate">{user.email}</p>
                      </div>
                      <Link
                        to="/profil"
                        className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-white/70 transition hover:bg-white/5 hover:text-fg"
                      >
                        <UserIcon className="h-4 w-4" />
                        Profil
                      </Link>
                      <button
                        onClick={() => signOut()}
                        className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-rose-600 dark:text-rose-300 transition hover:bg-rose-500/10"
                      >
                        <LogOut className="h-4 w-4" />
                        Déconnexion
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <Link
                to="/login"
                className="hidden sm:inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-brand-500 to-brand-400 px-4 py-2 text-sm font-medium text-white shadow-lg shadow-brand-500/30 transition hover:shadow-brand-500/50"
              >
                Connexion
              </Link>
            )}

            {/* Mobile hamburger */}
            <button
              onClick={() => setMobileOpen((v) => !v)}
              className="md:hidden flex h-9 w-9 items-center justify-center rounded-lg text-white/60 transition hover:bg-white/5 hover:text-fg"
              aria-label="Menu"
              aria-expanded={mobileOpen}
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile drawer */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="md:hidden overflow-hidden border-t border-white/10"
          >
            <div className="px-4 py-3 space-y-1">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    'block rounded-lg px-3 py-2.5 text-sm font-medium transition',
                    isActive(link.to)
                      ? 'bg-white/10 text-fg'
                      : 'text-white/50 hover:bg-white/5 hover:text-fg',
                  )}
                >
                  {link.label}
                </Link>
              ))}
              {!user && (
                <Link
                  to="/login"
                  className="block rounded-lg px-3 py-2.5 text-sm font-medium text-brand-400 hover:bg-white/5"
                >
                  Connexion
                </Link>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  )
}
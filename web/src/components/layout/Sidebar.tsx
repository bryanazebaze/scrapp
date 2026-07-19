/**
 * Sidebar — admin navigation sidebar.
 * Fixed left, w-64, glass background. Nav items with Lucide icons.
 * Includes "Retour au site" link and Sign out button.
 * Mobile: collapses to a top bar with hamburger.
 */
import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard,
  Building2,
  Clock,
  Globe,
  MapPin,
  CalendarClock,
  ArrowLeft,
  LogOut,
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import ThemeToggle from '@/components/ui/ThemeToggle'

interface NavItem {
  label: string
  to: string
  icon: typeof LayoutDashboard
}

const items: NavItem[] = [
  { label: 'Dashboard', to: '/admin', icon: LayoutDashboard },
  { label: 'Annonces', to: '/admin/annonces', icon: Building2 },
  { label: "File d'attente", to: '/admin/file-attente', icon: Clock },
  { label: 'Sources', to: '/admin/sources', icon: Globe },
  { label: 'Quartiers', to: '/admin/quartiers', icon: MapPin },
  { label: 'Jobs', to: '/admin/jobs', icon: CalendarClock },
]

function PrismLogo() {
  return (
    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-[#F18B3A] to-[#E94E1B] shadow-lg shadow-brand-500/30">
      <svg viewBox="0 0 24 24" className="h-5 w-5 text-white" fill="none">
        <path
          d="M12 2L22 8.5V15.5L12 22L2 15.5V8.5L12 2Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path
          d="M12 7L17 10V14L12 17L7 14V10L12 7Z"
          fill="currentColor"
          fillOpacity="0.4"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  )
}

export default function Sidebar() {
  const { signOut } = useAuth()
  const [mobileOpen, setMobileOpen] = useState(false)

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 h-16 border-b border-white/10 shrink-0">
        <PrismLogo />
        <div className="flex flex-col">
          <span className="text-sm font-semibold text-fg">
            Central<span className="brand-text">Immo</span>
          </span>
          <span className="text-[10px] uppercase tracking-wider text-white/40">Admin</span>
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto no-scrollbar">
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/admin'}
            onClick={() => setMobileOpen(false)}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-white/10 border-l-2 border-brand-500 text-fg'
                  : 'text-white/50 hover:bg-white/5 hover:text-fg border-l-2 border-transparent',
              )
            }
          >
            <item.icon className="h-5 w-5 shrink-0" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 py-4 border-t border-white/10 space-y-1 shrink-0">
        <Link
          to="/"
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white/50 transition hover:bg-white/5 hover:text-fg"
        >
          <ArrowLeft className="h-5 w-5 shrink-0" />
          Retour au site
        </Link>
        <div className="flex items-center justify-between px-3 py-2.5">
          <span className="text-sm font-medium text-white/50">Thème</span>
          <ThemeToggle />
        </div>
        <button
          onClick={() => signOut()}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-rose-600 dark:text-rose-300 transition hover:bg-rose-500/10"
        >
          <LogOut className="h-5 w-5 shrink-0" />
          Déconnexion
        </button>
      </div>
    </div>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex fixed left-0 top-0 bottom-0 w-64 glass border-r border-white/10 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile top bar */}
      <div className="md:hidden fixed top-0 left-0 right-0 z-30 glass border-b border-white/10">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <PrismLogo />
            <span className="text-sm font-semibold text-fg">
              Central<span className="brand-text">Immo</span> Admin
            </span>
          </div>
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-white/60 transition hover:bg-white/5 hover:text-fg"
            aria-label="Menu admin"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        <AnimatePresence>
          {mobileOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="overflow-hidden"
            >
              <div className="h-[calc(100vh-4rem)]">
                <SidebarContent />
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Spacer for mobile top bar */}
      <div className="md:hidden h-16 shrink-0" />
    </>
  )
}
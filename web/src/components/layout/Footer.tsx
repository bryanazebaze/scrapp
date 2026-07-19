/**
 * Footer — glass footer with logo, tagline, and link columns.
 * Bottom row: copyright + data disclaimer.
 */
import { Link } from 'react-router-dom'

const columns = [
  {
    title: 'Explorer',
    links: [
      { label: 'Rechercher', to: '/recherche' },
      { label: 'Quartiers', to: '/quartiers' },
      { label: 'Assistant IA', to: '/chat' },
    ],
  },
  {
    title: 'Entreprise',
    links: [
      { label: 'Connexion', to: '/login' },
      { label: 'Profil', to: '/profil' },
      { label: 'Favoris', to: '/favoris' },
    ],
  },
  {
    title: 'Légal',
    links: [
      { label: 'Confidentialité', to: '/' },
      { label: "Conditions d'utilisation", to: '/' },
      { label: 'Cookies', to: '/' },
    ],
  },
]

export default function Footer() {
  return (
    <footer className="glass border-t border-white/10 mt-12">
      <div className="mx-auto max-w-7xl px-4 md:px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand + tagline */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 mb-3">
              <div className="flex h-8 w-8 items-center justify-center overflow-hidden rounded-xl">
                <img src="/logo.png" alt="Logo" className="h-full w-full object-cover" />
              </div>
              <span className="text-base font-semibold text-fg">
                Central<span className="brand-text">Immo</span>
              </span>
            </div>
            <p className="text-sm text-white/40 max-w-xs">
              Agrégateur immobilier intelligent pour le Cameroun
            </p>
          </div>

          {/* Link columns */}
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="mb-3 text-sm font-semibold text-white/60">{col.title}</h4>
              <ul className="space-y-2">
                {col.links.map((link) => (
                  <li key={link.label}>
                    <Link
                      to={link.to}
                      className="text-sm text-white/40 transition hover:text-white/70"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom row */}
        <div className="mt-8 pt-6 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p className="text-xs text-white/30">
            © 2026 CentralImmo
          </p>
          <p className="text-xs text-white/20 text-center sm:text-right">
            Données synthétiques — toujours vérifier auprès de l'agence
          </p>
        </div>
      </div>
    </footer>
  )
}
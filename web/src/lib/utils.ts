import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs))
}

export function formatXAF(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(n) + ' FCFA'
}

export function formatNumber(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-FR').format(n)
}

export function formatCompact(n: number | null | undefined): string {
  if (n == null) return '—'
  return new Intl.NumberFormat('fr-FR', { notation: 'compact', maximumFractionDigits: 1 }).format(n)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }) }
  catch { return '—' }
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) }
  catch { return '—' }
}

export function relativeTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso).getTime()
  const now = Date.now()
  const diff = Math.round((d - now) / 1000)
  const abs = Math.abs(diff)
  const rtf = new Intl.RelativeTimeFormat('fr', { numeric: 'auto' })
  if (abs < 60) return rtf.format(Math.round(diff), 'second')
  if (abs < 3600) return rtf.format(Math.round(diff / 60), 'minute')
  if (abs < 86400) return rtf.format(Math.round(diff / 3600), 'hour')
  if (abs < 2592000) return rtf.format(Math.round(diff / 86400), 'day')
  if (abs < 31536000) return rtf.format(Math.round(diff / 2592000), 'month')
  return rtf.format(Math.round(diff / 31536000), 'year')
}

export function scoreColor(score: number | null | undefined): string {
  if (score == null) return 'text-ink-900/40 dark:text-white/40'
  if (score >= 8) return 'text-prism-emerald'
  if (score >= 6) return 'text-prism-amber'
  if (score >= 4) return 'text-brand-500'
  return 'text-rose-600 dark:text-rose-400'
}

export function scoreBg(score: number | null | undefined): string {
  if (score == null) return 'bg-ink-900/5 dark:bg-white/5'
  if (score >= 8) return 'bg-prism-emerald/12'
  if (score >= 6) return 'bg-prism-amber/15'
  if (score >= 4) return 'bg-brand-500/10'
  return 'bg-rose-500/10'
}

export function scoreLabel(score: number | null | undefined): string {
  if (score == null) return 'N/A'
  if (score >= 8) return 'Excellent'
  if (score >= 6) return 'Bon'
  if (score >= 4) return 'Moyen'
  return 'Faible'
}

export function verdictColor(v: string | null | undefined): string {
  if (v === 'below_market') return 'text-prism-emerald'
  if (v === 'around_market') return 'text-prism-amber'
  if (v === 'above_market') return 'text-rose-600 dark:text-rose-400'
  return 'text-ink-900/40 dark:text-white/40'
}

export function verdictLabel(v: string | null | undefined): string {
  if (v === 'below_market') return 'Sous le marché'
  if (v === 'around_market') return 'Dans le marché'
  if (v === 'above_market') return 'Au-dessus du marché'
  return 'Données insuffisantes'
}

export function statusColor(s: string | null | undefined): string {
  if (!s) return 'text-ink-900/40 dark:text-white/40'
  if (['auto_promoted', 'human_approved', 'succeeded', 'connected', 'ok', 'available'].includes(s)) return 'text-prism-emerald'
  if (['pending', 'scheduled', 'running'].includes(s)) return 'text-prism-amber'
  if (['rejected', 'failed', 'error', 'degraded', 'removed'].includes(s)) return 'text-rose-600 dark:text-rose-400'
  return 'text-prism-cyan'
}

export function percent(n: number | null | undefined): string {
  if (n == null) return '—'
  const sign = n > 0 ? '+' : ''
  return `${sign}${n.toFixed(1)}%`
}

export function categoryLabel(c: 'Structure' | 'Land' | null | undefined): string {
  if (c === 'Structure') return 'Structure'
  if (c === 'Land') return 'Terrain'
  return '—'
}

export function formatXAFPerSqm(n: number | null | undefined): string {
  if (n == null) return '—'
  return `${formatXAF(n)}/m²`
}
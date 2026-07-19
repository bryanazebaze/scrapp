import { auth } from '@/firebase'

const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Keys used in localStorage for the JWT-based admin session.
export const ADMIN_TOKEN_KEY = 'centralimmo:admin_token'
export const ADMIN_EMAIL_KEY = 'centralimmo:admin_email'

export function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function clearAdminToken(): void {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
  localStorage.removeItem(ADMIN_EMAIL_KEY)
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...((init.headers as Record<string, string>) || {})
  }
  // Prefer the JWT admin token; fall back to the Firebase ID token.
  const adminToken = getAdminToken()
  if (adminToken) {
    headers.Authorization = `Bearer ${adminToken}`
  } else if (auth.currentUser) {
    try { headers.Authorization = `Bearer ${await auth.currentUser.getIdToken()}` } catch { /* ignore */ }
  }
  // Accept-Language: fr (default) or en — toggled by language switcher in navbar
  headers['Accept-Language'] = localStorage.getItem('lang') || 'fr'

  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`
    try { const body = await res.json(); if (body?.detail) msg = body.detail } catch { /* ignore */ }
    throw new Error(msg)
  }
  if (res.status === 204) return undefined as T
  return await res.json() as T
}

export const api = {
  get: <T>(path: string): Promise<T> => request<T>(path),
  post: <T>(path: string, body?: unknown): Promise<T> =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body: unknown): Promise<T> =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T>(path: string): Promise<T> => request<T>(path, { method: 'DELETE' })
}

// Helper to build query strings from a params object, skipping null/empty/NaN values.
export function buildQuery(params: Record<string, unknown> | object): string {
  const qs = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => {
    if (v == null || v === '' || (typeof v === 'number' && isNaN(v))) return
    qs.append(k, String(v))
  })
  const s = qs.toString()
  return s ? `?${s}` : ''
}
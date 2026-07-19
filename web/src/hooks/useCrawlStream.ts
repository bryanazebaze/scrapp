/**
 * useCrawlStream — fetch-based SSE consumer for crawl progress.
 * Uses fetch + ReadableStream to support admin JWT auth headers
 * (EventSource doesn't support custom headers).
 */
import { useState, useCallback, useRef } from 'react'
import { getAdminToken, ADMIN_TOKEN_KEY } from '@/lib/api'

const SSE_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface CrawlProgressState {
  status: 'idle' | 'connecting' | 'streaming' | 'done' | 'error'
  sourceSlug: string | null
  currentPage: number
  listingsFound: number
  message: string
  stats: Record<string, unknown> | null
  error: string | null
  newListings: number
  duplicates: number
  pendingCount: number
  autoPromoted: number
  recrawl: number
  removed: number
}

const initialState: CrawlProgressState = {
  status: 'idle',
  sourceSlug: null,
  currentPage: 0,
  listingsFound: 0,
  message: '',
  stats: null,
  error: null,
  newListings: 0,
  duplicates: 0,
  pendingCount: 0,
  autoPromoted: 0,
  recrawl: 0,
  removed: 0,
}

export function useCrawlStream() {
  const [state, setState] = useState<CrawlProgressState>(initialState)
  const abortRef = useRef<AbortController | null>(null)

  const startCrawl = useCallback(async (slug: string) => {
    // Abort any existing crawl
    if (abortRef.current) {
      abortRef.current.abort()
    }

    const controller = new AbortController()
    abortRef.current = controller

    setState({ ...initialState, status: 'connecting', sourceSlug: slug })

    const token = getAdminToken()
    try {
      const response = await fetch(`${SSE_BASE}/admin/sources/${slug}/crawl/stream`, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          'Accept': 'text/event-stream',
        },
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('No response body reader available')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      setState(prev => ({ ...prev, status: 'streaming' }))

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })

        // Parse SSE frames from the buffer
        const lines = buffer.split('\n')
        buffer = lines.pop() || '' // Keep incomplete line in buffer

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const data = JSON.parse(dataStr)

              if (currentEvent === 'progress' || data.type === 'progress') {
                setState(prev => ({
                  ...prev,
                  currentPage: data.page ?? prev.currentPage,
                  listingsFound: data.listings ?? prev.listingsFound,
                  message: data.message ?? prev.message,
                }))
              } else if (currentEvent === 'error' || data.type === 'error') {
                setState(prev => ({
                  ...prev,
                  error: data.message ?? 'Erreur inconnue',
                }))
              } else if (currentEvent === 'done' || data.type === 'done') {
                const stats = data.stats || {}
                // Ingest stats keys: new, recrawl, rejected, linked, created_canonical, removed
                setState(prev => ({
                  ...prev,
                  status: 'done',
                  stats,
                  newListings: (stats as Record<string, number>).new || 0,
                  duplicates: (stats as Record<string, number>).linked || 0,
                  pendingCount: (stats as Record<string, number>).pending || 0,
                  autoPromoted: ((stats as Record<string, number>).created_canonical || 0) + ((stats as Record<string, number>).linked || 0),
                  recrawl: (stats as Record<string, number>).recrawl || 0,
                  removed: (stats as Record<string, number>).removed || 0,
                  message: 'Crawl terminé',
                }))
              }
            } catch {
              // Skip unparseable SSE data
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Erreur de connexion SSE',
      }))
    }
  }, [])

  const resetCrawl = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setState(initialState)
  }, [])

  return { state, startCrawl, resetCrawl }
}

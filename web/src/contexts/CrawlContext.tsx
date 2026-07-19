/**
 * CrawlContext — global crawl state shared across admin pages.
 * When a crawl is launched from Sources or Jobs, both pages see the same
 * live SSE progress and listing data.
 */
import { createContext, useContext, useState, useCallback, useRef, ReactNode } from 'react'
import { getAdminToken } from '@/lib/api'

const SSE_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export interface CrawlListing {
  index: number
  url_source: string | null
  title_raw: string | null
  price_raw: string | null
  price_parsed: number | null
  currency: string | null
  location_raw: string | null
  description_raw: string | null
  property_type_raw: string | null
  images_raw: string[]
  match_confidence: number | null
  payload: Record<string, unknown> | null
}

export interface CrawlState {
  status: 'idle' | 'connecting' | 'streaming' | 'done' | 'error'
  sourceSlug: string | null
  currentPage: number
  listingsFound: number
  message: string
  error: string | null
  stats: Record<string, unknown> | null
  newListings: number
  duplicates: number
  pendingCount: number
  autoPromoted: number
  recrawl: number
  removed: number
  // Test crawl listing data
  listings: CrawlListing[]
}

const initialState: CrawlState = {
  status: 'idle',
  sourceSlug: null,
  currentPage: 0,
  listingsFound: 0,
  message: '',
  error: null,
  stats: null,
  newListings: 0,
  duplicates: 0,
  pendingCount: 0,
  autoPromoted: 0,
  recrawl: 0,
  removed: 0,
  listings: [],
}

interface CrawlContextValue {
  state: CrawlState
  startCrawl: (slug: string, testMode?: boolean, maxPages?: number) => void
  stopCrawl: () => void
}

const CrawlContext = createContext<CrawlContextValue>({
  state: initialState,
  startCrawl: () => {},
  stopCrawl: () => {},
})

export function CrawlProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<CrawlState>(initialState)
  const abortRef = useRef<AbortController | null>(null)

  const stopCrawl = useCallback(() => {
    if (abortRef.current) {
      abortRef.current.abort()
      abortRef.current = null
    }
    setState(initialState)
  }, [])

  const startCrawl = useCallback(async (slug: string, testMode = true, maxPages = 1) => {
    if (abortRef.current) {
      abortRef.current.abort()
    }
    const controller = new AbortController()
    abortRef.current = controller

    const endpoint = testMode
      ? `/admin/sources/${slug}/crawl/test/stream?max_pages=${maxPages}`
      : `/admin/sources/${slug}/crawl/stream`

    setState({ ...initialState, status: 'connecting', sourceSlug: slug })

    const token = getAdminToken()
    try {
      const response = await fetch(`${SSE_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          Accept: 'text/event-stream',
        },
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No reader')

      const decoder = new TextDecoder()
      let buffer = ''

      setState(prev => ({ ...prev, status: 'streaming' }))

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const data = JSON.parse(dataStr)
              const eventType = currentEvent || data.type

              if (eventType === 'progress') {
                setState(prev => ({
                  ...prev,
                  currentPage: data.page ?? prev.currentPage,
                  listingsFound: data.listings ?? prev.listingsFound,
                  message: data.message ?? prev.message,
                }))
              } else if (eventType === 'listing') {
                setState(prev => ({
                  ...prev,
                  listings: [...prev.listings, data as CrawlListing],
                }))
              } else if (eventType === 'error') {
                setState(prev => ({ ...prev, error: data.message ?? 'Erreur' }))
              } else if (eventType === 'done') {
                const stats = data.stats || {}
                setState(prev => ({
                  ...prev,
                  status: 'done',
                  stats,
                  newListings: (stats as Record<string, number>).new || (stats as Record<string, number>).total || 0,
                  duplicates: (stats as Record<string, number>).linked || 0,
                  pendingCount: (stats as Record<string, number>).pending || 0,
                  autoPromoted: ((stats as Record<string, number>).created_canonical || 0) + ((stats as Record<string, number>).linked || 0),
                  recrawl: (stats as Record<string, number>).recrawl || 0,
                  removed: (stats as Record<string, number>).removed || 0,
                  message: 'Crawl terminé',
                }))
              }
            } catch { /* skip unparseable */ }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === 'AbortError') return
      setState(prev => ({
        ...prev,
        status: 'error',
        error: err instanceof Error ? err.message : 'Erreur SSE',
      }))
    }
  }, [])

  return (
    <CrawlContext.Provider value={{ state, startCrawl, stopCrawl }}>
      {children}
    </CrawlContext.Provider>
  )
}

export function useCrawlContext() {
  return useContext(CrawlContext)
}

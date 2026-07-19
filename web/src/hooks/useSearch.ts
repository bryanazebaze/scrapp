import { useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '@/lib/api'
import type { AnnonceBreve } from '@/lib/types'

export interface SearchParams {
  q: string
  skip?: number
  limit?: number
  city?: string
  neighborhood?: string
  min_price?: number
  max_price?: number
  property_type?: string
}

export function useSearch(params: SearchParams) {
  const q = buildQuery(params)
  return useQuery<AnnonceBreve[]>({
    enabled: !!params.q && params.q.trim().length > 0,
    queryKey: ['search', q],
    queryFn: () => api.get(`/search${q}`),
    placeholderData: (prev) => prev
  })
}
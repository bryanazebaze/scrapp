import { useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '@/lib/api'
import type { LocationSchema, NeighborhoodAnalyticsSchema, TrendingNeighborhood } from '@/lib/types'

export function useNeighborhoods(city?: string) {
  const q = buildQuery({ city })
  return useQuery<LocationSchema[]>({
    queryKey: ['neighborhoods', city || 'all'],
    queryFn: () => api.get(`/neighborhoods${q}`)
  })
}

export function useNeighborhoodAnalytics(slug: string | undefined, propertyType?: string) {
  const q = buildQuery({ property_type: propertyType })
  return useQuery<NeighborhoodAnalyticsSchema>({
    enabled: !!slug,
    queryKey: ['neighborhood', slug, propertyType || 'all'],
    queryFn: () => api.get(`/neighborhoods/${slug}${q}`)
  })
}

export function useCityNeighborhoods(city: string | undefined) {
  return useQuery<NeighborhoodAnalyticsSchema[]>({
    enabled: !!city,
    queryKey: ['city-neighborhoods', city],
    queryFn: () => api.get(`/neighborhoods/city/${encodeURIComponent(city!)}`)
  })
}

export function useTrendingNeighborhoods(limit = 10) {
  return useQuery<TrendingNeighborhood[]>({
    queryKey: ['trending', limit],
    queryFn: () => api.get(`/neighborhoods/trending/list?limit=${limit}`)
  })
}
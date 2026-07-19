import { useQuery } from '@tanstack/react-query'
import { api, buildQuery } from '@/lib/api'
import type { AnnonceBreve } from '@/lib/types'

export interface ListingsParams {
  skip?: number
  limit?: number
  property_type?: string
  city?: string
  neighborhood?: string
  min_price?: number
  max_price?: number
  min_bedrooms?: number
  max_bedrooms?: number
  min_area?: number
  max_area?: number
  min_bathrooms?: number
  q?: string
}

export function useListings(params: ListingsParams = {}) {
  const q = buildQuery({ skip: 0, limit: 50, ...params })
  return useQuery<AnnonceBreve[]>({
    queryKey: ['listings', q],
    queryFn: () => api.get(`/annonces${q}`),
    placeholderData: (prev) => prev
  })
}

export function useNearby(lat: number, lng: number, radiusKm = 5) {
  const q = buildQuery({ lat, lng, radius_km: radiusKm })
  return useQuery<AnnonceBreve[]>({
    enabled: !isNaN(lat) && !isNaN(lng),
    queryKey: ['nearby', q],
    queryFn: () => api.get(`/annonces/nearby${q}`)
  })
}
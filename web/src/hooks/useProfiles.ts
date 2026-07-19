import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { CityProfileSchema, NeighborhoodProfileSchema } from '@/lib/types'

export function useCities() {
  return useQuery<CityProfileSchema[]>({
    queryKey: ['cities'],
    queryFn: () => api.get('/profiles/cities')
  })
}

export function useCityProfile(city: string | undefined) {
  return useQuery<CityProfileSchema>({
    enabled: !!city,
    queryKey: ['city-profile', city],
    queryFn: () => api.get(`/profiles/cities/${encodeURIComponent(city!)}`)
  })
}

export function useCityNeighborhoodProfiles(city: string | undefined) {
  return useQuery<NeighborhoodProfileSchema[]>({
    enabled: !!city,
    queryKey: ['city-neighborhood-profiles', city],
    queryFn: () => api.get(`/profiles/city/${encodeURIComponent(city!)}/neighborhoods`)
  })
}

export function useNeighborhoodProfileByLocation(locationId: number | string | undefined) {
  return useQuery<NeighborhoodProfileSchema>({
    enabled: locationId != null,
    queryKey: ['neighborhood-profile-by-loc', String(locationId)],
    queryFn: () => api.get(`/profiles/neighborhoods/by-location/${locationId}`)
  })
}
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { SourceSchema, SchedulerJobSchema, CrawlResult, HealthSchema, PendingItem, ReviewAction, CrawlSessionSummary, DashboardStats, DuplicateItem } from '@/lib/types'

export function usePendingReviews(skip = 0, limit = 50) {
  return useQuery<PendingItem[]>({
    queryKey: ['pending', skip, limit],
    queryFn: () => api.get(`/admin/review/pending?skip=${skip}&limit=${limit}`)
  })
}

export function useReviewAction() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: ReviewAction['action'] }) =>
      api.post<{ ok: boolean; review_status: string }>(`/admin/review/${id}`, { action }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pending'] })
      qc.invalidateQueries({ queryKey: ['listings'] })
    }
  })
}

export function useSources() {
  return useQuery<SourceSchema[]>({
    queryKey: ['sources'],
    queryFn: () => api.get('/admin/sources')
  })
}

export function useToggleSource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => api.post<SourceSchema>(`/admin/sources/${slug}/toggle`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sources'] })
  })
}

export function useCrawlSource() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (slug: string) => api.post<CrawlResult>(`/admin/sources/${slug}/crawl`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['sources'] })
  })
}

export function useRecomputeAnalytics() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: () => api.post<CrawlResult>('/admin/analytics/recompute'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['neighborhood'] })
      qc.invalidateQueries({ queryKey: ['city-neighborhoods'] })
      qc.invalidateQueries({ queryKey: ['trending'] })
    }
  })
}

export function useJobs() {
  return useQuery<SchedulerJobSchema[]>({
    queryKey: ['jobs'],
    queryFn: () => api.get('/admin/jobs'),
    refetchInterval: 30_000
  })
}

export function useHealth() {
  return useQuery<HealthSchema>({
    queryKey: ['health'],
    queryFn: () => api.get('/health'),
    refetchInterval: 15_000
  })
}

export function useDashboard() {
  return useQuery<DashboardStats>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/admin/dashboard'),
    refetchInterval: 60_000,
  })
}

export function useCrawlSessions(slug: string | null, limit = 10) {
  return useQuery<CrawlSessionSummary[]>({
    queryKey: ['crawl-sessions', slug, limit],
    queryFn: () => api.get(`/admin/sources/${slug}/crawl/sessions?limit=${limit}`),
    enabled: !!slug,
  })
}

export function useDuplicates(skip = 0, limit = 50) {
  return useQuery<DuplicateItem[]>({
    queryKey: ['duplicates', skip, limit],
    queryFn: () => api.get(`/admin/review/duplicates?skip=${skip}&limit=${limit}`),
  })
}

export function useValidateDuplicate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, action }: { id: number; action: 'confirm_duplicate' | 'not_duplicate' }) =>
      api.post<{ ok: boolean; action: string }>(`/admin/review/duplicates/${id}`, { action }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['duplicates'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
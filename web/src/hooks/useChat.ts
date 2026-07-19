import { useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { ChatMessage, ChatResponse } from '@/lib/types'

export function useChat() {
  return useMutation<ChatResponse, Error, { message: string; history: ChatMessage[]; language?: 'fr' | 'en' }>({
    mutationFn: (body) => api.post<ChatResponse>('/chat', { language: 'fr', ...body })
  })
}
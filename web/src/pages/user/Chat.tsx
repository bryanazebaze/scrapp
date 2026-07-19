import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Sparkles, Wrench } from 'lucide-react'
import { useChat } from '@/hooks/useChat'
import type { ChatMessage, ChatResponse, AnnonceBreve } from '@/lib/types'
import { cn } from '@/lib/utils'
import ListingCard from '@/components/listings/ListingCard'
import Spinner from '@/components/ui/Spinner'
import Footer from '@/components/layout/Footer'

interface ExtendedChatMessage extends ChatMessage {
  properties?: AnnonceBreve[]
  toolUsed?: string | null
  toolMetadata?: ChatResponse['tool_metadata'] | null
}

const SUGGESTED_PROMPTS = [
  'Quartiers en hausse à Douala',
  '3 chambres à Bonamoussadi < 100k',
  'Maisons à Yaoundé entre 20 et 50 millions',
  'Studios abordables à Akwa',
]

function MessageBubble({ msg }: { msg: ExtendedChatMessage }) {
  const isUser = msg.role === 'user'

  return (
    <div className={cn('flex w-full', isUser ? 'justify-end' : 'justify-start')}>
      <div className={cn('max-w-[85%] space-y-3', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'rounded-2xl px-4 py-3 text-sm',
            isUser
              ? 'bg-gradient-to-r from-brand-500 to-brand-400 text-white'
              : 'glass text-fg',
          )}
        >
          <p className="whitespace-pre-wrap">{msg.content}</p>
        </div>

        {/* Inline property cards */}
        {msg.properties && msg.properties.length > 0 && (
          <div className="grid w-full grid-cols-1 gap-3 sm:grid-cols-2">
            {msg.properties.slice(0, 4).map((p) => (
              <ListingCard key={p.id} listing={p} />
            ))}
          </div>
        )}

        {/* Tool badge */}
        {msg.toolUsed && (
          <div className="inline-flex items-center gap-1.5 rounded-lg bg-white/5 px-2.5 py-1 text-xs text-white/40">
            <Wrench className="h-3 w-3" aria-hidden="true" />
            Outil: {msg.toolUsed}
          </div>
        )}
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ExtendedChatMessage[]>([
    {
      role: 'assistant',
      content:
        "Bonjour ! Je suis votre assistant immobilier. Posez-moi vos questions sur le marché immobilier camerounais — quartiers, prix, biens disponibles...",
    },
  ])
  const [input, setInput] = useState('')
  const chat = useChat()
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  const send = async (text?: string) => {
    const msg = (text ?? input).trim()
    if (!msg || chat.isPending) return

    const userMsg: ExtendedChatMessage = { role: 'user', content: msg }
    const history: ChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }))

    setMessages((prev) => [...prev, userMsg])
    setInput('')

    try {
      const res: ChatResponse = await chat.mutateAsync({
        message: msg,
        history,
        language: 'fr',
      })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply,
          properties: res.properties,
          toolUsed: res.tool_used,
          toolMetadata: res.tool_metadata,
        },
      ])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "Désolé, une erreur est survenue. Réessayez dans un instant.",
        },
      ])
    }
  }

  return (
    <div className="flex min-h-[calc(100vh-4rem)] flex-col px-4 pb-6">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="mb-4"
        >
          <h1 className="flex items-center gap-2 text-2xl font-bold text-fg">
            <Sparkles className="h-6 w-6 text-brand-500" aria-hidden="true" />
            Assistant immobilier
          </h1>
          <p className="text-sm text-white/50">
            Posez vos questions sur le marché immobilier camerounais.
          </p>
        </motion.div>

        {/* Messages */}
        <div
          ref={scrollRef}
          className="glass flex-1 space-y-4 overflow-y-auto rounded-2xl p-4"
        >
          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
              >
                <MessageBubble msg={msg} />
              </motion.div>
            ))}
          </AnimatePresence>

          {chat.isPending && (
            <div className="flex justify-start">
              <div className="glass rounded-2xl px-4 py-3">
                <Spinner size={20} />
              </div>
            </div>
          )}
        </div>

        {/* Suggested prompts */}
        <div className="mt-3 flex flex-wrap gap-2">
          {SUGGESTED_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => send(p)}
              disabled={chat.isPending}
              className="rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-fg/70 transition hover:border-white/20 hover:text-fg disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>

        {/* Input */}
        <form
          onSubmit={(e) => {
            e.preventDefault()
            send()
          }}
          className="mt-3 flex items-center gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question..."
            disabled={chat.isPending}
            className="glass-input flex-1"
            aria-label="Message"
          />
          <button
            type="submit"
            disabled={!input.trim() || chat.isPending}
            aria-label="Envoyer"
            className="inline-flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-brand-500 to-brand-400 text-white transition hover:shadow-lg hover:shadow-brand-500/40 disabled:opacity-50"
          >
            <Send className="h-5 w-5" />
          </button>
        </form>
      </div>
      <Footer />
    </div>
  )
}
import { useState, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ImageOff, ChevronLeft, ChevronRight } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ListingGalleryProps {
  images: string[]
}

export default function ListingGallery({ images }: ListingGalleryProps) {
  const [index, setIndex] = useState(0)
  const hasImages = images.length > 0
  const current = hasImages ? images[index] : null

  const goLeft = useCallback(() => {
    if (!hasImages) return
    setIndex((i) => (i === 0 ? images.length - 1 : i - 1))
  }, [hasImages, images.length])

  const goRight = useCallback(() => {
    if (!hasImages) return
    setIndex((i) => (i === images.length - 1 ? 0 : i + 1))
  }, [hasImages, images.length])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowLeft') goLeft()
      if (e.key === 'ArrowRight') goRight()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [goLeft, goRight])

  if (!hasImages) {
    return (
      <div className="glass flex aspect-video w-full items-center justify-center rounded-2xl">
        <div className="flex flex-col items-center gap-3">
          <ImageOff className="h-12 w-12 text-white/30" aria-hidden="true" />
          <p className="text-sm text-white/40">Aucune image disponible</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Main image */}
      <div className="glass relative aspect-video overflow-hidden rounded-2xl">
        <AnimatePresence mode="wait">
          <motion.img
            key={index}
            src={current!}
            alt={`Image ${index + 1} sur ${images.length}`}
            initial={{ opacity: 0, scale: 1.02 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="h-full w-full object-cover"
          />
        </AnimatePresence>

        {images.length > 1 && (
          <>
            <button
              onClick={goLeft}
              aria-label="Image précédente"
              className="absolute left-3 top-1/2 -translate-y-1/2 rounded-xl bg-ink-900/60 p-2 backdrop-blur-md transition hover:bg-ink-900/80"
            >
              <ChevronLeft className="h-5 w-5 text-white" />
            </button>
            <button
              onClick={goRight}
              aria-label="Image suivante"
              className="absolute right-3 top-1/2 -translate-y-1/2 rounded-xl bg-ink-900/60 p-2 backdrop-blur-md transition hover:bg-ink-900/80"
            >
              <ChevronRight className="h-5 w-5 text-white" />
            </button>
            <div className="absolute bottom-3 right-3 rounded-lg bg-ink-900/60 px-2.5 py-1 backdrop-blur-md">
              <span className="text-xs text-white/80">
                {index + 1} / {images.length}
              </span>
            </div>
          </>
        )}
      </div>

      {/* Thumbnails */}
      {images.length > 1 && (
        <div className="flex gap-2 overflow-x-auto no-scrollbar">
          {images.map((src, i) => (
            <button
              key={i}
              onClick={() => setIndex(i)}
              aria-label={`Sélectionner l'image ${i + 1}`}
              className={cn(
                'h-16 w-24 shrink-0 overflow-hidden rounded-lg border-2 transition',
                i === index
                  ? 'border-brand-500'
                  : 'border-transparent opacity-60 hover:opacity-100',
              )}
            >
              <img
                src={src}
                alt={`Miniature ${i + 1}`}
                loading="lazy"
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
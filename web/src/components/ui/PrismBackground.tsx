/**
 * PrismBackground — fixed full-screen animated aurora-mesh background.
 * Colors swap via CSS vars (--blob-*) set in index.css for light/dark.
 * Light mode additionally renders a subtle network-particles canvas.
 * Renders behind all content (fixed inset-0 -z-10).
 */
import { useEffect, useRef } from 'react'
import { useTheme } from '@/contexts/ThemeContext'

/** Light-mode-only subtle network of nodes + connecting lines. */
function NetworkParticles() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Respect reduced-motion preference: render nothing.
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) return

    let raf = 0
    let width = 0
    let height = 0
    let dpr = 1

    interface Node {
      x: number
      y: number
      vx: number
      vy: number
      r: number
    }
    let nodes: Node[] = []

    // Warm, muted particle palette matching the light-mode prism accents.
    const nodeColor = '196, 96, 64'      // dusty terracotta
    const lineColor = '138, 58, 92'      // dusty plum
    const accentColor = '197, 142, 64'   // muted ochre

    const NODE_COUNT_BASE = 46
    const MAX_DIST = 150      // px — link distance
    const MOUSE_DIST = 190    // px — mouse influence radius

    const mouse = { x: -9999, y: -9999 }

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2)
      width = canvas.clientWidth
      height = canvas.clientHeight
      canvas.width = Math.floor(width * dpr)
      canvas.height = Math.floor(height * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      // Scale node count with viewport area, capped for perf.
      const target = Math.round(
        Math.min(80, NODE_COUNT_BASE * Math.sqrt((width * height) / (1280 * 720))),
      )
      nodes = Array.from({ length: target }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 0.22,
        vy: (Math.random() - 0.5) * 0.22,
        r: 1.1 + Math.random() * 1.6,
      }))
    }

    const onPointerMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect()
      mouse.x = e.clientX - rect.left
      mouse.y = e.clientY - rect.top
    }
    const onPointerLeave = () => {
      mouse.x = -9999
      mouse.y = -9999
    }

    const draw = () => {
      ctx.clearRect(0, 0, width, height)

      // Update positions
      for (const n of nodes) {
        n.x += n.vx
        n.y += n.vy
        if (n.x < 0 || n.x > width) n.vx *= -1
        if (n.y < 0 || n.y > height) n.vy *= -1
        // Soft drift toward mouse (subtle attraction)
        const dxm = mouse.x - n.x
        const dym = mouse.y - n.y
        const dm = Math.hypot(dxm, dym)
        if (dm < MOUSE_DIST) {
          const pull = (1 - dm / MOUSE_DIST) * 0.04
          n.vx += (dxm / (dm || 1)) * pull
          n.vy += (dym / (dm || 1)) * pull
        }
        // Friction to keep velocities bounded
        n.vx *= 0.992
        n.vy *= 0.992
      }

      // Draw links
      for (let i = 0; i < nodes.length; i++) {
        const a = nodes[i]
        for (let j = i + 1; j < nodes.length; j++) {
          const b = nodes[j]
          const dx = a.x - b.x
          const dy = a.y - b.y
          const dist = Math.hypot(dx, dy)
          if (dist < MAX_DIST) {
            const t = 1 - dist / MAX_DIST
            const alpha = t * 0.14
            ctx.strokeStyle = `rgba(${lineColor}, ${alpha})`
            ctx.lineWidth = 0.6
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.stroke()
          }
        }
      }

      // Draw nodes
      for (const n of nodes) {
        const dm = Math.hypot(mouse.x - n.x, mouse.y - n.y)
        const near = dm < MOUSE_DIST
        const alpha = near ? 0.5 : 0.28
        const color = near ? accentColor : nodeColor
        ctx.fillStyle = `rgba(${color}, ${alpha})`
        ctx.beginPath()
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2)
        ctx.fill()
      }

      raf = requestAnimationFrame(draw)
    }

    resize()
    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', onPointerMove)
    window.addEventListener('pointerleave', onPointerLeave)
    raf = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', onPointerMove)
      window.removeEventListener('pointerleave', onPointerLeave)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="absolute inset-0 h-full w-full"
      style={{ pointerEvents: 'none' }}
    />
  )
}

export default function PrismBackground() {
  const { theme } = useTheme()
  const isLight = theme === 'light'

  return (
    <div
      aria-hidden="true"
      className="fixed inset-0 -z-10 overflow-hidden"
      style={{ backgroundColor: 'var(--page-bg)' }}
    >
      {/* Aurora blobs (colors + opacity via CSS vars) */}
      <div
        className="absolute -top-[10%] -left-[10%] h-[55vw] w-[55vw] rounded-full blur-3xl animate-aurora-slow"
        style={{
          opacity: 'var(--blob-opacity)',
          background:
            'radial-gradient(circle at center, var(--blob-1) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute -top-[5%] right-[5%] h-[50vw] w-[50vw] rounded-full blur-3xl animate-aurora-fast"
        style={{
          opacity: 'var(--blob-opacity)',
          background:
            'radial-gradient(circle at center, var(--blob-2) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute bottom-[5%] left-[15%] h-[45vw] w-[45vw] rounded-full blur-3xl animate-aurora-slow"
        style={{
          opacity: 'var(--blob-opacity)',
          background:
            'radial-gradient(circle at center, var(--blob-3) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute bottom-[0%] right-[10%] h-[40vw] w-[40vw] rounded-full blur-3xl animate-aurora-slow"
        style={{
          opacity: 'var(--blob-opacity)',
          background:
            'radial-gradient(circle at center, var(--blob-4) 0%, transparent 70%)',
        }}
      />

      {/* Network particles — light mode only */}
      {isLight && <NetworkParticles />}

      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0"
        style={{
          backgroundImage:
            'linear-gradient(var(--grid-line) 1px, transparent 1px), linear-gradient(90deg, var(--grid-line) 1px, transparent 1px)',
          backgroundSize: '60px 60px',
          opacity: 'var(--grid-opacity)',
        }}
      />

      {/* Noise overlay */}
      <svg
        className="absolute inset-0 h-full w-full"
        style={{ opacity: 'var(--noise-opacity)' }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <filter id="noise">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves="4"
            stitchTiles="stitch"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#noise)" />
      </svg>
    </div>
  )
}
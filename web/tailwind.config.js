/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        // Brand — warm terracotta orange (single source of truth, both modes)
        brand: {
          50: '#FFF8F4', 100: '#FDE8D4', 200: '#FBC9A3', 300: '#F7A66E',
          400: '#F18B3A', 500: '#E94E1B', 600: '#C2410C', 700: '#9A320A',
          800: '#732208', 900: '#4D1705'
        },
        // Prism — semantic accent labels. Values swap via CSS vars:
        // light = warm palette, dark = cool original palette.
        prism: {
          violet:  'rgb(var(--prism-violet) / <alpha-value>)',
          cyan:    'rgb(var(--prism-cyan) / <alpha-value>)',
          fuchsia: 'rgb(var(--prism-fuchsia) / <alpha-value>)',
          amber:   'rgb(var(--prism-amber) / <alpha-value>)',
          emerald: 'rgb(var(--prism-emerald) / <alpha-value>)',
        },
        // Ink — warm near-black. Swaps via CSS var (light=#1A1A17, dark=#07071a).
        // Used as dark text on bright badges and as deep surface bg in both modes.
        ink: {
          900: 'rgb(var(--ink-900) / <alpha-value>)',
          800: 'rgb(var(--ink-800) / <alpha-value>)',
          700: 'rgb(var(--ink-700) / <alpha-value>)',
        },
        success: '#1F8A4C',
        warning: '#D97706',
        danger:  '#C8322B',
        info:    '#2E6FB7',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif']
      },
      backdropBlur: { xs: '4px', '2xl': '40px', '3xl': '60px' },
      boxShadow: {
        glass:    '0 8px 32px var(--shadow-glass)',
        'glass-lg': '0 12px 48px var(--shadow-glass-lg)',
        card:     '0 2px 12px var(--shadow-card)',
        'card-hover': '0 8px 24px var(--shadow-card-hover)',
      },
      animation: {
        'aurora-slow': 'aurora 22s ease-in-out infinite',
        'aurora-fast': 'aurora 14s ease-in-out infinite',
        shimmer: 'shimmer 2.5s linear infinite',
        float: 'float 6s ease-in-out infinite',
        'fade-in': 'fadeIn 0.5s ease-out both',
        'slide-up': 'slideUp 0.5s ease-out both'
      },
      keyframes: {
        aurora: {
          '0%,100%': { transform: 'translate(0,0) scale(1)' },
          '33%': { transform: 'translate(6%,-4%) scale(1.08)' },
          '66%': { transform: 'translate(-5%,5%) scale(0.96)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' }
        },
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } }
      }
    }
  },
  plugins: []
}
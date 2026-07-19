/**
 * SearchInput — glass pill input with search icon and optional submit button.
 * Calls onSubmit on Enter key press.
 */
import { Search } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  onSubmit?: () => void
  placeholder?: string
  className?: string
}

export default function SearchInput({
  value,
  onChange,
  onSubmit,
  placeholder = 'Rechercher des annonces...',
  className,
}: SearchInputProps) {
  const [focused, setFocused] = useState(false)

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && onSubmit) {
      onSubmit()
    }
  }

  return (
    <div
      className={cn(
        'relative flex items-center w-full',
        className,
      )}
    >
      <Search
        className="absolute left-4 h-5 w-5 text-white/40 pointer-events-none"
        aria-hidden="true"
      />
      <label htmlFor="search-input" className="sr-only">
        {placeholder}
      </label>
      <input
        id="search-input"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder}
        className={cn(
          'glass-input w-full rounded-full pl-12 pr-4 text-base',
          focused && 'border-white/30 bg-white/[0.08]',
        )}
        aria-label={placeholder}
      />
    </div>
  )
}
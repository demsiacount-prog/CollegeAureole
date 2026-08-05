import { Search } from 'lucide-react'
import { Input } from './Input'

interface SearchInputProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchInput({ value, onChange, placeholder = 'Rechercher…', className }: SearchInputProps) {
  return (
    <div className={`relative max-w-sm ${className ?? ''}`}>
      <Search strokeWidth={1.75} className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-[var(--color-ink-faint)]" />
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-9"
      />
    </div>
  )
}

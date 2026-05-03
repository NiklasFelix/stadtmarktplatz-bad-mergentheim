import { Loader2 } from 'lucide-react'
import { clsx } from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  text?: string
  className?: string
}

const sizes = { sm: 16, md: 24, lg: 36 }

export function LoadingSpinner({ size = 'md', text, className }: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3 py-12', className)}>
      <Loader2 className="animate-spin text-primary-600" size={sizes[size]} />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  )
}

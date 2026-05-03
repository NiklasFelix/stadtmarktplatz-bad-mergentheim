import { clsx } from 'clsx'
import { CheckCircle2, Clock, Lock, XCircle } from 'lucide-react'
import type { ProductAvailability } from '../../types'
import { AVAILABILITY_LABELS } from '../../utils/formatters'

interface AvailabilityBadgeProps {
  availability: ProductAvailability
  className?: string
}

const config: Record<ProductAvailability, { icon: React.ReactNode; classes: string }> = {
  available:   { icon: <CheckCircle2 size={11} />, classes: 'bg-green-100 text-green-800' },
  on_request:  { icon: <Clock size={11} />,        classes: 'bg-amber-100 text-amber-700' },
  reserved:    { icon: <Lock size={11} />,         classes: 'bg-blue-100 text-blue-700' },
  unavailable: { icon: <XCircle size={11} />,      classes: 'bg-red-100 text-red-700' },
}

export function AvailabilityBadge({ availability, className }: AvailabilityBadgeProps) {
  const { icon, classes } = config[availability]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium',
        classes,
        className
      )}
    >
      {icon}
      {AVAILABILITY_LABELS[availability]}
    </span>
  )
}

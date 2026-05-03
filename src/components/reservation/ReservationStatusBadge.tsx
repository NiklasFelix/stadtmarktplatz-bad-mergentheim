import { clsx } from 'clsx'
import type { ReservationStatus } from '../../types'
import { RESERVATION_STATUS_LABELS, RESERVATION_STATUS_COLORS } from '../../utils/formatters'

interface ReservationStatusBadgeProps {
  status: ReservationStatus
  className?: string
}

export function ReservationStatusBadge({ status, className }: ReservationStatusBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        RESERVATION_STATUS_COLORS[status],
        className
      )}
    >
      {RESERVATION_STATUS_LABELS[status]}
    </span>
  )
}

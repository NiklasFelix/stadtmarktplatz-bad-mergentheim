import { useState, useMemo } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Search, ArrowRight, Filter, ClipboardList } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'
import { ReservationStatusBadge } from '../../components/reservation/ReservationStatusBadge'
import { EmptyState } from '../../components/ui/EmptyState'
import { formatDate, formatPickupTime, RESERVATION_STATUS_LABELS } from '../../utils/formatters'
import type { ReservationStatus } from '../../types'

const STATUS_OPTIONS: (ReservationStatus | 'all')[] = ['all', 'received', 'confirmed', 'ready', 'completed', 'cancelled']

export function SellerReservationsPage() {
  const { currentMerchantId } = useAuthStore()
  const { reservations, products } = useDataStore()
  const [searchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState<ReservationStatus | 'all'>(
    (searchParams.get('status') as ReservationStatus) ?? 'all'
  )

  const merchantReservations = reservations.filter((r) => r.merchantId === currentMerchantId)

  const filtered = useMemo(() => {
    return merchantReservations
      .filter((r) => {
        if (status !== 'all' && r.status !== status) return false
        if (search) {
          const q = search.toLowerCase()
          return (
            r.reservationNumber.toLowerCase().includes(q) ||
            r.customer.firstName.toLowerCase().includes(q) ||
            r.customer.lastName.toLowerCase().includes(q) ||
            r.customer.email.toLowerCase().includes(q)
          )
        }
        return true
      })
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
  }, [merchantReservations, status, search])

  const counts = STATUS_OPTIONS.reduce((acc, s) => {
    acc[s] = s === 'all'
      ? merchantReservations.length
      : merchantReservations.filter((r) => r.status === s).length
    return acc
  }, {} as Record<string, number>)

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Reservierungen</h1>
        <p className="text-gray-500 mt-1">{merchantReservations.length} Reservierungen insgesamt</p>
      </div>

      {/* Status filter tabs */}
      <div className="flex flex-wrap gap-2 mb-5 overflow-x-auto pb-1">
        {STATUS_OPTIONS.map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-all border whitespace-nowrap ${
              status === s
                ? 'bg-primary-700 text-white border-primary-700'
                : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'
            }`}
          >
            {s === 'all' ? 'Alle' : RESERVATION_STATUS_LABELS[s]}
            <span className={`ml-1.5 text-xs px-1.5 py-0.5 rounded-full ${
              status === s ? 'bg-white/20 text-white' : 'bg-gray-100 text-gray-600'
            }`}>
              {counts[s]}
            </span>
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="relative mb-5">
        <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Suchen nach Name, E-Mail, Reservierungsnummer…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
        />
      </div>

      {/* Reservation list */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<ClipboardList size={40} />}
          title="Keine Reservierungen"
          description={status !== 'all' ? 'Keine Reservierungen mit diesem Status.' : 'Es sind noch keine Reservierungen eingegangen.'}
        />
      ) : (
        <div className="space-y-3">
          {filtered.map((r) => {
            const product = products.find((p) => p.id === r.productId)
            return (
              <Link
                key={r.id}
                to={`/seller/reservierungen/${r.id}`}
                className="card p-4 flex items-center gap-4 hover:shadow-card-hover transition-all group"
              >
                {/* Product thumbnail */}
                {product?.images[0] && (
                  <img
                    src={product.images[0]}
                    alt={product.name}
                    className="w-14 h-14 rounded-lg object-cover shrink-0"
                  />
                )}

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-gray-900 text-sm">{r.customer.firstName} {r.customer.lastName}</span>
                    <span className="text-xs text-gray-400 font-mono">{r.reservationNumber}</span>
                  </div>
                  <p className="text-sm text-gray-600 truncate mt-0.5">{product?.name ?? '—'} · {r.quantity}×</p>
                  <div className="flex items-center gap-3 mt-1 flex-wrap">
                    <span className="text-xs text-gray-400">Eingegangen: {formatDate(r.createdAt)}</span>
                    <span className="text-xs text-secondary-600">Abholung: {formatPickupTime(r.pickupTime)}</span>
                  </div>
                </div>

                {/* Status + Arrow */}
                <div className="flex items-center gap-3 shrink-0">
                  <ReservationStatusBadge status={r.status} />
                  <ArrowRight size={16} className="text-gray-300 group-hover:text-primary-500 transition-colors" />
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}

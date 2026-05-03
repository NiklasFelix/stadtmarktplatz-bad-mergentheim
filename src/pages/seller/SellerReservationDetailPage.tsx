import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  ArrowLeft, Phone, Mail, Clock, CheckCircle2, XCircle,
  Package, User, MessageSquare, Save, Search
} from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { updateReservationStatus } from '../../services/api'
import { ReservationStatusBadge } from '../../components/reservation/ReservationStatusBadge'
import { Textarea } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { EmptyState } from '../../components/ui/EmptyState'
import {
  formatDate, formatPickupTime, formatPrice,
  RESERVATION_STATUS_LABELS
} from '../../utils/formatters'
import type { ReservationStatus } from '../../types'

const STATUS_FLOW: Record<ReservationStatus, ReservationStatus[]> = {
  received:  ['confirmed', 'cancelled'],
  confirmed: ['ready', 'cancelled'],
  ready:     ['completed', 'cancelled'],
  completed: [],
  cancelled: [],
}

export function SellerReservationDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { reservations, products } = useDataStore()
  const updateStatus = useDataStore((s) => s.updateReservationStatus)
  const [notes, setNotes] = useState('')
  const [saving, setSaving] = useState(false)
  const [notesSaved, setNotesSaved] = useState(false)

  const reservation = reservations.find((r) => r.id === id)
  const product = reservation ? products.find((p) => p.id === reservation.productId) : null

  if (!reservation || !product) {
    return (
      <div className="py-20 text-center">
        <EmptyState icon={<Search size={36} />} title="Reservierung nicht gefunden" />
        <Link to="/seller/reservierungen" className="btn-outline mt-4 inline-flex items-center gap-2">
          <ArrowLeft size={16} />Zurück
        </Link>
      </div>
    )
  }

  const nextStatuses = STATUS_FLOW[reservation.status]
  const currentNotes = reservation.merchantNotes ?? ''

  async function handleStatusChange(newStatus: ReservationStatus) {
    setSaving(true)
    await updateReservationStatus(reservation!.id, newStatus)
    setSaving(false)
  }

  async function saveNotes() {
    setSaving(true)
    useDataStore.getState().updateReservation(reservation!.id, { merchantNotes: notes || currentNotes })
    setSaving(false)
    setNotesSaved(true)
    setTimeout(() => setNotesSaved(false), 2000)
  }

  const statusButtonVariants: Record<ReservationStatus, 'primary' | 'secondary' | 'danger'> = {
    confirmed: 'primary',
    ready: 'secondary',
    completed: 'primary',
    cancelled: 'danger',
    received: 'primary',
  }

  return (
    <div>
      {/* Back + title */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/seller/reservierungen" className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reservierung</h1>
          <p className="text-gray-500 text-sm font-mono">{reservation.reservationNumber}</p>
        </div>
        <div className="ml-auto">
          <ReservationStatusBadge status={reservation.status} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main */}
        <div className="lg:col-span-2 space-y-5">
          {/* Customer info */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <User size={18} className="text-primary-600" />
              Kundendaten
            </h2>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs text-gray-400 mb-1">Name</p>
                <p className="font-medium text-gray-900">{reservation.customer.firstName} {reservation.customer.lastName}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 mb-1">E-Mail</p>
                <a href={`mailto:${reservation.customer.email}`} className="font-medium text-primary-700 hover:underline text-sm break-all">
                  {reservation.customer.email}
                </a>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <a
                href={`tel:${reservation.customer.phone}`}
                className="flex items-center gap-2 text-sm bg-primary-50 text-primary-700 px-3 py-2 rounded-lg hover:bg-primary-100 transition-colors"
              >
                <Phone size={14} />
                {reservation.customer.phone}
              </a>
              <a
                href={`mailto:${reservation.customer.email}`}
                className="flex items-center gap-2 text-sm bg-gray-50 text-gray-600 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <Mail size={14} />
                E-Mail senden
              </a>
            </div>
            {reservation.customer.message && (
              <div className="mt-4 p-3 bg-amber-50 rounded-xl border border-amber-100">
                <p className="text-xs font-medium text-amber-700 mb-1 flex items-center gap-1">
                  <MessageSquare size={12} /> Nachricht des Kunden:
                </p>
                <p className="text-sm text-amber-900">{reservation.customer.message}</p>
              </div>
            )}
          </div>

          {/* Product */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Package size={18} className="text-primary-600" />
              Reserviertes Produkt
            </h2>
            <div className="flex gap-4">
              {product.images[0] && (
                <img src={product.images[0]} alt={product.name} className="w-20 h-20 rounded-xl object-cover shrink-0" />
              )}
              <div>
                <p className="font-semibold text-gray-900">{product.name}</p>
                <p className="text-sm text-gray-500 mt-1">{formatPrice(product.price)}</p>
                <p className="text-sm text-gray-600 mt-1">Menge: <strong>{reservation.quantity}×</strong></p>
              </div>
            </div>
          </div>

          {/* Pickup time */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock size={18} className="text-primary-600" />
              Abholtermin
            </h2>
            <p className="text-xl font-bold text-gray-900">{formatPickupTime(reservation.pickupTime)}</p>
            <p className="text-sm text-gray-500 mt-2">Reservierung eingegangen: {formatDate(reservation.createdAt)}</p>
            <p className="text-sm text-gray-500">Zuletzt aktualisiert: {formatDate(reservation.updatedAt)}</p>
          </div>

          {/* Merchant notes */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <MessageSquare size={18} className="text-primary-600" />
              Interne Notizen
            </h2>
            {currentNotes && (
              <div className="mb-3 p-3 bg-gray-50 rounded-lg text-sm text-gray-700">
                {currentNotes}
              </div>
            )}
            <Textarea
              placeholder="Interne Notizen zur Reservierung (nur für Sie sichtbar)…"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
            />
            <Button
              variant="outline"
              size="sm"
              className="mt-2"
              loading={saving}
              leftIcon={notesSaved ? <CheckCircle2 size={14} /> : <Save size={14} />}
              onClick={saveNotes}
            >
              {notesSaved ? 'Gespeichert!' : 'Notiz speichern'}
            </Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Status actions */}
          {nextStatuses.length > 0 && (
            <div className="card p-5">
              <h3 className="font-semibold text-gray-900 mb-4">Status ändern</h3>
              <div className="space-y-2">
                {nextStatuses.map((nextStatus) => (
                  <Button
                    key={nextStatus}
                    variant={statusButtonVariants[nextStatus]}
                    className="w-full"
                    loading={saving}
                    leftIcon={
                      nextStatus === 'cancelled' ? <XCircle size={16} /> :
                      nextStatus === 'completed' ? <CheckCircle2 size={16} /> :
                      <Clock size={16} />
                    }
                    onClick={() => handleStatusChange(nextStatus)}
                  >
                    {RESERVATION_STATUS_LABELS[nextStatus]}
                  </Button>
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-3">Aktueller Status: <strong>{RESERVATION_STATUS_LABELS[reservation.status]}</strong></p>
            </div>
          )}

          {/* Status history */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Zeitlinie</h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 text-sm">
                <div className="w-2 h-2 rounded-full bg-primary-500 mt-1.5 shrink-0" />
                <div>
                  <p className="font-medium text-gray-700">Reservierung eingegangen</p>
                  <p className="text-xs text-gray-400">{formatDate(reservation.createdAt)}</p>
                </div>
              </div>
              {reservation.updatedAt !== reservation.createdAt && (
                <div className="flex items-start gap-3 text-sm">
                  <div className="w-2 h-2 rounded-full bg-secondary-500 mt-1.5 shrink-0" />
                  <div>
                    <p className="font-medium text-gray-700">Status geändert: {RESERVATION_STATUS_LABELS[reservation.status]}</p>
                    <p className="text-xs text-gray-400">{formatDate(reservation.updatedAt)}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

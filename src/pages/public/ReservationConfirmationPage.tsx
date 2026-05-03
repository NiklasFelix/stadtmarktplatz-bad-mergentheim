import { useParams, Link } from 'react-router-dom'
import { CheckCircle2, Clock, MapPin, Phone, Mail, ArrowRight, Home, Search } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { formatPickupTime, formatDate, WEEKDAY_LABELS } from '../../utils/formatters'
import { AvailabilityBadge } from '../../components/product/AvailabilityBadge'
import { EmptyState } from '../../components/ui/EmptyState'

export function ReservationConfirmationPage() {
  const { id } = useParams<{ id: string }>()
  const reservations = useDataStore((s) => s.reservations)
  const products = useDataStore((s) => s.products)
  const merchants = useDataStore((s) => s.merchants)

  const reservation = reservations.find((r) => r.id === id)
  const product = reservation ? products.find((p) => p.id === reservation.productId) : null
  const merchant = reservation ? merchants.find((m) => m.id === reservation.merchantId) : null

  if (!reservation || !product || !merchant) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <EmptyState icon={<Search size={40} />} title="Reservierung nicht gefunden" />
        <Link to="/" className="btn-primary mt-4 inline-flex items-center gap-2">
          <Home size={16} />Zur Startseite
        </Link>
      </div>
    )
  }

  const today = ['sonntag', 'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag']
  const openDays = Object.keys(WEEKDAY_LABELS)
    .filter((d) => !merchant.openingHours[d as keyof typeof merchant.openingHours].closed)

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-12">
      {/* Success Banner */}
      <div className="text-center mb-10">
        <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckCircle2 size={40} className="text-green-600" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Reservierung eingegangen!</h1>
        <p className="text-gray-500 text-lg">
          Vielen Dank, {reservation.customer.firstName}! Ihre Anfrage wurde erfolgreich übermittelt.
        </p>
      </div>

      {/* Reservation Card */}
      <div className="card overflow-hidden mb-6">
        {/* Header */}
        <div className="bg-primary-700 px-6 py-5">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <div>
              <p className="text-primary-200 text-xs font-medium mb-1">RESERVIERUNGSNUMMER</p>
              <p className="text-white font-bold text-2xl tracking-wider">{reservation.reservationNumber}</p>
            </div>
            <div className="bg-white/20 rounded-xl px-4 py-2.5 text-center">
              <p className="text-primary-100 text-xs">Status</p>
              <p className="text-white font-semibold text-sm mt-0.5">Anfrage eingegangen</p>
            </div>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Product */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Ihr Produkt</p>
            <div className="flex gap-4">
              {product.images[0] && (
                <div className="w-20 h-20 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                  <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover" />
                </div>
              )}
              <div>
                <h3 className="font-semibold text-gray-900">{product.name}</h3>
                <p className="text-sm text-gray-500 mt-0.5">Menge: {reservation.quantity}×</p>
                <div className="mt-2">
                  <AvailabilityBadge availability={product.availability} />
                </div>
              </div>
            </div>
          </div>

          {/* Pickup */}
          <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
            <div className="flex items-center gap-2 mb-2">
              <Clock size={16} className="text-amber-600" />
              <p className="font-semibold text-amber-800">Gewünschte Abholzeit</p>
            </div>
            <p className="text-amber-900 font-medium text-lg">{formatPickupTime(reservation.pickupTime)}</p>
            <p className="text-amber-700 text-xs mt-1">Der Händler wird Ihre Abholzeit noch bestätigen.</p>
          </div>

          {/* Merchant */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Händler</p>
            <div className="flex gap-4">
              <div className="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                <img src={merchant.images.store} alt={merchant.name} className="w-full h-full object-cover" />
              </div>
              <div className="text-sm">
                <Link to={`/haendler/${merchant.slug}`} className="font-semibold text-gray-900 hover:text-primary-700">
                  {merchant.name}
                </Link>
                <div className="flex items-center gap-1 text-gray-500 mt-1">
                  <MapPin size={12} />{merchant.address.street}, {merchant.address.city}
                </div>
                {merchant.contact.phone && (
                  <div className="flex items-center gap-1 text-gray-500 mt-1">
                    <Phone size={12} />
                    <a href={`tel:${merchant.contact.phone}`} className="hover:text-primary-700">{merchant.contact.phone}</a>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Customer data */}
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Ihre Daten</p>
            <div className="grid grid-cols-2 gap-3 text-sm text-gray-700">
              <div>
                <p className="text-gray-400 text-xs mb-0.5">Name</p>
                <p className="font-medium">{reservation.customer.firstName} {reservation.customer.lastName}</p>
              </div>
              <div>
                <p className="text-gray-400 text-xs mb-0.5">E-Mail</p>
                <p className="font-medium break-all">{reservation.customer.email}</p>
              </div>
              <div>
                <p className="text-gray-400 text-xs mb-0.5">Telefon</p>
                <p className="font-medium">{reservation.customer.phone}</p>
              </div>
              <div>
                <p className="text-gray-400 text-xs mb-0.5">Erstellt am</p>
                <p className="font-medium">{formatDate(reservation.createdAt)}</p>
              </div>
            </div>
            {reservation.customer.message && (
              <div className="mt-3 bg-gray-50 rounded-lg p-3 text-sm text-gray-600">
                <p className="text-xs font-medium text-gray-400 mb-1">Ihre Nachricht:</p>
                {reservation.customer.message}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Info box */}
      <div className="card p-5 mb-6 bg-blue-50 border-blue-100">
        <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
          <Mail size={16} />
          Was passiert als nächstes?
        </h3>
        <div className="space-y-2 text-sm text-blue-800">
          <p>Eine Bestätigungs-E-Mail wurde an <strong>{reservation.customer.email}</strong> gesendet.</p>
          <p>Der Händler prüft die Verfügbarkeit und meldet sich bei Ihnen.</p>
          <p>Nach Bestätigung erhalten Sie eine E-Mail mit dem Abholtermin.</p>
          <p>Holen Sie Ihr Produkt im Geschäft ab und bezahlen Sie vor Ort.</p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col sm:flex-row gap-3">
        <Link
          to="/"
          className="flex items-center justify-center gap-2 flex-1 py-3 px-5 rounded-xl bg-primary-700 text-white font-semibold hover:bg-primary-800 transition-colors"
        >
          <Home size={16} />
          Zur Startseite
        </Link>
        <Link
          to={`/haendler/${merchant.slug}`}
          className="flex items-center justify-center gap-2 flex-1 py-3 px-5 rounded-xl border border-gray-300 text-gray-700 font-medium hover:border-primary-300 hover:text-primary-700 transition-colors"
        >
          Händlerprofil
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  )
}

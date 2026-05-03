import { Link } from 'react-router-dom'
import { User, Heart, Bookmark, ClipboardList, ArrowRight, LogIn } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore, useReservationsByCustomer } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { ReservationStatusBadge } from '../../components/reservation/ReservationStatusBadge'
import { formatDate, formatPrice } from '../../utils/formatters'
import { EmptyState } from '../../components/ui/EmptyState'

export function CustomerProfilePage() {
  const { currentUser, isLoggedIn } = useAuthStore()
  const { merchants, products } = useDataStore()
  const { favoriteMerchantIds, savedProductIds } = useCustomerStore()
  const reservations = useReservationsByCustomer(currentUser?.id ?? '')

  if (!isLoggedIn || !currentUser) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <EmptyState
          icon={<User size={40} />}
          title="Bitte anmelden"
          description="Um Ihr Profil zu sehen, melden Sie sich bitte an."
          action={
            <Link to="/" className="btn-primary mt-2 inline-flex items-center gap-2">
              <LogIn size={16} />Zur Startseite & Anmelden
            </Link>
          }
        />
      </div>
    )
  }

  const favoriteMerchants = favoriteMerchantIds
    .map((id) => merchants.find((m) => m.id === id))
    .filter(Boolean) as typeof merchants

  const savedProducts = savedProductIds
    .map((id) => products.find((p) => p.id === id))
    .filter(Boolean) as typeof products

  const activeReservations = reservations.filter((r) => !['completed', 'cancelled'].includes(r.status))
  const pastReservations = reservations.filter((r) => ['completed', 'cancelled'].includes(r.status))

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Profile Header */}
      <div className="card p-6 mb-6">
        <div className="flex items-center gap-5">
          <img
            src={currentUser.avatarUrl ?? `https://ui-avatars.com/api/?name=${encodeURIComponent(currentUser.name)}&background=1b4f8a&color=fff&size=128`}
            alt={currentUser.name}
            className="w-16 h-16 sm:w-20 sm:h-20 rounded-full object-cover ring-4 ring-primary-100"
          />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{currentUser.name}</h1>
            <p className="text-gray-500">{currentUser.email}</p>
            <div className="mt-2 flex gap-3 text-sm text-gray-600">
              <span className="flex items-center gap-1"><Heart size={13} className="text-red-400" />{favoriteMerchantIds.length} Favoriten</span>
              <span className="flex items-center gap-1"><Bookmark size={13} className="text-primary-500" />{savedProductIds.length} Gemerkt</span>
              <span className="flex items-center gap-1"><ClipboardList size={13} className="text-secondary-500" />{reservations.length} Reservierungen</span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Active reservations */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <ClipboardList size={18} className="text-primary-600" />
                Aktive Reservierungen ({activeReservations.length})
              </h2>
            </div>
            {activeReservations.length === 0 ? (
              <EmptyState icon={<ClipboardList size={36} />} title="Keine aktiven Reservierungen" description="Stöbern Sie in den Produkten und reservieren Sie Ihren Favoriten." className="py-8" />
            ) : (
              <div className="space-y-3">
                {activeReservations.map((r) => {
                  const product = products.find((p) => p.id === r.productId)
                  const merchant = merchants.find((m) => m.id === r.merchantId)
                  return (
                    <div key={r.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-xl">
                      {product?.images[0] && (
                        <img src={product.images[0]} alt={product.name} className="w-12 h-12 rounded-lg object-cover shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 text-sm truncate">{product?.name}</p>
                        <p className="text-xs text-gray-500">{merchant?.name}</p>
                        <p className="text-xs text-gray-400 mt-0.5">{formatDate(r.pickupTime)}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <ReservationStatusBadge status={r.status} />
                        <p className="text-xs text-gray-400 mt-1 font-mono">{r.reservationNumber}</p>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Past reservations */}
          {pastReservations.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <ClipboardList size={18} className="text-gray-400" />
                Vergangene Reservierungen
              </h2>
              <div className="space-y-2">
                {pastReservations.map((r) => {
                  const product = products.find((p) => p.id === r.productId)
                  const merchant = merchants.find((m) => m.id === r.merchantId)
                  return (
                    <div key={r.id} className="flex items-center gap-3 p-3 rounded-xl">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-700 text-sm truncate">{product?.name}</p>
                        <p className="text-xs text-gray-400">{merchant?.name} · {formatDate(r.createdAt)}</p>
                      </div>
                      <ReservationStatusBadge status={r.status} />
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>

        {/* Right sidebar */}
        <div className="space-y-5">
          {/* Favorite merchants */}
          <div className="card p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                <Heart size={16} className="text-red-400" />
                Favoriten ({favoriteMerchants.length})
              </h3>
              <Link to="/favoriten" className="text-xs text-primary-700 hover:underline flex items-center gap-1">
                Alle <ArrowRight size={12} />
              </Link>
            </div>
            {favoriteMerchants.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">Noch keine Favoriten gespeichert.</p>
            ) : (
              <div className="space-y-2.5">
                {favoriteMerchants.slice(0, 4).map((m) => (
                  <Link key={m.id} to={`/haendler/${m.slug}`} className="flex items-center gap-2.5 group">
                    <img src={m.images.store} alt={m.name} className="w-9 h-9 rounded-lg object-cover" />
                    <div>
                      <p className="text-sm font-medium text-gray-800 group-hover:text-primary-700 transition-colors">{m.name}</p>
                      <p className="text-xs text-gray-400">{m.address.street}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Saved products */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Bookmark size={16} className="text-primary-600" />
              Gemerkte Produkte ({savedProducts.length})
            </h3>
            {savedProducts.length === 0 ? (
              <p className="text-sm text-gray-400 py-4 text-center">Noch keine Produkte gemerkt.</p>
            ) : (
              <div className="space-y-2.5">
                {savedProducts.slice(0, 4).map((p) => (
                  <Link key={p.id} to={`/produkte/${p.slug}`} className="flex items-center gap-2.5 group">
                    <img src={p.images[0]} alt={p.name} className="w-9 h-9 rounded-lg object-cover" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-800 group-hover:text-primary-700 transition-colors truncate">{p.name}</p>
                      <p className="text-xs text-secondary-600">{formatPrice(p.price)}</p>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Quick actions */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-3">Schnellzugriff</h3>
            <div className="space-y-2">
              <Link to="/haendler" className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary-700 p-2 rounded-lg hover:bg-gray-50">
                <User size={14} />Händler entdecken
              </Link>
              <Link to="/produkte" className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary-700 p-2 rounded-lg hover:bg-gray-50">
                <Bookmark size={14} />Produkte stöbern
              </Link>
              <Link to="/karte" className="flex items-center gap-2 text-sm text-gray-600 hover:text-primary-700 p-2 rounded-lg hover:bg-gray-50">
                <ClipboardList size={14} />Karte öffnen
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

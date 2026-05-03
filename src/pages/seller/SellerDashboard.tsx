import { Link } from 'react-router-dom'
import {
  ClipboardList, Package, CheckCircle2, Clock, TrendingUp,
  AlertCircle, ArrowRight, Calendar
} from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'
import { ReservationStatusBadge } from '../../components/reservation/ReservationStatusBadge'
import { formatDate } from '../../utils/formatters'

export function SellerDashboard() {
  const { currentMerchantId } = useAuthStore()
  const { merchants, products, reservations } = useDataStore()

  const merchant = merchants.find((m) => m.id === currentMerchantId)
  const merchantProducts = products.filter((p) => p.merchantId === currentMerchantId)
  const merchantReservations = reservations.filter((r) => r.merchantId === currentMerchantId)

  const stats = {
    received:  merchantReservations.filter((r) => r.status === 'received').length,
    confirmed: merchantReservations.filter((r) => r.status === 'confirmed').length,
    ready:     merchantReservations.filter((r) => r.status === 'ready').length,
    activeProducts: merchantProducts.filter((p) => p.active).length,
    totalProducts: merchantProducts.length,
  }

  const todayStr = new Date().toDateString()
  const todayPickups = merchantReservations.filter(
    (r) => new Date(r.pickupTime).toDateString() === todayStr && !['cancelled', 'completed'].includes(r.status)
  )

  const recentReservations = [...merchantReservations]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 5)

  if (!merchant) {
    return <p className="text-gray-500">Kein Händler gefunden.</p>
  }

  return (
    <div>
      {/* Page title */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 mt-1">Willkommen zurück, {merchant.name}</p>
      </div>

      {/* Status banner */}
      {stats.received > 0 && (
        <div className="mb-6 flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <AlertCircle size={20} className="text-amber-600 shrink-0" />
          <p className="text-amber-800 text-sm">
            Sie haben <strong>{stats.received} neue{stats.received !== 1 ? '' : ''} Reservierungsanfrage{stats.received !== 1 ? 'n' : ''}</strong>, die noch nicht bearbeitet wurde{stats.received !== 1 ? 'n' : ''}.
          </p>
          <Link to="/seller/reservierungen" className="ml-auto text-amber-700 font-semibold text-sm hover:underline whitespace-nowrap flex items-center gap-1">
            Jetzt ansehen <ArrowRight size={14} />
          </Link>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Neue Anfragen', value: stats.received, icon: <AlertCircle size={20} className="text-amber-500" />, color: 'bg-amber-50', link: '/seller/reservierungen?status=received' },
          { label: 'Bestätigt', value: stats.confirmed, icon: <CheckCircle2 size={20} className="text-green-500" />, color: 'bg-green-50', link: '/seller/reservierungen?status=confirmed' },
          { label: 'Abholbereit', value: stats.ready, icon: <Clock size={20} className="text-blue-500" />, color: 'bg-blue-50', link: '/seller/reservierungen?status=ready' },
          { label: 'Akt. Produkte', value: stats.activeProducts, icon: <Package size={20} className="text-primary-500" />, color: 'bg-primary-50', link: '/seller/produkte' },
        ].map((stat) => (
          <Link key={stat.label} to={stat.link} className={`card p-5 ${stat.color} border-0 hover:shadow-card-hover transition-shadow`}>
            <div className="flex items-center justify-between mb-2">
              {stat.icon}
              <ArrowRight size={14} className="text-gray-300" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-sm text-gray-600 mt-1">{stat.label}</div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Today's pickups */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Calendar size={18} className="text-primary-600" />
              Heutige Abholungen
            </h2>
            <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">
              {new Date().toLocaleDateString('de-DE', { weekday: 'short', day: 'numeric', month: 'short' })}
            </span>
          </div>
          {todayPickups.length === 0 ? (
            <p className="text-sm text-gray-400 py-4 text-center">Keine Abholungen für heute geplant.</p>
          ) : (
            <div className="space-y-3">
              {todayPickups.map((r) => {
                const product = useDataStore.getState().products.find((p) => p.id === r.productId)
                return (
                  <div key={r.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm font-semibold text-primary-700 w-12 shrink-0">
                      {new Date(r.pickupTime).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 text-sm truncate">{product?.name}</p>
                      <p className="text-xs text-gray-500">{r.customer.firstName} {r.customer.lastName}</p>
                    </div>
                    <ReservationStatusBadge status={r.status} />
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Recent reservations */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <ClipboardList size={18} className="text-primary-600" />
              Letzte Reservierungen
            </h2>
            <Link to="/seller/reservierungen" className="text-xs text-primary-700 hover:underline flex items-center gap-1">
              Alle <ArrowRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {recentReservations.map((r) => {
              const product = useDataStore.getState().products.find((p) => p.id === r.productId)
              return (
                <Link
                  key={r.id}
                  to={`/seller/reservierungen/${r.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{product?.name}</p>
                    <p className="text-xs text-gray-400">
                      {r.customer.firstName} {r.customer.lastName} · {formatDate(r.createdAt)}
                    </p>
                  </div>
                  <ReservationStatusBadge status={r.status} />
                </Link>
              )
            })}
          </div>
        </div>

        {/* Profile completeness */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-primary-600" />
            Profil-Status
          </h2>
          {[
            { label: 'Basisinformationen', done: true },
            { label: 'Öffnungszeiten gepflegt', done: true },
            { label: 'Ladenfotos hochgeladen', done: !!merchant.images.store },
            { label: 'Produkte angelegt', done: merchantProducts.length > 0 },
            { label: 'Click & Collect aktiviert', done: merchant.clickAndCollect },
            { label: 'Kontaktdaten vollständig', done: !!(merchant.contact.phone && merchant.contact.email) },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-3 py-2 border-b border-gray-50 last:border-0">
              <div className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 ${item.done ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'}`}>
                {item.done ? <CheckCircle2 size={12} /> : <div className="w-2 h-2 rounded-full bg-gray-300" />}
              </div>
              <span className={`text-sm ${item.done ? 'text-gray-700' : 'text-gray-400'}`}>{item.label}</span>
              {!item.done && (
                <Link to="/seller/profil" className="ml-auto text-xs text-primary-700 hover:underline">Ergänzen</Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

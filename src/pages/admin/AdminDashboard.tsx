import { Link } from 'react-router-dom'
import { Store, Package, Tag, ClipboardList, ArrowRight, TrendingUp, Users } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { ReservationStatusBadge } from '../../components/reservation/ReservationStatusBadge'
import { formatDate, MERCHANT_STATUS_LABELS, MERCHANT_STATUS_COLORS } from '../../utils/formatters'

export function AdminDashboard() {
  const { merchants, products, reservations, categories } = useDataStore()

  const stats = [
    { label: 'Händler gesamt', value: merchants.length, active: merchants.filter((m) => m.status === 'active').length, icon: <Store size={20} className="text-primary-600" />, link: '/admin/haendler' },
    { label: 'Produkte gesamt', value: products.length, active: products.filter((p) => p.active).length, icon: <Package size={20} className="text-secondary-500" />, link: '/admin/haendler' },
    { label: 'Reservierungen', value: reservations.length, active: reservations.filter((r) => r.status === 'received').length, icon: <ClipboardList size={20} className="text-blue-500" />, link: '/admin/haendler' },
    { label: 'Kategorien', value: categories.length, active: categories.length, icon: <Tag size={20} className="text-accent-500" />, link: '/admin/kategorien' },
  ]

  const recentReservations = [...reservations]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 8)

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin-Dashboard</h1>
        <p className="text-gray-500 mt-1">Übersicht der Stadtmarktplatz-Plattform</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((stat) => (
          <Link key={stat.label} to={stat.link} className="card p-5 hover:shadow-card-hover transition-shadow">
            <div className="flex items-center justify-between mb-3">
              {stat.icon}
              <ArrowRight size={14} className="text-gray-300" />
            </div>
            <div className="text-3xl font-bold text-gray-900">{stat.value}</div>
            <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            <div className="text-xs text-green-600 mt-1">{stat.active} aktiv</div>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Merchants list */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <Store size={18} className="text-primary-600" />
              Händler-Übersicht
            </h2>
            <Link to="/admin/haendler" className="text-xs text-primary-700 hover:underline flex items-center gap-1">
              Alle verwalten <ArrowRight size={12} />
            </Link>
          </div>
          <div className="space-y-2">
            {merchants.map((m) => (
              <div key={m.id} className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors">
                <img src={m.images.store} alt={m.name} className="w-10 h-10 rounded-lg object-cover shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{m.name}</p>
                  <p className="text-xs text-gray-400">{m.address.street}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${MERCHANT_STATUS_COLORS[m.status]}`}>
                  {MERCHANT_STATUS_LABELS[m.status]}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent reservations */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-900 flex items-center gap-2">
              <ClipboardList size={18} className="text-primary-600" />
              Letzte Reservierungen
            </h2>
          </div>
          <div className="space-y-2">
            {recentReservations.map((r) => {
              const merchant = merchants.find((m) => m.id === r.merchantId)
              return (
                <div key={r.id} className="flex items-center gap-3 p-2.5 rounded-lg">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-800 truncate">{r.customer.firstName} {r.customer.lastName}</p>
                    <p className="text-xs text-gray-400 truncate">{merchant?.name} · {formatDate(r.createdAt)}</p>
                  </div>
                  <ReservationStatusBadge status={r.status} />
                </div>
              )
            })}
          </div>
        </div>

        {/* Platform stats */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp size={18} className="text-primary-600" />
            Plattform-Statistik
          </h2>
          <div className="space-y-3">
            {[
              { label: 'Händler mit Click & Collect', value: merchants.filter((m) => m.clickAndCollect).length, total: merchants.length },
              { label: 'Featured Händler', value: merchants.filter((m) => m.featured).length, total: merchants.length },
              { label: 'Aktive Produkte', value: products.filter((p) => p.active).length, total: products.length },
              { label: 'Reservierbare Produkte', value: products.filter((p) => p.reservable && p.active).length, total: products.filter((p) => p.active).length },
              { label: 'Offene Reservierungen', value: reservations.filter((r) => ['received', 'confirmed', 'ready'].includes(r.status)).length, total: reservations.length },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{stat.label}</span>
                  <span className="font-semibold">{stat.value} / {stat.total}</span>
                </div>
                <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary-500 rounded-full"
                    style={{ width: `${stat.total > 0 ? (stat.value / stat.total) * 100 : 0}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick actions */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Users size={18} className="text-primary-600" />
            Schnellaktionen
          </h2>
          <div className="space-y-2">
            {[
              { label: 'Neuen Händler anlegen', link: '/admin/haendler/neu', icon: '🏪' },
              { label: 'Kategorien verwalten', link: '/admin/kategorien', icon: '🏷' },
              { label: 'Startseite anpassen', link: '/admin/inhalte', icon: '🌟' },
              { label: 'Zur öffentlichen Seite', link: '/', icon: '🌐' },
            ].map((action) => (
              <Link
                key={action.label}
                to={action.link}
                className="flex items-center gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
              >
                <span className="text-xl">{action.icon}</span>
                <span className="text-sm font-medium text-gray-700 group-hover:text-primary-700">{action.label}</span>
                <ArrowRight size={14} className="ml-auto text-gray-300 group-hover:text-primary-500" />
              </Link>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

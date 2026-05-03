import { useParams, Link } from 'react-router-dom'
import {
  MapPin, Phone, Mail, Globe, Clock, CheckCircle2, Heart,
  ShoppingBag, ArrowLeft, Image, Store
} from 'lucide-react'
import { useMerchantBySlug, useProductsByMerchant, useDataStore } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { ProductCard } from '../../components/product/ProductCard'
import { MerchantMap } from '../../components/map/MerchantMap'
import { EmptyState } from '../../components/ui/EmptyState'
import { WEEKDAY_LABELS } from '../../utils/formatters'

export function MerchantProfilePage() {
  const { slug } = useParams<{ slug: string }>()
  const merchant = useMerchantBySlug(slug ?? '')
  const products = useProductsByMerchant(merchant?.id ?? '')
  const categories = useDataStore((s) => s.categories)
  const { toggleFavoriteMerchant, isMerchantFavorite } = useCustomerStore()

  if (!merchant) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <EmptyState icon={<Store size={40} />} title="Händler nicht gefunden" description="Dieser Händler existiert nicht oder ist nicht mehr aktiv." />
        <Link to="/haendler" className="btn-outline mt-4 inline-flex items-center gap-2">
          <ArrowLeft size={16} />Zu allen Händlern
        </Link>
      </div>
    )
  }

  const merchantCategories = categories.filter((c) => merchant.categoryIds.includes(c.id))
  const isFavorite = isMerchantFavorite(merchant.id)
  const weekdays = Object.keys(WEEKDAY_LABELS) as (keyof typeof WEEKDAY_LABELS)[]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-primary-700">Start</Link>
        <span>/</span>
        <Link to="/haendler" className="hover:text-primary-700">Händler</Link>
        <span>/</span>
        <span className="text-gray-800 font-medium">{merchant.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-6">
          {/* Hero image */}
          <div className="relative rounded-2xl overflow-hidden aspect-video bg-gray-100">
            <img
              src={merchant.images.store}
              alt={`Laden von ${merchant.name}`}
              className="w-full h-full object-cover"
            />
            {merchant.clickAndCollect && (
              <div className="absolute top-4 left-4">
                <span className="inline-flex items-center gap-1.5 bg-white text-primary-700 font-semibold text-sm px-3 py-1.5 rounded-full shadow-md">
                  <CheckCircle2 size={14} />
                  Click & Collect
                </span>
              </div>
            )}
          </div>

          {/* Merchant header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              {/* Categories */}
              <div className="flex flex-wrap gap-1.5 mb-2">
                {merchantCategories.map((cat) => (
                  <span
                    key={cat.id}
                    className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-medium"
                    style={{ backgroundColor: `${cat.color}18`, color: cat.color }}
                  >
                    {cat.icon} {cat.name}
                  </span>
                ))}
              </div>
              <h1 className="text-3xl font-bold text-gray-900">{merchant.name}</h1>
              <div className="flex items-center gap-1.5 text-gray-500 mt-1">
                <MapPin size={14} />
                <span className="text-sm">{merchant.address.street}, {merchant.address.zip} {merchant.address.city}</span>
              </div>
            </div>

            <button
              onClick={() => toggleFavoriteMerchant(merchant.id)}
              className={`p-3 rounded-xl border transition-all shrink-0 ${
                isFavorite
                  ? 'bg-red-50 border-red-200 text-red-500'
                  : 'bg-white border-gray-200 text-gray-400 hover:border-red-200 hover:text-red-400'
              }`}
              title={isFavorite ? 'Aus Favoriten entfernen' : 'Zu Favoriten hinzufügen'}
            >
              <Heart size={20} fill={isFavorite ? 'currentColor' : 'none'} />
            </button>
          </div>

          {/* Description */}
          <div className="card p-6">
            <h2 className="font-semibold text-gray-900 mb-3 text-lg">Über {merchant.name}</h2>
            <p className="text-gray-600 leading-relaxed">{merchant.description}</p>
          </div>

          {/* Team image */}
          {merchant.images.team && (
            <div className="card p-6">
              <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <Image size={18} className="text-primary-600" />
                Das Team
              </h2>
              <div className="rounded-xl overflow-hidden">
                <img
                  src={merchant.images.team}
                  alt={`Team von ${merchant.name}`}
                  className="w-full h-56 object-cover"
                />
              </div>
            </div>
          )}

          {/* Products */}
          <div>
            <div className="flex items-center justify-between mb-5">
              <h2 className="text-xl font-bold text-gray-900">
                Produkte von {merchant.name}
              </h2>
              <Link
                to={`/produkte?haendler=${merchant.id}`}
                className="text-sm text-primary-700 font-medium hover:underline flex items-center gap-1"
              >
                Alle anzeigen
                <ShoppingBag size={14} />
              </Link>
            </div>

            {products.length === 0 ? (
              <EmptyState
                icon={<ShoppingBag size={36} />}
                title="Noch keine Produkte"
                description="Dieser Händler hat noch keine Produkte eingestellt."
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {products.slice(0, 6).map((p) => (
                  <ProductCard key={p.id} product={p} showMerchant={false} />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* CTA Card */}
          <div className="card p-5 bg-primary-700 text-white">
            {merchant.clickAndCollect ? (
              <>
                <CheckCircle2 size={24} className="text-green-300 mb-3" />
                <h3 className="font-semibold text-lg mb-2">Click & Collect verfügbar</h3>
                <p className="text-primary-200 text-sm mb-4 leading-relaxed">
                  Reservieren Sie Produkte online und holen Sie sie bequem im Laden ab.
                </p>
                <Link
                  to={`/produkte?haendler=${merchant.id}`}
                  className="block text-center bg-white text-primary-800 font-semibold py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                >
                  Produkte reservieren
                </Link>
              </>
            ) : (
              <>
                <ShoppingBag size={24} className="text-primary-300 mb-3" />
                <h3 className="font-semibold text-lg mb-2">Produkte ansehen</h3>
                <p className="text-primary-200 text-sm mb-4">Stöbern Sie im Sortiment dieses Händlers.</p>
                <Link
                  to={`/produkte?haendler=${merchant.id}`}
                  className="block text-center bg-white text-primary-800 font-semibold py-2.5 px-4 rounded-lg hover:bg-gray-50 transition-colors text-sm"
                >
                  Sortiment ansehen
                </Link>
              </>
            )}
          </div>

          {/* Contact */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Kontakt</h3>
            <div className="space-y-3">
              {merchant.contact.phone && (
                <a href={`tel:${merchant.contact.phone}`} className="flex items-center gap-3 text-sm text-gray-600 hover:text-primary-700 transition-colors group">
                  <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center group-hover:bg-primary-100">
                    <Phone size={14} className="text-primary-600" />
                  </div>
                  {merchant.contact.phone}
                </a>
              )}
              {merchant.contact.email && (
                <a href={`mailto:${merchant.contact.email}`} className="flex items-center gap-3 text-sm text-gray-600 hover:text-primary-700 transition-colors group">
                  <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center group-hover:bg-primary-100">
                    <Mail size={14} className="text-primary-600" />
                  </div>
                  <span className="break-all">{merchant.contact.email}</span>
                </a>
              )}
              {merchant.contact.website && (
                <a href={merchant.contact.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-3 text-sm text-gray-600 hover:text-primary-700 transition-colors group">
                  <div className="w-8 h-8 bg-primary-50 rounded-lg flex items-center justify-center group-hover:bg-primary-100">
                    <Globe size={14} className="text-primary-600" />
                  </div>
                  Website besuchen
                </a>
              )}
            </div>
          </div>

          {/* Opening Hours */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <Clock size={16} className="text-primary-600" />
              Öffnungszeiten
            </h3>
            <div className="space-y-2">
              {weekdays.map((day) => {
                const hours = merchant.openingHours[day]
                const today = ['sonntag', 'montag', 'dienstag', 'mittwoch', 'donnerstag', 'freitag', 'samstag'][new Date().getDay()]
                const isToday = day === today
                return (
                  <div
                    key={day}
                    className={`flex justify-between items-center text-sm py-1 ${isToday ? 'font-semibold text-primary-700' : 'text-gray-600'}`}
                  >
                    <span>{WEEKDAY_LABELS[day]}</span>
                    <span className={hours.closed ? 'text-gray-400' : ''}>
                      {hours.closed ? 'Geschlossen' : `${hours.open} – ${hours.close} Uhr`}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Address + Map */}
          <div className="card p-5">
            <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <MapPin size={16} className="text-primary-600" />
              Standort
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              {merchant.address.street}<br />
              {merchant.address.zip} {merchant.address.city}
              {merchant.address.district && ` (${merchant.address.district})`}
            </p>
            <MerchantMap
              merchants={[merchant]}
              highlightedId={merchant.id}
              height="200px"
              zoom={16}
            />
            <a
              href={`https://www.openstreetmap.org/search?query=${encodeURIComponent(`${merchant.address.street}, ${merchant.address.city}`)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 block text-center text-xs text-primary-700 hover:underline"
            >
              In OpenStreetMap öffnen →
            </a>
          </div>
        </div>
      </div>
    </div>
  )
}

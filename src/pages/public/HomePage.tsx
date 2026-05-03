import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  MapPin, ShoppingBag, CheckCircle2, ArrowRight, Store,
  Star, Package, Users, Truck, Search, ClipboardList
} from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { MerchantCard } from '../../components/merchant/MerchantCard'
import { ProductCard } from '../../components/product/ProductCard'
import { MerchantMap } from '../../components/map/MerchantMap'
import { CategoryIcon } from '../../components/ui/CategoryIcon'

export function HomePage() {
  const { merchants, products, categories, featuredContent } = useDataStore()
  const [mapVisible, setMapVisible] = useState(false)

  const featuredMerchantIds = featuredContent
    .filter((fc) => fc.type === 'merchant' && fc.active)
    .sort((a, b) => a.position - b.position)
    .map((fc) => fc.refId)

  const featuredProductIds = featuredContent
    .filter((fc) => fc.type === 'product' && fc.active)
    .sort((a, b) => a.position - b.position)
    .map((fc) => fc.refId)

  const featuredMerchants = featuredMerchantIds
    .map((id) => merchants.find((m) => m.id === id))
    .filter(Boolean)
    .slice(0, 4) as typeof merchants

  const featuredProducts = featuredProductIds
    .map((id) => products.find((p) => p.id === id))
    .filter(Boolean)
    .slice(0, 4) as typeof products

  const stats = [
    { label: 'Lokale Händler', value: merchants.filter((m) => m.status === 'active').length, icon: <Store size={22} className="text-primary-600" /> },
    { label: 'Produkte', value: products.filter((p) => p.active).length, icon: <Package size={22} className="text-secondary-500" /> },
    { label: 'Kategorien', value: categories.length, icon: <Star size={22} className="text-accent-500" /> },
    { label: 'Click & Collect', value: merchants.filter((m) => m.clickAndCollect).length, icon: <Truck size={22} className="text-blue-500" /> },
  ]

  return (
    <div>
      {/* ---- HERO ---- */}
      <section className="relative min-h-[600px] flex items-center overflow-hidden bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700">
        {/* Background image with overlay */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=1920&q=80"
            alt="Lokales Einkaufen in Bad Mergentheim"
            className="w-full h-full object-cover opacity-20"
          />
        </div>

        {/* Decorative elements */}
        <div className="absolute top-20 right-10 w-64 h-64 bg-secondary-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-10 left-10 w-96 h-96 bg-primary-400/10 rounded-full blur-3xl" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 w-full">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white/90 text-sm font-medium px-4 py-2 rounded-full mb-6 border border-white/20">
              <MapPin size={14} className="text-secondary-300" />
              Bad Mergentheim
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
              Dein lokaler<br />
              <span className="text-secondary-300">Marktplatz</span><br />
              digital.
            </h1>

            <p className="text-lg sm:text-xl text-white/80 leading-relaxed mb-8 max-w-xl">
              Entdecken sie die Vielfalt unsere Händler in Bad Mergentheim – auf der Karte, nach Kategorie oder konkret nach Produkten. Mit einfacher Click &amp; Collect-Reservierung.
            </p>

            <div className="flex flex-wrap gap-3">
              <Link
                to="/haendler"
                className="flex items-center gap-2 bg-white text-primary-800 font-semibold px-6 py-3 rounded-xl hover:bg-gray-50 transition-colors shadow-lg"
              >
                <Store size={18} />
                Händler entdecken
              </Link>
              <Link
                to="/karte"
                className="flex items-center gap-2 bg-white/10 backdrop-blur-sm text-white font-semibold px-6 py-3 rounded-xl border border-white/30 hover:bg-white/20 transition-colors"
              >
                <MapPin size={18} />
                Karte ansehen
              </Link>
              <Link
                to="/produkte"
                className="flex items-center gap-2 bg-secondary-500 text-white font-semibold px-6 py-3 rounded-xl hover:bg-secondary-600 transition-colors shadow-lg"
              >
                <ShoppingBag size={18} />
                Produkte
              </Link>
            </div>

            {/* Click & Collect Banner */}
            <div className="mt-8 flex items-center gap-3 bg-white/10 backdrop-blur-sm rounded-xl p-4 border border-white/20 w-fit">
              <CheckCircle2 size={20} className="text-green-300 shrink-0" />
              <div>
                <p className="text-white font-semibold text-sm">Click & Collect verfügbar</p>
                <p className="text-white/70 text-xs">Online reservieren, vor Ort abholen</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---- STATS ---- */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="flex justify-center mb-2">{stat.icon}</div>
                <div className="text-3xl font-bold text-gray-900">{stat.value}+</div>
                <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- HOW IT WORKS ---- */}
      <section className="bg-stone-50 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900">So funktioniert Click & Collect</h2>
            <p className="text-gray-500 mt-3 text-lg max-w-xl mx-auto">
              Einfach online reservieren und im Laden abholen – ohne Wartezeit.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { step: '1', icon: <Search size={20} className="text-primary-700" />, title: 'Händler entdecken', text: 'Stöbern Sie in der Händlerliste oder auf der interaktiven Karte.' },
              { step: '2', icon: <ShoppingBag size={20} className="text-primary-700" />, title: 'Produkt auswählen', text: 'Finden Sie das gewünschte Produkt und prüfen Sie die Verfügbarkeit.' },
              { step: '3', icon: <ClipboardList size={20} className="text-primary-700" />, title: 'Reservieren', text: 'Füllen Sie das Reservierungsformular aus und wählen Sie eine Abholzeit.' },
              { step: '4', icon: <CheckCircle2 size={20} className="text-primary-700" />, title: 'Abholen', text: 'Holen Sie Ihr reserviertes Produkt bequem vor Ort ab.' },
            ].map((step) => (
              <div key={step.step} className="card p-6 text-center">
                <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  {step.icon}
                </div>
                <div className="text-xs font-bold text-primary-600 mb-1">SCHRITT {step.step}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{step.title}</h3>
                <p className="text-sm text-gray-500 leading-relaxed">{step.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---- FEATURED MERCHANTS ---- */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Ausgewählte Händler</h2>
              <p className="text-gray-500 mt-1">Entdecken Sie die beliebtesten Geschäfte in Bad Mergentheim</p>
            </div>
            <Link
              to="/haendler"
              className="hidden sm:flex items-center gap-2 text-primary-700 font-medium text-sm hover:text-primary-800"
            >
              Alle Händler <ArrowRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {featuredMerchants.map((merchant) => (
              <MerchantCard key={merchant.id} merchant={merchant} />
            ))}
          </div>

          <div className="mt-6 text-center sm:hidden">
            <Link to="/haendler" className="inline-flex items-center gap-2 text-primary-700 font-medium text-sm">
              Alle Händler ansehen <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* ---- CATEGORIES ---- */}
      <section className="py-16 bg-stone-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900">Nach Kategorie stöbern</h2>
            <p className="text-gray-500 mt-2">Finden Sie genau das, was Sie suchen.</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
            {categories.slice(0, 10).map((cat) => (
              <Link
                key={cat.id}
                to={`/haendler?kategorien=${cat.slug}`}
                className="card p-4 text-center hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-200 group"
              >
                <div
                  className="w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-3 transition-transform group-hover:scale-110"
                  style={{ backgroundColor: `${cat.color}18` }}
                >
                  <CategoryIcon name={cat.icon} size={22} style={{ color: cat.color }} />
                </div>
                <p className="text-sm font-medium text-gray-800 leading-tight">{cat.name}</p>
                <p className="text-xs text-gray-400 mt-1">
                  {merchants.filter((m) => m.categoryIds.includes(cat.id) && m.status === 'active').length} Händler
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ---- FEATURED PRODUCTS ---- */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-gray-900">Empfohlene Produkte</h2>
              <p className="text-gray-500 mt-1">Jetzt online reservieren, vor Ort abholen</p>
            </div>
            <Link
              to="/produkte"
              className="hidden sm:flex items-center gap-2 text-primary-700 font-medium text-sm hover:text-primary-800"
            >
              Alle Produkte <ArrowRight size={16} />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {featuredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </section>

      {/* ---- MAP PREVIEW ---- */}
      <section className="py-16 bg-stone-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900">Alle Händler auf einen Blick</h2>
            <p className="text-gray-500 mt-2 max-w-lg mx-auto">
              Finden Sie Händler in Ihrer Nähe auf der interaktiven Karte.
            </p>
          </div>

          {mapVisible ? (
            <MerchantMap height="450px" />
          ) : (
            <div className="relative">
              <div
                className="aspect-video max-h-[450px] rounded-xl overflow-hidden bg-gray-200 cursor-pointer group"
                onClick={() => setMapVisible(true)}
              >
                <img
                  src="https://images.unsplash.com/photo-1524661135-423995f22d0b?w=1200&q=80"
                  alt="Karte von Bad Mergentheim"
                  className="w-full h-full object-cover group-hover:opacity-90 transition-opacity"
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="bg-white/95 rounded-2xl px-8 py-5 text-center shadow-xl">
                    <MapPin size={28} className="text-primary-700 mx-auto mb-2" />
                    <p className="font-semibold text-gray-900">Karte laden</p>
                    <p className="text-sm text-gray-500 mt-1">Klicken zum Aktivieren</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          <div className="text-center mt-6">
            <Link
              to="/karte"
              className="inline-flex items-center gap-2 bg-primary-700 text-white font-semibold px-6 py-3 rounded-xl hover:bg-primary-800 transition-colors"
            >
              <MapPin size={18} />
              Vollständige Kartenansicht
            </Link>
          </div>
        </div>
      </section>

      {/* ---- CTA ---- */}
      <section className="bg-primary-800 py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Händler in Bad Mergentheim –<br />digital sichtbar werden
          </h2>
          <p className="text-primary-200 text-lg mb-8 leading-relaxed">
            Sind Sie Händler in Bad Mergentheim? Registrieren Sie sich kostenlos und erreichen Sie Ihre Kunden digital.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:info@stadtmarktplatz-bm.de"
              className="flex items-center justify-center gap-2 bg-secondary-500 text-white font-semibold px-8 py-3 rounded-xl hover:bg-secondary-600 transition-colors"
            >
              <Users size={18} />
              Händler werden
            </a>
            <Link
              to="/haendler"
              className="flex items-center justify-center gap-2 bg-white/10 text-white font-semibold px-8 py-3 rounded-xl border border-white/20 hover:bg-white/20 transition-colors"
            >
              Händler ansehen
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

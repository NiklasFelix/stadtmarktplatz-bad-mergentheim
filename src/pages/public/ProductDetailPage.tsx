import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Store, Tag, ArrowLeft, Bookmark, ShoppingBag } from 'lucide-react'
import { useProductBySlug, useDataStore } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { AvailabilityBadge } from '../../components/product/AvailabilityBadge'
import { EmptyState } from '../../components/ui/EmptyState'
import { CategoryIcon } from '../../components/ui/CategoryIcon'
import { formatPrice } from '../../utils/formatters'

export function ProductDetailPage() {
  const { slug } = useParams<{ slug: string }>()
  const product = useProductBySlug(slug ?? '')
  const merchants = useDataStore((s) => s.merchants)
  const categories = useDataStore((s) => s.categories)
  const { toggleSavedProduct, isProductSaved } = useCustomerStore()
  const navigate = useNavigate()

  if (!product) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-20 text-center">
        <EmptyState icon={<ShoppingBag size={40} />} title="Produkt nicht gefunden" description="Dieses Produkt existiert nicht oder wurde deaktiviert." />
        <Link to="/produkte" className="btn-outline mt-4 inline-flex items-center gap-2">
          <ArrowLeft size={16} />Zurück zu Produkten
        </Link>
      </div>
    )
  }

  const merchant = merchants.find((m) => m.id === product.merchantId)
  const productCategories = categories.filter((c) => product.categoryIds.includes(c.id))
  const isSaved = isProductSaved(product.id)
  const [selectedSize, setSelectedSize] = useState<string>('')

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/" className="hover:text-primary-700">Start</Link>
        <span>/</span>
        <Link to="/produkte" className="hover:text-primary-700">Produkte</Link>
        <span>/</span>
        <span className="text-gray-800 font-medium line-clamp-1">{product.name}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Product Image */}
        <div>
          <div className="aspect-square rounded-2xl overflow-hidden bg-gray-100">
            {product.images[0] ? (
              <img
                src={product.images[0]}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-300">
                <ShoppingBag size={64} />
              </div>
            )}
          </div>
          {/* Gallery thumbnails */}
          {product.images.length > 1 && (
            <div className="flex gap-2 mt-3">
              {product.images.slice(1, 4).map((img, i) => (
                <div key={i} className="w-20 h-20 rounded-lg overflow-hidden bg-gray-100">
                  <img src={img} alt="" className="w-full h-full object-cover" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Product Details */}
        <div className="flex flex-col">
          {/* Categories */}
          <div className="flex flex-wrap gap-1.5 mb-3">
            {productCategories.map((cat) => (
              <span
                key={cat.id}
                className="inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full font-medium"
                style={{ backgroundColor: `${cat.color}18`, color: cat.color }}
              >
                <CategoryIcon name={cat.icon} size={11} /> {cat.name}
              </span>
            ))}
          </div>

          <div className="flex items-start justify-between gap-4 mb-4">
            <h1 className="text-3xl font-bold text-gray-900 leading-tight">{product.name}</h1>
            <button
              onClick={() => toggleSavedProduct(product.id)}
              className={`p-2.5 rounded-xl border transition-all shrink-0 ${
                isSaved ? 'bg-primary-50 border-primary-200 text-primary-700' : 'border-gray-200 text-gray-400 hover:border-primary-200 hover:text-primary-600'
              }`}
            >
              <Bookmark size={18} fill={isSaved ? 'currentColor' : 'none'} />
            </button>
          </div>

          {/* Price */}
          <div className="text-4xl font-bold text-gray-900 mb-3">{formatPrice(product.price)}</div>

          {/* Availability */}
          <div className="mb-5">
            <AvailabilityBadge availability={product.availability} />
          </div>

          {/* Description */}
          <p className="text-gray-600 leading-relaxed mb-6">{product.description}</p>

          {/* Size selection */}
          {product.sizes && product.sizes.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-medium text-gray-700 mb-2">
                Größe wählen
                {selectedSize && <span className="ml-2 text-primary-700 font-semibold">{selectedSize}</span>}
              </p>
              <div className="flex flex-wrap gap-2">
                {product.sizes.map((s) => (
                  <button
                    key={s}
                    onClick={() => setSelectedSize(selectedSize === s ? '' : s)}
                    className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${selectedSize === s ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-gray-700 border-gray-300 hover:border-primary-400'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {product.tags.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-6">
              {product.tags.map((tag) => (
                <span key={tag} className="inline-flex items-center gap-1 text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full">
                  <Tag size={10} />{tag}
                </span>
              ))}
            </div>
          )}

          {/* Merchant */}
          {merchant && (
            <div className="card p-4 mb-6">
              <p className="text-xs text-gray-500 mb-2">Angeboten von</p>
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                  <img src={merchant.images.store} alt={merchant.name} className="w-full h-full object-cover" />
                </div>
                <div>
                  <Link to={`/haendler/${merchant.slug}`} className="font-semibold text-gray-900 hover:text-primary-700 transition-colors">
                    {merchant.name}
                  </Link>
                  <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                    <Store size={11} />
                    {merchant.address.street}, {merchant.address.city}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Click & Collect info */}
          {merchant?.clickAndCollect && (
            <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-6">
              <p className="text-sm font-semibold text-green-800 mb-1">✓ Click & Collect verfügbar</p>
              <p className="text-xs text-green-700">Reservieren Sie dieses Produkt online und holen Sie es im Laden ab.</p>
            </div>
          )}

          {/* CTA */}
          <div className="flex flex-col sm:flex-row gap-3 mt-auto">
            {product.reservable && product.availability !== 'unavailable' ? (
              <button
                onClick={() => {
                  const params = selectedSize ? `?groesse=${encodeURIComponent(selectedSize)}` : ''
                  navigate(`/reservierung/${product.id}${params}`)
                }}
                className="flex-1 btn-primary py-3 text-base rounded-xl"
              >
                {selectedSize ? `Größe ${selectedSize} reservieren` : 'Jetzt reservieren'}
              </button>
            ) : (
              <div className="flex-1 py-3 rounded-xl bg-gray-100 text-gray-400 text-center text-sm font-medium">
                {product.availability === 'unavailable' ? 'Nicht verfügbar' : 'Nicht reservierbar'}
              </div>
            )}
            {merchant && (
              <Link
                to={`/haendler/${merchant.slug}`}
                className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium text-sm hover:border-primary-300 hover:text-primary-700 transition-colors"
              >
                <Store size={16} />
                Händlerprofil
              </Link>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

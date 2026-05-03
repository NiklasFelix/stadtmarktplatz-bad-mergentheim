import { Link } from 'react-router-dom'
import { Bookmark, ShoppingBag, Store } from 'lucide-react'
import { clsx } from 'clsx'
import type { Product } from '../../types'
import { useDataStore } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { formatPrice } from '../../utils/formatters'
import { AvailabilityBadge } from './AvailabilityBadge'

interface ProductCardProps {
  product: Product
  showMerchant?: boolean
}

export function ProductCard({ product, showMerchant = true }: ProductCardProps) {
  const merchants = useDataStore((s) => s.merchants)
  const { toggleSavedProduct, isProductSaved } = useCustomerStore()
  const merchant = merchants.find((m) => m.id === product.merchantId)
  const isSaved = isProductSaved(product.id)

  return (
    <div className="card group relative flex flex-col hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-200">
      {/* Product image */}
      <Link to={`/produkte/${product.slug}`} className="block overflow-hidden">
        <div className="aspect-[4/3] bg-gray-100 overflow-hidden">
          {product.images[0] ? (
            <img
              src={product.images[0]}
              alt={product.name}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-300">
              <ShoppingBag size={40} />
            </div>
          )}
        </div>
      </Link>

      {/* Save button */}
      <button
        onClick={() => toggleSavedProduct(product.id)}
        className={clsx(
          'absolute top-3 right-3 p-1.5 rounded-full shadow-md transition-all',
          isSaved
            ? 'bg-primary-700 text-white'
            : 'bg-white/90 text-gray-400 hover:text-primary-600 hover:bg-white'
        )}
        title={isSaved ? 'Gespeichert' : 'Produkt merken'}
      >
        <Bookmark size={14} fill={isSaved ? 'currentColor' : 'none'} />
      </button>

      {/* Featured badge */}
      {product.featured && (
        <div className="absolute top-3 left-3">
          <span className="bg-secondary-500 text-white text-xs font-semibold px-2 py-0.5 rounded-full shadow-sm">
            Empfehlung
          </span>
        </div>
      )}

      {/* Content */}
      <div className="flex flex-col flex-1 p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <Link to={`/produkte/${product.slug}`}>
            <h3 className="font-semibold text-gray-900 text-sm leading-snug group-hover:text-primary-700 transition-colors line-clamp-2">
              {product.name}
            </h3>
          </Link>
        </div>

        <p className="text-xs text-gray-500 leading-relaxed line-clamp-2 mb-3 flex-1">
          {product.description}
        </p>

        {/* Merchant */}
        {showMerchant && merchant && (
          <Link
            to={`/haendler/${merchant.slug}`}
            className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-primary-600 transition-colors mb-3"
          >
            <Store size={11} />
            {merchant.name}
          </Link>
        )}

        {/* Price + Availability */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="font-bold text-gray-900 text-base">
            {formatPrice(product.price)}
          </span>
          <AvailabilityBadge availability={product.availability} />
        </div>

        {/* Actions */}
        {product.reservable && product.availability !== 'unavailable' && (
          <Link
            to={`/reservierung/${product.id}`}
            className="w-full text-center text-xs font-semibold py-2 px-4 rounded-lg bg-primary-700 text-white hover:bg-primary-800 transition-colors"
          >
            Reservieren
          </Link>
        )}
      </div>
    </div>
  )
}

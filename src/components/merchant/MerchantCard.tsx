import { Link } from 'react-router-dom'
import { MapPin, Phone, Heart, ShoppingBag, CheckCircle2 } from 'lucide-react'
import { clsx } from 'clsx'
import type { Merchant } from '../../types'
import { useDataStore } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { Badge } from '../ui/Badge'

interface MerchantCardProps {
  merchant: Merchant
  highlighted?: boolean
  compact?: boolean
}

export function MerchantCard({ merchant, highlighted, compact }: MerchantCardProps) {
  const categories = useDataStore((s) => s.categories)
  const { toggleFavoriteMerchant, isMerchantFavorite } = useCustomerStore()
  const isFavorite = isMerchantFavorite(merchant.id)
  const merchantCategories = categories.filter((c) => merchant.categoryIds.includes(c.id))

  return (
    <div
      className={clsx(
        'card group relative flex flex-col overflow-hidden',
        highlighted ? 'ring-2 ring-primary-400' : '',
        'hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-200'
      )}
    >
      {/* Store image */}
      <Link to={`/haendler/${merchant.slug}`} className="block overflow-hidden">
        <div className="aspect-[4/3] overflow-hidden bg-gray-100">
          <img
            src={merchant.images.store}
            alt={`Laden von ${merchant.name}`}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        </div>
      </Link>

      {/* Favorite button */}
      <button
        onClick={() => toggleFavoriteMerchant(merchant.id)}
        className={clsx(
          'absolute top-3 right-3 p-2 rounded-full shadow-md transition-all',
          isFavorite
            ? 'bg-red-500 text-white'
            : 'bg-white/90 text-gray-400 hover:text-red-400 hover:bg-white'
        )}
        title={isFavorite ? 'Aus Favoriten entfernen' : 'Zu Favoriten hinzufügen'}
      >
        <Heart size={14} fill={isFavorite ? 'currentColor' : 'none'} />
      </button>

      {/* Click & Collect badge */}
      {merchant.clickAndCollect && (
        <div className="absolute top-3 left-3">
          <span className="inline-flex items-center gap-1 bg-white/95 text-primary-700 text-xs font-semibold px-2 py-1 rounded-full shadow-sm">
            <CheckCircle2 size={11} />
            Click & Collect
          </span>
        </div>
      )}

      {/* Content */}
      <div className="flex flex-col flex-1 p-4">
        {/* Categories */}
        <div className="flex flex-wrap gap-1 mb-2">
          {merchantCategories.slice(0, 2).map((cat) => (
            <span
              key={cat.id}
              className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ backgroundColor: `${cat.color}18`, color: cat.color }}
            >
              {cat.icon} {cat.name}
            </span>
          ))}
        </div>

        <Link to={`/haendler/${merchant.slug}`}>
          <h3 className="font-semibold text-gray-900 group-hover:text-primary-700 transition-colors leading-snug mb-1">
            {merchant.name}
          </h3>
        </Link>

        {!compact && (
          <p className="text-sm text-gray-500 leading-relaxed flex-1 line-clamp-2 mb-3">
            {merchant.shortDescription}
          </p>
        )}

        {/* Address */}
        <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-3">
          <MapPin size={12} className="shrink-0" />
          <span>{merchant.address.street}, {merchant.address.city}</span>
        </div>

        {/* Actions */}
        <div className="flex gap-2 mt-auto">
          <Link
            to={`/haendler/${merchant.slug}`}
            className="flex-1 text-center text-xs font-medium py-2 px-3 rounded-lg border border-gray-200 text-gray-600 hover:border-primary-300 hover:text-primary-700 hover:bg-primary-50 transition-colors"
          >
            Profil ansehen
          </Link>
          <Link
            to={`/produkte?haendler=${merchant.id}`}
            className="flex items-center gap-1 text-xs font-medium py-2 px-3 rounded-lg bg-primary-700 text-white hover:bg-primary-800 transition-colors"
          >
            <ShoppingBag size={12} />
            Produkte
          </Link>
        </div>
      </div>
    </div>
  )
}

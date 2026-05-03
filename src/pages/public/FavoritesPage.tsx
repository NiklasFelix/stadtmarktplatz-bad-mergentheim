import { Link } from 'react-router-dom'
import { Heart, ArrowRight, ShoppingBag } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useCustomerStore } from '../../store/useCustomerStore'
import { MerchantCard } from '../../components/merchant/MerchantCard'
import { ProductCard } from '../../components/product/ProductCard'
import { EmptyState } from '../../components/ui/EmptyState'

export function FavoritesPage() {
  const { merchants, products } = useDataStore()
  const { favoriteMerchantIds, savedProductIds } = useCustomerStore()

  const favoriteMerchants = favoriteMerchantIds
    .map((id) => merchants.find((m) => m.id === id))
    .filter(Boolean) as typeof merchants

  const savedProducts = savedProductIds
    .map((id) => products.find((p) => p.id === id))
    .filter(Boolean) as typeof products

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <Heart size={28} className="text-red-400" />
          Meine Favoriten & Merkliste
        </h1>
        <p className="text-gray-500">
          {favoriteMerchants.length} Händler und {savedProducts.length} Produkte gespeichert
        </p>
      </div>

      {/* Favorite merchants */}
      <section className="mb-12">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <Heart size={18} className="text-red-400" />
            Lieblingsläden ({favoriteMerchants.length})
          </h2>
          <Link to="/haendler" className="text-sm text-primary-700 hover:underline flex items-center gap-1">
            Mehr entdecken <ArrowRight size={14} />
          </Link>
        </div>
        {favoriteMerchants.length === 0 ? (
          <EmptyState
            icon={<Heart size={36} />}
            title="Noch keine Lieblingshändler"
            description="Klicken Sie auf das Herz-Symbol in der Händlerkarte, um Lieblingshändler zu speichern."
            action={
              <Link to="/haendler" className="btn-outline mt-2 inline-flex items-center gap-2">
                Händler entdecken <ArrowRight size={15} />
              </Link>
            }
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {favoriteMerchants.map((m) => (
              <MerchantCard key={m.id} merchant={m} />
            ))}
          </div>
        )}
      </section>

      {/* Saved products */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
            <span>🔖</span>
            Gemerkte Produkte ({savedProducts.length})
          </h2>
          <Link to="/produkte" className="text-sm text-primary-700 hover:underline flex items-center gap-1">
            Mehr entdecken <ArrowRight size={14} />
          </Link>
        </div>
        {savedProducts.length === 0 ? (
          <EmptyState
            icon={<ShoppingBag size={36} />}
            title="Noch keine gemerkten Produkte"
            description="Klicken Sie auf das Lesezeichen-Symbol in der Produktkarte, um Produkte zu speichern."
            action={
              <Link to="/produkte" className="btn-outline mt-2 inline-flex items-center gap-2">
                Produkte entdecken <ArrowRight size={15} />
              </Link>
            }
          />
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {savedProducts.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}

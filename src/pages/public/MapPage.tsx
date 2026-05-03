import { useState } from 'react'
import { Link } from 'react-router-dom'
import { List } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { MerchantMap } from '../../components/map/MerchantMap'
import { CategoryFilter } from '../../components/filters/CategoryFilter'

export function MapPage() {
  const { merchants, categories } = useDataStore()
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [highlightedId, setHighlightedId] = useState<string | null>(null)

  const filtered = merchants.filter((m) => {
    if (m.status !== 'active') return false
    return selectedCategories.length === 0 || selectedCategories.some((cid) => m.categoryIds.includes(cid))
  })

  const highlighted = highlightedId ? merchants.find((m) => m.id === highlightedId) : null

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Karte: Händler in Bad Mergentheim</h1>
        <p className="text-gray-500">{filtered.length} Händler auf der Karte</p>
      </div>

      <div className="mb-4 overflow-x-auto pb-2">
        <CategoryFilter
          categories={categories}
          selectedIds={selectedCategories}
          onChange={setSelectedCategories}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Map */}
        <div className="lg:col-span-2">
          <MerchantMap
            merchants={filtered}
            highlightedId={highlightedId}
            onMarkerClick={setHighlightedId}
            height="600px"
          />
        </div>

        {/* Merchant list sidebar */}
        <div className="space-y-3 max-h-[620px] overflow-y-auto pr-1">
          <p className="text-sm font-medium text-gray-500 flex items-center gap-2 sticky top-0 bg-stone-50 py-1">
            <List size={14} />
            {filtered.length} Händler
          </p>
          {filtered.map((m) => {
            const cats = categories.filter((c) => m.categoryIds.includes(c.id))
            return (
              <div
                key={m.id}
                onClick={() => setHighlightedId(m.id === highlightedId ? null : m.id)}
                className={`card p-3.5 cursor-pointer transition-all ${
                  m.id === highlightedId ? 'ring-2 ring-primary-400 shadow-card-hover' : 'hover:shadow-card-hover'
                }`}
              >
                <div className="flex gap-3">
                  <div className="w-14 h-14 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                    <img src={m.images.store} alt={m.name} className="w-full h-full object-cover" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex gap-1 mb-1 flex-wrap">
                      {cats.slice(0, 1).map((c) => (
                        <span key={c.id} className="text-xs px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${c.color}20`, color: c.color }}>
                          {c.icon}
                        </span>
                      ))}
                    </div>
                    <Link
                      to={`/haendler/${m.slug}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-semibold text-sm text-gray-900 hover:text-primary-700 transition-colors leading-tight block"
                    >
                      {m.name}
                    </Link>
                    <p className="text-xs text-gray-500 mt-0.5 leading-tight">{m.address.street}</p>
                    {m.clickAndCollect && (
                      <span className="text-xs text-primary-600 font-medium mt-1 block">✓ Click & Collect</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

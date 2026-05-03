import { useState, useMemo, useRef } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { Search, X, SlidersHorizontal, ShoppingBag } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { ProductCard } from '../../components/product/ProductCard'
import { CategoryFilter } from '../../components/filters/CategoryFilter'
import { EmptyState } from '../../components/ui/EmptyState'
import type { ProductAvailability } from '../../types'
import { AVAILABILITY_LABELS } from '../../utils/formatters'

const AVAILABILITY_OPTIONS: ProductAvailability[] = ['available', 'on_request', 'reserved', 'unavailable']

function tokenMatch(text: string, tokens: string[]): boolean {
  const lower = text.toLowerCase()
  return tokens.every((t) => lower.includes(t))
}

export function ProductsPage() {
  const { products, merchants, categories } = useDataStore()
  const [searchParams] = useSearchParams()
  const merchantFilter = searchParams.get('haendler')

  const [search, setSearch] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedAvailability, setSelectedAvailability] = useState<ProductAvailability | ''>('')
  const [onlyFeatured, setOnlyFeatured] = useState(false)
  const [onlyReservable, setOnlyReservable] = useState(false)
  const [showFilters, setShowFilters] = useState(false)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef<HTMLInputElement>(null)

  const filteredMerchant = merchantFilter
    ? merchants.find((m) => m.id === merchantFilter)
    : null

  const tokens = useMemo(
    () => search.trim().toLowerCase().split(/\s+/).filter(Boolean),
    [search]
  )

  const filtered = useMemo(() => {
    return products.filter((p) => {
      if (!p.active) return false
      if (merchantFilter && p.merchantId !== merchantFilter) return false

      if (tokens.length > 0) {
        const merchant = merchants.find((m) => m.id === p.merchantId)
        const matchesSearch =
          tokenMatch(p.name, tokens) ||
          tokenMatch(p.description, tokens) ||
          p.tags.some((t) => tokenMatch(t, tokens)) ||
          (merchant ? tokenMatch(merchant.name, tokens) : false) ||
          categories
            .filter((c) => p.categoryIds.includes(c.id))
            .some((c) => tokenMatch(c.name, tokens))
        if (!matchesSearch) return false
      }

      const matchesCategories =
        selectedCategories.length === 0 ||
        selectedCategories.some((cid) => p.categoryIds.includes(cid))

      const matchesAvailability =
        !selectedAvailability || p.availability === selectedAvailability

      const matchesFeatured = !onlyFeatured || p.featured
      const matchesReservable = !onlyReservable || p.reservable

      return matchesCategories && matchesAvailability && matchesFeatured && matchesReservable
    })
  }, [products, merchantFilter, tokens, selectedCategories, selectedAvailability, onlyFeatured, onlyReservable, merchants, categories])

  const suggestions = useMemo(() => {
    if (tokens.length === 0) return []
    return products
      .filter((p) => p.active && tokenMatch(p.name, tokens))
      .slice(0, 5)
  }, [products, tokens])

  const hasFilters = search || selectedCategories.length > 0 || selectedAvailability || onlyFeatured || onlyReservable

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-6">
        {filteredMerchant ? (
          <>
            <nav className="flex items-center gap-2 text-sm text-gray-500 mb-4">
              <Link to="/haendler" className="hover:text-primary-700">Händler</Link>
              <span>/</span>
              <Link to={`/haendler/${filteredMerchant.slug}`} className="hover:text-primary-700">{filteredMerchant.name}</Link>
              <span>/</span>
              <span className="text-gray-800">Produkte</span>
            </nav>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Produkte von {filteredMerchant.name}</h1>
            <p className="text-gray-500">{filtered.length} Produkte verfügbar</p>
          </>
        ) : (
          <>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">Alle Produkte</h1>
            <p className="text-gray-500">{products.filter((p) => p.active).length} Produkte aus {merchants.filter((m) => m.status === 'active').length} Händlern</p>
          </>
        )}
      </div>

      {/* Search */}
      <div className="flex gap-3 mb-5">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            ref={searchRef}
            type="text"
            placeholder="Produkt, Händler, Kategorie oder Schlagwort …"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setShowSuggestions(true) }}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            className="w-full pl-10 pr-10 py-2.5 rounded-xl border border-gray-300 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
          />
          {search && (
            <button
              onClick={() => { setSearch(''); setShowSuggestions(false); searchRef.current?.focus() }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X size={14} />
            </button>
          )}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 overflow-hidden">
              {suggestions.map((p) => {
                const merchant = merchants.find((m) => m.id === p.merchantId)
                return (
                  <button
                    key={p.id}
                    onMouseDown={() => { setSearch(p.name); setShowSuggestions(false) }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left hover:bg-gray-50 transition-colors"
                  >
                    <ShoppingBag size={13} className="text-gray-400 shrink-0" />
                    <span className="font-medium text-gray-800 flex-1">{p.name}</span>
                    {merchant && <span className="text-gray-400 text-xs">{merchant.name}</span>}
                  </button>
                )
              })}
            </div>
          )}
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl border text-sm font-medium transition-colors ${
            showFilters ? 'bg-primary-700 text-white border-primary-700' : 'bg-white border-gray-300 text-gray-600 hover:border-gray-400'
          }`}
        >
          <SlidersHorizontal size={15} />
          Filter
          {hasFilters && <span className="w-1.5 h-1.5 rounded-full bg-secondary-500" />}
        </button>
      </div>

      {/* Expanded filters */}
      {showFilters && (
        <div className="card p-5 mb-5 space-y-4">
          <div>
            <p className="text-sm font-medium text-gray-700 mb-2.5">Kategorie</p>
            <div className="overflow-x-auto pb-1">
              <CategoryFilter
                categories={categories}
                selectedIds={selectedCategories}
                onChange={setSelectedCategories}
              />
            </div>
          </div>
          <div className="flex flex-wrap gap-4">
            <div>
              <p className="text-sm font-medium text-gray-700 mb-2">Verfügbarkeit</p>
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedAvailability('')}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${!selectedAvailability ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}`}
                >
                  Alle
                </button>
                {AVAILABILITY_OPTIONS.map((avail) => (
                  <button
                    key={avail}
                    onClick={() => setSelectedAvailability(avail === selectedAvailability ? '' : avail)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${selectedAvailability === avail ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300'}`}
                  >
                    {AVAILABILITY_LABELS[avail]}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-3">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={onlyFeatured}
                onChange={(e) => setOnlyFeatured(e.target.checked)}
                className="rounded border-gray-300 text-primary-600"
              />
              Nur Empfehlungen
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={onlyReservable}
                onChange={(e) => setOnlyReservable(e.target.checked)}
                className="rounded border-gray-300 text-primary-600"
              />
              Nur reservierbar
            </label>
          </div>
          {hasFilters && (
            <button
              onClick={() => {
                setSearch('')
                setSelectedCategories([])
                setSelectedAvailability('')
                setOnlyFeatured(false)
                setOnlyReservable(false)
              }}
              className="text-xs text-red-600 hover:underline"
            >
              Alle Filter zurücksetzen
            </button>
          )}
        </div>
      )}

      {/* Results */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<ShoppingBag size={40} />}
          title="Keine Produkte gefunden"
          description={search.trim() ? `Für „${search.trim()}" wurden keine Produkte gefunden. Prüfen Sie die Schreibweise oder passen Sie die Filter an.` : 'Passen Sie die Filtereinstellungen an.'}
        />
      ) : (
        <>
          {hasFilters && (
            <p className="text-sm text-gray-500 mb-4">{filtered.length} Produkt{filtered.length !== 1 ? 'e' : ''} gefunden</p>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
            {filtered.map((p) => (
              <ProductCard key={p.id} product={p} showMerchant={!merchantFilter} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

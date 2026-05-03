import { useState, useMemo, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, Map, List, SlidersHorizontal, X, Store } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { MerchantCard } from '../../components/merchant/MerchantCard'
import { MerchantMap } from '../../components/map/MerchantMap'
import { CategoryFilter } from '../../components/filters/CategoryFilter'
import { EmptyState } from '../../components/ui/EmptyState'

type ViewMode = 'list' | 'map' | 'split'

function tokenMatch(text: string, tokens: string[]): boolean {
  const lower = text.toLowerCase()
  return tokens.every((t) => lower.includes(t))
}

export function MerchantsPage() {
  const { merchants, categories } = useDataStore()
  const [searchParams, setSearchParams] = useSearchParams()

  const [search, setSearch] = useState('')
  const [selectedCategories, setSelectedCategories] = useState<string[]>(() => {
    const slug = searchParams.get('kategorien')
    if (!slug) return []
    const cat = categories.find((c) => c.slug === slug)
    return cat ? [cat.id] : []
  })
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [highlightedId, setHighlightedId] = useState<string | null>(null)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const searchRef = useRef<HTMLInputElement>(null)

  const activeMerchants = useMemo(
    () => merchants.filter((m) => m.status === 'active'),
    [merchants]
  )

  const tokens = useMemo(
    () => search.trim().toLowerCase().split(/\s+/).filter(Boolean),
    [search]
  )

  const filtered = useMemo(() => {
    return activeMerchants.filter((m) => {
      const matchesSearch =
        tokens.length === 0 ||
        tokenMatch(m.name, tokens) ||
        tokenMatch(m.shortDescription, tokens) ||
        tokenMatch(m.description, tokens) ||
        (m.address.district ? tokenMatch(m.address.district, tokens) : false) ||
        tokenMatch(m.address.street, tokens) ||
        categories
          .filter((c) => m.categoryIds.includes(c.id))
          .some((c) => tokenMatch(c.name, tokens))

      const matchesCategories =
        selectedCategories.length === 0 ||
        selectedCategories.some((cid) => m.categoryIds.includes(cid))

      return matchesSearch && matchesCategories
    })
  }, [activeMerchants, tokens, selectedCategories, categories])

  const suggestions = useMemo(() => {
    if (tokens.length === 0) return []
    return activeMerchants
      .filter((m) => tokenMatch(m.name, tokens))
      .slice(0, 5)
  }, [activeMerchants, tokens])

  const clickCollectCount = filtered.filter((m) => m.clickAndCollect).length
  const hasFilter = search.trim().length > 0 || selectedCategories.length > 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Händler in Bad Mergentheim</h1>
        <p className="text-gray-500">
          {activeMerchants.length} lokale Händler – {clickCollectCount} mit Click &amp; Collect
        </p>
      </div>

      {/* Search + View Toggle */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
          <input
            ref={searchRef}
            type="text"
            placeholder="Name, Kategorie, Straße oder Beschreibung …"
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
          {/* Suggestions dropdown */}
          {showSuggestions && suggestions.length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 overflow-hidden">
              {suggestions.map((m) => (
                <button
                  key={m.id}
                  onMouseDown={() => { setSearch(m.name); setShowSuggestions(false) }}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left hover:bg-gray-50 transition-colors"
                >
                  <Store size={13} className="text-gray-400 shrink-0" />
                  <span className="font-medium text-gray-800">{m.name}</span>
                  <span className="text-gray-400 text-xs ml-auto">{m.address.street}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* View mode toggle */}
        <div className="flex items-center bg-white border border-gray-200 rounded-xl p-1 gap-1">
          {([
            { mode: 'list', icon: <List size={16} />, label: 'Liste' },
            { mode: 'split', icon: <SlidersHorizontal size={16} />, label: 'Karte + Liste' },
            { mode: 'map',  icon: <Map size={16} />,  label: 'Karte' },
          ] as const).map(({ mode, icon, label }) => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                viewMode === mode
                  ? 'bg-primary-700 text-white'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              {icon}
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Category Filter */}
      <div className="mb-6 overflow-x-auto pb-2">
        <CategoryFilter
          categories={categories}
          selectedIds={selectedCategories}
          onChange={setSelectedCategories}
        />
      </div>

      {/* Results count */}
      {hasFilter && (
        <div className="mb-4 flex items-center gap-3">
          <p className="text-sm text-gray-500">
            {filtered.length} {filtered.length === 1 ? 'Händler' : 'Händler'} gefunden
            {search.trim() && <span className="text-gray-400"> für „{search.trim()}"</span>}
          </p>
          <button
            onClick={() => { setSearch(''); setSelectedCategories([]) }}
            className="text-xs text-primary-700 hover:underline"
          >
            Filter zurücksetzen
          </button>
        </div>
      )}

      {/* Content */}
      {filtered.length === 0 ? (
        <EmptyState
          icon={<Search size={40} />}
          title="Keine Händler gefunden"
          description={search.trim() ? `Für „${search.trim()}" wurden keine Händler gefunden. Prüfen Sie die Schreibweise oder wählen Sie eine andere Kategorie.` : 'Keine Händler in dieser Kategorie.'}
          action={
            <button
              onClick={() => { setSearch(''); setSelectedCategories([]) }}
              className="btn-primary mt-2"
            >
              Filter zurücksetzen
            </button>
          }
        />
      ) : viewMode === 'list' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filtered.map((m) => (
            <MerchantCard key={m.id} merchant={m} />
          ))}
        </div>
      ) : viewMode === 'map' ? (
        <MerchantMap
          merchants={filtered}
          highlightedId={highlightedId}
          onMarkerClick={setHighlightedId}
          height="600px"
        />
      ) : (
        // Split view
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[700px]">
          {/* Left: scrollable list */}
          <div className="overflow-y-auto space-y-3 pr-2">
            {filtered.map((m) => (
              <div
                key={m.id}
                onMouseEnter={() => setHighlightedId(m.id)}
                onMouseLeave={() => setHighlightedId(null)}
              >
                <MerchantCard merchant={m} compact highlighted={highlightedId === m.id} />
              </div>
            ))}
          </div>
          {/* Right: map */}
          <div className="sticky top-4">
            <MerchantMap
              merchants={filtered}
              highlightedId={highlightedId}
              onMarkerClick={setHighlightedId}
              height="100%"
            />
          </div>
        </div>
      )}
    </div>
  )
}

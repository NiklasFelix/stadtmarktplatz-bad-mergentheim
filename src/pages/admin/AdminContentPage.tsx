import { useState } from 'react'
import { GripVertical, Eye, EyeOff, Save, CheckCircle2 } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { Button } from '../../components/ui/Button'
import type { FeaturedContent } from '../../types'

export function AdminContentPage() {
  const { featuredContent, merchants, products, updateFeaturedContent } = useDataStore()
  const [content, setContent] = useState<FeaturedContent[]>(featuredContent)
  const [saved, setSaved] = useState(false)

  const featuredMerchants = content.filter((fc) => fc.type === 'merchant').sort((a, b) => a.position - b.position)
  const featuredProducts = content.filter((fc) => fc.type === 'product').sort((a, b) => a.position - b.position)

  function toggleActive(id: string) {
    setContent((prev) => prev.map((fc) => fc.id === id ? { ...fc, active: !fc.active } : fc))
  }

  function save() {
    updateFeaturedContent(content)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  function ContentRow({ fc }: { fc: FeaturedContent }) {
    const merchant = fc.type === 'merchant' ? merchants.find((m) => m.id === fc.refId) : null
    const product = fc.type === 'product' ? products.find((p) => p.id === fc.refId) : null
    const item = merchant ?? product
    const image = merchant?.images.store ?? product?.images[0] ?? ''
    const name = merchant?.name ?? product?.name ?? 'Unbekannt'

    return (
      <div className={`flex items-center gap-3 p-3 rounded-xl border transition-all ${fc.active ? 'border-gray-200 bg-white' : 'border-dashed border-gray-200 bg-gray-50 opacity-60'}`}>
        <GripVertical size={16} className="text-gray-300 cursor-grab shrink-0" />
        <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100 shrink-0">
          {image && <img src={image} alt={name} className="w-full h-full object-cover" />}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-gray-900 text-sm truncate">{name}</p>
          <p className="text-xs text-gray-400">Position {fc.position}</p>
        </div>
        <button
          onClick={() => toggleActive(fc.id)}
          className={`p-2 rounded-lg transition-colors ${fc.active ? 'text-green-600 hover:bg-green-50' : 'text-gray-400 hover:bg-gray-100'}`}
          title={fc.active ? 'Deaktivieren' : 'Aktivieren'}
        >
          {fc.active ? <Eye size={16} /> : <EyeOff size={16} />}
        </button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Startseite verwalten</h1>
          <p className="text-gray-500 mt-1">Steuern Sie, welche Inhalte auf der Startseite erscheinen.</p>
        </div>
        <Button
          variant={saved ? 'secondary' : 'primary'}
          leftIcon={saved ? <CheckCircle2 size={16} /> : <Save size={16} />}
          onClick={save}
        >
          {saved ? 'Gespeichert!' : 'Änderungen speichern'}
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Featured merchants */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Ausgewählte Händler ({featuredMerchants.filter((fc) => fc.active).length} aktiv)</h2>
          <div className="space-y-2">
            {featuredMerchants.map((fc) => <ContentRow key={fc.id} fc={fc} />)}
          </div>
        </div>

        {/* Featured products */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-900 mb-4">Empfohlene Produkte ({featuredProducts.filter((fc) => fc.active).length} aktiv)</h2>
          <div className="space-y-2">
            {featuredProducts.map((fc) => <ContentRow key={fc.id} fc={fc} />)}
          </div>
        </div>
      </div>

      <div className="mt-6 p-4 bg-blue-50 rounded-xl border border-blue-100">
        <p className="text-sm text-blue-800">
          <strong>Hinweis:</strong> Deaktivierte Einträge werden auf der Startseite ausgeblendet. Die Reihenfolge entspricht der Position. Für vollständige Drag-&-Drop-Sortierung kann später eine Bibliothek wie <code>@dnd-kit/core</code> integriert werden.
        </p>
      </div>
    </div>
  )
}

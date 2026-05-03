import { useState } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { Button } from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import type { Category } from '../../types'

export function AdminCategoriesPage() {
  const { categories, merchants, products } = useDataStore()
  const [showForm, setShowForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newIcon, setNewIcon] = useState('🏷')
  const [newColor, setNewColor] = useState('#1b4f8a')

  function addCategory() {
    if (!newName.trim()) return
    const cat: Category = {
      id: `cat-${Date.now()}`,
      name: newName,
      slug: newName.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''),
      icon: newIcon,
      color: newColor,
    }
    useDataStore.getState().categories.push(cat)
    setNewName('')
    setNewIcon('🏷')
    setShowForm(false)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Kategorien</h1>
          <p className="text-gray-500 mt-1">{categories.length} Kategorien</p>
        </div>
        <Button variant="primary" leftIcon={<Plus size={16} />} onClick={() => setShowForm(!showForm)}>
          Neue Kategorie
        </Button>
      </div>

      {/* Add form */}
      {showForm && (
        <div className="card p-5 mb-6 border-2 border-primary-200">
          <h3 className="font-semibold text-gray-900 mb-4">Neue Kategorie anlegen</h3>
          <div className="flex flex-wrap gap-3 items-end">
            <div className="w-48">
              <Input label="Name" value={newName} onChange={(e) => setNewName(e.target.value)} placeholder="z. B. Musik & Kultur" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Icon (Emoji)</label>
              <input
                type="text"
                value={newIcon}
                onChange={(e) => setNewIcon(e.target.value)}
                className="input-field w-20 text-center text-xl"
                maxLength={2}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Farbe</label>
              <input type="color" value={newColor} onChange={(e) => setNewColor(e.target.value)} className="h-10 w-12 rounded-lg border border-gray-300 cursor-pointer" />
            </div>
            <Button variant="primary" onClick={addCategory}>Anlegen</Button>
            <Button variant="ghost" onClick={() => setShowForm(false)}>Abbrechen</Button>
          </div>
        </div>
      )}

      {/* Categories grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((cat) => {
          const merchantCount = merchants.filter((m) => m.categoryIds.includes(cat.id) && m.status === 'active').length
          const productCount = products.filter((p) => p.categoryIds.includes(cat.id) && p.active).length
          return (
            <div key={cat.id} className="card p-5 flex items-center gap-4">
              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl shrink-0"
                style={{ backgroundColor: `${cat.color}20` }}
              >
                {cat.icon}
              </div>
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{cat.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {merchantCount} Händler · {productCount} Produkte
                </p>
                <p className="text-xs text-gray-300 font-mono mt-0.5">{cat.slug}</p>
              </div>
              <div
                className="w-5 h-5 rounded-full border border-white shadow-sm shrink-0"
                style={{ backgroundColor: cat.color }}
              />
            </div>
          )
        })}
      </div>
    </div>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Plus, Edit, Power, PowerOff, X, Save, CheckCircle2 } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'
import { AvailabilityBadge } from '../../components/product/AvailabilityBadge'
import { EmptyState } from '../../components/ui/EmptyState'
import { Input, Textarea, Select } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { formatPrice, slugify } from '../../utils/formatters'
import type { ProductAvailability } from '../../types'

interface QuickAddForm {
  name: string
  description: string
  priceType: 'fixed' | 'range' | 'on_request'
  priceFixed: number
  priceMin: number
  priceMax: number
  availability: ProductAvailability
  reservable: boolean
  categoryId: string
  imageUrl: string
}

export function SellerProductsPage() {
  const { currentMerchantId } = useAuthStore()
  const { products, categories, updateProduct, addProduct } = useDataStore()
  const navigate = useNavigate()

  const [showInlineForm, setShowInlineForm] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const merchantProducts = products.filter((p) => p.merchantId === currentMerchantId)
  const activeCount = merchantProducts.filter((p) => p.active).length

  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<QuickAddForm>({
    defaultValues: {
      priceType: 'fixed',
      availability: 'available',
      reservable: true,
    },
  })

  const priceType = watch('priceType')

  async function onQuickSubmit(data: QuickAddForm) {
    if (!currentMerchantId) return
    setSaving(true)
    const price = data.priceType === 'fixed'
      ? { type: 'fixed' as const, value: data.priceFixed }
      : data.priceType === 'range'
      ? { type: 'range' as const, min: data.priceMin, max: data.priceMax }
      : { type: 'on_request' as const }
    const now = new Date().toISOString()
    addProduct({
      id: `prod-${Date.now()}`,
      slug: slugify(data.name),
      merchantId: currentMerchantId,
      name: data.name,
      description: data.description,
      price,
      categoryIds: data.categoryId ? [data.categoryId] : [],
      tags: [],
      images: data.imageUrl ? [data.imageUrl] : [],
      availability: data.availability,
      featured: false,
      reservable: data.reservable,
      active: true,
      createdAt: now,
      updatedAt: now,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => {
      setSaved(false)
      setShowInlineForm(false)
      reset()
    }, 900)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Meine Produkte</h1>
          <p className="text-gray-500 mt-1">{activeCount} aktive von {merchantProducts.length} Produkten</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => { setShowInlineForm((v) => !v); setSaved(false) }}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-colors ${showInlineForm ? 'bg-gray-100 text-gray-700 hover:bg-gray-200' : 'bg-primary-700 text-white hover:bg-primary-800'}`}
          >
            {showInlineForm ? <X size={16} /> : <Plus size={16} />}
            {showInlineForm ? 'Abbrechen' : 'Neues Produkt'}
          </button>
          <Link
            to="/seller/produkte/neu"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-gray-300 text-gray-600 font-medium text-sm hover:border-gray-400 transition-colors"
            title="Vollständiges Formular öffnen"
          >
            <Edit size={16} />
            Erweitertes Formular
          </Link>
        </div>
      </div>

      {/* Inline quick-add form */}
      {showInlineForm && (
        <div className="card p-6 mb-6 border-2 border-primary-200 bg-primary-50/30">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Plus size={18} className="text-primary-700" />
            Neues Produkt anlegen
          </h2>
          <form onSubmit={handleSubmit(onQuickSubmit)} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Produktname *"
                placeholder="z. B. Regionaler Honig 500g"
                error={errors.name?.message}
                {...register('name', { required: 'Bitte Produktname eingeben' })}
              />
              <Select
                label="Kategorie"
                placeholder="Kategorie wählen…"
                options={categories.map((c) => ({ value: c.id, label: c.name }))}
                {...register('categoryId')}
              />
            </div>
            <Textarea
              label="Beschreibung *"
              placeholder="Beschreiben Sie Ihr Produkt – Besonderheiten, Herkunft, Qualität…"
              rows={3}
              error={errors.description?.message}
              {...register('description', { required: 'Bitte Beschreibung eingeben' })}
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Preis</label>
              <div className="flex gap-2 mb-3">
                {(['fixed', 'range', 'on_request'] as const).map((t) => (
                  <label key={t} className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm transition-colors ${watch('priceType') === t ? 'border-primary-400 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-600 bg-white'}`}>
                    <input type="radio" value={t} {...register('priceType')} className="sr-only" />
                    {t === 'fixed' ? 'Festpreis' : t === 'range' ? 'Preisspanne' : 'Auf Anfrage'}
                  </label>
                ))}
              </div>
              {priceType === 'fixed' && (
                <Input type="number" step="0.01" min="0" placeholder="z. B. 12.90" leftIcon={<span className="text-xs">€</span>} {...register('priceFixed', { valueAsNumber: true })} />
              )}
              {priceType === 'range' && (
                <div className="grid grid-cols-2 gap-3">
                  <Input type="number" step="0.01" min="0" placeholder="Von (€)" {...register('priceMin', { valueAsNumber: true })} />
                  <Input type="number" step="0.01" min="0" placeholder="Bis (€)" {...register('priceMax', { valueAsNumber: true })} />
                </div>
              )}
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Verfügbarkeit"
                options={[
                  { value: 'available', label: 'Verfügbar' },
                  { value: 'on_request', label: 'Auf Anfrage' },
                  { value: 'reserved', label: 'Reserviert' },
                  { value: 'unavailable', label: 'Nicht verfügbar' },
                ]}
                {...register('availability')}
              />
              <Input label="Bild-URL (optional)" type="url" placeholder="https://…" {...register('imageUrl')} />
            </div>
            <div className="flex items-center justify-between pt-1">
              <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('reservable')} />
                Click &amp; Collect erlauben
              </label>
              <div className="flex gap-2">
                <Button
                  type="submit"
                  variant={saved ? 'secondary' : 'primary'}
                  loading={saving}
                  leftIcon={saved ? <CheckCircle2 size={16} /> : <Save size={16} />}
                >
                  {saved ? 'Gespeichert!' : 'Produkt anlegen'}
                </Button>
                <button
                  type="button"
                  onClick={() => navigate('/seller/produkte/neu')}
                  className="text-xs text-primary-700 hover:underline px-2"
                >
                  Weitere Optionen →
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {merchantProducts.length === 0 && !showInlineForm ? (
        <EmptyState
          title="Noch keine Produkte"
          description="Legen Sie Ihr erstes Produkt an, damit Kunden es online finden und reservieren können."
          action={
            <button
              onClick={() => setShowInlineForm(true)}
              className="btn-primary mt-2 inline-flex items-center gap-2"
            >
              <Plus size={16} />Erstes Produkt anlegen
            </button>
          }
        />
      ) : merchantProducts.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="text-left px-5 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Produkt</th>
                  <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden md:table-cell">Preis</th>
                  <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide">Verfügbarkeit</th>
                  <th className="text-left px-4 py-3.5 text-xs font-semibold text-gray-500 uppercase tracking-wide hidden sm:table-cell">Status</th>
                  <th className="px-4 py-3.5" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {merchantProducts.map((p) => (
                  <tr key={p.id} className={`group ${!p.active ? 'opacity-60' : ''}`}>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        {p.images[0] && (
                          <img src={p.images[0]} alt={p.name} className="w-10 h-10 rounded-lg object-cover shrink-0" />
                        )}
                        <div>
                          <p className="font-medium text-gray-900">{p.name}</p>
                          <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{p.description}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 hidden md:table-cell font-medium text-gray-700">
                      {formatPrice(p.price)}
                    </td>
                    <td className="px-4 py-4">
                      <AvailabilityBadge availability={p.availability} />
                    </td>
                    <td className="px-4 py-4 hidden sm:table-cell">
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${p.active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                        {p.active ? 'Aktiv' : 'Inaktiv'}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                        <Link
                          to={`/seller/produkte/${p.id}/bearbeiten`}
                          className="p-1.5 rounded-lg text-gray-400 hover:text-primary-700 hover:bg-primary-50 transition-colors"
                          title="Bearbeiten"
                        >
                          <Edit size={15} />
                        </Link>
                        <button
                          onClick={() => updateProduct(p.id, { active: !p.active })}
                          className={`p-1.5 rounded-lg transition-colors ${p.active ? 'text-gray-400 hover:text-red-500 hover:bg-red-50' : 'text-gray-400 hover:text-green-600 hover:bg-green-50'}`}
                          title={p.active ? 'Deaktivieren' : 'Aktivieren'}
                        >
                          {p.active ? <PowerOff size={15} /> : <Power size={15} />}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { ArrowLeft, Save, CheckCircle2 } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'
import { Input, Textarea, Select } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { slugify } from '../../utils/formatters'
import type { ProductAvailability } from '../../types'

const CLOTHING_SIZES_LETTER = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
const CLOTHING_SIZES_NUMERIC = ['34', '36', '38', '40', '42', '44', '46', '48']
const CLOTHING_CATEGORY_ID = 'cat-1'

interface ProductFormData {
  name: string
  description: string
  priceType: 'fixed' | 'range' | 'on_request'
  priceFixed: number
  priceMin: number
  priceMax: number
  availability: ProductAvailability
  reservable: boolean
  featured: boolean
  imageUrl: string
  tags: string
  categoryId: string
}

export function SellerProductFormPage() {
  const { id } = useParams<{ id?: string }>()
  const navigate = useNavigate()
  const { currentMerchantId } = useAuthStore()
  const { products, categories, addProduct, updateProduct } = useDataStore()
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [selectedSizes, setSelectedSizes] = useState<string[]>(existingProduct?.sizes ?? [])
  const [sizeMode, setSizeMode] = useState<'letter' | 'numeric'>('letter')

  const existingProduct = id ? products.find((p) => p.id === id) : null
  const isEdit = !!existingProduct

  const { register, handleSubmit, watch, reset, formState: { errors } } = useForm<ProductFormData>({
    defaultValues: existingProduct ? {
      name: existingProduct.name,
      description: existingProduct.description,
      priceType: existingProduct.price.type,
      priceFixed: existingProduct.price.type === 'fixed' ? existingProduct.price.value : 0,
      priceMin: existingProduct.price.type === 'range' ? existingProduct.price.min : 0,
      priceMax: existingProduct.price.type === 'range' ? existingProduct.price.max : 0,
      availability: existingProduct.availability,
      reservable: existingProduct.reservable,
      featured: existingProduct.featured,
      imageUrl: existingProduct.images[0] ?? '',
      tags: existingProduct.tags.join(', '),
      categoryId: existingProduct.categoryIds[0] ?? '',
    } : {
      priceType: 'fixed',
      availability: 'available',
      reservable: true,
      featured: false,
    },
  })

  const priceType = watch('priceType')
  const categoryId = watch('categoryId')
  const isClothing = categoryId === CLOTHING_CATEGORY_ID

  function toggleSize(s: string) {
    setSelectedSizes((prev) => prev.includes(s) ? prev.filter((x) => x !== s) : [...prev, s])
  }

  async function onSubmit(data: ProductFormData) {
    if (!currentMerchantId) return
    setSaving(true)

    const price = data.priceType === 'fixed'
      ? { type: 'fixed' as const, value: data.priceFixed }
      : data.priceType === 'range'
      ? { type: 'range' as const, min: data.priceMin, max: data.priceMax }
      : { type: 'on_request' as const }

    const tags = data.tags.split(',').map((t) => t.trim()).filter(Boolean)
    const now = new Date().toISOString()

    if (isEdit && existingProduct) {
      updateProduct(existingProduct.id, {
        name: data.name,
        description: data.description,
        price,
        availability: data.availability,
        reservable: data.reservable,
        featured: data.featured,
        images: data.imageUrl ? [data.imageUrl] : existingProduct.images,
        tags,
        categoryIds: data.categoryId ? [data.categoryId] : existingProduct.categoryIds,
        sizes: isClothing && selectedSizes.length > 0 ? selectedSizes : undefined,
      })
    } else {
      addProduct({
        id: `prod-${Date.now()}`,
        slug: slugify(data.name),
        merchantId: currentMerchantId,
        name: data.name,
        description: data.description,
        price,
        categoryIds: data.categoryId ? [data.categoryId] : [],
        tags,
        images: data.imageUrl ? [data.imageUrl] : [],
        availability: data.availability,
        featured: data.featured,
        reservable: data.reservable,
        active: true,
        sizes: isClothing && selectedSizes.length > 0 ? selectedSizes : undefined,
        createdAt: now,
        updatedAt: now,
      })
    }

    setSaving(false)
    setSaved(true)
    setTimeout(() => {
      navigate('/seller/produkte')
    }, 800)
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/seller/produkte" className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">
          {isEdit ? `${existingProduct.name} bearbeiten` : 'Neues Produkt anlegen'}
        </h1>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-5">
          <Input
            label="Produktname *"
            placeholder="z. B. Regionaler Honig 500g"
            error={errors.name?.message}
            {...register('name', { required: 'Bitte Produktname eingeben' })}
          />

          <Textarea
            label="Beschreibung *"
            placeholder="Beschreiben Sie Ihr Produkt – Besonderheiten, Herkunft, Qualität…"
            rows={4}
            error={errors.description?.message}
            {...register('description', { required: 'Bitte Beschreibung eingeben' })}
          />

          {/* Price */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Preis</label>
            <div className="flex gap-2 mb-3">
              {(['fixed', 'range', 'on_request'] as const).map((t) => (
                <label key={t} className={`flex items-center gap-2 px-3 py-2 rounded-lg border cursor-pointer text-sm transition-colors ${watch('priceType') === t ? 'border-primary-400 bg-primary-50 text-primary-700' : 'border-gray-200 text-gray-600'}`}>
                  <input type="radio" value={t} {...register('priceType')} className="sr-only" />
                  {t === 'fixed' ? 'Festpreis' : t === 'range' ? 'Preisspanne' : 'Auf Anfrage'}
                </label>
              ))}
            </div>
            {priceType === 'fixed' && (
              <Input
                type="number"
                step="0.01"
                min="0"
                placeholder="z. B. 12.90"
                leftIcon={<span className="text-xs">€</span>}
                {...register('priceFixed', { valueAsNumber: true })}
              />
            )}
            {priceType === 'range' && (
              <div className="grid grid-cols-2 gap-3">
                <Input type="number" step="0.01" min="0" placeholder="Von (€)" {...register('priceMin', { valueAsNumber: true })} />
                <Input type="number" step="0.01" min="0" placeholder="Bis (€)" {...register('priceMax', { valueAsNumber: true })} />
              </div>
            )}
          </div>

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

          <Select
            label="Kategorie"
            placeholder="Kategorie wählen…"
            options={useDataStore.getState().categories.map((c) => ({ value: c.id, label: `${c.icon} ${c.name}` }))}
            {...register('categoryId')}
          />

          {isClothing && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-sm font-medium text-gray-700">Verfügbare Größen</label>
                <div className="flex gap-1">
                  {(['letter', 'numeric'] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      onClick={() => setSizeMode(m)}
                      className={`text-xs px-2.5 py-1 rounded-full border transition-colors ${sizeMode === m ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-gray-500 border-gray-200 hover:border-gray-300'}`}
                    >
                      {m === 'letter' ? 'Buchstaben (S–XXL)' : 'Numerisch (36–48)'}
                    </button>
                  ))}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {(sizeMode === 'letter' ? CLOTHING_SIZES_LETTER : CLOTHING_SIZES_NUMERIC).map((s) => (
                  <button
                    key={s}
                    type="button"
                    onClick={() => toggleSize(s)}
                    className={`px-3 py-1.5 rounded-lg border text-sm font-medium transition-colors ${selectedSizes.includes(s) ? 'bg-primary-700 text-white border-primary-700' : 'bg-white text-gray-600 border-gray-200 hover:border-primary-300'}`}
                  >
                    {s}
                  </button>
                ))}
              </div>
              {selectedSizes.length > 0 && (
                <p className="text-xs text-gray-400 mt-1.5">Ausgewählt: {selectedSizes.join(', ')}</p>
              )}
            </div>
          )}

          <Input
            label="Bild-URL"
            type="url"
            placeholder="https://beispiel.de/bild.jpg"
            hint="Direkte URL zu einem Produktbild."
            {...register('imageUrl')}
          />

          <Input
            label="Tags (kommagetrennt)"
            placeholder="z. B. regional, Bio, Geschenk"
            {...register('tags')}
          />

          <div className="flex flex-col gap-3 pt-2">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('reservable')} />
              <span className="text-sm text-gray-700">Click & Collect – Reservierung erlauben</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('featured')} />
              <span className="text-sm text-gray-700">Als Empfehlung hervorheben</span>
            </label>
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="submit"
              variant={saved ? 'secondary' : 'primary'}
              size="lg"
              loading={saving}
              leftIcon={saved ? <CheckCircle2 size={18} /> : <Save size={18} />}
              className="flex-1"
            >
              {saved ? 'Gespeichert!' : isEdit ? 'Änderungen speichern' : 'Produkt anlegen'}
            </Button>
            <Link
              to="/seller/produkte"
              className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-300 text-gray-600 font-medium text-sm hover:border-gray-400 transition-colors"
            >
              Abbrechen
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

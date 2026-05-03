import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { ArrowLeft, Save, CheckCircle2 } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { Input, Textarea, Select } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { slugify } from '../../utils/formatters'

interface MerchantFormData {
  name: string
  shortDescription: string
  description: string
  categoryId: string
  phone: string
  email: string
  website: string
  street: string
  zip: string
  city: string
  lat: number
  lng: number
  storeImage: string
  clickAndCollect: boolean
  featured: boolean
}

const DEFAULT_HOURS = {
  montag:     { open: '09:00', close: '18:00', closed: false },
  dienstag:   { open: '09:00', close: '18:00', closed: false },
  mittwoch:   { open: '09:00', close: '18:00', closed: false },
  donnerstag: { open: '09:00', close: '18:00', closed: false },
  freitag:    { open: '09:00', close: '18:30', closed: false },
  samstag:    { open: '09:00', close: '14:00', closed: false },
  sonntag:    { open: '00:00', close: '00:00', closed: true },
}

export function AdminMerchantFormPage() {
  const navigate = useNavigate()
  const { categories, addMerchant } = useDataStore()
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<MerchantFormData>({
    defaultValues: {
      zip: '97980',
      city: 'Bad Mergentheim',
      lat: 49.4928,
      lng: 9.7745,
      clickAndCollect: true,
      featured: false,
    },
  })

  async function onSubmit(data: MerchantFormData) {
    setSaving(true)
    const now = new Date().toISOString()
    addMerchant({
      id: `merchant-${Date.now()}`,
      slug: slugify(data.name),
      userId: 'user-new',
      name: data.name,
      categoryIds: data.categoryId ? [data.categoryId] : [],
      shortDescription: data.shortDescription,
      description: data.description,
      address: { street: data.street, zip: data.zip, city: data.city },
      coordinates: { lat: data.lat, lng: data.lng },
      contact: {
        phone: data.phone || undefined,
        email: data.email || undefined,
        website: data.website || undefined,
      },
      openingHours: DEFAULT_HOURS,
      images: { store: data.storeImage || 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800&q=80' },
      clickAndCollect: data.clickAndCollect,
      featured: data.featured,
      status: 'pending',
      createdAt: now,
      updatedAt: now,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => navigate('/admin/haendler'), 800)
  }

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/admin/haendler" className="p-2 rounded-lg hover:bg-gray-100 text-gray-500 transition-colors">
          <ArrowLeft size={20} />
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Neuen Händler anlegen</h1>
      </div>

      <div className="max-w-2xl">
        <form onSubmit={handleSubmit(onSubmit)} className="card p-6 space-y-5">
          <Input
            label="Geschäftsname *"
            placeholder="z. B. Buchhandlung Musterbach"
            error={errors.name?.message}
            {...register('name', { required: 'Pflichtfeld' })}
          />
          <Input
            label="Kurzbeschreibung *"
            error={errors.shortDescription?.message}
            {...register('shortDescription', { required: 'Pflichtfeld' })}
          />
          <Textarea label="Ausführliche Beschreibung" rows={4} {...register('description')} />

          <Select
            label="Hauptkategorie"
            placeholder="Kategorie wählen…"
            options={categories.map((c) => ({ value: c.id, label: `${c.icon} ${c.name}` }))}
            {...register('categoryId')}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Telefon" placeholder="07931 / …" {...register('phone')} />
            <Input label="E-Mail" type="email" {...register('email')} />
          </div>
          <Input label="Website" type="url" placeholder="https://…" {...register('website')} />

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <Input label="Straße und Nr. *" error={errors.street?.message} {...register('street', { required: 'Pflichtfeld' })} />
            </div>
            <Input label="PLZ" {...register('zip')} />
          </div>
          <Input label="Ort" {...register('city')} />

          <div className="grid grid-cols-2 gap-3">
            <Input label="Breite (lat)" type="number" step="0.0001" {...register('lat', { valueAsNumber: true })} hint="z. B. 49.4928" />
            <Input label="Länge (lng)" type="number" step="0.0001" {...register('lng', { valueAsNumber: true })} hint="z. B. 9.7745" />
          </div>

          <Input label="Ladenbild-URL" type="url" placeholder="https://images.unsplash.com/…" {...register('storeImage')} />

          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('clickAndCollect')} />
              Click & Collect
            </label>
            <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
              <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('featured')} />
              Als Featured anzeigen
            </label>
          </div>

          <p className="text-xs text-gray-400">Status wird auf „Ausstehend" gesetzt. Händler muss noch freigeschaltet werden.</p>

          <div className="flex gap-3 pt-2">
            <Button type="submit" variant={saved ? 'secondary' : 'primary'} size="lg" loading={saving} leftIcon={saved ? <CheckCircle2 size={18} /> : <Save size={18} />} className="flex-1">
              {saved ? 'Gespeichert!' : 'Händler anlegen'}
            </Button>
            <Link to="/admin/haendler" className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-300 text-gray-600 font-medium text-sm">
              Abbrechen
            </Link>
          </div>
        </form>
      </div>
    </div>
  )
}

import { useState, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { Save, CheckCircle2, Globe, Phone, Mail, MapPin, Camera, Upload, X } from 'lucide-react'
import { useAuthStore } from '../../store/useAuthStore'
import { useDataStore } from '../../store/useDataStore'
import { Input, Textarea } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { WEEKDAY_LABELS } from '../../utils/formatters'
import type { OpeningDay } from '../../types'

interface ProfileFormData {
  name: string
  shortDescription: string
  description: string
  phone: string
  email: string
  website: string
  street: string
  zip: string
  city: string
  storeImage: string
  clickAndCollect: boolean
}

export function SellerProfilePage() {
  const { currentMerchantId } = useAuthStore()
  const { merchants, updateMerchant } = useDataStore()
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [logoPreview, setLogoPreview] = useState<string>(merchant?.images.logo ?? '')
  const logoInputRef = useRef<HTMLInputElement>(null)

  function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => setLogoPreview(reader.result as string)
    reader.readAsDataURL(file)
  }

  const merchant = merchants.find((m) => m.id === currentMerchantId)

  const { register, handleSubmit } = useForm<ProfileFormData>({
    defaultValues: merchant ? {
      name: merchant.name,
      shortDescription: merchant.shortDescription,
      description: merchant.description,
      phone: merchant.contact.phone ?? '',
      email: merchant.contact.email ?? '',
      website: merchant.contact.website ?? '',
      street: merchant.address.street,
      zip: merchant.address.zip,
      city: merchant.address.city,
      storeImage: merchant.images.store,
      clickAndCollect: merchant.clickAndCollect,
    } : {},
  })

  const [openingHours, setOpeningHours] = useState(
    merchant?.openingHours ?? {}
  )

  function updateDay(day: string, field: keyof OpeningDay, value: string | boolean) {
    setOpeningHours((prev) => ({
      ...prev,
      [day]: { ...(prev as any)[day], [field]: value },
    }))
  }

  async function onSubmit(data: ProfileFormData) {
    if (!merchant) return
    setSaving(true)
    updateMerchant(merchant.id, {
      name: data.name,
      shortDescription: data.shortDescription,
      description: data.description,
      contact: {
        phone: data.phone || undefined,
        email: data.email || undefined,
        website: data.website || undefined,
      },
      address: { ...merchant.address, street: data.street, zip: data.zip, city: data.city },
      images: { ...merchant.images, store: data.storeImage || merchant.images.store, logo: logoPreview || merchant.images.logo },
      clickAndCollect: data.clickAndCollect,
      openingHours: openingHours as typeof merchant.openingHours,
    })
    setSaving(false)
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  if (!merchant) {
    return <p className="text-gray-500">Kein Händlerprofil gefunden.</p>
  }

  const weekdays = Object.keys(WEEKDAY_LABELS) as (keyof typeof WEEKDAY_LABELS)[]

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Mein Händlerprofil</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
        {/* Basic info */}
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 text-lg">Stammdaten</h2>

          {/* Profile / logo image upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center gap-1.5">
              <Camera size={14} className="text-gray-400" />
              Profilbild / Logo
            </label>
            <div className="flex items-center gap-4">
              <div className="relative w-20 h-20 rounded-xl overflow-hidden bg-gray-100 border-2 border-dashed border-gray-300 shrink-0">
                {logoPreview ? (
                  <>
                    <img src={logoPreview} alt="Logo" className="w-full h-full object-cover" />
                    <button
                      type="button"
                      onClick={() => { setLogoPreview(''); if (logoInputRef.current) logoInputRef.current.value = '' }}
                      className="absolute top-1 right-1 bg-black/50 text-white rounded-full p-0.5 hover:bg-black/70 transition-colors"
                    >
                      <X size={10} />
                    </button>
                  </>
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-300">
                    <Camera size={24} />
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <button
                  type="button"
                  onClick={() => logoInputRef.current?.click()}
                  className="flex items-center gap-2 px-3 py-2 text-sm rounded-lg border border-gray-300 text-gray-600 hover:border-primary-400 hover:text-primary-700 transition-colors"
                >
                  <Upload size={14} />
                  Bild hochladen
                </button>
                <p className="text-xs text-gray-400">JPG, PNG oder WebP – max. 2 MB empfohlen</p>
              </div>
              <input
                ref={logoInputRef}
                type="file"
                accept="image/*"
                className="sr-only"
                onChange={handleLogoUpload}
              />
            </div>
          </div>

          <Input label="Geschäftsname" {...register('name')} />
          <Input label="Kurzbeschreibung (1–2 Sätze)" {...register('shortDescription')} />
          <Textarea label="Ausführliche Beschreibung" rows={5} {...register('description')} />
          <Input label="Ladenbild-URL" type="url" placeholder="https://…" {...register('storeImage')} hint="Direkte URL zu einem Foto Ihres Ladens (Außenansicht o. ä.)." />
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="rounded border-gray-300 text-primary-600" {...register('clickAndCollect')} />
            <div>
              <p className="text-sm font-medium text-gray-700">Click &amp; Collect aktivieren</p>
              <p className="text-xs text-gray-400">Kunden können Produkte reservieren und abholen.</p>
            </div>
          </label>
        </div>

        {/* Contact */}
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 text-lg">Kontaktdaten</h2>
          <Input label="Telefon" leftIcon={<Phone size={14} />} placeholder="07931 / 123 45" {...register('phone')} />
          <Input label="E-Mail" type="email" leftIcon={<Mail size={14} />} {...register('email')} />
          <Input label="Website" type="url" leftIcon={<Globe size={14} />} placeholder="https://www.ihr-laden.de" {...register('website')} />
        </div>

        {/* Address */}
        <div className="card p-6 space-y-4">
          <h2 className="font-semibold text-gray-900 text-lg flex items-center gap-2">
            <MapPin size={18} className="text-primary-600" />
            Adresse
          </h2>
          <Input label="Straße und Hausnummer" {...register('street')} />
          <div className="grid grid-cols-3 gap-3">
            <Input label="PLZ" {...register('zip')} />
            <div className="col-span-2"><Input label="Ort" {...register('city')} /></div>
          </div>
        </div>

        {/* Opening hours */}
        <div className="card p-6">
          <h2 className="font-semibold text-gray-900 text-lg mb-4">Öffnungszeiten</h2>
          <div className="space-y-3">
            {weekdays.map((day) => {
              const hours = (openingHours as any)[day] as OpeningDay
              if (!hours) return null
              return (
                <div key={day} className="flex items-center gap-3 flex-wrap">
                  <span className="w-24 text-sm font-medium text-gray-700">{WEEKDAY_LABELS[day]}</span>
                  <label className="flex items-center gap-1.5 text-sm text-gray-600">
                    <input
                      type="checkbox"
                      checked={hours.closed}
                      onChange={(e) => updateDay(day, 'closed', e.target.checked)}
                      className="rounded border-gray-300 text-primary-600"
                    />
                    Geschlossen
                  </label>
                  {!hours.closed && (
                    <>
                      <input
                        type="time"
                        value={hours.open}
                        onChange={(e) => updateDay(day, 'open', e.target.value)}
                        className="input-field w-28 text-sm"
                      />
                      <span className="text-gray-400 text-sm">–</span>
                      <input
                        type="time"
                        value={hours.close}
                        onChange={(e) => updateDay(day, 'close', e.target.value)}
                        className="input-field w-28 text-sm"
                      />
                    </>
                  )}
                </div>
              )
            })}
          </div>
        </div>

        {/* Submit */}
        <Button
          type="submit"
          variant={saved ? 'secondary' : 'primary'}
          size="lg"
          loading={saving}
          leftIcon={saved ? <CheckCircle2 size={18} /> : <Save size={18} />}
        >
          {saved ? 'Gespeichert!' : 'Profil speichern'}
        </Button>
      </form>
    </div>
  )
}

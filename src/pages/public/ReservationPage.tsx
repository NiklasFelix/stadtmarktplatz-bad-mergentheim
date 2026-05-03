import { useState } from 'react'
import { useParams, Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { ArrowLeft, CheckCircle2, Clock, ShieldCheck, ShoppingBag } from 'lucide-react'
import { useDataStore } from '../../store/useDataStore'
import { useAuthStore } from '../../store/useAuthStore'
import { createReservation } from '../../services/api'
import { Input, Textarea } from '../../components/ui/Input'
import { Button } from '../../components/ui/Button'
import { formatPrice } from '../../utils/formatters'
import { AvailabilityBadge } from '../../components/product/AvailabilityBadge'
import { EmptyState } from '../../components/ui/EmptyState'

interface ReservationFormData {
  firstName: string
  lastName: string
  email: string
  phone: string
  pickupDate: string
  pickupTime: string
  quantity: number
  message: string
  privacyAccepted: boolean
}

export function ReservationPage() {
  const { productId } = useParams<{ productId: string }>()
  const [urlParams] = useSearchParams()
  const selectedSize = urlParams.get('groesse') ?? ''
  const navigate = useNavigate()
  const { currentUser } = useAuthStore()
  const products = useDataStore((s) => s.products)
  const merchants = useDataStore((s) => s.merchants)
  const [loading, setLoading] = useState(false)

  const product = products.find((p) => p.id === productId)
  const merchant = product ? merchants.find((m) => m.id === product.merchantId) : null

  const { register, handleSubmit, formState: { errors } } = useForm<ReservationFormData>({
    defaultValues: {
      firstName: currentUser?.name?.split(' ')[0] ?? '',
      lastName: currentUser?.name?.split(' ').slice(1).join(' ') ?? '',
      email: currentUser?.email ?? '',
      quantity: 1,
    },
  })

  if (!product || !merchant) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <EmptyState icon={<ShoppingBag size={40} />} title="Produkt nicht gefunden" />
        <Link to="/produkte" className="btn-outline mt-4 inline-flex items-center gap-2">
          <ArrowLeft size={16} />Zurück
        </Link>
      </div>
    )
  }

  if (!product.reservable || product.availability === 'unavailable') {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center">
        <EmptyState icon={<ShoppingBag size={40} />} title="Reservierung nicht möglich" description="Dieses Produkt kann derzeit nicht reserviert werden." />
        <Link to={`/produkte/${product.slug}`} className="btn-outline mt-4 inline-flex items-center gap-2">
          <ArrowLeft size={16} />Zurück zum Produkt
        </Link>
      </div>
    )
  }

  async function onSubmit(data: ReservationFormData) {
    if (!product || !merchant) return
    setLoading(true)
    try {
      const pickupTime = new Date(`${data.pickupDate}T${data.pickupTime}:00`).toISOString()
      const reservation = await createReservation({
        productId: product.id,
        merchantId: merchant.id,
        customerId: currentUser?.id,
        customer: {
          firstName: data.firstName,
          lastName: data.lastName,
          email: data.email,
          phone: data.phone,
          message: [selectedSize ? `Gewünschte Größe: ${selectedSize}` : '', data.message || ''].filter(Boolean).join('\n') || undefined,
        },
        quantity: data.quantity,
        pickupTime,
        status: 'received',
      })
      navigate(`/reservierung/bestaetigung/${reservation.id}`)
    } finally {
      setLoading(false)
    }
  }

  // Build available pickup times for next 14 days
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const minDate = new Date(today)
  minDate.setDate(today.getDate() + 1)
  const maxDate = new Date(today)
  maxDate.setDate(today.getDate() + 14)

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 text-sm text-gray-500 mb-6">
        <Link to="/produkte" className="hover:text-primary-700">Produkte</Link>
        <span>/</span>
        <Link to={`/produkte/${product.slug}`} className="hover:text-primary-700">{product.name}</Link>
        <span>/</span>
        <span className="text-gray-800">Reservierung</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Form */}
        <div className="lg:col-span-3">
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Produkt reservieren</h1>
          <p className="text-gray-500 text-sm mb-6">Reservieren Sie das Produkt kostenlos und holen Sie es im Laden ab.</p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Name */}
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Vorname *"
                placeholder="Anna"
                error={errors.firstName?.message}
                {...register('firstName', { required: 'Bitte Vornamen eingeben' })}
              />
              <Input
                label="Nachname *"
                placeholder="Weber"
                error={errors.lastName?.message}
                {...register('lastName', { required: 'Bitte Nachnamen eingeben' })}
              />
            </div>

            <Input
              label="E-Mail-Adresse *"
              type="email"
              placeholder="anna.weber@beispiel.de"
              error={errors.email?.message}
              hint="Ihre Bestätigungs-E-Mail wird an diese Adresse gesendet."
              {...register('email', {
                required: 'Bitte E-Mail eingeben',
                pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Ungültige E-Mail-Adresse' },
              })}
            />

            <Input
              label="Telefonnummer *"
              type="tel"
              placeholder="07931 / 123 45 67"
              error={errors.phone?.message}
              hint="Für Rückfragen zur Reservierung."
              {...register('phone', { required: 'Bitte Telefonnummer eingeben' })}
            />

            {/* Pickup time */}
            <div className="grid grid-cols-2 gap-4">
              <Input
                label="Abholdatum *"
                type="date"
                min={minDate.toISOString().split('T')[0]}
                max={maxDate.toISOString().split('T')[0]}
                error={errors.pickupDate?.message}
                {...register('pickupDate', { required: 'Bitte Datum wählen' })}
              />
              <Input
                label="Abholzeit *"
                type="time"
                min="08:00"
                max="18:30"
                error={errors.pickupTime?.message}
                hint="Mo–Fr 09–18 Uhr, Sa 09–14 Uhr"
                {...register('pickupTime', { required: 'Bitte Uhrzeit wählen' })}
              />
            </div>

            <Input
              label="Anzahl"
              type="number"
              min={1}
              max={10}
              {...register('quantity', { valueAsNumber: true, min: 1, max: 10 })}
            />

            <Textarea
              label="Nachricht an den Händler (optional)"
              placeholder="Haben Sie spezielle Wünsche oder Anmerkungen?"
              rows={3}
              {...register('message')}
            />

            {/* Privacy */}
            <div>
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  className="mt-1 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  {...register('privacyAccepted', { required: 'Bitte Datenschutzhinweis bestätigen' })}
                />
                <span className="text-sm text-gray-600 leading-relaxed">
                  Ich habe die{' '}
                  <a href="#" className="text-primary-700 hover:underline">Datenschutzerklärung</a>{' '}
                  gelesen und stimme der Verarbeitung meiner Daten zur Bearbeitung meiner Reservierungsanfrage zu. *
                </span>
              </label>
              {errors.privacyAccepted && (
                <p className="mt-1 text-xs text-red-600">{errors.privacyAccepted.message}</p>
              )}
            </div>

            <p className="text-xs text-gray-400">* Pflichtfelder. Ihre Daten werden ausschließlich zur Bearbeitung der Reservierung genutzt.</p>

            {/* Submit */}
            <div className="flex gap-3 pt-2">
              <Button
                type="submit"
                variant="primary"
                size="lg"
                loading={loading}
                className="flex-1"
                leftIcon={<CheckCircle2 size={18} />}
              >
                Reservierung absenden
              </Button>
              <Link
                to={`/produkte/${product.slug}`}
                className="flex items-center gap-2 px-5 py-3 rounded-xl border border-gray-300 text-gray-600 font-medium text-sm hover:border-gray-400 transition-colors"
              >
                <ArrowLeft size={16} />
                Zurück
              </Link>
            </div>
          </form>
        </div>

        {/* Sidebar: Product summary */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card p-5 sticky top-4">
            <h3 className="font-semibold text-gray-900 mb-4">Ihre Reservierung</h3>
            <div className="aspect-video rounded-xl overflow-hidden bg-gray-100 mb-4">
              {product.images[0] && (
                <img src={product.images[0]} alt={product.name} className="w-full h-full object-cover" />
              )}
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">{product.name}</h4>
            <div className="text-2xl font-bold text-gray-900 mb-2">{formatPrice(product.price)}</div>
            <AvailabilityBadge availability={product.availability} />
            {selectedSize && (
              <div className="mt-2 inline-flex items-center gap-1.5 bg-primary-50 text-primary-700 text-xs font-semibold px-2.5 py-1 rounded-full border border-primary-200">
                Größe: {selectedSize}
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-gray-100 space-y-3">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <div className="w-8 h-8 rounded-lg overflow-hidden bg-gray-100 shrink-0">
                  <img src={merchant.images.store} alt={merchant.name} className="w-full h-full object-cover" />
                </div>
                <div>
                  <p className="font-medium text-gray-800">{merchant.name}</p>
                  <p className="text-xs text-gray-400">{merchant.address.street}</p>
                </div>
              </div>
            </div>

            <div className="mt-4 p-3 bg-blue-50 rounded-xl">
              <p className="text-xs text-blue-800 font-medium flex items-center gap-1.5 mb-1">
                <Clock size={12} />
                Wie geht es weiter?
              </p>
              <ol className="text-xs text-blue-700 space-y-1 list-decimal ml-4">
                <li>Reservierung wird dem Händler übermittelt.</li>
                <li>Händler bestätigt die Verfügbarkeit.</li>
                <li>Sie erhalten eine Bestätigung.</li>
                <li>Abholung zum gewünschten Termin.</li>
              </ol>
            </div>

            <div className="mt-3 flex items-center gap-2 text-xs text-gray-400">
              <ShieldCheck size={12} className="text-green-500" />
              Kostenlose Reservierung, keine Zahlungsdaten
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

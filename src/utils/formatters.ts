import { format, parseISO, isToday, isTomorrow, isYesterday } from 'date-fns'
import { de } from 'date-fns/locale'
import type { ProductPrice, ReservationStatus, ProductAvailability, MerchantStatus } from '../types'

export function formatPrice(price: ProductPrice): string {
  if (price.type === 'fixed') {
    return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(price.value)
  }
  if (price.type === 'range') {
    const fmt = (v: number) => new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(v)
    return `${fmt(price.min)} – ${fmt(price.max)}`
  }
  return 'Preis auf Anfrage'
}

export function formatDate(dateString: string): string {
  const date = parseISO(dateString)
  if (isToday(date)) return `Heute, ${format(date, 'HH:mm')} Uhr`
  if (isTomorrow(date)) return `Morgen, ${format(date, 'HH:mm')} Uhr`
  if (isYesterday(date)) return `Gestern, ${format(date, 'HH:mm')} Uhr`
  return format(date, "dd. MMMM yyyy, HH:mm 'Uhr'", { locale: de })
}

export function formatDateShort(dateString: string): string {
  return format(parseISO(dateString), 'dd.MM.yyyy', { locale: de })
}

export function formatDateLong(dateString: string): string {
  return format(parseISO(dateString), "EEEE, dd. MMMM yyyy", { locale: de })
}

export function formatPickupTime(dateString: string): string {
  return format(parseISO(dateString), "dd. MMMM yyyy 'um' HH:mm 'Uhr'", { locale: de })
}

export const RESERVATION_STATUS_LABELS: Record<ReservationStatus, string> = {
  received:  'Eingegangen',
  confirmed: 'Bestätigt',
  ready:     'Abholbereit',
  completed: 'Abgeschlossen',
  cancelled: 'Storniert',
}

export const RESERVATION_STATUS_COLORS: Record<ReservationStatus, string> = {
  received:  'bg-blue-100 text-blue-800',
  confirmed: 'bg-primary-100 text-primary-800',
  ready:     'bg-accent-100 text-accent-700',
  completed: 'bg-gray-100 text-gray-700',
  cancelled: 'bg-red-100 text-red-700',
}

export const AVAILABILITY_LABELS: Record<ProductAvailability, string> = {
  available:   'Verfügbar',
  on_request:  'Auf Anfrage',
  reserved:    'Reserviert',
  unavailable: 'Nicht verfügbar',
}

export const AVAILABILITY_COLORS: Record<ProductAvailability, string> = {
  available:   'bg-accent-100 text-accent-700',
  on_request:  'bg-amber-100 text-amber-700',
  reserved:    'bg-blue-100 text-blue-700',
  unavailable: 'bg-red-100 text-red-700',
}

export const MERCHANT_STATUS_LABELS: Record<MerchantStatus, string> = {
  active:   'Aktiv',
  pending:  'Ausstehend',
  inactive: 'Inaktiv',
}

export const MERCHANT_STATUS_COLORS: Record<MerchantStatus, string> = {
  active:   'bg-accent-100 text-accent-700',
  pending:  'bg-amber-100 text-amber-700',
  inactive: 'bg-gray-100 text-gray-600',
}

export const WEEKDAY_LABELS = {
  montag:     'Montag',
  dienstag:   'Dienstag',
  mittwoch:   'Mittwoch',
  donnerstag: 'Donnerstag',
  freitag:    'Freitag',
  samstag:    'Samstag',
  sonntag:    'Sonntag',
} as const

export function generateReservationNumber(): string {
  const ts = Date.now().toString(36).toUpperCase()
  const rand = Math.random().toString(36).substring(2, 6).toUpperCase()
  return `BM-${ts}-${rand}`
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/ä/g, 'ae')
    .replace(/ö/g, 'oe')
    .replace(/ü/g, 'ue')
    .replace(/ß/g, 'ss')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

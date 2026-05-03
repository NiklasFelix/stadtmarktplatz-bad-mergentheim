// ============================================================
// CORE TYPES
// Datenmodell für den Stadtmarktplatz Bad Mergentheim
// Mockdaten: src/data/ – für echtes Backend: src/services/api.ts anpassen
// ============================================================

export type UserRole = 'customer' | 'merchant' | 'admin'

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  avatarUrl?: string
  createdAt: string
}

export interface CustomerProfile {
  userId: string
  phone?: string
  favoritesMerchantIds: string[]
  savedProductIds: string[]
}

export interface Category {
  id: string
  name: string
  slug: string
  icon: string
  color: string
  description?: string
}

export interface OpeningDay {
  open: string
  close: string
  closed: boolean
}

export type OpeningHours = {
  montag: OpeningDay
  dienstag: OpeningDay
  mittwoch: OpeningDay
  donnerstag: OpeningDay
  freitag: OpeningDay
  samstag: OpeningDay
  sonntag: OpeningDay
}

export interface MerchantAddress {
  street: string
  zip: string
  city: string
  district?: string
}

export interface MerchantContact {
  phone?: string
  email?: string
  website?: string
}

export interface MerchantImages {
  store: string
  team?: string
  logo?: string
  gallery?: string[]
}

export interface GeoCoordinates {
  lat: number
  lng: number
}

export type MerchantStatus = 'active' | 'pending' | 'inactive'

export interface Merchant {
  id: string
  slug: string
  userId: string
  name: string
  categoryIds: string[]
  shortDescription: string
  description: string
  address: MerchantAddress
  coordinates: GeoCoordinates
  contact: MerchantContact
  openingHours: OpeningHours
  images: MerchantImages
  clickAndCollect: boolean
  featured: boolean
  status: MerchantStatus
  createdAt: string
  updatedAt: string
}

export type ProductAvailability = 'available' | 'on_request' | 'reserved' | 'unavailable'

export type ProductPrice =
  | { type: 'fixed'; value: number }
  | { type: 'range'; min: number; max: number }
  | { type: 'on_request' }

export interface Product {
  id: string
  slug: string
  merchantId: string
  name: string
  description: string
  price: ProductPrice
  categoryIds: string[]
  tags: string[]
  images: string[]
  availability: ProductAvailability
  featured: boolean
  reservable: boolean
  active: boolean
  stock?: number
  sizes?: string[]
  createdAt: string
  updatedAt: string
}

export type ReservationStatus =
  | 'received'
  | 'confirmed'
  | 'ready'
  | 'completed'
  | 'cancelled'

export interface ReservationCustomer {
  firstName: string
  lastName: string
  email: string
  phone: string
  message?: string
}

export interface Reservation {
  id: string
  reservationNumber: string
  productId: string
  merchantId: string
  customerId?: string
  customer: ReservationCustomer
  quantity: number
  pickupTime: string
  status: ReservationStatus
  merchantNotes?: string
  createdAt: string
  updatedAt: string
}

export interface FeaturedContent {
  id: string
  type: 'merchant' | 'product'
  refId: string
  position: number
  active: boolean
  title?: string
  subtitle?: string
}

// ---- Helper / derived types ----

export interface MerchantWithCategory extends Merchant {
  categories: Category[]
}

export interface ProductWithMerchant extends Product {
  merchant: Merchant
  categories: Category[]
}

export interface ReservationWithDetails extends Reservation {
  product: Product
  merchant: Merchant
}

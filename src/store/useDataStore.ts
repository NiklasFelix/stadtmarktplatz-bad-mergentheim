import { create } from 'zustand'
import type { Merchant, Product, Reservation, Category, FeaturedContent, ReservationStatus } from '../types'
import { MERCHANTS } from '../data/merchants'
import { PRODUCTS } from '../data/products'
import { RESERVATIONS } from '../data/reservations'
import { CATEGORIES } from '../data/categories'
import { generateReservationNumber } from '../utils/formatters'

interface DataState {
  merchants: Merchant[]
  products: Product[]
  reservations: Reservation[]
  categories: Category[]
  featuredContent: FeaturedContent[]

  // Merchant actions
  addMerchant: (merchant: Merchant) => void
  updateMerchant: (id: string, updates: Partial<Merchant>) => void
  deleteMerchant: (id: string) => void

  // Product actions
  addProduct: (product: Product) => void
  updateProduct: (id: string, updates: Partial<Product>) => void
  deleteProduct: (id: string) => void

  // Reservation actions
  addReservation: (res: Omit<Reservation, 'id' | 'reservationNumber' | 'createdAt' | 'updatedAt'>) => Reservation
  updateReservationStatus: (id: string, status: ReservationStatus, notes?: string) => void
  updateReservation: (id: string, updates: Partial<Reservation>) => void

  // Featured content
  updateFeaturedContent: (content: FeaturedContent[]) => void
}

export const useDataStore = create<DataState>()((set, get) => ({
  merchants: MERCHANTS,
  products: PRODUCTS,
  reservations: RESERVATIONS,
  categories: CATEGORIES,
  featuredContent: [
    { id: 'fc-1', type: 'merchant', refId: 'merchant-1', position: 1, active: true },
    { id: 'fc-2', type: 'merchant', refId: 'merchant-2', position: 2, active: true },
    { id: 'fc-3', type: 'merchant', refId: 'merchant-3', position: 3, active: true },
    { id: 'fc-4', type: 'merchant', refId: 'merchant-7', position: 4, active: true },
    { id: 'fc-5', type: 'product',  refId: 'prod-9',     position: 1, active: true },
    { id: 'fc-6', type: 'product',  refId: 'prod-1',     position: 2, active: true },
    { id: 'fc-7', type: 'product',  refId: 'prod-15',    position: 3, active: true },
    { id: 'fc-8', type: 'product',  refId: 'prod-22',    position: 4, active: true },
  ],

  addMerchant(merchant) {
    set((s) => ({ merchants: [...s.merchants, merchant] }))
  },

  updateMerchant(id, updates) {
    set((s) => ({
      merchants: s.merchants.map((m) =>
        m.id === id ? { ...m, ...updates, updatedAt: new Date().toISOString() } : m
      ),
    }))
  },

  deleteMerchant(id) {
    set((s) => ({ merchants: s.merchants.filter((m) => m.id !== id) }))
  },

  addProduct(product) {
    set((s) => ({ products: [...s.products, product] }))
  },

  updateProduct(id, updates) {
    set((s) => ({
      products: s.products.map((p) =>
        p.id === id ? { ...p, ...updates, updatedAt: new Date().toISOString() } : p
      ),
    }))
  },

  deleteProduct(id) {
    set((s) => ({ products: s.products.filter((p) => p.id !== id) }))
  },

  addReservation(resData) {
    const now = new Date().toISOString()
    const reservation: Reservation = {
      ...resData,
      id: `res-${Date.now()}`,
      reservationNumber: generateReservationNumber(),
      status: 'received',
      createdAt: now,
      updatedAt: now,
    }
    set((s) => ({ reservations: [reservation, ...s.reservations] }))
    return reservation
  },

  updateReservationStatus(id, status, notes) {
    set((s) => ({
      reservations: s.reservations.map((r) =>
        r.id === id
          ? {
              ...r,
              status,
              merchantNotes: notes ?? r.merchantNotes,
              updatedAt: new Date().toISOString(),
            }
          : r
      ),
    }))
  },

  updateReservation(id, updates) {
    set((s) => ({
      reservations: s.reservations.map((r) =>
        r.id === id ? { ...r, ...updates, updatedAt: new Date().toISOString() } : r
      ),
    }))
  },

  updateFeaturedContent(content) {
    set({ featuredContent: content })
  },
}))

// Selectors
export function useMerchantById(id: string) {
  return useDataStore((s) => s.merchants.find((m) => m.id === id))
}

export function useMerchantBySlug(slug: string) {
  return useDataStore((s) => s.merchants.find((m) => m.slug === slug))
}

export function useProductsByMerchant(merchantId: string) {
  return useDataStore((s) => s.products.filter((p) => p.merchantId === merchantId && p.active))
}

export function useProductBySlug(slug: string) {
  return useDataStore((s) => s.products.find((p) => p.slug === slug))
}

export function useReservationsByMerchant(merchantId: string) {
  return useDataStore((s) => s.reservations.filter((r) => r.merchantId === merchantId))
}

export function useReservationsByCustomer(customerId: string) {
  return useDataStore((s) => s.reservations.filter((r) => r.customerId === customerId))
}

export function useCategoryById(id: string) {
  return useDataStore((s) => s.categories.find((c) => c.id === id))
}

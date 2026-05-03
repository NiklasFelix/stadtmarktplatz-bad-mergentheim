/**
 * Mock Service Layer – Stadtmarktplatz Bad Mergentheim
 *
 * Diese Datei simuliert eine REST-API via In-Memory-State (Zustand Store).
 * Für ein echtes Backend: Ersetze die Implementierungen durch fetch()/axios()-Aufrufe.
 * Alle Funktionen geben Promises zurück, damit der Switch nahtlos ist.
 *
 * Echtes Backend später anschließen:
 *   const BASE = import.meta.env.VITE_API_URL
 *   export async function getMerchants() {
 *     const res = await fetch(`${BASE}/merchants`)
 *     return res.json()
 *   }
 */

import { useDataStore } from '../store/useDataStore'
import type { Merchant, Product, Reservation, ReservationStatus } from '../types'

const delay = (ms = 200) => new Promise((r) => setTimeout(r, ms))

// ---- Merchants ----

export async function getMerchants(): Promise<Merchant[]> {
  await delay()
  return useDataStore.getState().merchants
}

export async function getMerchantBySlug(slug: string): Promise<Merchant | undefined> {
  await delay()
  return useDataStore.getState().merchants.find((m) => m.slug === slug)
}

export async function getMerchantById(id: string): Promise<Merchant | undefined> {
  await delay()
  return useDataStore.getState().merchants.find((m) => m.id === id)
}

export async function updateMerchant(id: string, updates: Partial<Merchant>): Promise<void> {
  await delay()
  useDataStore.getState().updateMerchant(id, updates)
}

export async function createMerchant(merchant: Merchant): Promise<void> {
  await delay()
  useDataStore.getState().addMerchant(merchant)
}

// ---- Products ----

export async function getProducts(): Promise<Product[]> {
  await delay()
  return useDataStore.getState().products.filter((p) => p.active)
}

export async function getProductsByMerchant(merchantId: string): Promise<Product[]> {
  await delay()
  return useDataStore.getState().products.filter((p) => p.merchantId === merchantId)
}

export async function getProductBySlug(slug: string): Promise<Product | undefined> {
  await delay()
  return useDataStore.getState().products.find((p) => p.slug === slug)
}

export async function updateProduct(id: string, updates: Partial<Product>): Promise<void> {
  await delay()
  useDataStore.getState().updateProduct(id, updates)
}

export async function createProduct(product: Product): Promise<void> {
  await delay()
  useDataStore.getState().addProduct(product)
}

export async function deleteProduct(id: string): Promise<void> {
  await delay()
  useDataStore.getState().deleteProduct(id)
}

// ---- Reservations ----

export async function createReservation(
  data: Omit<Reservation, 'id' | 'reservationNumber' | 'createdAt' | 'updatedAt'>
): Promise<Reservation> {
  await delay(400)
  return useDataStore.getState().addReservation(data)
}

export async function getReservationsByMerchant(merchantId: string): Promise<Reservation[]> {
  await delay()
  return useDataStore.getState().reservations.filter((r) => r.merchantId === merchantId)
}

export async function getReservationsByCustomer(customerId: string): Promise<Reservation[]> {
  await delay()
  return useDataStore.getState().reservations.filter((r) => r.customerId === customerId)
}

export async function getReservationById(id: string): Promise<Reservation | undefined> {
  await delay()
  return useDataStore.getState().reservations.find((r) => r.id === id)
}

export async function updateReservationStatus(
  id: string,
  status: ReservationStatus,
  notes?: string
): Promise<void> {
  await delay()
  useDataStore.getState().updateReservationStatus(id, status, notes)
}

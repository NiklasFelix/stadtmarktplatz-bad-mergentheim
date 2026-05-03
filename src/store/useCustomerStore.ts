import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface CustomerState {
  favoriteMerchantIds: string[]
  savedProductIds: string[]
  toggleFavoriteMerchant: (id: string) => void
  toggleSavedProduct: (id: string) => void
  isMerchantFavorite: (id: string) => boolean
  isProductSaved: (id: string) => boolean
}

export const useCustomerStore = create<CustomerState>()(
  persist(
    (set, get) => ({
      favoriteMerchantIds: ['merchant-1', 'merchant-3'],
      savedProductIds: ['prod-9', 'prod-15', 'prod-22'],

      toggleFavoriteMerchant(id) {
        set((s) => ({
          favoriteMerchantIds: s.favoriteMerchantIds.includes(id)
            ? s.favoriteMerchantIds.filter((fid) => fid !== id)
            : [...s.favoriteMerchantIds, id],
        }))
      },

      toggleSavedProduct(id) {
        set((s) => ({
          savedProductIds: s.savedProductIds.includes(id)
            ? s.savedProductIds.filter((sid) => sid !== id)
            : [...s.savedProductIds, id],
        }))
      },

      isMerchantFavorite(id) {
        return get().favoriteMerchantIds.includes(id)
      },

      isProductSaved(id) {
        return get().savedProductIds.includes(id)
      },
    }),
    { name: 'stadtmarkt-customer' }
  )
)

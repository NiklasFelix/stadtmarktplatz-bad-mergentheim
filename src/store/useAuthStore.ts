import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, UserRole } from '../types'
import { DEMO_USERS, DEMO_ACCOUNTS } from '../data/users'

interface AuthState {
  currentUser: User | null
  currentMerchantId: string | null
  isLoggedIn: boolean
  login: (userId: string) => void
  loginAsMerchant: (userId: string, merchantId: string) => void
  logout: () => void
  switchRole: (accountIndex: number) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      currentUser: null,
      currentMerchantId: null,
      isLoggedIn: false,

      login(userId) {
        const user = DEMO_USERS.find((u) => u.id === userId) ?? null
        set({ currentUser: user, isLoggedIn: !!user, currentMerchantId: null })
      },

      loginAsMerchant(userId, merchantId) {
        const user = DEMO_USERS.find((u) => u.id === userId) ?? null
        set({ currentUser: user, isLoggedIn: !!user, currentMerchantId: merchantId })
      },

      logout() {
        set({ currentUser: null, isLoggedIn: false, currentMerchantId: null })
      },

      switchRole(accountIndex) {
        const account = DEMO_ACCOUNTS[accountIndex]
        if (!account) return
        const user = DEMO_USERS.find((u) => u.id === account.userId) ?? null
        set({
          currentUser: user,
          isLoggedIn: !!user,
          currentMerchantId: 'merchantId' in account ? account.merchantId ?? null : null,
        })
      },
    }),
    { name: 'stadtmarkt-auth' }
  )
)

export function useCurrentRole(): UserRole | null {
  return useAuthStore((s) => s.currentUser?.role ?? null)
}

export function useCurrentMerchantId(): string | null {
  return useAuthStore((s) => s.currentMerchantId)
}

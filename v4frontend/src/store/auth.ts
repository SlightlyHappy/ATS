import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User, AuthResponse } from '../types'
import { authService } from '../services/auth'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (credentials: { email: string; password: string }) => Promise<void>
  register: (userData: { email: string; password: string; username: string }) => Promise<void>
  logout: () => Promise<void>
  clearError: () => void
  setUser: (user: User) => void
  updateCredits: (newBalance: number) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials) => {
        set({ isLoading: true, error: null })
        
        try {
          const response: AuthResponse = await authService.login(credentials)
          
          authService.storeTokens(response.access_token, response.refresh_token)
          
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.error || 'Login failed'
          })
          throw error
        }
      },

      register: async (userData) => {
        set({ isLoading: true, error: null })
        
        try {
          await authService.register(userData)
          set({ isLoading: false, error: null })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.error || 'Registration failed'
          })
          throw error
        }
      },

      logout: async () => {
        set({ isLoading: true })
        
        try {
          await authService.logout()
        } catch (error) {
          // Continue with logout even if API call fails
          console.error('Logout error:', error)
        } finally {
          authService.clearTokens()
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null
          })
        }
      },

      clearError: () => {
        set({ error: null })
      },

      setUser: (user: User) => {
        set({ user, isAuthenticated: true })
      },

      updateCredits: (newBalance: number) => {
        const { user } = get()
        if (user) {
          set({ user: { ...user, credits_balance: newBalance } })
        }
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

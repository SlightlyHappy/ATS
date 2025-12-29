import api, { apiCall } from './api'
import type { User, AuthResponse, LoginForm, RegisterForm } from '../types'

export const authService = {
  async login(credentials: LoginForm): Promise<AuthResponse> {
    return apiCall(() => api.post<AuthResponse>('/auth/login', credentials))
  },

  async register(userData: RegisterForm): Promise<{ message: string; user_id: string; credits_balance: number }> {
    return apiCall(() => api.post('/auth/register', userData))
  },

  async logout(): Promise<void> {
    try {
      await apiCall(() => api.post('/auth/logout'))
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    }
  },

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return apiCall(() => api.post<AuthResponse>('/auth/refresh', { refresh_token: refreshToken }))
  },

  getStoredToken(): string | null {
    return localStorage.getItem('access_token')
  },

  getStoredRefreshToken(): string | null {
    return localStorage.getItem('refresh_token')
  },

  storeTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  },

  clearTokens(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  isAuthenticated(): boolean {
    return !!this.getStoredToken()
  }
}

import api, { apiCall } from './api'
import type { CreditInfo } from '../types'

export const creditService = {
  async getUserCredits(userId: string): Promise<CreditInfo> {
    return apiCall(() => api.get(`/queue/user/${userId}/credits`))
  },

  async addCredits(userId: string, amount: number, description: string): Promise<{ message: string; new_balance: number }> {
    return apiCall(() => api.post(`/queue/user/${userId}/credits/add`, {
      amount,
      description
    }))
  }
}

import { create } from 'zustand'
import { creditsAPI, subscriptionsAPI, plansAPI } from '../services/api'

const useCreditStore = create((set, get) => ({
  balance: 0,
  totalGranted: 0,
  totalUsed: 0,
  usagePercentage: 0,
  subscription: null,
  plans: [],
  isLoading: false,
  error: null,

  fetchBalance: async () => {
    set({ isLoading: true })
    try {
      const response = await creditsAPI.balance()
      set({ 
        balance: response.data.current_balance,
        totalGranted: response.data.total_granted,
        totalUsed: response.data.total_used,
        usagePercentage: response.data.usage_percentage,
        isLoading: false 
      })
    } catch (error) {
      set({ error: error.message, isLoading: false })
    }
  },

  fetchSubscription: async () => {
    set({ isLoading: true })
    try {
      const response = await subscriptionsAPI.current()
      set({ subscription: response.data, isLoading: false })
    } catch (error) {
      set({ subscription: null, isLoading: false })
    }
  },

  fetchPlans: async () => {
    try {
      const response = await plansAPI.list()
      set({ plans: response.data })
    } catch (error) {
      set({ error: error.message })
    }
  },

  subscribe: async (planSlug) => {
    set({ isLoading: true, error: null })
    try {
      const response = await subscriptionsAPI.subscribe(planSlug)
      set({ subscription: response.data, isLoading: false })
      get().fetchBalance()
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Subscription failed'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  changePlan: async (planSlug) => {
    set({ isLoading: true, error: null })
    try {
      const response = await subscriptionsAPI.change(planSlug)
      set({ subscription: response.data, isLoading: false })
      get().fetchBalance()
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail || 'Plan change failed'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  cancelSubscription: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await subscriptionsAPI.cancel()
      set({ subscription: null, isLoading: false })
      get().fetchBalance()
      return { success: true, message: response.data.message }
    } catch (error) {
      const message = error.response?.data?.detail || 'Cancellation failed'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  checkCredits: async (amount) => {
    try {
      const response = await creditsAPI.check(amount)
      return response.data
    } catch (error) {
      return { sufficient: false, balance: 0, required: amount }
    }
  },

  deductCredits: (amount) => {
    set(state => ({
      balance: Math.max(0, state.balance - amount),
      totalUsed: state.totalUsed + amount,
    }))
  },

  clearError: () => set({ error: null }),
}))

export default useCreditStore

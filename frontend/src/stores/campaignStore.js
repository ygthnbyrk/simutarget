import { create } from 'zustand'
import api from '../services/api'

export const useCampaignStore = create((set, get) => ({
  campaigns: [],
  currentCampaign: null,
  testResults: null,
  isLoading: false,
  isTestRunning: false,
  error: null,

  createCampaign: async (name, content, region) => {
    set({ isLoading: true, error: null })
    try {
      const response = await api.post('/api/v1/campaigns/', { name, content, region })
      const campaign = response.data
      set((state) => ({
        campaigns: [...state.campaigns, campaign],
        currentCampaign: campaign,
        isLoading: false,
      }))
      return { success: true, campaign }
    } catch (error) {
      const message = error.response?.data?.detail || 'Kampanya oluşturulamadı'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  runTest: async (campaignId, personaCount, filters = {}) => {
    set({ isTestRunning: true, error: null, testResults: null })
    try {
      const response = await api.post(`/api/v1/campaigns/${campaignId}/test`, {
        persona_count: personaCount,
        filters,
      })
      set({ testResults: response.data, isTestRunning: false })
      return { success: true, results: response.data }
    } catch (error) {
      const message = error.response?.data?.detail || 'Test başarısız'
      set({ error: message, isTestRunning: false })
      return { success: false, error: message }
    }
  },

  runABCompare: async (campaignId, optionA, optionB, personaCount, filters = {}) => {
    set({ isTestRunning: true, error: null, testResults: null })
    try {
      const response = await api.post(`/api/v1/campaigns/${campaignId}/ab-compare`, {
        option_a: optionA,
        option_b: optionB,
        persona_count: personaCount,
        filters,
      })
      set({ testResults: response.data, isTestRunning: false })
      return { success: true, results: response.data }
    } catch (error) {
      const message = error.response?.data?.detail || 'A/B test başarısız'
      set({ error: message, isTestRunning: false })
      return { success: false, error: message }
    }
  },

  fetchCampaigns: async () => {
    set({ isLoading: true })
    try {
      const response = await api.get('/api/v1/campaigns/')
      set({ campaigns: response.data, isLoading: false })
    } catch (error) {
      set({ error: error.message, isLoading: false })
    }
  },

  clearResults: () => set({ testResults: null, error: null }),

  clear: () => set({
    campaigns: [],
    currentCampaign: null,
    testResults: null,
    error: null,
  }),
}))

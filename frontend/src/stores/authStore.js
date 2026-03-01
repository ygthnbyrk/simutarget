// frontend/src/stores/authStore.js
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../services/api'

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Email/Password ile giriş
      login: async (email, password) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/login', { email, password })
          const { access_token, user } = response.data
          
          localStorage.setItem('token', access_token)
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          set({ user, token: access_token, isAuthenticated: true, isLoading: false })
          return { success: true }
        } catch (error) {
          const message = error.response?.data?.detail || 'Login failed'
          set({ error: message, isLoading: false })
          return { success: false, error: message }
        }
      },

      // Google OAuth ile giriş
      loginWithGoogle: async (credential) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/google', { credential })
          const { access_token, user } = response.data
          
          localStorage.setItem('token', access_token)
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          set({ user, token: access_token, isAuthenticated: true, isLoading: false })
          return { success: true }
        } catch (error) {
          const message = error.response?.data?.detail || 'Google login failed'
          set({ error: message, isLoading: false })
          return { success: false, error: message }
        }
      },

      // Email ile kayıt
      register: async (email, password, name) => {
        set({ isLoading: true, error: null })
        try {
          const response = await api.post('/auth/register', { email, password, name })
          const { access_token, user } = response.data
          
          localStorage.setItem('token', access_token)
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          set({ user, token: access_token, isAuthenticated: true, isLoading: false })
          return { success: true }
        } catch (error) {
          const message = error.response?.data?.detail || 'Registration failed'
          set({ error: message, isLoading: false })
          return { success: false, error: message }
        }
      },

      // Çıkış
      logout: () => {
        localStorage.removeItem('token')
        delete api.defaults.headers.common['Authorization']
        set({ user: null, token: null, isAuthenticated: false })
      },

      // Profil bilgilerini getir
      fetchProfile: async () => {
        const token = get().token || localStorage.getItem('token')
        if (!token) return
        
        try {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          const response = await api.get('/auth/profile')
          set({ user: response.data, isAuthenticated: true })
        } catch (error) {
          get().logout()
        }
      },

      // Token'ı yükle (sayfa yenilemelerinde)
      loadToken: () => {
        const token = localStorage.getItem('token')
        if (token) {
          api.defaults.headers.common['Authorization'] = `Bearer ${token}`
          set({ token, isAuthenticated: true })
        }
      },

      // Hata temizle
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token }),
    }
  )
)

export default useAuthStore

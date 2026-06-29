import axios from 'axios'

// Production'da VITE_API_URL env variable kullan, yoksa relative path (dev proxy)
const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/v1` 
  : '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  profile: () => api.get('/auth/profile'),

  // Şifre sıfırlama (Oturum #8.3)
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', {
    token,
    new_password: newPassword,
  }),
}

export const plansAPI = {
  list: () => api.get('/plans'),
}

// ============================================
// SUBSCRIPTIONS API
// (subscribe/change/cancel kaldırıldı — Oturum #8.2)
// Yeni akış: lemonsqueezyAPI.checkout / .portal
// ============================================
export const subscriptionsAPI = {
  current: () => api.get('/subscriptions/current'),
}

// ============================================
// LEMON SQUEEZY API (Oturum #8.2)
// ============================================
export const lemonsqueezyAPI = {
  /**
   * Backend'den LS checkout URL al.
   * @param {string} planSlug - 'disposable' | 'starter' | 'pro' | 'business'
   * @param {string} redirectUrl - Ödeme sonrası dönülecek URL
   * @param {string} billingPeriod - 'monthly' | 'yearly' (varsayılan monthly)
   * @returns {Promise<{checkout_url, checkout_id, plan_slug, plan_name, expires_at}>}
   */
  checkout: (planSlug, redirectUrl, billingPeriod = 'monthly') => api.post('/lemonsqueezy/checkout', {
    plan_slug: planSlug,
    redirect_url: redirectUrl,
    billing_period: billingPeriod,
  }),

  /**
   * LS Customer Portal URL al — kullanıcı orada subscription'ını yönetir
   * (cancel, kart günceller, fatura indirir).
   */
  portal: () => api.post('/lemonsqueezy/portal'),
}

export const creditsAPI = {
  balance: () => api.get('/credits/balance'),
  check: (amount) => api.get(`/credits/check/${amount}`),
}

export const featuresAPI = {
  checkFilter: (filterName) => api.get(`/features/filter/${filterName}`),
  checkTestType: (testType) => api.get(`/features/test/${testType}`),
}

export const campaignsAPI = {
  create: (data) => api.post('/campaigns/', data),
  list: () => api.get('/campaigns/'),
  get: (id) => api.get(`/campaigns/${id}`),
  results: (id) => api.get(`/campaigns/${id}/results`),
  delete: (id) => api.delete(`/campaigns/${id}`),
  test: (id, data) => api.post(`/campaigns/${id}/test`, data),
  abCompare: (id, data) => api.post(`/campaigns/${id}/compare`, data),
  multiCompare: (id, data) => api.post(`/campaigns/${id}/multi-compare`, data),

  // Görsel upload/delete
  uploadImage: (campaignId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/campaigns/${campaignId}/upload-image`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteImage: (campaignId) => api.delete(`/campaigns/${campaignId}/image`),
}

// ============================================
// ADMIN API (sadece role=admin user için, backend 403 ile korunur)
// ============================================

export const adminAPI = {
  stats: () => api.get('/admin/stats'),
  users: (params) => api.get('/admin/users', { params }),
  subscriptions: (params) => api.get('/admin/subscriptions', { params }),
  campaigns: (params) => api.get('/admin/campaigns', { params }),
  recentActivity: (limit = 20) => api.get('/admin/recent-activity', { params: { limit } }),
}

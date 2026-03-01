import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
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
}

export const plansAPI = {
  list: () => api.get('/plans'),
}

export const subscriptionsAPI = {
  current: () => api.get('/subscriptions/current'),
  subscribe: (planSlug) => api.post('/subscriptions/subscribe', { plan_slug: planSlug }),
  change: (planSlug) => api.post('/subscriptions/change', { plan_slug: planSlug }),
  cancel: () => api.post('/subscriptions/cancel'),
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
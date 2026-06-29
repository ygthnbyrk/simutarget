import { create } from 'zustand'
import { creditsAPI, subscriptionsAPI, plansAPI, lemonsqueezyAPI } from '../services/api'

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
      // 404 normal — kullanıcının subscription'ı yok
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

  // ============================================
  // LEMON SQUEEZY CHECKOUT FLOW (Oturum #8.2)
  // ============================================

  /**
   * Yeni plana abone ol — LS checkout overlay açar.
   *
   * Akış:
   *   1. Backend'den checkout URL al (POST /lemonsqueezy/checkout)
   *   2. window.LemonSqueezy.Url.Open(url) ile overlay aç
   *   3. Kullanıcı kart girer, öder
   *   4. LS webhook → backend DB'yi günceller
   *   5. Kullanıcı redirectUrl'e döner (?checkout=success)
   *   6. Profile/Dashboard auto-refresh ile yeni subscription görünür
   *
   * @param {string} planSlug
   * @param {string} billingPeriod - 'monthly' | 'yearly' (varsayılan monthly)
   * @returns {Promise<{success, checkoutUrl?, error?}>}
   */
  subscribe: async (planSlug, billingPeriod = 'monthly') => {
    set({ isLoading: true, error: null })
    try {
      const redirectUrl = `${window.location.origin}/dashboard?checkout=success`
      const response = await lemonsqueezyAPI.checkout(planSlug, redirectUrl, billingPeriod)
      const checkoutUrl = response.data.checkout_url

      // Lemon.js overlay aç (index.html'de script yüklü, window.LemonSqueezy global)
      if (typeof window !== 'undefined' && window.LemonSqueezy && window.LemonSqueezy.Url) {
        window.LemonSqueezy.Url.Open(checkoutUrl)
      } else {
        // Fallback: Lemon.js yüklenmemişse, full page redirect
        console.warn('Lemon.js yüklenmemiş, full page redirect kullanılıyor')
        window.location.href = checkoutUrl
      }

      set({ isLoading: false })
      return { success: true, checkoutUrl }
    } catch (error) {
      const message = error.response?.data?.detail || 'Checkout açılamadı. Lütfen tekrar deneyin.'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  /**
   * Plan değişikliği — şu an için subscribe ile aynı akış.
   *
   * UX notu: Kullanıcının zaten aktif aboneliği varsa, Profile.jsx önce
   * uyarı modal'ı gösterir ("Önce mevcut aboneliği iptal edin"). Burada
   * yalnızca yeni plan için checkout açılır.
   */
  changePlan: async (planSlug, billingPeriod = 'monthly') => {
    return get().subscribe(planSlug, billingPeriod)
  },

  /**
   * Customer Portal aç (cancel/kart güncelleme/fatura için).
   * Yeni sekmede LS portal'ı açar.
   */
  openCustomerPortal: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await lemonsqueezyAPI.portal()
      const portalUrl = response.data.portal_url
      window.open(portalUrl, '_blank', 'noopener,noreferrer')
      set({ isLoading: false })
      return { success: true }
    } catch (error) {
      const message = error.response?.data?.detail
        || 'Portal açılamadı. Henüz aktif aboneliğiniz olmayabilir.'
      set({ error: message, isLoading: false })
      return { success: false, error: message }
    }
  },

  /**
   * Cancel subscription — kullanıcıyı LS customer portal'a yönlendirir.
   * (Eski DB-only cancel kaldırıldı, çünkü gerçek ödeme provider'da kesinti
   * devam ederdi.)
   */
  cancelSubscription: async () => {
    return get().openCustomerPortal()
  },

  // ============================================
  // CREDIT HELPERS
  // ============================================

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

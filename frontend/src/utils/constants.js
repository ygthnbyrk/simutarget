// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Regions
export const REGIONS = [
  { code: 'TR', name: 'Turkey', flag: '🇹🇷' },
  { code: 'US', name: 'USA', flag: '🇺🇸' },
  { code: 'EU', name: 'Europe', flag: '🇪🇺' },
  { code: 'MENA', name: 'MENA', flag: '🌍' },
]

// Plan slugs
export const PLAN_SLUGS = {
  BASIC: 'basic',
  PRO: 'pro',
  BUSINESS: 'business',
  ENTERPRISE: 'enterprise',
}

// Colors (matching CSS variables)
export const COLORS = {
  primary: '#06B6D4',
  secondary: '#8B5CF6',
  success: '#10B981',
  danger: '#EF4444',
  warning: '#F59E0B',
}

// Chart colors
export const CHART_COLORS = {
  positive: '#10B981',
  negative: '#EF4444',
  neutral: '#6B7280',
}

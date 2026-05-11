// frontend/src/pages/AdminDashboard.jsx
import { useEffect, useState, useMemo, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, Area, AreaChart,
} from 'recharts'
import {
  Users, UserPlus, DollarSign, TrendingUp, CreditCard, AlertTriangle,
  Rocket, Activity, RefreshCw, Search, LogOut, ChevronLeft, ChevronRight,
  XCircle, CheckCircle2, Clock, PauseCircle, Filter, ArrowLeft,
  BadgeDollarSign, Sparkles, BarChart3, PieChart,
} from 'lucide-react'
import { adminAPI } from '../services/api'
import useAuthStore from '../stores/authStore'


// ============================================
// FORMATTING & TRANSLATION
// ============================================

const fmtNum = (n) => new Intl.NumberFormat('tr-TR').format(n ?? 0)
const fmtUSD = (n) => `$${(n ?? 0).toFixed(2)}`
const fmtPct = (n) => `%${(n ?? 0).toFixed(1)}`

const fmtDate = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleDateString('tr-TR', {
    day: '2-digit', month: 'short', year: 'numeric',
  })
}

const fmtDateTime = (iso) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('tr-TR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const fmtShortDate = (iso) => {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })
}

// Status enum → Türkçe etiket + renk
const STATUS_META = {
  active:     { label: 'Aktif',          cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  cancelled:  { label: 'İptal',          cls: 'bg-rose-50 text-rose-700 border-rose-200' },
  past_due:   { label: 'Gecikmeli',      cls: 'bg-amber-50 text-amber-700 border-amber-200' },
  paused:     { label: 'Duraklatıldı',   cls: 'bg-slate-100 text-slate-700 border-slate-200' },
  completed:  { label: 'Tamamlandı',     cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
  running:    { label: 'Çalışıyor',      cls: 'bg-blue-50 text-blue-700 border-blue-200' },
  pending:    { label: 'Beklemede',      cls: 'bg-slate-100 text-slate-700 border-slate-200' },
  failed:     { label: 'Başarısız',      cls: 'bg-rose-50 text-rose-700 border-rose-200' },
}


// ============================================
// SMALL COMPONENTS
// ============================================

function StatCard({ icon: Icon, label, value, sublabel, trend, accent = 'indigo' }) {
  const accents = {
    indigo:  { bar: 'bg-indigo-500',  icon: 'bg-indigo-50 text-indigo-600',  ring: 'ring-indigo-100' },
    emerald: { bar: 'bg-emerald-500', icon: 'bg-emerald-50 text-emerald-600', ring: 'ring-emerald-100' },
    amber:   { bar: 'bg-amber-500',   icon: 'bg-amber-50 text-amber-600',    ring: 'ring-amber-100' },
    rose:    { bar: 'bg-rose-500',    icon: 'bg-rose-50 text-rose-600',      ring: 'ring-rose-100' },
    blue:    { bar: 'bg-blue-500',    icon: 'bg-blue-50 text-blue-600',      ring: 'ring-blue-100' },
    purple:  { bar: 'bg-purple-500',  icon: 'bg-purple-50 text-purple-600',  ring: 'ring-purple-100' },
    slate:   { bar: 'bg-slate-400',   icon: 'bg-slate-50 text-slate-600',    ring: 'ring-slate-100' },
  }
  const a = accents[accent] || accents.indigo
  return (
    <div className="relative bg-white rounded-xl border border-slate-200/70 shadow-sm hover:shadow-md transition-shadow overflow-hidden group">
      <div className={`absolute top-0 left-0 h-1 w-full ${a.bar} opacity-90`} />
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2 rounded-lg ${a.icon} ring-4 ${a.ring}`}>
            {Icon && <Icon size={18} strokeWidth={2.2} />}
          </div>
          {trend && (
            <span className="text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full">
              {trend}
            </span>
          )}
        </div>
        <div className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-1">{label}</div>
        <div className="text-2xl font-bold text-slate-900 tabular-nums">{value}</div>
        {sublabel && <div className="text-xs text-slate-500 mt-1">{sublabel}</div>}
      </div>
    </div>
  )
}

function FunnelBar({ label, count, percent, max, color = 'indigo' }) {
  const width = max > 0 ? (count / max) * 100 : 0
  const colors = {
    indigo:  'from-indigo-500 to-indigo-400',
    emerald: 'from-emerald-500 to-emerald-400',
    amber:   'from-amber-500 to-amber-400',
  }
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex justify-between items-baseline mb-1.5">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <div className="text-sm">
          <span className="font-semibold text-slate-900">{fmtNum(count)}</span>
          <span className="text-slate-400 ml-1.5">({fmtPct(percent)})</span>
        </div>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full bg-gradient-to-r ${colors[color]} transition-all duration-500`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, cls: 'bg-slate-100 text-slate-700 border-slate-200' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${meta.cls}`}>
      {meta.label}
    </span>
  )
}

function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200 bg-slate-50">
      <div className="text-sm text-slate-600">
        Toplam <strong className="text-slate-900">{fmtNum(total)}</strong> kayıt ·
        Sayfa <strong className="text-slate-900">{page}</strong> / {totalPages}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <button
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-slate-300 bg-white text-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition"
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, accent = 'slate' }) {
  const colors = {
    slate:   'text-slate-700',
    indigo:  'text-indigo-700',
    emerald: 'text-emerald-700',
  }
  return (
    <h2 className={`flex items-center gap-2 text-sm font-bold uppercase tracking-wider mb-3 ${colors[accent]}`}>
      {Icon && <Icon size={14} />}
      {title}
    </h2>
  )
}


// ============================================
// MAIN DASHBOARD
// ============================================

export default function AdminDashboard() {
  const { user, logout } = useAuthStore()

  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  const [activeTab, setActiveTab] = useState('users')

  const [users, setUsers] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [usersLoading, setUsersLoading] = useState(false)
  const [userSearch, setUserSearch] = useState('')

  const [subs, setSubs] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [subsLoading, setSubsLoading] = useState(false)
  const [subsStatus, setSubsStatus] = useState('')

  const [campaigns, setCampaigns] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [campaignsLoading, setCampaignsLoading] = useState(false)

  const [activity, setActivity] = useState([])
  const [activityLoading, setActivityLoading] = useState(false)
  const [activityFilter, setActivityFilter] = useState('all')

  // ---- LOADERS ----

  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    setStatsError(null)
    try {
      const res = await adminAPI.stats()
      setStats(res.data)
    } catch (e) {
      setStatsError(e.response?.data?.detail || 'İstatistikler yüklenemedi')
    } finally {
      setStatsLoading(false)
    }
  }, [])

  const loadUsers = useCallback(async (page = 1, search = '') => {
    setUsersLoading(true)
    try {
      const res = await adminAPI.users({ page, page_size: 25, ...(search ? { search } : {}) })
      setUsers(res.data)
    } catch (e) { console.error('Users load error', e) } finally { setUsersLoading(false) }
  }, [])

  const loadSubs = useCallback(async (page = 1, status = '') => {
    setSubsLoading(true)
    try {
      const res = await adminAPI.subscriptions({ page, page_size: 25, ...(status ? { status } : {}) })
      setSubs(res.data)
    } catch (e) { console.error('Subs load error', e) } finally { setSubsLoading(false) }
  }, [])

  const loadCampaigns = useCallback(async (page = 1) => {
    setCampaignsLoading(true)
    try {
      const res = await adminAPI.campaigns({ page, page_size: 25 })
      setCampaigns(res.data)
    } catch (e) { console.error('Campaigns load error', e) } finally { setCampaignsLoading(false) }
  }, [])

  const loadActivity = useCallback(async () => {
    setActivityLoading(true)
    try {
      const res = await adminAPI.recentActivity(50)
      setActivity(res.data.items || [])
    } catch (e) { console.error('Activity load error', e) } finally { setActivityLoading(false) }
  }, [])

  useEffect(() => {
    loadStats()
    loadUsers(1, '')
  }, [loadStats, loadUsers])

  useEffect(() => {
    if (activeTab === 'subscriptions' && subs.items.length === 0) loadSubs(1, '')
    if (activeTab === 'campaigns' && campaigns.items.length === 0) loadCampaigns(1)
    if (activeTab === 'recent' && activity.length === 0) loadActivity()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  // Activity filtreleme + grouplama
  const filteredActivity = useMemo(() => {
    if (activityFilter === 'all') return activity
    const filterMap = {
      users: ['user_signup'],
      payments: ['subscription_created'],
      cancellations: ['subscription_cancelled'],
      campaigns: ['campaign_run'],
    }
    const types = filterMap[activityFilter] || []
    return activity.filter((a) => types.includes(a.type))
  }, [activity, activityFilter])

  const groupedActivity = useMemo(() => {
    const now = new Date()
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
    const yesterday = new Date(today); yesterday.setDate(yesterday.getDate() - 1)
    const weekAgo = new Date(today); weekAgo.setDate(weekAgo.getDate() - 7)

    const groups = { Bugün: [], Dün: [], 'Bu Hafta': [], 'Daha Önce': [] }
    filteredActivity.forEach((item) => {
      const ts = new Date(item.timestamp)
      if (ts >= today) groups['Bugün'].push(item)
      else if (ts >= yesterday) groups['Dün'].push(item)
      else if (ts >= weekAgo) groups['Bu Hafta'].push(item)
      else groups['Daha Önce'].push(item)
    })
    return groups
  }, [filteredActivity])


  // ---- RENDER ----

  return (
    <div className="min-h-screen bg-slate-50">
      {/* HEADER */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center text-white font-bold shadow-sm">
              S
            </div>
            <div>
              <h1 className="text-base font-bold text-slate-900 leading-tight">SimuTarget Admin</h1>
              <div className="text-xs text-slate-500 leading-tight">İç Yönetim Paneli</div>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-slate-900 transition"
            >
              <ArrowLeft size={15} /> Dashboard
            </Link>
            <div className="h-6 w-px bg-slate-200" />
            <span className="text-sm text-slate-600 hidden md:inline">{user?.email}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm text-rose-600 hover:text-rose-700 transition"
            >
              <LogOut size={15} /> Çıkış
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Reload */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Genel Bakış</h2>
            <p className="text-sm text-slate-500 mt-0.5">Tüm metrikler gerçek zamanlı</p>
          </div>
          <button
            onClick={loadStats}
            disabled={statsLoading}
            className="flex items-center gap-1.5 text-sm px-3 py-2 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 transition shadow-sm"
          >
            <RefreshCw size={14} className={statsLoading ? 'animate-spin' : ''} />
            {statsLoading ? 'Yükleniyor…' : 'Yenile'}
          </button>
        </div>

        {statsError && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-lg p-3 text-sm flex items-center gap-2">
            <AlertTriangle size={16} /> {statsError}
          </div>
        )}

        {stats && (
          <>
            {/* KULLANICILAR */}
            <section>
              <SectionHeader icon={Users} title="Kullanıcılar" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  icon={Users}
                  label="Toplam Üye"
                  value={fmtNum(stats.cards.total_users)}
                  accent="indigo"
                />
                <StatCard
                  icon={UserPlus}
                  label="Bugün"
                  value={fmtNum(stats.cards.users_today)}
                  sublabel={stats.cards.users_today > 0 ? 'Yeni kayıt' : 'Henüz yeni üye yok'}
                  accent="emerald"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Son 7 Gün"
                  value={fmtNum(stats.cards.users_7d)}
                  accent="indigo"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Son 30 Gün"
                  value={fmtNum(stats.cards.users_30d)}
                  accent="indigo"
                />
              </div>
            </section>

            {/* GELİR */}
            <section>
              <SectionHeader icon={BadgeDollarSign} title="Gelir & Abonelikler" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  icon={DollarSign}
                  label="Aylık Gelir"
                  value={fmtUSD(stats.cards.mrr_usd)}
                  sublabel="MRR"
                  accent="emerald"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Yıllık Gelir"
                  value={fmtUSD(stats.cards.arr_usd)}
                  sublabel="ARR (MRR × 12)"
                  accent="emerald"
                />
                <StatCard
                  icon={CreditCard}
                  label="Aktif Abonelik"
                  value={fmtNum(stats.cards.active_subscriptions)}
                  accent="blue"
                />
                <StatCard
                  icon={AlertTriangle}
                  label="Ödeme Bekleyen"
                  value={fmtNum(stats.cards.past_due_subscriptions)}
                  sublabel={stats.cards.past_due_subscriptions > 0 ? 'Müdahale gerekli' : 'Hepsi güncel'}
                  accent={stats.cards.past_due_subscriptions > 0 ? 'amber' : 'slate'}
                />
              </div>
            </section>

            {/* AKTİVİTE */}
            <section>
              <SectionHeader icon={Activity} title="Aktivite" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  icon={Rocket}
                  label="Toplam Kampanya"
                  value={fmtNum(stats.cards.total_campaigns)}
                  accent="purple"
                />
                <StatCard
                  icon={Sparkles}
                  label="Bugün"
                  value={fmtNum(stats.cards.campaigns_today)}
                  accent="purple"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Son 7 Gün"
                  value={fmtNum(stats.cards.campaigns_7d)}
                  accent="purple"
                />
                <StatCard
                  icon={XCircle}
                  label="İptal Abonelik"
                  value={fmtNum(stats.cards.cancelled_subscriptions)}
                  sublabel="Tüm zamanlar"
                  accent="rose"
                />
              </div>
            </section>

            {/* CHARTS */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <BarChart3 size={15} className="text-indigo-500" />
                    Günlük Yeni Üye
                  </h3>
                  <span className="text-xs text-slate-500">Son 30 gün</span>
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={stats.daily_signups} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g_signups" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={fmtShortDate}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                      interval={4}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [v, 'Yeni üye']}
                      contentStyle={{
                        borderRadius: 8, border: '1px solid #e2e8f0',
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#6366f1"
                      strokeWidth={2.5}
                      fill="url(#g_signups)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <DollarSign size={15} className="text-emerald-500" />
                    Günlük Gelir
                  </h3>
                  <span className="text-xs text-slate-500">Son 30 gün</span>
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={stats.daily_revenue} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g_revenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#10b981" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="date"
                      tickFormatter={fmtShortDate}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                      interval={4}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(v) => `$${v}`}
                    />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [fmtUSD(v), 'Gelir']}
                      contentStyle={{
                        borderRadius: 8, border: '1px solid #e2e8f0',
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', fontSize: 12,
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={2.5}
                      fill="url(#g_revenue)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* PLAN BREAKDOWN + FUNNEL */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <PieChart size={15} className="text-purple-500" />
                    Plan Bazında Aktif Abonelikler
                  </h3>
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={stats.plan_breakdown} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                    <XAxis
                      dataKey="plan_name"
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={{ stroke: '#e2e8f0' }}
                    />
                    <YAxis
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      tickLine={false}
                      axisLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip
                      formatter={(v, key) => {
                        if (key === 'active_count') return [v, 'Aktif Sub']
                        if (key === 'monthly_revenue_usd') return [fmtUSD(v), 'Aylık Gelir']
                        return [v, key]
                      }}
                      contentStyle={{
                        borderRadius: 8, border: '1px solid #e2e8f0',
                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)', fontSize: 12,
                      }}
                    />
                    <Bar dataKey="active_count" fill="#6366f1" radius={[6, 6, 0, 0]} name="Aktif" />
                    <Bar dataKey="monthly_revenue_usd" fill="#10b981" radius={[6, 6, 0, 0]} name="Gelir" />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-500 justify-center">
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-sm bg-indigo-500" /> Aktif Abonelik
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="w-3 h-3 rounded-sm bg-emerald-500" /> Aylık Gelir ($)
                  </span>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200/70 shadow-sm p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                    <TrendingUp size={15} className="text-amber-500" />
                    Dönüşüm Hunisi
                  </h3>
                </div>
                {stats.conversion_funnel && (() => {
                  const f = stats.conversion_funnel
                  const max = f.signed_up || 1
                  return (
                    <>
                      <FunnelBar
                        label="Kayıt oldu"
                        count={f.signed_up}
                        percent={100}
                        max={max}
                        color="indigo"
                      />
                      <FunnelBar
                        label="İlk kampanyayı çalıştırdı"
                        count={f.ran_first_campaign}
                        percent={f.signup_to_activation_pct}
                        max={max}
                        color="amber"
                      />
                      <FunnelBar
                        label="Ücretli aboneliği var"
                        count={f.has_paid_subscription}
                        percent={f.overall_conversion_pct}
                        max={max}
                        color="emerald"
                      />
                      <div className="mt-5 pt-4 border-t border-slate-100 grid grid-cols-3 gap-3 text-center">
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Kayıt → Aktivasyon</div>
                          <div className="text-sm font-semibold text-slate-900">
                            {fmtPct(f.signup_to_activation_pct)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Aktivasyon → Ödeme</div>
                          <div className="text-sm font-semibold text-slate-900">
                            {fmtPct(f.activation_to_paid_pct)}
                          </div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Toplam Dönüşüm</div>
                          <div className="text-sm font-bold text-indigo-600">
                            {fmtPct(f.overall_conversion_pct)}
                          </div>
                        </div>
                      </div>
                    </>
                  )
                })()}
              </div>
            </section>
          </>
        )}

        {/* TABS */}
        <section className="bg-white rounded-xl border border-slate-200/70 shadow-sm overflow-hidden">
          {/* Tab navigation - defansif CSS ile (image 2'deki birleşik görüntü için) */}
          <div
            className="flex border-b border-slate-200 bg-slate-50/50"
            style={{ display: 'flex', gap: 0 }}
          >
            {[
              ['users',         'Üyeler',          Users],
              ['subscriptions', 'Abonelikler',     CreditCard],
              ['campaigns',     'Kampanyalar',     Rocket],
              ['recent',        'Son Aktivite',    Activity],
            ].map(([key, label, Icon]) => {
              const active = activeTab === key
              return (
                <button
                  key={key}
                  type="button"
                  onClick={() => setActiveTab(key)}
                  style={{
                    paddingLeft: 20, paddingRight: 20,
                    paddingTop: 14, paddingBottom: 14,
                    display: 'inline-flex', alignItems: 'center', gap: 8,
                    fontSize: 14, fontWeight: 500,
                    borderBottom: active ? '2px solid #6366f1' : '2px solid transparent',
                    color: active ? '#4f46e5' : '#64748b',
                    background: 'transparent',
                    cursor: 'pointer',
                    transition: 'all .15s',
                  }}
                  className="hover:text-slate-900"
                >
                  <Icon size={15} />
                  {label}
                </button>
              )
            })}
          </div>

          {/* === USERS TAB === */}
          {activeTab === 'users' && (
            <div>
              <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
                <div className="relative flex-1 max-w-md">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    placeholder="E-posta veya isimde ara…"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && loadUsers(1, userSearch)}
                    className="w-full pl-9 pr-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                  />
                </div>
                <button
                  onClick={() => loadUsers(1, userSearch)}
                  className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition"
                >
                  Ara
                </button>
                {userSearch && (
                  <button
                    onClick={() => { setUserSearch(''); loadUsers(1, '') }}
                    className="px-3 py-1.5 text-sm text-slate-600 hover:text-slate-900 transition"
                  >
                    Temizle
                  </button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>E-posta</Th>
                      <Th>İsim</Th>
                      <Th>Rol</Th>
                      <Th>Plan</Th>
                      <Th>Kampanya</Th>
                      <Th>Kayıt Tarihi</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {usersLoading && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>
                    )}
                    {!usersLoading && users.items.length === 0 && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kayıt yok</td></tr>
                    )}
                    {users.items.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50 transition">
                        <Td className="text-slate-400">#{u.id}</Td>
                        <Td className="font-medium text-slate-900">{u.email}</Td>
                        <Td>{u.name}</Td>
                        <Td>
                          {u.role === 'admin' ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                              Admin
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400">Kullanıcı</span>
                          )}
                        </Td>
                        <Td>{u.current_plan || <span className="text-slate-400">—</span>}</Td>
                        <Td>{fmtNum(u.total_campaigns)}</Td>
                        <Td className="text-slate-500">{fmtDateTime(u.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={users.page}
                total={users.total}
                pageSize={users.page_size}
                onChange={(p) => loadUsers(p, userSearch)}
              />
            </div>
          )}

          {/* === SUBSCRIPTIONS TAB === */}
          {activeTab === 'subscriptions' && (
            <div>
              <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2">
                <Filter size={15} className="text-slate-400" />
                <span className="text-sm text-slate-600">Durum:</span>
                <select
                  value={subsStatus}
                  onChange={(e) => { setSubsStatus(e.target.value); loadSubs(1, e.target.value) }}
                  className="px-3 py-1.5 text-sm border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500/30 focus:border-indigo-500"
                >
                  <option value="">Tümü</option>
                  <option value="active">Aktif</option>
                  <option value="cancelled">İptal</option>
                  <option value="past_due">Gecikmeli</option>
                  <option value="paused">Duraklatıldı</option>
                </select>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>E-posta</Th>
                      <Th>Plan</Th>
                      <Th>Durum</Th>
                      <Th>Dönem Sonu</Th>
                      <Th>LS ID</Th>
                      <Th>Oluşturma</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {subsLoading && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>
                    )}
                    {!subsLoading && subs.items.length === 0 && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kayıt yok</td></tr>
                    )}
                    {subs.items.map((s) => (
                      <tr key={s.id} className="hover:bg-slate-50 transition">
                        <Td className="text-slate-400">#{s.id}</Td>
                        <Td className="font-medium text-slate-900">{s.user_email}</Td>
                        <Td>{s.plan_name}</Td>
                        <Td><StatusBadge status={s.status} /></Td>
                        <Td>{fmtDate(s.current_period_end)}</Td>
                        <Td>
                          {s.lemonsqueezy_subscription_id ? (
                            <code className="text-xs text-slate-500">{s.lemonsqueezy_subscription_id}</code>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </Td>
                        <Td className="text-slate-500">{fmtDateTime(s.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={subs.page}
                total={subs.total}
                pageSize={subs.page_size}
                onChange={(p) => loadSubs(p, subsStatus)}
              />
            </div>
          )}

          {/* === CAMPAIGNS TAB === */}
          {activeTab === 'campaigns' && (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>E-posta</Th>
                      <Th>Kampanya</Th>
                      <Th>Tür</Th>
                      <Th>Bölge</Th>
                      <Th>Persona</Th>
                      <Th>Durum</Th>
                      <Th>Kredi</Th>
                      <Th>Oluşturma</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {campaignsLoading && (
                      <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>
                    )}
                    {!campaignsLoading && campaigns.items.length === 0 && (
                      <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kampanya yok</td></tr>
                    )}
                    {campaigns.items.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-50 transition">
                        <Td className="text-slate-400">#{c.id}</Td>
                        <Td className="font-medium text-slate-900">{c.user_email}</Td>
                        <Td>{c.name}</Td>
                        <Td><span className="text-xs px-2 py-0.5 bg-slate-100 text-slate-700 rounded">{c.type}</span></Td>
                        <Td>{c.region}</Td>
                        <Td className="tabular-nums">{fmtNum(c.persona_count)}</Td>
                        <Td><StatusBadge status={c.status} /></Td>
                        <Td className="tabular-nums">{fmtNum(c.credits_consumed)}</Td>
                        <Td className="text-slate-500">{fmtDateTime(c.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={campaigns.page}
                total={campaigns.total}
                pageSize={campaigns.page_size}
                onChange={(p) => loadCampaigns(p)}
              />
            </div>
          )}

          {/* === RECENT ACTIVITY TAB === */}
          {activeTab === 'recent' && (
            <div>
              {/* Filter pills */}
              <div className="px-4 py-3 border-b border-slate-200 flex items-center gap-2 flex-wrap">
                {[
                  ['all',           'Tümü',         null],
                  ['users',         'Üye',          UserPlus],
                  ['payments',      'Ödeme',        DollarSign],
                  ['cancellations', 'İptal',        XCircle],
                  ['campaigns',     'Kampanya',     Rocket],
                ].map(([key, label, Icon]) => {
                  const active = activityFilter === key
                  return (
                    <button
                      key={key}
                      onClick={() => setActivityFilter(key)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full transition ${
                        active
                          ? 'bg-indigo-600 text-white shadow-sm'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                      }`}
                    >
                      {Icon && <Icon size={12} />}
                      {label}
                    </button>
                  )
                })}
                <span className="ml-auto text-xs text-slate-500">
                  {filteredActivity.length} kayıt
                </span>
              </div>

              {/* Grouped list */}
              <div className="p-4 max-h-[600px] overflow-y-auto">
                {activityLoading && (
                  <div className="text-center text-sm text-slate-500 py-8">Yükleniyor…</div>
                )}
                {!activityLoading && filteredActivity.length === 0 && (
                  <div className="text-center text-sm text-slate-500 py-8">Aktivite yok</div>
                )}
                {!activityLoading && Object.entries(groupedActivity).map(([groupLabel, items]) => {
                  if (items.length === 0) return null
                  return (
                    <div key={groupLabel} className="mb-4 last:mb-0">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 px-2">
                        {groupLabel} <span className="text-slate-300">·</span> {items.length}
                      </div>
                      <ul className="space-y-1">
                        {items.map((a, idx) => (
                          <ActivityRow key={`${groupLabel}-${idx}`} item={a} />
                        ))}
                      </ul>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}


// ============================================
// ACTIVITY ROW
// ============================================

function ActivityRow({ item }) {
  const config = {
    user_signup:             { Icon: UserPlus,    cls: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    subscription_created:    { Icon: DollarSign,  cls: 'bg-blue-50 text-blue-600 border-blue-100' },
    subscription_cancelled:  { Icon: AlertTriangle, cls: 'bg-amber-50 text-amber-600 border-amber-100' },
    campaign_run:            { Icon: Rocket,      cls: 'bg-purple-50 text-purple-600 border-purple-100' },
  }
  const c = config[item.type] || { Icon: Activity, cls: 'bg-slate-50 text-slate-600 border-slate-100' }
  const Icon = c.Icon

  // Saat formatı: bugünse sadece saat, değilse tarih+saat
  const ts = new Date(item.timestamp)
  const today = new Date()
  const isToday = ts.toDateString() === today.toDateString()
  const timeStr = isToday
    ? ts.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
    : ts.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })

  return (
    <li className="flex items-center gap-3 py-2 px-2 hover:bg-slate-50 rounded-md transition">
      <div className={`flex-shrink-0 w-8 h-8 rounded-md border flex items-center justify-center ${c.cls}`}>
        <Icon size={14} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-900 font-medium truncate">{item.title}</div>
        <div className="text-xs text-slate-500 truncate">
          {item.user_email}
          {item.subtitle && <span className="text-slate-400"> · {item.subtitle}</span>}
        </div>
      </div>
      <div className="flex-shrink-0 text-xs text-slate-400 tabular-nums">
        {timeStr}
      </div>
    </li>
  )
}


// ============================================
// TABLE CELL HELPERS
// ============================================

function Th({ children }) {
  return (
    <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
      {children}
    </th>
  )
}

function Td({ children, className = '' }) {
  return (
    <td className={`px-4 py-2.5 text-sm text-slate-700 whitespace-nowrap ${className}`}>
      {children}
    </td>
  )
}
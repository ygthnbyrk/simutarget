// frontend/src/pages/AdminDashboard.jsx
import { useEffect, useState, useMemo, useCallback, useRef } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, Area, AreaChart,
} from 'recharts'
import {
  Users, UserPlus, DollarSign, TrendingUp, CreditCard, AlertTriangle,
  Rocket, Activity, RefreshCw, Search, LogOut, ChevronLeft, ChevronRight,
  XCircle, Filter, ArrowLeft, BadgeDollarSign, Sparkles, BarChart3, PieChart,
  Info, Pause, Play, Wifi,
} from 'lucide-react'
import { adminAPI } from '../services/api'
import useAuthStore from '../stores/authStore'


// ============================================
// CONFIG
// ============================================

const REFRESH_INTERVAL_MS = 30_000  // 30 saniye


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

const STATUS_META = {
  active:     { label: 'Aktif',          cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  cancelled:  { label: 'İptal',          cls: 'bg-rose-500/10 text-rose-400 border-rose-500/30' },
  past_due:   { label: 'Gecikmeli',      cls: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
  paused:     { label: 'Duraklatıldı',   cls: 'bg-slate-500/10 text-slate-400 border-slate-500/30' },
  completed:  { label: 'Tamamlandı',     cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
  running:    { label: 'Çalışıyor',      cls: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
  pending:    { label: 'Beklemede',      cls: 'bg-slate-500/10 text-slate-400 border-slate-500/30' },
  failed:     { label: 'Başarısız',      cls: 'bg-rose-500/10 text-rose-400 border-rose-500/30' },
}


// ============================================
// TIME AGO COMPONENT (her saniye güncel)
// ============================================

function TimeAgo({ date }) {
  const [, setTick] = useState(0)
  useEffect(() => {
    const i = setInterval(() => setTick((t) => t + 1), 1000)
    return () => clearInterval(i)
  }, [])

  if (!date) return null
  const seconds = Math.floor((Date.now() - date.getTime()) / 1000)
  if (seconds < 5) return 'şimdi'
  if (seconds < 60) return `${seconds}sn önce`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}dk önce`
  return `${Math.floor(seconds / 3600)}sa önce`
}


// ============================================
// SMALL COMPONENTS
// ============================================

function StatCard({ icon: Icon, label, value, sublabel, tooltip, accent = 'indigo' }) {
  const accents = {
    indigo:  { bar: 'from-indigo-500 to-violet-500',   icon: 'bg-indigo-500/10 text-indigo-400'   },
    violet:  { bar: 'from-violet-500 to-purple-500',   icon: 'bg-violet-500/10 text-violet-400'   },
    emerald: { bar: 'from-emerald-500 to-teal-500',    icon: 'bg-emerald-500/10 text-emerald-400' },
    amber:   { bar: 'from-amber-500 to-orange-500',    icon: 'bg-amber-500/10 text-amber-400'     },
    rose:    { bar: 'from-rose-500 to-pink-500',       icon: 'bg-rose-500/10 text-rose-400'       },
    blue:    { bar: 'from-blue-500 to-cyan-500',       icon: 'bg-blue-500/10 text-blue-400'       },
    purple:  { bar: 'from-purple-500 to-fuchsia-500',  icon: 'bg-purple-500/10 text-purple-400'   },
    slate:   { bar: 'from-slate-500 to-slate-600',     icon: 'bg-slate-500/10 text-slate-400'     },
  }
  const a = accents[accent] || accents.indigo
  return (
    <div className="relative bg-slate-900/80 rounded-xl border border-slate-800 hover:border-slate-700 backdrop-blur-sm transition-all overflow-hidden group">
      <div className={`absolute top-0 left-0 h-1 w-full bg-gradient-to-r ${a.bar} opacity-90`} />
      <div className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className={`p-2 rounded-lg ${a.icon}`}>
            {Icon && <Icon size={18} strokeWidth={2.2} />}
          </div>
          {tooltip && (
            <div className="group/tooltip relative">
              <Info size={13} className="text-slate-500 cursor-help" />
              <div className="invisible group-hover/tooltip:visible absolute right-0 top-5 z-20 w-56 p-2 text-xs text-slate-200 bg-slate-800 border border-slate-700 rounded-md shadow-xl">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <div className="text-xs font-medium text-slate-400 uppercase tracking-wider mb-1">{label}</div>
        <div className="text-2xl font-bold text-white tabular-nums">{value}</div>
        {sublabel && <div className="text-xs text-slate-500 mt-1">{sublabel}</div>}
      </div>
    </div>
  )
}

function FunnelBar({ label, count, percent, max, color = 'indigo' }) {
  const width = max > 0 ? (count / max) * 100 : 0
  const colors = {
    indigo:  'from-indigo-500 to-violet-500',
    emerald: 'from-emerald-500 to-teal-500',
    amber:   'from-amber-500 to-orange-500',
  }
  return (
    <div className="mb-4 last:mb-0">
      <div className="flex justify-between items-baseline mb-1.5">
        <span className="text-sm font-medium text-slate-300">{label}</span>
        <div className="text-sm">
          <span className="font-semibold text-white">{fmtNum(count)}</span>
          <span className="text-slate-500 ml-1.5">({fmtPct(percent)})</span>
        </div>
      </div>
      <div className="w-full bg-slate-800/80 rounded-full h-2.5 overflow-hidden">
        <div
          className={`h-2.5 rounded-full bg-gradient-to-r ${colors[color]} transition-all duration-500`}
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const meta = STATUS_META[status] || { label: status, cls: 'bg-slate-500/10 text-slate-400 border-slate-500/30' }
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${meta.cls}`}>
      {meta.label}
    </span>
  )
}

function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 bg-slate-900/50">
      <div className="text-sm text-slate-400">
        Toplam <strong className="text-slate-200">{fmtNum(total)}</strong> kayıt ·
        Sayfa <strong className="text-slate-200">{page}</strong> / {totalPages}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-slate-700 bg-slate-800/60 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition"
        >
          <ChevronLeft size={14} /> Önceki
        </button>
        <button
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="flex items-center gap-1 px-3 py-1.5 text-sm rounded-md border border-slate-700 bg-slate-800/60 text-slate-300 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 transition"
        >
          Sonraki <ChevronRight size={14} />
        </button>
      </div>
    </div>
  )
}

function SectionHeader({ icon: Icon, title }) {
  return (
    <h2 className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest mb-3 text-slate-400">
      {Icon && <Icon size={13} />}
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
  const [lastUpdated, setLastUpdated] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const refreshTimerRef = useRef(null)

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

  // Aktif tab'ı ref'te tut, polling closure'ı için
  const activeTabRef = useRef(activeTab)
  useEffect(() => { activeTabRef.current = activeTab }, [activeTab])


  // ---- LOADERS ----

  const loadStats = useCallback(async (silent = false) => {
    if (!silent) setStatsLoading(true)
    setStatsError(null)
    try {
      const res = await adminAPI.stats()
      setStats(res.data)
      setLastUpdated(new Date())
    } catch (e) {
      setStatsError(e.response?.data?.detail || 'İstatistikler yüklenemedi')
    } finally {
      if (!silent) setStatsLoading(false)
    }
  }, [])

  const loadUsers = useCallback(async (page = 1, search = '', silent = false) => {
    if (!silent) setUsersLoading(true)
    try {
      const res = await adminAPI.users({ page, page_size: 25, ...(search ? { search } : {}) })
      setUsers(res.data)
    } catch (e) { console.error('Users load error', e) } finally { if (!silent) setUsersLoading(false) }
  }, [])

  const loadSubs = useCallback(async (page = 1, status = '', silent = false) => {
    if (!silent) setSubsLoading(true)
    try {
      const res = await adminAPI.subscriptions({ page, page_size: 25, ...(status ? { status } : {}) })
      setSubs(res.data)
    } catch (e) { console.error('Subs load error', e) } finally { if (!silent) setSubsLoading(false) }
  }, [])

  const loadCampaigns = useCallback(async (page = 1, silent = false) => {
    if (!silent) setCampaignsLoading(true)
    try {
      const res = await adminAPI.campaigns({ page, page_size: 25 })
      setCampaigns(res.data)
    } catch (e) { console.error('Campaigns load error', e) } finally { if (!silent) setCampaignsLoading(false) }
  }, [])

  const loadActivity = useCallback(async (silent = false) => {
    if (!silent) setActivityLoading(true)
    try {
      const res = await adminAPI.recentActivity(50)
      setActivity(res.data.items || [])
    } catch (e) { console.error('Activity load error', e) } finally { if (!silent) setActivityLoading(false) }
  }, [])

  // Manuel yenile - tüm görünür içeriği yenile
  const refreshAll = useCallback((silent = false) => {
    loadStats(silent)
    const tab = activeTabRef.current
    if (tab === 'users') loadUsers(users.page, userSearch, silent)
    else if (tab === 'subscriptions') loadSubs(subs.page, subsStatus, silent)
    else if (tab === 'campaigns') loadCampaigns(campaigns.page, silent)
    else if (tab === 'recent') loadActivity(silent)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [loadStats, loadUsers, loadSubs, loadCampaigns, loadActivity, users.page, userSearch, subs.page, subsStatus, campaigns.page])

  // İlk yükleme
  useEffect(() => {
    loadStats()
    loadUsers(1, '')
  }, [loadStats, loadUsers])

  // Tab değiştiğinde lazy load
  useEffect(() => {
    if (activeTab === 'subscriptions' && subs.items.length === 0) loadSubs(1, '')
    if (activeTab === 'campaigns' && campaigns.items.length === 0) loadCampaigns(1)
    if (activeTab === 'recent' && activity.length === 0) loadActivity()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  // AUTO-REFRESH: 30sn'de bir, tab visible ise, silent mode (loading spinner göstermez)
  useEffect(() => {
    if (!autoRefresh) {
      if (refreshTimerRef.current) {
        clearInterval(refreshTimerRef.current)
        refreshTimerRef.current = null
      }
      return
    }

    const tick = () => {
      if (document.hidden) return  // Tab background'daysa atla
      refreshAll(true)
    }

    refreshTimerRef.current = setInterval(tick, REFRESH_INTERVAL_MS)

    // Tab tekrar görünür olduğunda hemen yenile
    const onVisible = () => {
      if (!document.hidden) refreshAll(true)
    }
    document.addEventListener('visibilitychange', onVisible)

    return () => {
      clearInterval(refreshTimerRef.current)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [autoRefresh, refreshAll])

  // ---- DERIVED ----

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
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 80% 50% at 50% 0%, rgba(99, 102, 241, 0.08), transparent 70%)',
        }}
      />

      {/* HEADER (sticky, tüm controls burada) */}
      <header className="relative bg-slate-950/90 border-b border-slate-800 sticky top-0 z-20 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between gap-4 flex-wrap">
          {/* Sol: Logo */}
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold shadow-lg"
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)' }}
            >
              S
            </div>
            <div>
              <h1 className="text-base font-bold text-white leading-tight">SimuTarget Admin</h1>
              <div className="text-xs text-slate-500 leading-tight">İç Yönetim Paneli</div>
            </div>
          </div>

          {/* Orta: Live indicator + son güncelleme + manuel yenile + auto-refresh toggle */}
          <div className="flex items-center gap-2 flex-wrap">
            {autoRefresh && lastUpdated && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/60 px-2.5 py-1.5 rounded-md border border-slate-800">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                Canlı · <TimeAgo date={lastUpdated} />
              </div>
            )}
            {!autoRefresh && lastUpdated && (
              <div className="flex items-center gap-1.5 text-xs text-slate-400 bg-slate-900/60 px-2.5 py-1.5 rounded-md border border-slate-800">
                <span className="inline-flex h-2 w-2 rounded-full bg-slate-500" />
                Durduruldu · <TimeAgo date={lastUpdated} />
              </div>
            )}

            <button
              onClick={() => refreshAll(false)}
              disabled={statsLoading}
              title="Şimdi yenile"
              className="flex items-center gap-1.5 text-sm px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-md hover:bg-slate-800 hover:border-slate-600 text-slate-200 disabled:opacity-50 transition"
            >
              <RefreshCw size={14} className={statsLoading ? 'animate-spin' : ''} />
              <span className="hidden md:inline">Yenile</span>
            </button>

            <button
              onClick={() => setAutoRefresh((v) => !v)}
              title={autoRefresh ? 'Otomatik yenilemeyi duraklat' : 'Otomatik yenilemeyi başlat'}
              className={`flex items-center gap-1.5 text-sm px-3 py-1.5 border rounded-md transition ${
                autoRefresh
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300 hover:bg-emerald-500/15'
                  : 'bg-slate-900 border-slate-700 text-slate-300 hover:bg-slate-800'
              }`}
            >
              {autoRefresh ? <Pause size={14} /> : <Play size={14} />}
              <span className="hidden lg:inline">{autoRefresh ? '30sn' : 'Başlat'}</span>
            </button>
          </div>

          {/* Sağ: User actions */}
          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition"
            >
              <ArrowLeft size={15} /> <span className="hidden md:inline">Dashboard</span>
            </Link>
            <div className="h-6 w-px bg-slate-800 hidden md:block" />
            <span className="text-sm text-slate-400 hidden lg:inline">{user?.email}</span>
            <button
              onClick={logout}
              className="flex items-center gap-1.5 text-sm text-rose-400 hover:text-rose-300 transition"
            >
              <LogOut size={15} /> <span className="hidden md:inline">Çıkış</span>
            </button>
          </div>
        </div>
      </header>

      <main className="relative max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Title */}
        <div>
          <h2 className="text-2xl font-bold text-white">Genel Bakış</h2>
          <p className="text-sm text-slate-400 mt-0.5">
            {autoRefresh
              ? `Her ${REFRESH_INTERVAL_MS / 1000} saniyede otomatik yenilenir`
              : 'Otomatik yenileme duraklatıldı'}
          </p>
        </div>

        {statsError && (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 rounded-lg p-3 text-sm flex items-center gap-2">
            <AlertTriangle size={16} /> {statsError}
          </div>
        )}

        {stats && (
          <>
            {/* KULLANICILAR */}
            <section>
              <SectionHeader icon={Users} title="Kullanıcılar" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard icon={Users}    label="Toplam Üye"  value={fmtNum(stats.cards.total_users)} accent="indigo" />
                <StatCard icon={UserPlus} label="Bugün"       value={fmtNum(stats.cards.users_today)}
                          sublabel={stats.cards.users_today > 0 ? 'Yeni kayıt' : 'Henüz yeni üye yok'} accent="emerald" />
                <StatCard icon={TrendingUp} label="Son 7 Gün"  value={fmtNum(stats.cards.users_7d)}  accent="violet" />
                <StatCard icon={TrendingUp} label="Son 30 Gün" value={fmtNum(stats.cards.users_30d)} accent="violet" />
              </div>
            </section>

            {/* GELİR */}
            <section>
              <SectionHeader icon={BadgeDollarSign} title="Gelir & Abonelikler" />
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard
                  icon={DollarSign}
                  label="Aylık MRR"
                  value={fmtUSD(stats.cards.mrr_usd)}
                  sublabel="Aktif aboneliklerin aylık toplamı"
                  tooltip="Bu ay tüm aktif aboneliklerden elde edilen tekrarlayan gelir. İptal eden kullanıcılar — dönem sonuna kadar erişimleri sürse bile — bu rakama dahil değildir."
                  accent="emerald"
                />
                <StatCard
                  icon={TrendingUp}
                  label="Yıllık ARR (Tahmin)"
                  value={fmtUSD(stats.cards.arr_usd)}
                  sublabel="MRR × 12 (basit projeksiyon)"
                  tooltip="ARR = MRR × 12. Bu basit bir projeksiyondur; gerçek yıllık gelir churn ve yeni satışlara göre değişir. Yıllık plan satılmaya başlandığında bu hesap güncellenmelidir."
                  accent="emerald"
                />
                <StatCard icon={CreditCard} label="Aktif Abonelik" value={fmtNum(stats.cards.active_subscriptions)} accent="blue" />
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
                <StatCard icon={Rocket}    label="Toplam Kampanya" value={fmtNum(stats.cards.total_campaigns)} accent="purple" />
                <StatCard icon={Sparkles}  label="Bugün"           value={fmtNum(stats.cards.campaigns_today)} accent="purple" />
                <StatCard icon={TrendingUp} label="Son 7 Gün"      value={fmtNum(stats.cards.campaigns_7d)}    accent="purple" />
                <StatCard icon={XCircle}   label="İptal Abonelik"  value={fmtNum(stats.cards.cancelled_subscriptions)}
                          sublabel="Tüm zamanlar (churn)" accent="rose" />
              </div>
            </section>

            {/* CHARTS */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Günlük Yeni Üye" subtitle="Son 30 gün" icon={BarChart3} iconColor="text-indigo-400">
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={stats.daily_signups} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g_signups" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#818cf8" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="#818cf8" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="date" tickFormatter={fmtShortDate} tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#1e293b' }} interval={4} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [v, 'Yeni üye']}
                      contentStyle={{ borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="value" stroke="#818cf8" strokeWidth={2.5} fill="url(#g_signups)" />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Günlük Gelir" subtitle="Son 30 gün" icon={DollarSign} iconColor="text-emerald-400">
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={stats.daily_revenue} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g_revenue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#34d399" stopOpacity={0.5} />
                        <stop offset="100%" stopColor="#34d399" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="date" tickFormatter={fmtShortDate} tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#1e293b' }} interval={4} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [fmtUSD(v), 'Gelir']}
                      contentStyle={{ borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 12 }}
                    />
                    <Area type="monotone" dataKey="value" stroke="#34d399" strokeWidth={2.5} fill="url(#g_revenue)" />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>
            </section>

            {/* PLAN BREAKDOWN + FUNNEL */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <ChartCard title="Plan Bazında Aktif Abonelikler" icon={PieChart} iconColor="text-purple-400">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={stats.plan_breakdown} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis dataKey="plan_name" tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={{ stroke: '#1e293b' }} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} tickLine={false} axisLine={false} allowDecimals={false} />
                    <Tooltip
                      formatter={(v, key) => {
                        if (key === 'active_count') return [v, 'Aktif Sub']
                        if (key === 'monthly_revenue_usd') return [fmtUSD(v), 'Aylık Gelir']
                        return [v, key]
                      }}
                      contentStyle={{ borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 12 }}
                      cursor={{ fill: 'rgba(99,102,241,0.05)' }}
                    />
                    <Bar dataKey="active_count" fill="#818cf8" radius={[6, 6, 0, 0]} name="Aktif" />
                    <Bar dataKey="monthly_revenue_usd" fill="#34d399" radius={[6, 6, 0, 0]} name="Gelir" />
                  </BarChart>
                </ResponsiveContainer>
                <div className="flex items-center gap-4 mt-2 text-xs text-slate-400 justify-center">
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-indigo-400" /> Aktif Abonelik</span>
                  <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-sm bg-emerald-400" /> Aylık Gelir ($)</span>
                </div>
              </ChartCard>

              <ChartCard title="Dönüşüm Hunisi" icon={TrendingUp} iconColor="text-amber-400">
                {stats.conversion_funnel && (() => {
                  const f = stats.conversion_funnel
                  const max = f.signed_up || 1
                  return (
                    <>
                      <FunnelBar label="Kayıt oldu" count={f.signed_up} percent={100} max={max} color="indigo" />
                      <FunnelBar label="İlk kampanyayı çalıştırdı" count={f.ran_first_campaign} percent={f.signup_to_activation_pct} max={max} color="amber" />
                      <FunnelBar label="Ücretli aboneliği var" count={f.has_paid_subscription} percent={f.overall_conversion_pct} max={max} color="emerald" />
                      <div className="mt-5 pt-4 border-t border-slate-800 grid grid-cols-3 gap-3 text-center">
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Kayıt → Aktivasyon</div>
                          <div className="text-sm font-semibold text-slate-200">{fmtPct(f.signup_to_activation_pct)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Aktivasyon → Ödeme</div>
                          <div className="text-sm font-semibold text-slate-200">{fmtPct(f.activation_to_paid_pct)}</div>
                        </div>
                        <div>
                          <div className="text-xs text-slate-500 mb-0.5">Toplam Dönüşüm</div>
                          <div className="text-sm font-bold text-indigo-400">{fmtPct(f.overall_conversion_pct)}</div>
                        </div>
                      </div>
                    </>
                  )
                })()}
              </ChartCard>
            </section>
          </>
        )}

        {/* TABS */}
        <section className="bg-slate-900/60 rounded-xl border border-slate-800 backdrop-blur-sm overflow-hidden">
          <div
            className="border-b border-slate-800 bg-slate-900/80"
            style={{ display: 'flex', gap: 0, overflowX: 'auto' }}
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
                    borderBottom: active ? '2px solid #818cf8' : '2px solid transparent',
                    color: active ? '#a5b4fc' : '#94a3b8',
                    background: 'transparent',
                    cursor: 'pointer',
                    transition: 'all .15s',
                    whiteSpace: 'nowrap',
                  }}
                  className="hover:!text-white"
                >
                  <Icon size={15} />
                  {label}
                </button>
              )
            })}
          </div>

          {activeTab === 'users' && (
            <div>
              <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
                <div className="relative flex-1 max-w-md">
                  <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    placeholder="E-posta veya isimde ara…"
                    value={userSearch}
                    onChange={(e) => setUserSearch(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && loadUsers(1, userSearch)}
                    className="w-full pl-9 pr-3 py-1.5 text-sm bg-slate-800/60 border border-slate-700 rounded-md text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500"
                  />
                </div>
                <button onClick={() => loadUsers(1, userSearch)} className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-500 transition shadow-sm">Ara</button>
                {userSearch && (
                  <button onClick={() => { setUserSearch(''); loadUsers(1, '') }} className="px-3 py-1.5 text-sm text-slate-400 hover:text-white transition">Temizle</button>
                )}
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-slate-900/80">
                    <tr>
                      <Th>ID</Th><Th>E-posta</Th><Th>İsim</Th><Th>Rol</Th>
                      <Th>Plan</Th><Th>Kampanya</Th><Th>Kayıt Tarihi</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {usersLoading && <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>}
                    {!usersLoading && users.items.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kayıt yok</td></tr>}
                    {users.items.map((u) => (
                      <tr key={u.id} className="border-t border-slate-800 hover:bg-slate-800/40 transition">
                        <Td className="text-slate-500">#{u.id}</Td>
                        <Td className="font-medium text-slate-100">{u.email}</Td>
                        <Td>{u.name}</Td>
                        <Td>
                          {u.role === 'admin'
                            ? <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">Admin</span>
                            : <span className="text-xs text-slate-500">Kullanıcı</span>}
                        </Td>
                        <Td>{u.current_plan || <span className="text-slate-500">—</span>}</Td>
                        <Td className="tabular-nums">{fmtNum(u.total_campaigns)}</Td>
                        <Td className="text-slate-400">{fmtDateTime(u.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={users.page} total={users.total} pageSize={users.page_size} onChange={(p) => loadUsers(p, userSearch)} />
            </div>
          )}

          {activeTab === 'subscriptions' && (
            <div>
              <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2">
                <Filter size={15} className="text-slate-500" />
                <span className="text-sm text-slate-400">Durum:</span>
                <select
                  value={subsStatus}
                  onChange={(e) => { setSubsStatus(e.target.value); loadSubs(1, e.target.value) }}
                  className="px-3 py-1.5 text-sm bg-slate-800/60 border border-slate-700 rounded-md text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/40 focus:border-indigo-500"
                >
                  <option value="">Tümü</option>
                  <option value="active">Aktif</option>
                  <option value="cancelled">İptal</option>
                  <option value="past_due">Gecikmeli</option>
                  <option value="paused">Duraklatıldı</option>
                </select>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-slate-900/80">
                    <tr>
                      <Th>ID</Th><Th>E-posta</Th><Th>Plan</Th><Th>Durum</Th>
                      <Th>Dönem Sonu</Th><Th>LS ID</Th><Th>Oluşturma</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {subsLoading && <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>}
                    {!subsLoading && subs.items.length === 0 && <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kayıt yok</td></tr>}
                    {subs.items.map((s) => (
                      <tr key={s.id} className="border-t border-slate-800 hover:bg-slate-800/40 transition">
                        <Td className="text-slate-500">#{s.id}</Td>
                        <Td className="font-medium text-slate-100">{s.user_email}</Td>
                        <Td>{s.plan_name}</Td>
                        <Td><StatusBadge status={s.status} /></Td>
                        <Td>{fmtDate(s.current_period_end)}</Td>
                        <Td>{s.lemonsqueezy_subscription_id ? <code className="text-xs text-slate-400">{s.lemonsqueezy_subscription_id}</code> : <span className="text-slate-500">—</span>}</Td>
                        <Td className="text-slate-400">{fmtDateTime(s.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={subs.page} total={subs.total} pageSize={subs.page_size} onChange={(p) => loadSubs(p, subsStatus)} />
            </div>
          )}

          {activeTab === 'campaigns' && (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-slate-900/80">
                    <tr>
                      <Th>ID</Th><Th>E-posta</Th><Th>Kampanya</Th><Th>Tür</Th>
                      <Th>Bölge</Th><Th>Persona</Th><Th>Durum</Th><Th>Kredi</Th><Th>Oluşturma</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {campaignsLoading && <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">Yükleniyor…</td></tr>}
                    {!campaignsLoading && campaigns.items.length === 0 && <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-slate-500">Henüz kampanya yok</td></tr>}
                    {campaigns.items.map((c) => (
                      <tr key={c.id} className="border-t border-slate-800 hover:bg-slate-800/40 transition">
                        <Td className="text-slate-500">#{c.id}</Td>
                        <Td className="font-medium text-slate-100">{c.user_email}</Td>
                        <Td>{c.name}</Td>
                        <Td><span className="text-xs px-2 py-0.5 bg-slate-800 text-slate-300 rounded">{c.type}</span></Td>
                        <Td>{c.region}</Td>
                        <Td className="tabular-nums">{fmtNum(c.persona_count)}</Td>
                        <Td><StatusBadge status={c.status} /></Td>
                        <Td className="tabular-nums">{fmtNum(c.credits_consumed)}</Td>
                        <Td className="text-slate-400">{fmtDateTime(c.created_at)}</Td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination page={campaigns.page} total={campaigns.total} pageSize={campaigns.page_size} onChange={(p) => loadCampaigns(p)} />
            </div>
          )}

          {activeTab === 'recent' && (
            <div>
              <div className="px-4 py-3 border-b border-slate-800 flex items-center gap-2 flex-wrap">
                {[
                  ['all',           'Tümü',     null],
                  ['users',         'Üye',      UserPlus],
                  ['payments',      'Ödeme',    DollarSign],
                  ['cancellations', 'İptal',    XCircle],
                  ['campaigns',     'Kampanya', Rocket],
                ].map(([key, label, Icon]) => {
                  const active = activityFilter === key
                  return (
                    <button
                      key={key}
                      onClick={() => setActivityFilter(key)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-full transition border ${
                        active
                          ? 'bg-indigo-500 border-indigo-400 text-white shadow-sm shadow-indigo-500/30'
                          : 'bg-slate-800/40 border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-slate-600'
                      }`}
                    >
                      {Icon && <Icon size={12} />}
                      {label}
                    </button>
                  )
                })}
                <span className="ml-auto text-xs text-slate-500">{filteredActivity.length} kayıt</span>
              </div>

              <div className="p-4 max-h-[600px] overflow-y-auto">
                {activityLoading && <div className="text-center text-sm text-slate-500 py-8">Yükleniyor…</div>}
                {!activityLoading && filteredActivity.length === 0 && <div className="text-center text-sm text-slate-500 py-8">Aktivite yok</div>}
                {!activityLoading && Object.entries(groupedActivity).map(([groupLabel, items]) => {
                  if (items.length === 0) return null
                  return (
                    <div key={groupLabel} className="mb-4 last:mb-0">
                      <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2 px-2">
                        {groupLabel} <span className="text-slate-600">·</span> {items.length}
                      </div>
                      <ul className="space-y-1">
                        {items.map((a, idx) => <ActivityRow key={`${groupLabel}-${idx}`} item={a} />)}
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
// CHART CARD WRAPPER
// ============================================

function ChartCard({ title, subtitle, icon: Icon, iconColor, children }) {
  return (
    <div className="bg-slate-900/60 rounded-xl border border-slate-800 backdrop-blur-sm p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-200">
          {Icon && <Icon size={15} className={iconColor} />}
          {title}
        </h3>
        {subtitle && <span className="text-xs text-slate-500">{subtitle}</span>}
      </div>
      {children}
    </div>
  )
}


// ============================================
// ACTIVITY ROW
// ============================================

function ActivityRow({ item }) {
  const config = {
    user_signup:             { Icon: UserPlus,      cls: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
    subscription_created:    { Icon: DollarSign,    cls: 'bg-blue-500/10 text-blue-400 border-blue-500/30' },
    subscription_cancelled:  { Icon: AlertTriangle, cls: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
    campaign_run:            { Icon: Rocket,        cls: 'bg-purple-500/10 text-purple-400 border-purple-500/30' },
  }
  const c = config[item.type] || { Icon: Activity, cls: 'bg-slate-500/10 text-slate-400 border-slate-500/30' }
  const Icon = c.Icon

  const ts = new Date(item.timestamp)
  const today = new Date()
  const isToday = ts.toDateString() === today.toDateString()
  const timeStr = isToday
    ? ts.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
    : ts.toLocaleString('tr-TR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })

  return (
    <li className="flex items-center gap-3 py-2 px-2 hover:bg-slate-800/40 rounded-md transition">
      <div className={`flex-shrink-0 w-8 h-8 rounded-md border flex items-center justify-center ${c.cls}`}>
        <Icon size={14} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-100 font-medium truncate">{item.title}</div>
        <div className="text-xs text-slate-500 truncate">
          {item.user_email}
          {item.subtitle && <span className="text-slate-600"> · {item.subtitle}</span>}
        </div>
      </div>
      <div className="flex-shrink-0 text-xs text-slate-500 tabular-nums">{timeStr}</div>
    </li>
  )
}


// ============================================
// TABLE HELPERS
// ============================================

function Th({ children }) {
  return <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">{children}</th>
}

function Td({ children, className = '' }) {
  return <td className={`px-4 py-2.5 text-sm text-slate-300 whitespace-nowrap ${className}`}>{children}</td>
}
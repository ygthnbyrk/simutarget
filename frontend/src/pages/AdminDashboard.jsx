// frontend/src/pages/AdminDashboard.jsx
import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  BarChart, Bar, CartesianGrid, Legend,
} from 'recharts'
import { adminAPI } from '../services/api'
import useAuthStore from '../stores/authStore'

// ============================================
// FORMATTING HELPERS
// ============================================

const fmtNum = (n) => new Intl.NumberFormat('en-US').format(n ?? 0)
const fmtUSD = (n) => `$${(n ?? 0).toFixed(2)}`
const fmtPct = (n) => `${(n ?? 0).toFixed(1)}%`

const fmtDate = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short', year: 'numeric' })
}

const fmtDateTime = (iso) => {
  if (!iso) return '-'
  const d = new Date(iso)
  return d.toLocaleString('tr-TR', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const fmtShortDate = (iso) => {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleDateString('tr-TR', { day: '2-digit', month: 'short' })
}


// ============================================
// SMALL UI COMPONENTS
// ============================================

function StatCard({ label, value, sublabel, accent = 'gray' }) {
  const accentClasses = {
    gray: 'border-gray-200',
    green: 'border-green-300 bg-green-50',
    red: 'border-red-300 bg-red-50',
    blue: 'border-blue-300 bg-blue-50',
    yellow: 'border-yellow-300 bg-yellow-50',
  }
  return (
    <div className={`bg-white rounded-lg shadow-sm border ${accentClasses[accent]} p-4`}>
      <div className="text-xs uppercase tracking-wider text-gray-500 mb-1">{label}</div>
      <div className="text-2xl font-semibold text-gray-900">{value}</div>
      {sublabel && <div className="text-xs text-gray-500 mt-1">{sublabel}</div>}
    </div>
  )
}

function FunnelBar({ label, count, percent, max }) {
  const width = max > 0 ? (count / max) * 100 : 0
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-gray-700">{label}</span>
        <span className="text-gray-500">
          {fmtNum(count)} <span className="text-gray-400">({fmtPct(percent)})</span>
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3">
        <div
          className="bg-indigo-500 h-3 rounded-full transition-all"
          style={{ width: `${width}%` }}
        />
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const styles = {
    active: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
    past_due: 'bg-yellow-100 text-yellow-800',
    paused: 'bg-gray-100 text-gray-800',
    completed: 'bg-green-100 text-green-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-gray-100 text-gray-800',
    failed: 'bg-red-100 text-red-800',
  }
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  )
}

function Pagination({ page, total, pageSize, onChange }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-gray-200 bg-gray-50 rounded-b-lg">
      <div className="text-sm text-gray-600">
        Toplam <strong>{fmtNum(total)}</strong> kayıt · Sayfa <strong>{page}</strong> / {totalPages}
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="px-3 py-1 text-sm rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
        >
          ‹ Önceki
        </button>
        <button
          onClick={() => onChange(page + 1)}
          disabled={page >= totalPages}
          className="px-3 py-1 text-sm rounded border border-gray-300 bg-white disabled:opacity-40 hover:bg-gray-50"
        >
          Sonraki ›
        </button>
      </div>
    </div>
  )
}


// ============================================
// MAIN DASHBOARD COMPONENT
// ============================================

export default function AdminDashboard() {
  const { user, logout } = useAuthStore()

  // Stats
  const [stats, setStats] = useState(null)
  const [statsError, setStatsError] = useState(null)
  const [statsLoading, setStatsLoading] = useState(true)

  // Tab state
  const [activeTab, setActiveTab] = useState('users')

  // Users tab
  const [users, setUsers] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [usersLoading, setUsersLoading] = useState(false)
  const [userSearch, setUserSearch] = useState('')

  // Subscriptions tab
  const [subs, setSubs] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [subsLoading, setSubsLoading] = useState(false)
  const [subsStatus, setSubsStatus] = useState('')

  // Campaigns tab
  const [campaigns, setCampaigns] = useState({ items: [], total: 0, page: 1, page_size: 25 })
  const [campaignsLoading, setCampaignsLoading] = useState(false)

  // Recent activity tab
  const [activity, setActivity] = useState([])
  const [activityLoading, setActivityLoading] = useState(false)


  // -------- Loaders --------

  const loadStats = useCallback(async () => {
    setStatsLoading(true)
    setStatsError(null)
    try {
      const res = await adminAPI.stats()
      setStats(res.data)
    } catch (e) {
      setStatsError(e.response?.data?.detail || 'Stats yüklenemedi')
    } finally {
      setStatsLoading(false)
    }
  }, [])

  const loadUsers = useCallback(async (page = 1, search = '') => {
    setUsersLoading(true)
    try {
      const res = await adminAPI.users({
        page, page_size: 25,
        ...(search ? { search } : {}),
      })
      setUsers(res.data)
    } catch (e) {
      console.error('Users load error', e)
    } finally {
      setUsersLoading(false)
    }
  }, [])

  const loadSubs = useCallback(async (page = 1, status = '') => {
    setSubsLoading(true)
    try {
      const res = await adminAPI.subscriptions({
        page, page_size: 25,
        ...(status ? { status } : {}),
      })
      setSubs(res.data)
    } catch (e) {
      console.error('Subs load error', e)
    } finally {
      setSubsLoading(false)
    }
  }, [])

  const loadCampaigns = useCallback(async (page = 1) => {
    setCampaignsLoading(true)
    try {
      const res = await adminAPI.campaigns({ page, page_size: 25 })
      setCampaigns(res.data)
    } catch (e) {
      console.error('Campaigns load error', e)
    } finally {
      setCampaignsLoading(false)
    }
  }, [])

  const loadActivity = useCallback(async () => {
    setActivityLoading(true)
    try {
      const res = await adminAPI.recentActivity(30)
      setActivity(res.data.items || [])
    } catch (e) {
      console.error('Activity load error', e)
    } finally {
      setActivityLoading(false)
    }
  }, [])

  // İlk yükleme
  useEffect(() => {
    loadStats()
    loadUsers(1, '')
  }, [loadStats, loadUsers])

  // Tab değişiminde lazy load
  useEffect(() => {
    if (activeTab === 'subscriptions' && subs.items.length === 0) loadSubs(1, '')
    if (activeTab === 'campaigns' && campaigns.items.length === 0) loadCampaigns(1)
    if (activeTab === 'recent' && activity.length === 0) loadActivity()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab])

  // -------- Render --------

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold text-gray-900">SimuTarget Admin</h1>
            <span className="text-xs px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded uppercase tracking-wider">
              internal
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
              ← Dashboard
            </Link>
            <span className="text-sm text-gray-500">{user?.email}</span>
            <button
              onClick={logout}
              className="text-sm text-red-600 hover:text-red-700"
            >
              Çıkış
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {/* Reload */}
        <div className="flex justify-end">
          <button
            onClick={loadStats}
            disabled={statsLoading}
            className="text-sm px-3 py-1 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
          >
            {statsLoading ? 'Yükleniyor…' : 'Yenile ⟳'}
          </button>
        </div>

        {statsError && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
            {statsError}
          </div>
        )}

        {/* Stats Cards */}
        {stats && (
          <>
            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Kullanıcılar
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label="Toplam Üye" value={fmtNum(stats.cards.total_users)} />
                <StatCard label="Bugün" value={fmtNum(stats.cards.users_today)} accent="green" />
                <StatCard label="Son 7 Gün" value={fmtNum(stats.cards.users_7d)} />
                <StatCard label="Son 30 Gün" value={fmtNum(stats.cards.users_30d)} />
              </div>
            </section>

            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Gelir & Abonelikler
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label="MRR" value={fmtUSD(stats.cards.mrr_usd)} accent="green" />
                <StatCard label="ARR" value={fmtUSD(stats.cards.arr_usd)} sublabel="(MRR × 12)" />
                <StatCard label="Aktif Sub" value={fmtNum(stats.cards.active_subscriptions)} accent="blue" />
                <StatCard
                  label="Past Due"
                  value={fmtNum(stats.cards.past_due_subscriptions)}
                  accent={stats.cards.past_due_subscriptions > 0 ? 'yellow' : 'gray'}
                />
              </div>
            </section>

            <section>
              <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Aktivite
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <StatCard label="Toplam Kampanya" value={fmtNum(stats.cards.total_campaigns)} />
                <StatCard label="Bugün" value={fmtNum(stats.cards.campaigns_today)} />
                <StatCard label="Son 7 Gün" value={fmtNum(stats.cards.campaigns_7d)} />
                <StatCard label="İptal Sub" value={fmtNum(stats.cards.cancelled_subscriptions)} />
              </div>
            </section>

            {/* Charts */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Günlük Yeni Üye (Son 30 Gün)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={stats.daily_signups}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={fmtShortDate}
                      tick={{ fontSize: 11 }}
                      interval={4}
                    />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [v, 'Yeni üye']}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#4f46e5"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Günlük Gelir (Son 30 Gün)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={stats.daily_revenue}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="date"
                      tickFormatter={fmtShortDate}
                      tick={{ fontSize: 11 }}
                      interval={4}
                    />
                    <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
                    <Tooltip
                      labelFormatter={fmtDate}
                      formatter={(v) => [fmtUSD(v), 'Gelir']}
                    />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ r: 3 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Plan Breakdown */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Plan Bazında Aktif Abonelikler</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={stats.plan_breakdown}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="plan_name" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} allowDecimals={false} />
                    <Tooltip
                      formatter={(v, key) => {
                        if (key === 'active_count') return [v, 'Aktif Sub']
                        if (key === 'monthly_revenue_usd') return [fmtUSD(v), 'Aylık Gelir']
                        return [v, key]
                      }}
                    />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Bar dataKey="active_count" fill="#4f46e5" name="Aktif Sub" />
                    <Bar dataKey="monthly_revenue_usd" fill="#10b981" name="Aylık Gelir ($)" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Conversion Funnel */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Conversion Funnel</h3>
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
                      />
                      <FunnelBar
                        label="İlk kampanyayı çalıştırdı"
                        count={f.ran_first_campaign}
                        percent={f.signup_to_activation_pct}
                        max={max}
                      />
                      <FunnelBar
                        label="Ücretli aboneliği var"
                        count={f.has_paid_subscription}
                        percent={f.overall_conversion_pct}
                        max={max}
                      />
                      <div className="mt-4 pt-3 border-t border-gray-100 text-xs text-gray-500 space-y-1">
                        <div>
                          Kayıt → Aktivasyon: <strong className="text-gray-700">
                            {fmtPct(f.signup_to_activation_pct)}
                          </strong>
                        </div>
                        <div>
                          Aktivasyon → Ödeme: <strong className="text-gray-700">
                            {fmtPct(f.activation_to_paid_pct)}
                          </strong>
                        </div>
                        <div>
                          Toplam Conversion: <strong className="text-indigo-600">
                            {fmtPct(f.overall_conversion_pct)}
                          </strong>
                        </div>
                      </div>
                    </>
                  )
                })()}
              </div>
            </section>
          </>
        )}

        {/* Tabs */}
        <section className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="border-b border-gray-200">
            <nav className="flex">
              {[
                ['users', 'Üyeler'],
                ['subscriptions', 'Abonelikler'],
                ['campaigns', 'Kampanyalar'],
                ['recent', 'Son Aktivite'],
              ].map(([key, label]) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`px-6 py-3 text-sm font-medium border-b-2 -mb-px transition ${
                    activeTab === key
                      ? 'border-indigo-500 text-indigo-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {label}
                </button>
              ))}
            </nav>
          </div>

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div>
              <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Email veya isimde ara…"
                  value={userSearch}
                  onChange={(e) => setUserSearch(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && loadUsers(1, userSearch)}
                  className="flex-1 px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <button
                  onClick={() => loadUsers(1, userSearch)}
                  className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
                >
                  Ara
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>Email</Th>
                      <Th>İsim</Th>
                      <Th>Rol</Th>
                      <Th>Plan</Th>
                      <Th>Kampanya</Th>
                      <Th>Kayıt</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {usersLoading && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">Yükleniyor…</td></tr>
                    )}
                    {!usersLoading && users.items.length === 0 && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">Kayıt yok</td></tr>
                    )}
                    {users.items.map((u) => (
                      <tr key={u.id} className="hover:bg-gray-50">
                        <Td>#{u.id}</Td>
                        <Td>{u.email}</Td>
                        <Td>{u.name}</Td>
                        <Td>
                          {u.role === 'admin' ? (
                            <span className="px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-700">
                              admin
                            </span>
                          ) : (
                            <span className="text-xs text-gray-500">user</span>
                          )}
                        </Td>
                        <Td>{u.current_plan || <span className="text-gray-400">—</span>}</Td>
                        <Td>{fmtNum(u.total_campaigns)}</Td>
                        <Td>{fmtDateTime(u.created_at)}</Td>
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

          {/* Subscriptions Tab */}
          {activeTab === 'subscriptions' && (
            <div>
              <div className="px-4 py-3 border-b border-gray-200 flex items-center gap-2">
                <select
                  value={subsStatus}
                  onChange={(e) => {
                    setSubsStatus(e.target.value)
                    loadSubs(1, e.target.value)
                  }}
                  className="px-3 py-1.5 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="">Tümü</option>
                  <option value="active">Active</option>
                  <option value="cancelled">Cancelled</option>
                  <option value="past_due">Past Due</option>
                  <option value="paused">Paused</option>
                </select>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>Email</Th>
                      <Th>Plan</Th>
                      <Th>Durum</Th>
                      <Th>Periyot Sonu</Th>
                      <Th>LS Sub ID</Th>
                      <Th>Oluşturuldu</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {subsLoading && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">Yükleniyor…</td></tr>
                    )}
                    {!subsLoading && subs.items.length === 0 && (
                      <tr><td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-500">Kayıt yok</td></tr>
                    )}
                    {subs.items.map((s) => (
                      <tr key={s.id} className="hover:bg-gray-50">
                        <Td>#{s.id}</Td>
                        <Td>{s.user_email}</Td>
                        <Td>{s.plan_name}</Td>
                        <Td><StatusBadge status={s.status} /></Td>
                        <Td>{fmtDate(s.current_period_end)}</Td>
                        <Td>
                          {s.lemonsqueezy_subscription_id ? (
                            <code className="text-xs text-gray-600">{s.lemonsqueezy_subscription_id}</code>
                          ) : (
                            <span className="text-gray-400">—</span>
                          )}
                        </Td>
                        <Td>{fmtDateTime(s.created_at)}</Td>
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

          {/* Campaigns Tab */}
          {activeTab === 'campaigns' && (
            <div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <Th>ID</Th>
                      <Th>Email</Th>
                      <Th>Kampanya</Th>
                      <Th>Tip</Th>
                      <Th>Bölge</Th>
                      <Th>Persona</Th>
                      <Th>Durum</Th>
                      <Th>Credits</Th>
                      <Th>Oluşturuldu</Th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {campaignsLoading && (
                      <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">Yükleniyor…</td></tr>
                    )}
                    {!campaignsLoading && campaigns.items.length === 0 && (
                      <tr><td colSpan={9} className="px-4 py-8 text-center text-sm text-gray-500">Kayıt yok</td></tr>
                    )}
                    {campaigns.items.map((c) => (
                      <tr key={c.id} className="hover:bg-gray-50">
                        <Td>#{c.id}</Td>
                        <Td>{c.user_email}</Td>
                        <Td>{c.name}</Td>
                        <Td><span className="text-xs px-2 py-0.5 bg-gray-100 rounded">{c.type}</span></Td>
                        <Td>{c.region}</Td>
                        <Td>{fmtNum(c.persona_count)}</Td>
                        <Td><StatusBadge status={c.status} /></Td>
                        <Td>{fmtNum(c.credits_consumed)}</Td>
                        <Td>{fmtDateTime(c.created_at)}</Td>
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

          {/* Recent Activity Tab */}
          {activeTab === 'recent' && (
            <div className="p-4">
              {activityLoading && (
                <div className="text-center text-sm text-gray-500 py-8">Yükleniyor…</div>
              )}
              {!activityLoading && activity.length === 0 && (
                <div className="text-center text-sm text-gray-500 py-8">Aktivite yok</div>
              )}
              <ul className="space-y-3">
                {activity.map((a, idx) => (
                  <li key={idx} className="flex items-start gap-3 p-3 bg-gray-50 rounded">
                    <span className="text-xl mt-0.5">
                      {a.type === 'user_signup' && '🎉'}
                      {a.type === 'subscription_created' && '💰'}
                      {a.type === 'subscription_cancelled' && '⚠️'}
                      {a.type === 'campaign_run' && '🚀'}
                    </span>
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-900">{a.title}</div>
                      {a.subtitle && <div className="text-xs text-gray-500 mt-0.5">{a.subtitle}</div>}
                      {a.user_email && <div className="text-xs text-gray-400 mt-0.5">{a.user_email}</div>}
                    </div>
                    <div className="text-xs text-gray-400 whitespace-nowrap">
                      {fmtDateTime(a.timestamp)}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}


// ============================================
// Tablo cell helper'ları
// ============================================

function Th({ children }) {
  return (
    <th className="px-4 py-2 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
      {children}
    </th>
  )
}

function Td({ children }) {
  return <td className="px-4 py-2 text-sm text-gray-700 whitespace-nowrap">{children}</td>
}

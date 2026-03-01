import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { TestTube, Swords, LayoutGrid, TrendingUp, CreditCard, ArrowRight, Zap, Users, BarChart3, Loader2, AlertCircle, RefreshCw, Activity } from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, CartesianGrid } from 'recharts'
import DashboardLayout from '../components/layout/DashboardLayout'
import useAuthStore from '../stores/authStore'
import useCreditStore from '../stores/creditStore'
import { campaignsAPI } from '../services/api'

// ── Helpers ──────────────────────────────────────────

function timeAgo(dateStr, t) {
  if (!dateStr) return ''
  const now = new Date()
  const date = new Date(dateStr)
  const seconds = Math.floor((now - date) / 1000)
  if (seconds < 60) return t('common.justNow')
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return t('common.mAgo', { count: minutes })
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return t('common.hAgo', { count: hours })
  const days = Math.floor(hours / 24)
  if (days < 7) return t('common.dAgo', { count: days })
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function getConversionFromSummary(summary) {
  if (!summary) return null
  if (summary.conversion_rate !== undefined) return Math.round(summary.conversion_rate)
  if (summary.a_percentage !== undefined && summary.b_percentage !== undefined) return Math.round(Math.max(summary.a_percentage, summary.b_percentage))
  if (summary.percentages) {
    const vals = Object.values(summary.percentages)
    return vals.length > 0 ? Math.round(Math.max(...vals)) : null
  }
  return null
}

function getTestTypeLabel(type, t) {
  if (!type) return t('testTypes.single')
  const tt = type.toLowerCase()
  if (tt === 'single') return t('testTypes.single')
  if (tt === 'ab' || tt === 'compare') return t('testTypes.ab')
  if (tt === 'multi') return t('testTypes.multi')
  return type
}

function getTestTypeBadge(type) {
  if (!type) return 'badge-success'
  const t = type.toLowerCase()
  if (t === 'ab' || t === 'compare') return 'badge-info'
  if (t === 'multi') return 'badge-warning'
  return 'badge-success'
}

const regionFlags = { TR: '🇹🇷', US: '🇺🇸', EU: '🇪🇺', MENA: '🌍' }
const CHART_COLORS = ['#06B6D4', '#8B5CF6', '#F59E0B', '#10B981', '#EF4444', '#3B82F6']

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '10px', padding: '12px 16px', boxShadow: '0 8px 24px rgba(0,0,0,0.4)' }}>
      <p style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ fontSize: '14px', fontWeight: '600', color: p.color }}>
          {p.name}: {typeof p.value === 'number' ? (p.name === 'Conversion' || p.name === 'Dönüşüm' ? `${p.value}%` : p.value) : p.value}
        </p>
      ))}
    </div>
  )
}

function SkeletonCard() {
  return (
    <div className="card" style={{ padding: '24px', height: '130px' }}>
      <div style={{ height: '14px', width: '60%', borderRadius: '4px', background: 'var(--color-bg-tertiary)', animation: 'pulse 1.5s ease-in-out infinite', marginBottom: '12px' }} />
      <div style={{ height: '30px', width: '40%', borderRadius: '4px', background: 'var(--color-bg-tertiary)', animation: 'pulse 1.5s ease-in-out infinite', animationDelay: '0.2s' }} />
    </div>
  )
}

function Dashboard() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const { user } = useAuthStore()
  const { balance, totalUsed, usagePercentage, subscription, fetchBalance, fetchSubscription } = useCreditStore()

  const [campaigns, setCampaigns] = useState([])
  const [isLoadingCampaigns, setIsLoadingCampaigns] = useState(true)
  const [campaignError, setCampaignError] = useState(null)

  useEffect(() => {
    fetchBalance()
    fetchSubscription()
    loadCampaigns()
  }, [])

  const loadCampaigns = async () => {
    setIsLoadingCampaigns(true)
    setCampaignError(null)
    try {
      const res = await campaignsAPI.list()
      setCampaigns(res.data || [])
    } catch (err) {
      setCampaignError(t('common.error'))
      setCampaigns([])
    } finally {
      setIsLoadingCampaigns(false)
    }
  }

  const completedCampaigns = campaigns.filter(c => c.status === 'completed')
  const thisMonthCampaigns = completedCampaigns.filter(c => {
    const d = new Date(c.created_at); const now = new Date()
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear()
  })

  const conversions = completedCampaigns.map(c => getConversionFromSummary(c.results_summary)).filter(v => v !== null)
  const avgConversion = conversions.length > 0 ? Math.round(conversions.reduce((a, b) => a + b, 0) / conversions.length) : 0
  const responseTimes = completedCampaigns.map(c => c.results_summary?.response_time_ms).filter(v => v != null)
  const avgResponseTime = responseTimes.length > 0 ? Math.round(responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length / 1000) : 0
  const totalPersonas = completedCampaigns.reduce((sum, c) => sum + (c.persona_count || 0), 0)

  // Chart data
  const convLabel = t('common.conversion')
  const conversionTrendData = completedCampaigns
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    .slice(-12)
    .map((c, i) => ({ name: c.name?.slice(0, 15) || `Test ${i + 1}`, [convLabel]: getConversionFromSummary(c.results_summary) || 0 }))

  const typeCounts = {}
  typeCounts[t('testTypes.single')] = 0
  typeCounts[t('testTypes.ab')] = 0
  typeCounts[t('testTypes.multi')] = 0
  completedCampaigns.forEach(c => { const l = getTestTypeLabel(c.type, t); if (typeCounts[l] !== undefined) typeCounts[l]++ })
  const typeDistributionData = Object.entries(typeCounts).filter(([, v]) => v > 0).map(([name, value]) => ({ name, value }))

  const regionCounts = {}
  completedCampaigns.forEach(c => { const r = c.region || 'TR'; regionCounts[r] = (regionCounts[r] || 0) + 1 })
  const testsLabel = t('dashboard.recentTests').split(' ')[0]
  const regionData = Object.entries(regionCounts).map(([name, val]) => ({ name: `${regionFlags[name] || ''} ${name}`, [testsLabel]: val }))

  const creditByDate = {}
  completedCampaigns.forEach(c => {
    const date = new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    creditByDate[date] = (creditByDate[date] || 0) + (c.credits_consumed || 0)
  })
  const creditsLabel = t('common.credits')
  const creditUsageData = Object.entries(creditByDate).map(([date, val]) => ({ date, [creditsLabel]: val }))

  const hasChartData = completedCampaigns.length >= 2
  const planSlug = subscription?.plan_slug || 'starter'
  const isDisposable = planSlug === 'disposable'
  const isBasicTier = planSlug === 'starter' || planSlug === 'disposable'
  const canSeeCharts = !isBasicTier

  const stats = [
    { title: t('dashboard.stats.credits'), value: balance || 0, total: subscription?.credits_monthly || 0, icon: CreditCard, showProgress: true, color: '#06B6D4' },
    { title: t('dashboard.stats.testsThisMonth'), value: thisMonthCampaigns.length, icon: TestTube, subtitle: t('dashboard.stats.totalCount', { count: completedCampaigns.length }), color: '#8B5CF6' },
    { title: t('dashboard.stats.avgConversion'), value: conversions.length > 0 ? `${avgConversion}%` : '—', icon: TrendingUp, subtitle: conversions.length > 0 ? t('dashboard.stats.fromTests', { count: conversions.length }) : t('dashboard.stats.noData'), color: '#10B981' },
    { title: t('dashboard.stats.personasTested'), value: totalPersonas, icon: Users, subtitle: avgResponseTime > 0 ? t('dashboard.stats.avgResponseTime', { seconds: avgResponseTime }) : '', color: '#F59E0B' },
  ]

  const recentTests = completedCampaigns.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 5)

  const quickActions = [
    { title: t('dashboard.actions.campaignTest'), description: t('dashboard.actions.campaignTestDesc'), icon: TestTube, href: '/dashboard/test', color: '#06B6D4' },
    { title: t('dashboard.actions.abCompare'), description: t('dashboard.actions.abCompareDesc'), icon: Swords, href: '/dashboard/ab', color: '#8B5CF6' },
    { title: t('dashboard.actions.multiCompare'), description: t('dashboard.actions.multiCompareDesc'), icon: LayoutGrid, href: '/dashboard/multi', color: '#3B82F6', badge: 'Business+' },
  ]

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

        {/* Welcome */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          style={{ marginBottom: '36px', padding: '28px 32px', borderRadius: '16px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.08), rgba(139, 92, 246, 0.08))', border: '1px solid rgba(6, 182, 212, 0.12)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h1 style={{ fontSize: '26px', fontWeight: '700', marginBottom: '4px' }}>{t('dashboard.welcomeBack', { name: user?.name?.split(' ')[0] || '' })} 👋</h1>
              <p style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>
                {subscription ? t('dashboard.onPlan', { plan: subscription.plan_name, credits: balance }) : t('dashboard.selectPlan')}
              </p>
            </div>
            {subscription && (
              <div style={{ padding: '8px 16px', borderRadius: '8px', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)', fontSize: '12px', fontWeight: '600', color: 'var(--color-accent-cyan)' }}>
                {subscription.plan_name}
              </div>
            )}
          </div>
        </motion.div>

        {/* Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '36px' }}>
          {isLoadingCampaigns ? <><SkeletonCard /><SkeletonCard /><SkeletonCard /><SkeletonCard /></> : stats.map((stat, i) => {
            const Icon = stat.icon
            return (
              <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
                className="card" style={{ padding: '22px', borderTop: `3px solid ${stat.color}`, position: 'relative', overflow: 'hidden' }}>
                <div style={{ position: 'absolute', top: '-20px', right: '-20px', width: '70px', height: '70px', borderRadius: '50%', background: `${stat.color}08`, filter: 'blur(20px)' }} />
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '10px', position: 'relative' }}>
                  <div>
                    <p style={{ color: 'var(--color-text-muted)', fontSize: '12px', marginBottom: '4px', fontWeight: '500' }}>{stat.title}</p>
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
                      <span style={{ fontSize: '28px', fontWeight: '700' }}>{stat.value}</span>
                      {stat.total > 0 && <span style={{ color: 'var(--color-text-muted)', fontSize: '13px' }}>/ {stat.total}</span>}
                    </div>
                  </div>
                  <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: `${stat.color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Icon style={{ width: '18px', height: '18px', color: stat.color }} />
                  </div>
                </div>
                {stat.subtitle && <div style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{stat.subtitle}</div>}
                {stat.showProgress && stat.total > 0 && (
                  <div style={{ height: '5px', borderRadius: '3px', background: 'var(--color-bg-tertiary)', marginTop: '12px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${Math.min(100, (stat.value / stat.total) * 100)}%`, borderRadius: '3px', transition: 'width 1s ease', background: `linear-gradient(90deg, ${stat.color}, #8B5CF6)` }} />
                  </div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* Charts */}
        {!isLoadingCampaigns && hasChartData && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} style={{ marginBottom: '36px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h2 style={{ fontSize: '18px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Activity style={{ width: '18px', height: '18px', color: 'var(--color-accent-cyan)' }} /> {t('dashboard.analytics')}
              </h2>
              {!canSeeCharts && <Link to="/dashboard/profile" style={{ fontSize: '12px', color: 'var(--color-accent-cyan)', textDecoration: 'none', fontWeight: '500' }}>{t('dashboard.upgradeForAnalytics')}</Link>}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: canSeeCharts ? '2fr 1fr' : '1fr', gap: '16px' }}>
              <div className="card" style={{ padding: '20px' }}>
                <h3 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{t('dashboard.conversionTrend')}</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={conversionTrendData}>
                    <defs><linearGradient id="convGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#06B6D4" stopOpacity={0.3} /><stop offset="95%" stopColor="#06B6D4" stopOpacity={0} /></linearGradient></defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} domain={[0, 100]} />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)', stroke: 'rgba(255,255,255,0.1)' }} />
                    <Area type="monotone" dataKey={convLabel} stroke="#06B6D4" strokeWidth={2} fill="url(#convGrad)" dot={{ fill: '#06B6D4', r: 3 }} activeDot={{ r: 5 }} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {canSeeCharts ? (
                <div className="card" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{t('dashboard.testDistribution')}</h3>
                  {typeDistributionData.length > 0 ? (
                    <>
                      <ResponsiveContainer width="100%" height={170}>
                        <PieChart><Pie data={typeDistributionData} cx="50%" cy="50%" innerRadius={48} outerRadius={70} paddingAngle={5} dataKey="value">
                          {typeDistributionData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                        </Pie><Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)', stroke: 'rgba(255,255,255,0.1)' }} /></PieChart>
                      </ResponsiveContainer>
                      <div style={{ display: 'flex', justifyContent: 'center', gap: '14px', marginTop: '4px' }}>
                        {typeDistributionData.map((d, i) => (
                          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: CHART_COLORS[i] }} />{d.name} ({d.value})
                          </div>
                        ))}
                      </div>
                    </>
                  ) : <div style={{ height: '170px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)', fontSize: '13px' }}>{t('dashboard.runDifferentTypes')}</div>}
                </div>
              ) : (
                <div className="card" style={{ padding: '20px', position: 'relative', overflow: 'hidden' }}>
                  <div style={{ position: 'absolute', inset: 0, background: 'rgba(10, 14, 26, 0.75)', backdropFilter: 'blur(4px)', zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
                    <Zap style={{ width: '22px', height: '22px', color: '#F59E0B', marginBottom: '6px' }} />
                    <p style={{ fontSize: '13px', fontWeight: '600' }}>{t('dashboard.proFeature')}</p>
                    <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>{t('dashboard.upgradeForCharts')}</p>
                  </div>
                  <div style={{ width: '100%', height: '200px', background: 'var(--color-bg-tertiary)', borderRadius: '8px', opacity: 0.3 }} />
                </div>
              )}
            </div>

            {canSeeCharts && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
                <div className="card" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{t('dashboard.testsByRegion')}</h3>
                  {regionData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={180}>
                      <BarChart data={regionData} barSize={32}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="name" tick={{ fill: '#6B7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)', stroke: 'rgba(255,255,255,0.1)' }} />
                        <Bar dataKey={testsLabel} radius={[6, 6, 0, 0]}>{regionData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}</Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  ) : <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>{t('common.noData')}</div>}
                </div>
                <div className="card" style={{ padding: '20px' }}>
                  <h3 style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{t('dashboard.creditUsage')}</h3>
                  {creditUsageData.length > 0 ? (
                    <ResponsiveContainer width="100%" height={180}>
                      <AreaChart data={creditUsageData}>
                        <defs><linearGradient id="creditGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.3} /><stop offset="95%" stopColor="#8B5CF6" stopOpacity={0} /></linearGradient></defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="date" tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fill: '#6B7280', fontSize: 10 }} axisLine={false} tickLine={false} allowDecimals={false} />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.05)', stroke: 'rgba(255,255,255,0.1)' }} />
                        <Area type="monotone" dataKey={creditsLabel} stroke="#8B5CF6" strokeWidth={2} fill="url(#creditGrad)" dot={{ fill: '#8B5CF6', r: 3 }} />
                      </AreaChart>
                    </ResponsiveContainer>
                  ) : <div style={{ height: '180px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--color-text-muted)' }}>{t('common.noData')}</div>}
                </div>
              </div>
            )}
          </motion.div>
        )}

        {/* Quick Actions */}
        <div style={{ marginBottom: '36px' }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>{t('dashboard.quickActions')}</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            {quickActions.map((action, i) => {
              const Icon = action.icon
              return (
                <motion.div key={i} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 + i * 0.08 }}>
                  <Link to={action.href} style={{ textDecoration: 'none' }}>
                    <div className="card" style={{ padding: '24px', cursor: 'pointer', transition: 'all 0.2s', borderLeft: `3px solid ${action.color}` }}
                      onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = `0 8px 24px ${action.color}15` }}
                      onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'none' }}>
                      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '14px' }}>
                        <div style={{ width: '44px', height: '44px', borderRadius: '12px', background: `${action.color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Icon style={{ width: '22px', height: '22px', color: action.color }} />
                        </div>
                        {action.badge && <span style={{ padding: '3px 8px', borderRadius: '9999px', fontSize: '10px', fontWeight: '600', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--color-accent-cyan)' }}>{action.badge}</span>}
                      </div>
                      <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px', color: 'var(--color-text-primary)' }}>{action.title}</h3>
                      <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', lineHeight: '1.4' }}>{action.description}</p>
                    </div>
                  </Link>
                </motion.div>
              )
            })}
          </div>
        </div>

        {/* Recent Tests */}
        <div style={{ marginBottom: '36px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600' }}>{t('dashboard.recentTests')}</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              {!isLoadingCampaigns && <button onClick={loadCampaigns} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', color: 'var(--color-text-muted)' }}><RefreshCw style={{ width: '15px', height: '15px' }} /></button>}
              <Link to="/dashboard/history" style={{ fontSize: '12px', color: 'var(--color-accent-cyan)', textDecoration: 'none', fontWeight: '500' }}>{t('common.viewAll')} →</Link>
            </div>
          </div>

          {isLoadingCampaigns ? (
            <div className="card" style={{ padding: '60px', textAlign: 'center' }}>
              <Loader2 style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
              <p style={{ color: 'var(--color-text-muted)', fontSize: '14px' }}>{t('dashboard.loadingCampaigns')}</p>
            </div>
          ) : campaignError ? (
            <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
              <AlertCircle style={{ width: '28px', height: '28px', color: 'var(--color-danger)', margin: '0 auto 12px' }} />
              <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', marginBottom: '12px' }}>{campaignError}</p>
              <button onClick={loadCampaigns} className="btn btn-secondary" style={{ fontSize: '13px' }}>{t('common.tryAgain')}</button>
            </div>
          ) : recentTests.length === 0 ? (
            <div className="card" style={{ padding: '48px', textAlign: 'center' }}>
              <BarChart3 style={{ width: '36px', height: '36px', color: 'var(--color-text-muted)', margin: '0 auto 12px' }} />
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '6px' }}>{t('dashboard.noTestsYet')}</h3>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '13px', marginBottom: '20px' }}>{t('dashboard.noTestsDesc')}</p>
              <Link to="/dashboard/test" className="btn btn-primary" style={{ padding: '10px 20px', fontSize: '13px' }}>{t('dashboard.runFirstTest')}</Link>
            </div>
          ) : (
            <div className="card" style={{ overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                    {[t('common.campaign'), t('common.type'), t('common.region'), t('common.conversion'), t('common.personas'), t('common.date')].map(h => (
                      <th key={h} style={{ textAlign: 'left', padding: '14px 18px', fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {recentTests.map((c) => {
                    const conv = getConversionFromSummary(c.results_summary)
                    return (
                      <tr key={c.id} style={{ borderBottom: '1px solid var(--color-border)', cursor: 'pointer', transition: 'background 0.15s' }}
                        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-bg-tertiary)'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                        onClick={() => navigate('/dashboard/history')}>
                        <td style={{ padding: '14px 18px', fontWeight: '500', fontSize: '13px', maxWidth: '220px' }}><div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.name}</div></td>
                        <td style={{ padding: '14px 18px' }}><span className={`badge ${getTestTypeBadge(c.type)}`}>{getTestTypeLabel(c.type, t)}</span></td>
                        <td style={{ padding: '14px 18px', fontSize: '13px' }}>{regionFlags[c.region]} {c.region}</td>
                        <td style={{ padding: '14px 18px' }}>
                          {conv !== null ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                              <div style={{ width: '70px', height: '5px', borderRadius: '3px', background: 'var(--color-bg-tertiary)' }}>
                                <div style={{ height: '100%', borderRadius: '3px', background: conv >= 60 ? 'var(--color-success)' : conv >= 40 ? 'var(--color-warning)' : 'var(--color-danger)', width: `${conv}%` }} />
                              </div>
                              <span style={{ fontSize: '12px', fontWeight: '500' }}>{conv}%</span>
                            </div>
                          ) : <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>—</span>}
                        </td>
                        <td style={{ padding: '14px 18px', fontSize: '13px', color: 'var(--color-text-muted)' }}>{c.persona_count}</td>
                        <td style={{ padding: '14px 18px', color: 'var(--color-text-muted)', fontSize: '12px' }}>{timeAgo(c.created_at, t)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Usage Summary */}
        {subscription && completedCampaigns.length > 0 && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.4 }} className="card" style={{ padding: '22px', marginBottom: '36px' }}>
            <h3 style={{ fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '14px' }}>{t('dashboard.usageSummary')}</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
              {[
                { label: t('dashboard.creditsUsed'), value: totalUsed },
                { label: t('dashboard.usageRate'), value: `${Math.round(usagePercentage || 0)}%` },
                { label: isDisposable ? t('dashboard.planType') : t('dashboard.planExpires'), value: isDisposable ? t('dashboard.oneTime') : (subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '—') },
                { label: t('dashboard.totalCampaigns'), value: campaigns.length },
              ].map((s, i) => (
                <div key={i}>
                  <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginBottom: '2px' }}>{s.label}</p>
                  <p style={{ fontSize: '20px', fontWeight: '700' }}>{s.value}</p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Upgrade CTA */}
        {(!subscription || isBasicTier) && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5 }}
            style={{ padding: '24px 28px', borderRadius: '14px', marginBottom: '36px', background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(139, 92, 246, 0.1))', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: 'linear-gradient(135deg, #06B6D4, #8B5CF6)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Zap style={{ width: '24px', height: '24px', color: 'white' }} />
                </div>
                <div>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '2px' }}>
                    {isDisposable ? t('dashboard.getSubscription') : t('dashboard.upgradeToPro')}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
                    {isDisposable ? t('dashboard.getSubscriptionDesc') : t('dashboard.upgradeToProDesc')}
                  </p>
                </div>
              </div>
              <Link to="/dashboard/profile" className="btn btn-primary" style={{ padding: '10px 20px', fontSize: '13px' }}>
                {t('dashboard.viewPlans')} <ArrowRight style={{ width: '15px', height: '15px' }} />
              </Link>
            </div>
          </motion.div>
        )}

        {!subscription && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.3 }} className="card" style={{ padding: '40px', textAlign: 'center', marginBottom: '36px' }}>
            <CreditCard style={{ width: '36px', height: '36px', color: 'var(--color-accent-cyan)', margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '6px' }}>{t('dashboard.choosePlan')}</h3>
            <p style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '20px' }}>{t('dashboard.choosePlanDesc')}</p>
            <Link to="/pricing" className="btn btn-primary" style={{ padding: '10px 24px' }}>{t('dashboard.viewPlans')}</Link>
          </motion.div>
        )}
      </div>

      <style>{`
        @keyframes pulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 0.8; } }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </DashboardLayout>
  )
}

export default Dashboard
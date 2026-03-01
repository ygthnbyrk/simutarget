import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Search, Trash2, History as HistoryIcon, Loader2, X, TrendingUp, Users, CheckCircle, XCircle, Trophy, ChevronDown, ChevronUp, FileText, MessageSquare, BarChart3, AlertCircle, FileDown } from 'lucide-react'
import DashboardLayout from '../components/layout/DashboardLayout'
import { campaignsAPI } from '../services/api'
import useCreditStore from '../stores/creditStore'
import { translatePersonaValue, getLocalizedReasoning } from '../utils/personaTranslations'
import { downloadCampaignPDF } from '../utils/pdfDownload'

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

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function isYes(decision) {
  if (!decision) return false
  const d = decision.toUpperCase()
  return d === 'YES' || d === 'EVET'
}

function getConversion(summary) {
  if (!summary) return null
  if (summary.conversion_rate !== undefined) return Math.round(summary.conversion_rate)
  if (summary.a_percentage !== undefined) return Math.round(Math.max(summary.a_percentage, summary.b_percentage))
  if (summary.percentages) {
    const vals = Object.values(summary.percentages)
    return vals.length > 0 ? Math.round(Math.max(...vals)) : null
  }
  return null
}

function getTypeLabel(type, t) {
  if (!type) return t('testTypes.single')
  const tt = type.toLowerCase()
  if (tt === 'single') return t('testTypes.single')
  if (tt === 'ab' || tt === 'compare') return t('testTypes.ab')
  if (tt === 'multi') return t('testTypes.multi')
  return type
}

function getTypeBadgeClass(type) {
  if (!type) return 'badge-success'
  const t = type.toLowerCase()
  if (t === 'ab' || t === 'compare') return 'badge-info'
  if (t === 'multi') return 'badge-warning'
  return 'badge-success'
}

const regionFlags = { TR: '🇹🇷', US: '🇺🇸', EU: '🇪🇺', MENA: '🌍' }

// ── Campaign Content Display ─────────────────────────

function CampaignContent({ content, type, t }) {
  if (!content) return null
  const typeLabel = getTypeLabel(type, t)
  const isSingle = typeLabel === t('testTypes.single')
  const isAB = typeLabel === t('testTypes.ab')
  const isMulti = typeLabel === t('testTypes.multi')

  if (isSingle) {
    const text = content.text || content.text_a || Object.values(content)[0] || ''
    return (
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <MessageSquare style={{ width: '16px', height: '16px', color: 'var(--color-accent-cyan)' }} />
          <span style={{ fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)' }}>{t('detail.campaignContent')}</span>
        </div>
        <div style={{ padding: '16px 20px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.06)', border: '1px solid rgba(6, 182, 212, 0.15)', fontSize: '14px', lineHeight: '1.7', color: 'var(--color-text-secondary)' }}>{text}</div>
      </div>
    )
  }

  if (isAB) {
    const textA = content.text_a || content.text || ''
    const textB = content.text_b || ''
    return (
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <MessageSquare style={{ width: '16px', height: '16px', color: 'var(--color-accent-cyan)' }} />
          <span style={{ fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)' }}>{t('detail.campaignVariants')}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
          <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(6, 182, 212, 0.06)', border: '1px solid rgba(6, 182, 212, 0.2)' }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--color-accent-cyan)', marginBottom: '8px', letterSpacing: '0.05em' }}>{t('detail.optionA')}</div>
            <div style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--color-text-secondary)' }}>{textA}</div>
          </div>
          <div style={{ padding: '16px', borderRadius: '10px', background: 'rgba(139, 92, 246, 0.06)', border: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <div style={{ fontSize: '12px', fontWeight: '700', color: '#8B5CF6', marginBottom: '8px', letterSpacing: '0.05em' }}>{t('detail.optionB')}</div>
            <div style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--color-text-secondary)' }}>{textB}</div>
          </div>
        </div>
      </div>
    )
  }

  if (isMulti) {
    const options = Object.entries(content).filter(([k]) => k !== 'type')
    const colors = ['#06B6D4', '#8B5CF6', '#F59E0B', '#10B981']
    return (
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <MessageSquare style={{ width: '16px', height: '16px', color: 'var(--color-accent-cyan)' }} />
          <span style={{ fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--color-text-muted)' }}>{t('detail.campaignOptions', { count: options.length })}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: options.length <= 2 ? '1fr 1fr' : 'repeat(2, 1fr)', gap: '12px' }}>
          {options.map(([key, val], i) => (
            <div key={key} style={{ padding: '16px', borderRadius: '10px', background: `${colors[i % colors.length]}08`, border: `1px solid ${colors[i % colors.length]}30` }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: colors[i % colors.length], marginBottom: '8px', letterSpacing: '0.05em' }}>{t('detail.option', { key })}</div>
              <div style={{ fontSize: '13px', lineHeight: '1.7', color: 'var(--color-text-secondary)' }}>{val}</div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return null
}

// ── Main Component ───────────────────────────────────

function History() {
  const { t, i18n } = useTranslation()
  const { subscription } = useCreditStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [filterType, setFilterType] = useState('all')
  const [campaigns, setCampaigns] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCampaign, setSelectedCampaign] = useState(null)
  const [detailData, setDetailData] = useState(null)
  const [isDetailLoading, setIsDetailLoading] = useState(false)
  const [expandedPersonas, setExpandedPersonas] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [pdfLoading, setPdfLoading] = useState(false)

  useEffect(() => { fetchCampaigns() }, [])

  const fetchCampaigns = async () => {
    setIsLoading(true)
    try {
      const res = await campaignsAPI.list()
      setCampaigns(res.data || [])
    } catch (err) {
      setError(t('common.error'))
    } finally {
      setIsLoading(false)
    }
  }

  const openDetail = async (campaign) => {
    setSelectedCampaign(campaign)
    setDetailData(null)
    setIsDetailLoading(true)
    setExpandedPersonas(false)
    try {
      const res = await campaignsAPI.results(campaign.id)
      setDetailData(res.data)
    } catch (err) {
      setDetailData({ error: t('common.error') })
    } finally {
      setIsDetailLoading(false)
    }
  }

  const closeDetail = () => { setSelectedCampaign(null); setDetailData(null) }

  const handleDelete = async (campaignId) => {
    setIsDeleting(true)
    try {
      await campaignsAPI.delete(campaignId)
      setCampaigns(prev => prev.filter(c => c.id !== campaignId))
      setDeleteConfirm(null)
      if (selectedCampaign?.id === campaignId) closeDetail()
    } catch (err) { /* ignore */ } finally { setIsDeleting(false) }
  }

  const filtered = campaigns.filter(c => {
    const typeRaw = c.type?.toLowerCase() || 'single'
    const matchType = filterType === 'all' || typeRaw === filterType || (filterType === 'a/b' && (typeRaw === 'ab' || typeRaw === 'compare'))
    const matchSearch = !searchQuery || c.name.toLowerCase().includes(searchQuery.toLowerCase())
    return matchType && matchSearch
  })

  const completed = campaigns.filter(c => c.status === 'completed')
  const totalPersonas = completed.reduce((s, c) => s + (c.persona_count || 0), 0)
  const totalCredits = completed.reduce((s, c) => s + (c.credits_consumed || 0), 0)
  const conversions = completed.map(c => getConversion(c.results_summary)).filter(v => v !== null)
  const avgConv = conversions.length > 0 ? Math.round(conversions.reduce((a, b) => a + b, 0) / conversions.length) : 0

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>

        {/* Header */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} style={{ marginBottom: '32px' }}>
          <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
            <HistoryIcon style={{ width: '28px', height: '28px', display: 'inline', marginRight: '10px', verticalAlign: 'middle', color: 'var(--color-accent-cyan)' }} />
            {t('history.title')}
          </h1>
          <p style={{ color: 'var(--color-text-muted)' }}>{t('history.subtitle')}</p>
        </motion.div>

        {/* Summary Stats */}
        {completed.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
            {[
              { label: t('history.stats.totalTests'), value: completed.length, icon: BarChart3, color: '#06B6D4' },
              { label: t('history.stats.totalPersonas'), value: totalPersonas, icon: Users, color: '#8B5CF6' },
              { label: t('history.stats.creditsUsed'), value: totalCredits, icon: FileText, color: '#F59E0B' },
              { label: t('history.stats.avgConversion'), value: `${avgConv}%`, icon: TrendingUp, color: '#10B981' },
            ].map((s, i) => {
              const Icon = s.icon
              return (
                <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.05 }}
                  className="card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: `${s.color}15`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Icon style={{ width: '20px', height: '20px', color: s.color }} />
                  </div>
                  <div>
                    <div style={{ fontSize: '22px', fontWeight: '700' }}>{s.value}</div>
                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{s.label}</div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        )}

        {/* Filters */}
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', flexWrap: 'wrap' }}>
          <div style={{ position: 'relative', flex: '1', minWidth: '200px', maxWidth: '400px' }}>
            <Search style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', width: '18px', height: '18px', color: 'var(--color-text-muted)' }} />
            <input type="text" placeholder={t('history.searchPlaceholder')} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
              style={{ width: '100%', padding: '12px 12px 12px 42px', borderRadius: '10px', background: 'var(--color-bg-tertiary)', border: '1px solid var(--color-border)', color: 'var(--color-text-primary)', fontSize: '14px', outline: 'none' }} />
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {[
              { key: 'all', label: t('history.filterAll') },
              { key: 'single', label: t('testTypes.single') },
              { key: 'a/b', label: t('testTypes.ab') },
              { key: 'multi', label: t('testTypes.multi') },
            ].map(f => (
              <button key={f.key} onClick={() => setFilterType(f.key)} style={{
                padding: '10px 18px', borderRadius: '10px', fontSize: '13px', fontWeight: '500', cursor: 'pointer',
                background: filterType === f.key ? 'var(--color-accent-cyan)' : 'var(--color-bg-tertiary)',
                color: filterType === f.key ? 'white' : 'var(--color-text-muted)',
                border: '1px solid ' + (filterType === f.key ? 'var(--color-accent-cyan)' : 'var(--color-border)'),
                transition: 'all 0.15s',
              }}>{f.label}</button>
            ))}
          </div>
        </div>

        {/* Campaign Table */}
        {isLoading ? (
          <div className="card" style={{ padding: '60px', textAlign: 'center' }}>
            <Loader2 style={{ width: '32px', height: '32px', color: 'var(--color-accent-cyan)', animation: 'spin 1s linear infinite', margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--color-text-muted)' }}>{t('history.loadingHistory')}</p>
          </div>
        ) : error ? (
          <div className="card" style={{ padding: '40px', textAlign: 'center' }}>
            <AlertCircle style={{ width: '32px', height: '32px', color: 'var(--color-danger)', margin: '0 auto 12px' }} />
            <p style={{ color: 'var(--color-text-muted)', marginBottom: '16px' }}>{error}</p>
            <button onClick={fetchCampaigns} className="btn btn-secondary">{t('common.tryAgain')}</button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="card" style={{ padding: '60px', textAlign: 'center' }}>
            <HistoryIcon style={{ width: '48px', height: '48px', color: 'var(--color-text-muted)', margin: '0 auto 16px' }} />
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>
              {campaigns.length === 0 ? t('history.noTestsYet') : t('history.noMatchingTests')}
            </h3>
            <p style={{ color: 'var(--color-text-muted)' }}>
              {campaigns.length === 0 ? t('history.noTestsDesc') : t('history.noMatchingDesc')}
            </p>
          </div>
        ) : (
          <div className="card" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  {[t('common.campaign'), t('common.type'), t('common.region'), t('common.results'), t('common.personas'), t('common.date'), t('common.actions')].map((h, i) => (
                    <th key={h} style={{ textAlign: i === 6 ? 'right' : 'left', padding: '16px 20px', fontSize: '13px', fontWeight: '600', color: 'var(--color-text-muted)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((campaign) => {
                  const conv = getConversion(campaign.results_summary)
                  return (
                    <tr key={campaign.id} onClick={() => campaign.status === 'completed' && openDetail(campaign)}
                      style={{ borderBottom: '1px solid var(--color-border)', cursor: campaign.status === 'completed' ? 'pointer' : 'default', transition: 'background 0.15s' }}
                      onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-bg-tertiary)'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                      <td style={{ padding: '16px 20px', fontWeight: '500', fontSize: '14px', maxWidth: '220px' }}><div style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{campaign.name}</div></td>
                      <td style={{ padding: '16px 20px' }}><span className={`badge ${getTypeBadgeClass(campaign.type)}`}>{getTypeLabel(campaign.type, t)}</span></td>
                      <td style={{ padding: '16px 20px', fontSize: '14px' }}>{regionFlags[campaign.region]} {campaign.region}</td>
                      <td style={{ padding: '16px 20px' }}>
                        {campaign.status === 'completed' && conv !== null ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <div style={{ width: '80px', height: '6px', borderRadius: '3px', background: 'var(--color-bg-tertiary)' }}>
                              <div style={{ height: '100%', borderRadius: '3px', background: conv >= 60 ? 'var(--color-success)' : conv >= 40 ? 'var(--color-warning)' : 'var(--color-danger)', width: `${conv}%` }} />
                            </div>
                            <span style={{ fontSize: '13px', fontWeight: '500' }}>{conv}%</span>
                          </div>
                        ) : <span className={`badge ${campaign.status === 'failed' ? 'badge-danger' : 'badge-warning'}`}>{campaign.status}</span>}
                      </td>
                      <td style={{ padding: '16px 20px', fontSize: '14px', color: 'var(--color-text-muted)' }}>{campaign.persona_count}</td>
                      <td style={{ padding: '16px 20px', fontSize: '13px', color: 'var(--color-text-muted)' }}>{timeAgo(campaign.created_at, t)}</td>
                      <td style={{ padding: '16px 20px', textAlign: 'right' }}>
                        <button onClick={(e) => { e.stopPropagation(); setDeleteConfirm(campaign.id) }}
                          style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '6px', color: 'var(--color-text-muted)', borderRadius: '6px', transition: 'color 0.15s' }}
                          onMouseEnter={(e) => e.currentTarget.style.color = 'var(--color-danger)'}
                          onMouseLeave={(e) => e.currentTarget.style.color = 'var(--color-text-muted)'}>
                          <Trash2 style={{ width: '16px', height: '16px' }} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirm Modal */}
      <AnimatePresence>
        {deleteConfirm && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={() => setDeleteConfirm(null)}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px' }}>
            <motion.div initial={{ scale: 0.9, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              style={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px', padding: '32px', maxWidth: '400px', width: '100%', textAlign: 'center' }}>
              <Trash2 style={{ width: '40px', height: '40px', color: 'var(--color-danger)', margin: '0 auto 16px' }} />
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '8px' }}>{t('history.deleteConfirm')}</h3>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '14px', marginBottom: '24px' }}>{t('history.deleteDesc')}</p>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                <button onClick={() => setDeleteConfirm(null)} className="btn btn-secondary" style={{ padding: '10px 24px' }}>{t('common.cancel')}</button>
                <button onClick={() => handleDelete(deleteConfirm)} disabled={isDeleting}
                  style={{ padding: '10px 24px', borderRadius: '10px', border: 'none', cursor: 'pointer', fontWeight: '600', background: 'var(--color-danger)', color: 'white', opacity: isDeleting ? 0.6 : 1 }}>
                  {isDeleting ? t('history.deleting') : t('common.delete')}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedCampaign && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            onClick={closeDetail}
            style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999, padding: '20px' }}>
            <motion.div initial={{ scale: 0.95, opacity: 0, y: 20 }} animate={{ scale: 1, opacity: 1, y: 0 }} exit={{ scale: 0.95, opacity: 0, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: '960px', width: '100%', maxHeight: '88vh', overflow: 'auto', padding: '0', background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px' }}>

              {/* Modal Header */}
              <div style={{ position: 'sticky', top: 0, background: '#1a1a2e', padding: '24px 32px', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', zIndex: 10, borderRadius: '16px 16px 0 0' }}>
                <div>
                  <h2 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '8px' }}>{selectedCampaign.name}</h2>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                    <span className={`badge ${getTypeBadgeClass(selectedCampaign.type)}`}>{getTypeLabel(selectedCampaign.type, t)}</span>
                    <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{regionFlags[selectedCampaign.region]} {selectedCampaign.region}</span>
                    <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{formatDate(selectedCampaign.created_at)}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {['pro', 'business', 'enterprise'].includes(subscription?.plan_slug) && selectedCampaign.status === 'completed' && (
                    <button
                      onClick={async (e) => {
                        e.stopPropagation()
                        setPdfLoading(true)
                        try { await downloadCampaignPDF(selectedCampaign.id, i18n.language) }
                        catch (err) { alert(err.message) }
                        finally { setPdfLoading(false) }
                      }}
                      disabled={pdfLoading}
                      style={{ display: 'flex', alignItems: 'center', gap: '6px', background: 'rgba(6, 182, 212, 0.15)', border: '1px solid rgba(6, 182, 212, 0.3)', borderRadius: '8px', color: 'var(--color-accent-cyan)', cursor: 'pointer', padding: '8px 14px', fontSize: '13px', fontWeight: '500' }}
                    >
                      {pdfLoading ? <Loader2 style={{ width: '14px', height: '14px', animation: 'spin 1s linear infinite' }} /> : <FileDown style={{ width: '14px', height: '14px' }} />}
                      PDF
                    </button>
                  )}
                  <button onClick={closeDetail} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text-muted)', padding: '4px' }}>
                    <X style={{ width: '24px', height: '24px' }} />
                  </button>
                </div>
              </div>

              {/* Modal Body */}
              <div style={{ padding: '28px 32px' }}>
                {isDetailLoading && (
                  <div style={{ textAlign: 'center', padding: '60px 0' }}>
                    <Loader2 style={{ width: '36px', height: '36px', color: 'var(--color-accent-cyan)', margin: '0 auto', animation: 'spin 1s linear infinite' }} />
                    <p style={{ marginTop: '12px', color: 'var(--color-text-muted)' }}>{t('common.loading')}</p>
                  </div>
                )}

                {detailData && !detailData.error && (
                  <>
                    <CampaignContent content={selectedCampaign.content} type={selectedCampaign.type} t={t} />

                    {detailData.summary && (
                      <>
                        {/* Single */}
                        {getTypeLabel(selectedCampaign.type, t) === t('testTypes.single') && (
                          <>
                            <div style={{ textAlign: 'center', marginBottom: '28px' }}>
                              <TrendingUp style={{ width: '36px', height: '36px', color: detailData.summary.conversion_rate >= 50 ? 'var(--color-success)' : 'var(--color-warning)', margin: '0 auto 8px auto' }} />
                              <div className="gradient-text" style={{ fontSize: '48px', fontWeight: '800' }}>{detailData.summary.conversion_rate?.toFixed(1)}%</div>
                              <div style={{ fontSize: '14px', color: 'var(--color-text-muted)' }}>{t('detail.conversionRate')}</div>
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '28px' }}>
                              {[
                                { icon: CheckCircle, value: detailData.summary.yes_count, label: t('detail.wouldBuy'), color: 'var(--color-success)' },
                                { icon: XCircle, value: detailData.summary.no_count, label: t('detail.wouldNot'), color: 'var(--color-danger)' },
                                { icon: Users, value: detailData.summary.total_personas, label: t('detail.total'), color: 'var(--color-accent-cyan)' },
                                { icon: TrendingUp, value: detailData.summary.avg_confidence, label: t('common.confidence'), color: '#F59E0B' },
                              ].map((s, i) => {
                                const Icon = s.icon
                                return (
                                  <div key={i} style={{ padding: '20px', background: 'var(--color-bg-tertiary)', borderRadius: '12px', textAlign: 'center' }}>
                                    <Icon style={{ width: '22px', height: '22px', color: s.color, margin: '0 auto 8px auto' }} />
                                    <div style={{ fontSize: '26px', fontWeight: '700' }}>{s.value}</div>
                                    <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>{s.label}</div>
                                  </div>
                                )
                              })}
                            </div>
                          </>
                        )}

                        {/* A/B */}
                        {getTypeLabel(selectedCampaign.type, t) === t('testTypes.ab') && (
                          <div style={{ marginBottom: '28px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '16px', alignItems: 'center', marginBottom: '20px' }}>
                              <div style={{ textAlign: 'center', padding: '24px', background: 'rgba(6, 182, 212, 0.08)', borderRadius: '12px', border: detailData.summary.a_percentage > detailData.summary.b_percentage ? '2px solid var(--color-accent-cyan)' : '1px solid transparent' }}>
                                <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--color-accent-cyan)', marginBottom: '8px' }}>{t('detail.optionA')}</div>
                                <div style={{ fontSize: '36px', fontWeight: '800' }}>{detailData.summary.a_percentage?.toFixed(1)}%</div>
                                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.votes', { count: detailData.summary.a_votes || 0 })}</div>
                                {detailData.summary.a_percentage > detailData.summary.b_percentage && <div style={{ marginTop: '8px' }}><Trophy style={{ width: '18px', height: '18px', color: '#F59E0B' }} /></div>}
                              </div>
                              <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--color-text-muted)' }}>{t('detail.vs')}</div>
                              <div style={{ textAlign: 'center', padding: '24px', background: 'rgba(139, 92, 246, 0.08)', borderRadius: '12px', border: detailData.summary.b_percentage > detailData.summary.a_percentage ? '2px solid #8B5CF6' : '1px solid transparent' }}>
                                <div style={{ fontSize: '12px', fontWeight: '700', color: '#8B5CF6', marginBottom: '8px' }}>{t('detail.optionB')}</div>
                                <div style={{ fontSize: '36px', fontWeight: '800' }}>{detailData.summary.b_percentage?.toFixed(1)}%</div>
                                <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.votes', { count: detailData.summary.b_votes || 0 })}</div>
                                {detailData.summary.b_percentage > detailData.summary.a_percentage && <div style={{ marginTop: '8px' }}><Trophy style={{ width: '18px', height: '18px', color: '#F59E0B' }} /></div>}
                              </div>
                            </div>
                            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                              <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.totalPersonas', { count: detailData.summary.total_personas })}</span>
                              <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.confidenceScore', { score: detailData.summary.avg_confidence })}</span>
                              {detailData.summary.neither_votes > 0 && <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.neither', { count: detailData.summary.neither_votes })}</span>}
                            </div>
                          </div>
                        )}

                        {/* Multi */}
                        {getTypeLabel(selectedCampaign.type, t) === t('testTypes.multi') && detailData.summary.percentages && (
                          <div style={{ marginBottom: '28px' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${Object.keys(detailData.summary.percentages).length}, 1fr)`, gap: '12px', marginBottom: '20px' }}>
                              {Object.entries(detailData.summary.percentages).sort(([,a],[,b]) => b - a).map(([key, pct], i) => {
                                const isWinner = i === 0
                                const colors = ['#06B6D4', '#8B5CF6', '#F59E0B', '#10B981']
                                return (
                                  <div key={key} style={{ textAlign: 'center', padding: '24px', borderRadius: '12px', background: `${colors[i % colors.length]}08`, border: isWinner ? `2px solid ${colors[i % colors.length]}` : '1px solid rgba(255,255,255,0.05)' }}>
                                    <div style={{ fontSize: '12px', fontWeight: '700', color: colors[i % colors.length], marginBottom: '8px' }}>{t('detail.option', { key })}</div>
                                    <div style={{ fontSize: '32px', fontWeight: '800' }}>{pct?.toFixed(1)}%</div>
                                    <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.votes', { count: detailData.summary.votes?.[key] || 0 })}</div>
                                    {isWinner && <div style={{ marginTop: '8px' }}><Trophy style={{ width: '18px', height: '18px', color: '#F59E0B' }} /></div>}
                                  </div>
                                )
                              })}
                            </div>
                            <div style={{ display: 'flex', gap: '16px', justifyContent: 'center' }}>
                              <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.totalPersonas', { count: detailData.summary.total_personas })}</span>
                              <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('detail.confidenceScore', { score: detailData.summary.avg_confidence })}</span>
                            </div>
                          </div>
                        )}

                        <div style={{ textAlign: 'center', padding: '12px', color: 'var(--color-text-muted)', fontSize: '13px', marginBottom: '24px', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '16px' }}>
                          {t('detail.responseTime', { time: (detailData.summary.response_time_ms / 1000).toFixed(1) })} • {t('detail.creditsUsedCount', { count: detailData.credits_consumed || selectedCampaign.credits_consumed })}
                        </div>
                      </>
                    )}

                    {/* Persona Responses */}
                    {detailData.persona_responses?.length > 0 && (
                      <div>
                        <button onClick={() => setExpandedPersonas(!expandedPersonas)}
                          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', background: 'var(--color-bg-tertiary)', borderRadius: '12px', border: 'none', cursor: 'pointer', color: 'var(--color-text-primary)', fontSize: '15px', fontWeight: '600' }}>
                          <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Users style={{ width: '18px', height: '18px' }} />
                            {t('detail.personaResponses', { count: detailData.persona_responses.length })}
                          </span>
                          {expandedPersonas ? <ChevronUp style={{ width: '18px', height: '18px' }} /> : <ChevronDown style={{ width: '18px', height: '18px' }} />}
                        </button>

                        {expandedPersonas && (
                          <div style={{ marginTop: '12px', overflow: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                              <thead>
                                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                                  {[t('detail.name'), t('detail.age'), t('detail.city'), t('detail.income'), t('detail.decision'), t('detail.conf'), t('detail.reasoning')].map(h => (
                                    <th key={h} style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)', fontWeight: '600' }}>{h}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {detailData.persona_responses.map((r, i) => (
                                  <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                                    <td style={{ padding: '12px 8px', fontWeight: '500' }}>{r.persona_data?.name}</td>
                                    <td style={{ padding: '12px 8px', textAlign: 'center' }}>{r.persona_data?.age}</td>
                                    <td style={{ padding: '12px 8px' }}>{r.persona_data?.city}</td>
                                    <td style={{ padding: '12px 8px' }}>{translatePersonaValue(r.persona_data?.income_level, i18n.language)}</td>
                                    <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                                      <span style={{
                                        padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: '600',
                                        background: isYes(r.decision) ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
                                        color: isYes(r.decision) ? 'var(--color-success)' : 'var(--color-danger)',
                                      }}>
                                        {isYes(r.decision) ? t('common.yes') : t('common.no')}
                                      </span>
                                    </td>
                                    <td style={{ padding: '12px 8px', textAlign: 'center' }}>{r.confidence}/10</td>
                                    <td style={{ padding: '12px 8px', maxWidth: '250px', fontSize: '12px', color: 'var(--color-text-secondary)', lineHeight: '1.5' }}>{getLocalizedReasoning(r.reasoning, i18n.language)}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    )}
                  </>
                )}

                {detailData?.error && <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-danger)' }}>{detailData.error}</div>}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </DashboardLayout>
  )
}

export default History

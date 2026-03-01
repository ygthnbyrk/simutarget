import { useState } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { LayoutGrid, Loader2, XCircle, Trophy, Users, TrendingUp, Plus, Trash2, Lock, FileDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../components/layout/DashboardLayout'
import PersonaFilters, { cleanFiltersForAPI } from '../components/PersonaFilters'
import useCreditStore from '../stores/creditStore'
import { campaignsAPI } from '../services/api'
import { getLocalizedReasoning } from '../utils/personaTranslations'
import { downloadCampaignPDF } from '../utils/pdfDownload'

function MultiCompare() {
  const { balance, subscription, fetchBalance, fetchSubscription } = useCreditStore()
  const { t, i18n } = useTranslation()
  const hasAccess = subscription && ['business', 'enterprise'].includes(subscription.plan_slug)

  const [testName, setTestName] = useState('')
  const [campaigns, setCampaigns] = useState(['', '', ''])
  const [region, setRegion] = useState('TR')
  const [personaCount, setPersonaCount] = useState(25)
  const [filters, setFilters] = useState({})
  const [pdfLoading, setPdfLoading] = useState(false)
  const [isTestRunning, setIsTestRunning] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [error, setError] = useState(null)

  const regions = [
    { code: 'TR', name: t('common.turkey'), flag: '🇹🇷' },
    { code: 'US', name: t('common.usa'), flag: '🇺🇸' },
    { code: 'EU', name: t('common.europe'), flag: '🇪🇺' },
    { code: 'MENA', name: t('common.mena'), flag: '🌍' },
  ]

  const labels = ['A', 'B', 'C', 'D']
  const colors = ['var(--color-accent-cyan)', 'var(--color-accent-purple)', 'var(--color-success)', 'var(--color-warning)']

  const addCampaign = () => {
    if (campaigns.length < 4) setCampaigns([...campaigns, ''])
  }

  const removeCampaign = (index) => {
    if (campaigns.length > 3) setCampaigns(campaigns.filter((_, i) => i !== index))
  }

  const updateCampaign = (index, value) => {
    const updated = [...campaigns]
    updated[index] = value
    setCampaigns(updated)
  }

  const totalCost = personaCount
  const allFilled = campaigns.every(c => c.trim().length > 0)

  // Gate check
  if (!hasAccess) {
    return (
      <DashboardLayout>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '32px' }}>
            <Lock style={{ width: '40px', height: '40px', color: 'var(--color-accent-blue)' }} />
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '16px' }}>{t('multiCompare.title')}</h1>
          <p style={{ fontSize: '18px', color: 'var(--color-text-muted)', maxWidth: '400px', marginBottom: '32px' }}>{t('multiCompare.lockedDesc')}</p>
          <Link to="/dashboard/profile" className="btn btn-primary" style={{ padding: '16px 32px', fontSize: '16px' }}>{t('multiCompare.upgradeToBusiness')}</Link>
        </div>
      </DashboardLayout>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (totalCost > balance) { setError(t('common.insufficientCredits')); return }
    if (!allFilled) { setError(t('multiCompare.fillAll')); return }
    setError(null); setTestResults(null); setIsTestRunning(true)

    try {
      // 1. Create campaign
      const campaignName = testName || `Multi Test ${new Date().toLocaleString()}`
      const createRes = await campaignsAPI.create({
        name: campaignName,
        content: campaigns[0],
        region: region,
      })
      const campaignId = createRes.data.id

      // 2. Build options dict: {"A": "...", "B": "...", "C": "..."}
      const options = {}
      campaigns.forEach((content, i) => {
        options[labels[i]] = content
      })

      // 3. Run multi compare
      const comparePayload = {
        options: options,
        persona_count: personaCount,
        region: region,
        lang: i18n.language,
      }
      const cleanedFilters = cleanFiltersForAPI(filters)
      if (cleanedFilters) comparePayload.filters = cleanedFilters

      const compareRes = await campaignsAPI.multiCompare(campaignId, comparePayload)

      const data = compareRes.data

      // Build sorted results for display
      const optionResults = Object.keys(data.votes).map(label => ({
        label,
        content: data.options[label] || '',
        votes: data.votes[label],
        percentage: data.percentages[label],
      }))
      optionResults.sort((a, b) => b.votes - a.votes)

      setTestResults({
        campaign_id: data.campaign_id || campaignId,
        options: optionResults,
        total_personas: data.total_personas,
        neither_votes: data.neither_votes,
        avg_confidence: data.avg_confidence,
        credits_used: data.credits_used,
        winner: optionResults[0].label,
        results: data.results || [],
      })

      fetchBalance()
      fetchSubscription()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Multi comparison failed. Please try again.'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setIsTestRunning(false)
    }
  }

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>{t('multiCompare.title')}</h1>
          <p style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>{t('multiCompare.subtitle')}</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ padding: '40px', marginBottom: '32px' }}>
            {/* Test Name */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Test Name (optional)</label>
              <input type="text" value={testName} onChange={(e) => setTestName(e.target.value)} className="input" placeholder="e.g., Q1 Market Comparison" />
            </div>

            {/* Campaign Inputs */}
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <label style={{ fontSize: '14px', fontWeight: '600' }}>Campaign Variants *</label>
                {campaigns.length < 4 && (
                  <button type="button" onClick={addCampaign} style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', borderRadius: '8px', border: '1px dashed var(--color-border)', background: 'transparent', color: 'var(--color-accent-cyan)', cursor: 'pointer', fontSize: '13px', fontWeight: '500' }}>
                    <Plus style={{ width: '14px', height: '14px' }} /> Add Option {labels[campaigns.length]}
                  </button>
                )}
              </div>

              <div style={{ display: 'grid', gap: '20px' }}>
                {campaigns.map((content, i) => (
                  <div key={i}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '8px', background: colors[i], color: i === 1 ? '#fff' : '#000', fontSize: '13px', fontWeight: '700' }}>{labels[i]}</span>
                      <span style={{ fontSize: '14px', fontWeight: '500' }}>Campaign {labels[i]}</span>
                      {i >= 3 && (
                        <button type="button" onClick={() => removeCampaign(i)} style={{ marginLeft: 'auto', background: 'transparent', border: 'none', cursor: 'pointer', color: 'var(--color-danger)', padding: '4px' }}>
                          <Trash2 style={{ width: '16px', height: '16px' }} />
                        </button>
                      )}
                    </div>
                    <textarea value={content} onChange={(e) => updateCampaign(i, e.target.value)} className="input" style={{ minHeight: '100px', resize: 'vertical' }} placeholder={`Enter campaign variant ${labels[i]}...`} required />
                  </div>
                ))}
              </div>
            </div>

            {/* Region Selection */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Target Region</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                {regions.map((r) => (
                  <button key={r.code} type="button" onClick={() => setRegion(r.code)}
                    style={{ padding: '20px', borderRadius: '12px', border: region === r.code ? '2px solid var(--color-accent-cyan)' : '1px solid var(--color-border)', background: region === r.code ? 'rgba(6, 182, 212, 0.1)' : 'var(--color-bg-secondary)', cursor: 'pointer', textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '8px' }}>{r.flag}</div>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>{r.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Persona Count */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('multiCompare.personaCount')}: 
                <input type="number" value={personaCount} onChange={(e) => setPersonaCount(Math.max(10, Math.min(2000, Number(e.target.value) || 10)))} min="10" max="2000" style={{ width: '70px', marginLeft: '8px', padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-secondary)', color: 'var(--color-accent-cyan)', fontSize: '14px', fontWeight: '700', textAlign: 'center' }} />
              </label>
              <input type="range" value={Math.min(personaCount, 500)} onChange={(e) => setPersonaCount(Number(e.target.value))} min="10" max="500" step="10" style={{ width: '100%', accentColor: 'var(--color-accent-cyan)' }} />
            </div>

            {/* Persona Filters */}
            <PersonaFilters
              planSlug={subscription?.plan_slug || 'starter'}
              filters={filters}
              onFiltersChange={setFilters}
            />

            {/* Cost Summary */}
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '24px', background: 'var(--color-bg-tertiary)', borderRadius: '12px', marginBottom: '24px' }}>
              <div>
                <div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('multiCompare.totalCost')}</div>
                <div style={{ fontSize: '28px', fontWeight: '700' }}>{totalCost} {t('common.credits')}</div>
                <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>{personaCount} personas × {campaigns.length} options</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('multiCompare.yourBalance')}</div>
                <div style={{ fontSize: '28px', fontWeight: '700', color: totalCost > balance ? 'var(--color-danger)' : 'var(--color-accent-cyan)' }}>{balance} {t('common.credits')}</div>
              </div>
            </div>

            {/* Error */}
            {error && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.1)', marginBottom: '24px' }}>
                <XCircle style={{ width: '20px', height: '20px', color: 'var(--color-danger)' }} />
                <span style={{ color: 'var(--color-danger)' }}>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button type="submit" disabled={isTestRunning || !allFilled || totalCost > balance} className="btn btn-primary" style={{ width: '100%', padding: '18px', fontSize: '16px', opacity: (isTestRunning || !allFilled || totalCost > balance) ? 0.5 : 1 }}>
              {isTestRunning ? <><Loader2 style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} /> Comparing {campaigns.length} Options... (this may take a moment)</> : <><LayoutGrid style={{ width: '20px', height: '20px' }} /> Compare {campaigns.length} Options</>}
            </button>
          </div>
        </form>

        {/* Results */}
        {testResults && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '700' }}>{t('multiCompare.comparisonResults')}</h2>
              {['pro', 'business', 'enterprise'].includes(subscription?.plan_slug) && testResults.campaign_id && (
                <button
                  onClick={async () => {
                    setPdfLoading(true)
                    try { await downloadCampaignPDF(testResults.campaign_id, i18n.language) }
                    catch (e) { alert(e.message) }
                    finally { setPdfLoading(false) }
                  }}
                  disabled={pdfLoading}
                  className="btn btn-secondary"
                  style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 20px', fontSize: '14px' }}
                >
                  {pdfLoading ? <Loader2 style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} /> : <FileDown style={{ width: '16px', height: '16px' }} />}
                  {t('common.downloadPDF')}
                </button>
              )}
            </div>

            {/* Winner Banner */}
            <div className="gradient-border" style={{ padding: '40px', textAlign: 'center', marginBottom: '32px' }}>
              <Trophy style={{ width: '48px', height: '48px', color: 'var(--color-warning)', margin: '0 auto 16px auto' }} />
              <div style={{ fontSize: '18px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('multiCompare.winner')}</div>
              <div className="gradient-text" style={{ fontSize: '48px', fontWeight: '800', marginBottom: '8px' }}>Option {testResults.winner}</div>
              <div style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>
                {testResults.options[0].percentage}% {t('multiCompare.preferredOption')} • Confidence: {testResults.avg_confidence}/10
              </div>
            </div>

            {/* Option Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: `repeat(${testResults.options.length}, 1fr)`, gap: '16px', marginBottom: '32px' }}>
              {testResults.options.map((opt, i) => (
                <div key={opt.label} className="card" style={{ padding: '28px', textAlign: 'center', border: i === 0 ? '2px solid var(--color-warning)' : '1px solid var(--color-border)', position: 'relative' }}>
                  {i === 0 && <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: 'var(--color-warning)', color: '#000', padding: '4px 16px', borderRadius: '12px', fontSize: '12px', fontWeight: '700' }}>{t('multiCompare.winnerBadge')}</div>}
                  <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '10px', background: colors[labels.indexOf(opt.label)], color: labels.indexOf(opt.label) === 1 ? '#fff' : '#000', fontSize: '18px', fontWeight: '700', margin: '0 auto 16px auto' }}>{opt.label}</div>
                  <div style={{ fontSize: '36px', fontWeight: '800', marginBottom: '4px', color: i === 0 ? 'var(--color-warning)' : 'var(--color-text-primary)' }}>{opt.percentage}%</div>
                  <div style={{ fontSize: '13px', color: 'var(--color-text-muted)', marginBottom: '12px' }}>{opt.votes} {t('multiCompare.votes')}</div>
                  <div style={{ padding: '12px', background: 'var(--color-bg-tertiary)', borderRadius: '8px', fontSize: '12px', color: 'var(--color-text-secondary)', textAlign: 'left' }}>
                    {opt.content.substring(0, 120)}{opt.content.length > 120 ? '...' : ''}
                  </div>
                </div>
              ))}
            </div>

            {/* Comparison Bars */}
            <div className="card" style={{ padding: '28px', marginBottom: '32px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('multiCompare.headToHead')}</h3>
              {testResults.options.map((opt) => (
                <div key={opt.label} style={{ marginBottom: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '22px', height: '22px', borderRadius: '6px', background: colors[labels.indexOf(opt.label)], color: labels.indexOf(opt.label) === 1 ? '#fff' : '#000', fontSize: '11px', fontWeight: '700' }}>{opt.label}</span>
                      Option {opt.label}
                    </span>
                    <span style={{ fontWeight: '600' }}>{opt.percentage}%</span>
                  </div>
                  <div style={{ height: '12px', borderRadius: '6px', background: 'var(--color-bg-tertiary)' }}>
                    <div style={{ height: '100%', borderRadius: '6px', background: colors[labels.indexOf(opt.label)], width: `${opt.percentage}%`, transition: 'width 0.8s ease' }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Persona Details */}
            {testResults.results?.length > 0 && (
              <div className="card" style={{ padding: '28px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('multiCompare.personaResponses')} ({testResults.results.length})</h3>
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>Name</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>Age</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>City</th>
                        <th style={{ textAlign: 'center', padding: '12px 8px', color: 'var(--color-text-muted)' }}>Choice</th>
                        <th style={{ textAlign: 'center', padding: '12px 8px', color: 'var(--color-text-muted)' }}>Conf.</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>Reasoning</th>
                      </tr>
                    </thead>
                    <tbody>
                      {testResults.results.map((r, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '12px 8px' }}>{r.persona_name}</td>
                          <td style={{ padding: '12px 8px' }}>{r.persona_age}</td>
                          <td style={{ padding: '12px 8px' }}>{r.persona_city}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                            <span style={{ padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: '600', background: `${colors[labels.indexOf(r.choice)] || 'grey'}20`, color: colors[labels.indexOf(r.choice)] || 'grey' }}>{r.choice}</span>
                          </td>
                          <td style={{ padding: '12px 8px', textAlign: 'center' }}>{r.confidence}/10</td>
                          <td style={{ padding: '12px 8px', maxWidth: '250px', fontSize: '12px', color: 'var(--color-text-secondary)' }}>{getLocalizedReasoning(r.reasoning, i18n.language)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </DashboardLayout>
  )
}

export default MultiCompare
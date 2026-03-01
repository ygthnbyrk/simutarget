import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { TestTube, Loader2, XCircle, CheckCircle, Users, TrendingUp, ImagePlus, Trash2, Lock, FileDown } from 'lucide-react'
import DashboardLayout from '../components/layout/DashboardLayout'
import PersonaFilters, { cleanFiltersForAPI } from '../components/PersonaFilters'
import useCreditStore from '../stores/creditStore'
import { campaignsAPI } from '../services/api'
import { translatePersonaValue, getLocalizedReasoning } from '../utils/personaTranslations'
import { downloadCampaignPDF } from '../utils/pdfDownload'

function CampaignTest() {
  const { balance, subscription, fetchBalance, fetchSubscription } = useCreditStore()
  const { t, i18n } = useTranslation()
  const [formData, setFormData] = useState({ name: '', content: '', region: 'TR', personaCount: 25 })
  const [filters, setFilters] = useState({})
  const [pdfLoading, setPdfLoading] = useState(false)
  const [isTestRunning, setIsTestRunning] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [error, setError] = useState(null)

  // Görsel state
  const [imageFile, setImageFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [imageUploading, setImageUploading] = useState(false)
  const fileInputRef = useRef(null)

  // Plan bazlı görsel erişimi: Pro, Business, Enterprise
  const planSlug = subscription?.plan_slug || 'starter'
  const canUploadImage = ['pro', 'business', 'enterprise'].includes(planSlug)

  const regions = [
    { code: 'TR', name: t('common.turkey'), flag: '🇹🇷' },
    { code: 'US', name: t('common.usa'), flag: '🇺🇸' },
    { code: 'EU', name: t('common.europe'), flag: '🇪🇺' },
    { code: 'MENA', name: t('common.mena'), flag: '🌍' },
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData({ ...formData, [name]: name === 'personaCount' ? Number(value) : value })
  }

  // Görsel seçme
  const handleImageSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Tip kontrolü
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowed.includes(file.type)) {
      setError('Unsupported image format. Use JPEG, PNG, WebP or GIF.')
      return
    }

    // Boyut kontrolü (5MB)
    if (file.size > 5 * 1024 * 1024) {
      setError('Image too large. Maximum size is 5MB.')
      return
    }

    setImageFile(file)
    setImagePreview(URL.createObjectURL(file))
    setError(null)
  }

  // Görsel kaldırma
  const handleImageRemove = () => {
    setImageFile(null)
    if (imagePreview) URL.revokeObjectURL(imagePreview)
    setImagePreview(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (formData.personaCount > balance) { setError('Insufficient credits'); return }
    if (!formData.content.trim() && !imageFile) { setError(t('campaignTest.fillCampaign')); return }
    setError(null); setTestResults(null); setIsTestRunning(true)

    try {
      // 1. Create campaign
      const campaignName = formData.name || `Test ${new Date().toLocaleString()}`
      const createRes = await campaignsAPI.create({
        name: campaignName,
        content: formData.content || '(Görsel kampanya)',
        region: formData.region,
      })
      const campaignId = createRes.data.id

      // 2. Upload image if selected
      if (imageFile) {
        setImageUploading(true)
        try {
          await campaignsAPI.uploadImage(campaignId, imageFile)
        } catch (uploadErr) {
          const msg = uploadErr.response?.data?.detail || 'Image upload failed'
          setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
          setIsTestRunning(false)
          setImageUploading(false)
          return
        }
        setImageUploading(false)
      }

      // 3. Run test
      const testPayload = {
        persona_count: formData.personaCount,
        region: formData.region,
        lang: i18n.language,
      }
      const cleanedFilters = cleanFiltersForAPI(filters)
      if (cleanedFilters) testPayload.filters = cleanedFilters

      const testRes = await campaignsAPI.test(campaignId, testPayload)

      const data = testRes.data
      setTestResults({
        campaign_id: data.campaign_id || campaignId,
        conversion_rate: data.conversion_rate,
        yes_count: data.yes_count,
        no_count: data.no_count,
        total_personas: data.total_personas,
        avg_confidence: data.avg_confidence,
        credits_used: data.credits_used,
        results: data.results || [],
      })

      // Refresh credits
      fetchBalance()
      fetchSubscription()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Test failed. Please try again.'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setIsTestRunning(false)
      setImageUploading(false)
    }
  }

  // Helper: check if decision is positive
  const isYes = (decision) => {
    if (typeof decision === 'boolean') return decision
    if (typeof decision === 'string') return ['EVET', 'YES', 'evet', 'yes', 'True', 'true'].includes(decision)
    return false
  }

  // Income level translation using shared utility
  const translateIncome = (raw) => translatePersonaValue(raw, i18n.language)

  // Group results by demographics
  const getDemographics = () => {
    if (!testResults?.results?.length) return null

    const byAge = {}
    const byIncome = {}

    testResults.results.forEach(r => {
      const age = r.persona_age
      let ageGroup = '51+'
      if (age < 26) ageGroup = '18-25'
      else if (age < 36) ageGroup = '26-35'
      else if (age < 51) ageGroup = '36-50'

      if (!byAge[ageGroup]) byAge[ageGroup] = { yes: 0, no: 0 }
      if (isYes(r.decision)) byAge[ageGroup].yes++
      else byAge[ageGroup].no++

      const rawIncome = r.persona_income || r.persona_data?.income_level || 'Unknown'
      const income = translateIncome(rawIncome)
      if (!byIncome[income]) byIncome[income] = { yes: 0, no: 0 }
      if (isYes(r.decision)) byIncome[income].yes++
      else byIncome[income].no++
    })

    return {
      by_age: Object.entries(byAge).map(([group, data]) => ({ group, ...data })),
      by_income: Object.entries(byIncome).map(([level, data]) => ({ level, ...data })),
    }
  }

  const demographics = testResults ? getDemographics() : null

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>{t('campaignTest.title')}</h1>
          <p style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>Test your campaign against AI-generated synthetic personas</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ padding: '40px', marginBottom: '32px' }}>
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('campaignTest.campaignName')}</label>
              <input type="text" name="name" value={formData.name} onChange={handleChange} className="input" placeholder="e.g., Summer Sale Campaign" />
            </div>

            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('campaignTest.campaignContent')} *</label>
              <textarea name="content" value={formData.content} onChange={handleChange} className="input" style={{ minHeight: '150px', resize: 'vertical' }} placeholder={t('campaignTest.campaignContentPlaceholder')} required={!imageFile} />
            </div>

            {/* ============================================ */}
            {/* GÖRSEL UPLOAD ALANI */}
            {/* ============================================ */}
            <div style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                <ImagePlus style={{ width: '16px', height: '16px', color: 'var(--color-accent-cyan)' }} />
                <label style={{ fontSize: '14px', fontWeight: '600' }}>Campaign Visual</label>
                {!canUploadImage && (
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', gap: '4px',
                    fontSize: '11px', fontWeight: '600', color: 'var(--color-accent-purple)',
                    background: 'rgba(168, 85, 247, 0.1)', padding: '2px 10px', borderRadius: '12px',
                  }}>
                    <Lock style={{ width: '10px', height: '10px' }} /> PRO+
                  </span>
                )}
              </div>

              {canUploadImage ? (
                <>
                  {!imagePreview ? (
                    /* Drop zone */
                    <div
                      onClick={() => fileInputRef.current?.click()}
                      onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
                      onDrop={(e) => {
                        e.preventDefault(); e.stopPropagation()
                        const file = e.dataTransfer.files?.[0]
                        if (file) {
                          const fakeEvent = { target: { files: [file] } }
                          handleImageSelect(fakeEvent)
                        }
                      }}
                      style={{
                        border: '2px dashed var(--color-border)',
                        borderRadius: '12px',
                        padding: '40px',
                        textAlign: 'center',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        background: 'var(--color-bg-secondary)',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-accent-cyan)'
                        e.currentTarget.style.background = 'rgba(6, 182, 212, 0.05)'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.borderColor = 'var(--color-border)'
                        e.currentTarget.style.background = 'var(--color-bg-secondary)'
                      }}
                    >
                      <ImagePlus style={{ width: '32px', height: '32px', color: 'var(--color-text-muted)', margin: '0 auto 12px auto' }} />
                      <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                        Click to upload or drag & drop
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>
                        JPEG, PNG, WebP, GIF — max 5MB
                      </div>
                    </div>
                  ) : (
                    /* Preview */
                    <div style={{
                      position: 'relative',
                      borderRadius: '12px',
                      overflow: 'hidden',
                      border: '1px solid var(--color-border)',
                    }}>
                      <img
                        src={imagePreview}
                        alt="Campaign visual"
                        style={{
                          width: '100%',
                          maxHeight: '250px',
                          objectFit: 'contain',
                          background: 'var(--color-bg-secondary)',
                          display: 'block',
                        }}
                      />
                      <button
                        type="button"
                        onClick={handleImageRemove}
                        style={{
                          position: 'absolute', top: '8px', right: '8px',
                          background: 'rgba(239, 68, 68, 0.9)', color: '#fff',
                          border: 'none', borderRadius: '8px', padding: '6px 12px',
                          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px',
                          fontSize: '12px', fontWeight: '600',
                        }}
                      >
                        <Trash2 style={{ width: '14px', height: '14px' }} /> Remove
                      </button>
                      <div style={{
                        padding: '8px 12px',
                        background: 'var(--color-bg-tertiary)',
                        fontSize: '12px', color: 'var(--color-text-muted)',
                        display: 'flex', justifyContent: 'space-between',
                      }}>
                        <span>{imageFile?.name}</span>
                        <span>{(imageFile?.size / 1024).toFixed(0)} KB</span>
                      </div>
                    </div>
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/jpeg,image/png,image/webp,image/gif"
                    onChange={handleImageSelect}
                    style={{ display: 'none' }}
                  />
                </>
              ) : (
                /* Locked state for Starter */
                <div style={{
                  border: '1px solid var(--color-border)',
                  borderRadius: '12px',
                  padding: '32px',
                  textAlign: 'center',
                  background: 'var(--color-bg-secondary)',
                  opacity: 0.7,
                }}>
                  <Lock style={{ width: '28px', height: '28px', color: 'var(--color-text-muted)', margin: '0 auto 8px auto' }} />
                  <div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
                    Image campaigns available on <strong>Pro</strong> plan and above
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>Target Region</label>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
                {regions.map((r) => (
                  <button key={r.code} type="button" onClick={() => setFormData({ ...formData, region: r.code })}
                    style={{ padding: '20px', borderRadius: '12px', border: formData.region === r.code ? '2px solid var(--color-accent-cyan)' : '1px solid var(--color-border)', background: formData.region === r.code ? 'rgba(6, 182, 212, 0.1)' : 'var(--color-bg-secondary)', cursor: 'pointer', textAlign: 'center' }}>
                    <div style={{ fontSize: '32px', marginBottom: '8px' }}>{r.flag}</div>
                    <div style={{ fontSize: '14px', fontWeight: '500' }}>{r.name}</div>
                  </button>
                ))}
              </div>
            </div>

            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('campaignTest.personaCount')}: 
                <input type="number" value={formData.personaCount} onChange={(e) => { const v = Math.max(10, Math.min(2000, Number(e.target.value) || 10)); setFormData({...formData, personaCount: v}) }} min="10" max="2000" style={{ width: '70px', marginLeft: '8px', padding: '4px 8px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-bg-secondary)', color: 'var(--color-accent-cyan)', fontSize: '14px', fontWeight: '700', textAlign: 'center' }} />
              </label>
              <input type="range" name="personaCount" value={Math.min(formData.personaCount, 500)} onChange={handleChange} min="10" max="500" step="10" style={{ width: '100%', accentColor: 'var(--color-accent-cyan)' }} />
            </div>

            {/* Persona Filters */}
            <PersonaFilters
              planSlug={subscription?.plan_slug || 'starter'}
              filters={filters}
              onFiltersChange={setFilters}
            />

            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '24px', background: 'var(--color-bg-tertiary)', borderRadius: '12px', marginBottom: '24px' }}>
              <div><div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('campaignTest.cost')}</div><div style={{ fontSize: '28px', fontWeight: '700' }}>{formData.personaCount} {t('common.credits')}</div></div>
              <div style={{ textAlign: 'right' }}><div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('campaignTest.yourBalance')}</div><div style={{ fontSize: '28px', fontWeight: '700', color: formData.personaCount > balance ? 'var(--color-danger)' : 'var(--color-accent-cyan)' }}>{balance} {t('common.credits')}</div></div>
            </div>

            {error && <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.1)', marginBottom: '24px' }}><XCircle style={{ width: '20px', height: '20px', color: 'var(--color-danger)' }} /><span style={{ color: 'var(--color-danger)' }}>{error}</span></div>}

            <button type="submit" disabled={isTestRunning || (!formData.content && !imageFile) || formData.personaCount > balance} className="btn btn-primary" style={{ width: '100%', padding: '18px', fontSize: '16px', opacity: (isTestRunning || (!formData.content && !imageFile) || formData.personaCount > balance) ? 0.5 : 1 }}>
              {isTestRunning ? (
                <>
                  <Loader2 style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} />
                  {imageUploading ? ' Uploading image...' : ` ${t('campaignTest.running')}`}
                </>
              ) : (
                <><TestTube style={{ width: '20px', height: '20px' }} /> {t('campaignTest.runTest')}{imageFile ? ' (with image)' : ''}</>
              )}
            </button>
          </div>
        </form>

        {testResults && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '700' }}>{t('campaignTest.testResults')}</h2>
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
            <div className="gradient-border" style={{ padding: '40px', textAlign: 'center', marginBottom: '24px' }}>
              <TrendingUp style={{ width: '48px', height: '48px', color: testResults.conversion_rate >= 50 ? 'var(--color-success)' : 'var(--color-warning)', margin: '0 auto 16px auto' }} />
              <div className="gradient-text" style={{ fontSize: '56px', fontWeight: '800', marginBottom: '8px' }}>{testResults.conversion_rate.toFixed(1)}%</div>
              <div style={{ fontSize: '18px', color: 'var(--color-text-muted)' }}>{t('campaignTest.conversionRate')}</div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '32px' }}>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><CheckCircle style={{ width: '28px', height: '28px', color: 'var(--color-success)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '32px', fontWeight: '700' }}>{testResults.yes_count}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('campaignTest.wouldBuy')}</div></div>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><XCircle style={{ width: '28px', height: '28px', color: 'var(--color-danger)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '32px', fontWeight: '700' }}>{testResults.no_count}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('campaignTest.wouldNot')}</div></div>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><Users style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '32px', fontWeight: '700' }}>{testResults.total_personas}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('campaignTest.total')}</div></div>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><TrendingUp style={{ width: '28px', height: '28px', color: 'var(--color-accent-purple)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '32px', fontWeight: '700' }}>{testResults.avg_confidence.toFixed(1)}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>{t('common.confidence')}</div></div>
            </div>

            {/* Demographics */}
            {demographics && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
                <div className="card" style={{ padding: '28px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('campaignTest.byAgeGroup')}</h3>
                  {demographics.by_age.map((g) => { const pct = g.yes + g.no > 0 ? (g.yes / (g.yes + g.no)) * 100 : 0; return (
                    <div key={g.group} style={{ marginBottom: '16px' }}><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>{g.group}</span><span style={{ color: 'var(--color-text-muted)' }}>{pct.toFixed(0)}%</span></div><div style={{ height: '8px', borderRadius: '4px', background: 'var(--color-bg-tertiary)' }}><div style={{ height: '100%', borderRadius: '4px', background: 'var(--color-success)', width: `${pct}%` }} /></div></div>
                  )})}
                </div>
                <div className="card" style={{ padding: '28px' }}>
                  <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('campaignTest.byIncomeLevel')}</h3>
                  {demographics.by_income.map((l) => { const pct = l.yes + l.no > 0 ? (l.yes / (l.yes + l.no)) * 100 : 0; return (
                    <div key={l.level} style={{ marginBottom: '16px' }}><div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}><span>{l.level}</span><span style={{ color: 'var(--color-text-muted)' }}>{pct.toFixed(0)}%</span></div><div style={{ height: '8px', borderRadius: '4px', background: 'var(--color-bg-tertiary)' }}><div style={{ height: '100%', borderRadius: '4px', background: 'var(--color-accent-cyan)', width: `${pct}%` }} /></div></div>
                  )})}
                </div>
              </div>
            )}

            {/* Persona Details */}
            {testResults.results?.length > 0 && (
              <div className="card" style={{ padding: '28px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('campaignTest.personaResponses')} ({testResults.results.length})</h3>
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.name')}</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.age')}</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.city')}</th>
                        <th style={{ textAlign: 'center', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.decision')}</th>
                        <th style={{ textAlign: 'center', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.conf')}</th>
                        <th style={{ textAlign: 'left', padding: '12px 8px', color: 'var(--color-text-muted)' }}>{t('detail.reasoning')}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {testResults.results.map((r, i) => (
                        <tr key={i} style={{ borderBottom: '1px solid var(--color-border)' }}>
                          <td style={{ padding: '12px 8px' }}>{r.persona_name}</td>
                          <td style={{ padding: '12px 8px' }}>{r.persona_age}</td>
                          <td style={{ padding: '12px 8px' }}>{r.persona_city}</td>
                          <td style={{ padding: '12px 8px', textAlign: 'center' }}>
                            <span style={{ padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: '600', background: isYes(r.decision) ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: isYes(r.decision) ? 'var(--color-success)' : 'var(--color-danger)' }}>{isYes(r.decision) ? t('common.yes') : t('common.no')}</span>
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

export default CampaignTest
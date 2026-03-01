import { useState, useRef } from 'react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'
import { Swords, Loader2, XCircle, Trophy, Users, TrendingUp, Lock, ImagePlus, Trash2, FileDown } from 'lucide-react'
import { Link } from 'react-router-dom'
import DashboardLayout from '../components/layout/DashboardLayout'
import PersonaFilters, { cleanFiltersForAPI } from '../components/PersonaFilters'
import useCreditStore from '../stores/creditStore'
import { campaignsAPI } from '../services/api'
import { getLocalizedReasoning } from '../utils/personaTranslations'
import { downloadCampaignPDF } from '../utils/pdfDownload'

// Reusable Image Upload Component
function ImageUploadBox({ imageFile, imagePreview, onSelect, onRemove, fileInputRef, label }) {
  const handleDrop = (e) => {
    e.preventDefault(); e.stopPropagation()
    const file = e.dataTransfer.files?.[0]
    if (file) onSelect({ target: { files: [file] } })
  }

  if (imagePreview) {
    return (
      <div style={{ position: 'relative', borderRadius: '10px', overflow: 'hidden', border: '1px solid var(--color-border)', marginTop: '12px' }}>
        <img src={imagePreview} alt={label} style={{ width: '100%', maxHeight: '140px', objectFit: 'contain', background: 'var(--color-bg-secondary)', display: 'block' }} />
        <button type="button" onClick={onRemove}
          style={{ position: 'absolute', top: '6px', right: '6px', background: 'rgba(239,68,68,0.9)', color: '#fff', border: 'none', borderRadius: '6px', padding: '4px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '3px', fontSize: '11px', fontWeight: '600' }}>
          <Trash2 style={{ width: '12px', height: '12px' }} /> Remove
        </button>
        <div style={{ padding: '6px 10px', background: 'var(--color-bg-tertiary)', fontSize: '11px', color: 'var(--color-text-muted)', display: 'flex', justifyContent: 'space-between' }}>
          <span>{imageFile?.name}</span>
          <span>{(imageFile?.size / 1024).toFixed(0)} KB</span>
        </div>
      </div>
    )
  }

  return (
    <div
      onClick={() => fileInputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); e.stopPropagation() }}
      onDrop={handleDrop}
      style={{
        border: '2px dashed var(--color-border)', borderRadius: '10px', padding: '20px',
        textAlign: 'center', cursor: 'pointer', transition: 'all 0.2s ease',
        background: 'var(--color-bg-secondary)', marginTop: '12px',
      }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = 'var(--color-accent-cyan)'; e.currentTarget.style.background = 'rgba(6,182,212,0.05)' }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.background = 'var(--color-bg-secondary)' }}
    >
      <ImagePlus style={{ width: '24px', height: '24px', color: 'var(--color-text-muted)', margin: '0 auto 6px auto' }} />
      <div style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Click or drop image (max 5MB)</div>
      <input ref={fileInputRef} type="file" accept="image/jpeg,image/png,image/webp,image/gif" onChange={onSelect} style={{ display: 'none' }} />
    </div>
  )
}

function ABCompare() {
  const { balance, subscription, fetchBalance, fetchSubscription } = useCreditStore()
  const { t, i18n } = useTranslation()
  const hasAccess = subscription && ['pro', 'business', 'enterprise'].includes(subscription.plan_slug)
  const canUploadImage = hasAccess // A/B zaten Pro+ — görsel de Pro+

  const [testName, setTestName] = useState('')
  const [contentA, setContentA] = useState('')
  const [contentB, setContentB] = useState('')
  const [region, setRegion] = useState('TR')
  const [personaCount, setPersonaCount] = useState(25)
  const [filters, setFilters] = useState({})
  const [pdfLoading, setPdfLoading] = useState(false)
  const [isTestRunning, setIsTestRunning] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [error, setError] = useState(null)

  // Image states for A and B
  const [imageFileA, setImageFileA] = useState(null)
  const [imagePreviewA, setImagePreviewA] = useState(null)
  const [imageFileB, setImageFileB] = useState(null)
  const [imagePreviewB, setImagePreviewB] = useState(null)
  const [imageUploading, setImageUploading] = useState(false)
  const fileInputRefA = useRef(null)
  const fileInputRefB = useRef(null)

  const regions = [
    { code: 'TR', name: t('common.turkey'), flag: '🇹🇷' },
    { code: 'US', name: t('common.usa'), flag: '🇺🇸' },
    { code: 'EU', name: t('common.europe'), flag: '🇪🇺' },
    { code: 'MENA', name: t('common.mena'), flag: '🌍' },
  ]

  // Image handlers
  const validateAndSetImage = (file, setFile, setPreview) => {
    if (!file) return
    const allowed = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
    if (!allowed.includes(file.type)) { setError('Unsupported format. Use JPEG, PNG, WebP or GIF.'); return }
    if (file.size > 5 * 1024 * 1024) { setError('Image too large. Max 5MB.'); return }
    setFile(file)
    setPreview(URL.createObjectURL(file))
    setError(null)
  }

  const handleImageSelectA = (e) => validateAndSetImage(e.target.files?.[0], setImageFileA, setImagePreviewA)
  const handleImageSelectB = (e) => validateAndSetImage(e.target.files?.[0], setImageFileB, setImagePreviewB)

  const handleImageRemoveA = () => {
    setImageFileA(null); if (imagePreviewA) URL.revokeObjectURL(imagePreviewA); setImagePreviewA(null)
    if (fileInputRefA.current) fileInputRefA.current.value = ''
  }
  const handleImageRemoveB = () => {
    setImageFileB(null); if (imagePreviewB) URL.revokeObjectURL(imagePreviewB); setImagePreviewB(null)
    if (fileInputRefB.current) fileInputRefB.current.value = ''
  }

  // Gate check
  if (!hasAccess) {
    return (
      <DashboardLayout>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
          <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: 'rgba(59, 130, 246, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '32px' }}>
            <Lock style={{ width: '40px', height: '40px', color: 'var(--color-accent-blue)' }} />
          </div>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '16px' }}>A/B Comparison</h1>
          <p style={{ fontSize: '18px', color: 'var(--color-text-muted)', maxWidth: '400px', marginBottom: '32px' }}>{t('abCompare.lockedDesc')}</p>
          <Link to="/dashboard/profile" className="btn btn-primary" style={{ padding: '16px 32px', fontSize: '16px' }}>{t('abCompare.upgradeToPro')}</Link>
        </div>
      </DashboardLayout>
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (personaCount > balance) { setError(t('common.insufficientCredits')); return }
    if (!contentA.trim() && !imageFileA) { setError('Please provide content or image for Campaign A'); return }
    if (!contentB.trim() && !imageFileB) { setError('Please provide content or image for Campaign B'); return }
    setError(null); setTestResults(null); setIsTestRunning(true)

    try {
      // 1. Create campaign with content A
      const campaignName = testName || `A/B Test ${new Date().toLocaleString()}`
      const createRes = await campaignsAPI.create({
        name: campaignName,
        content: contentA || '(Görsel kampanya A)',
        region: region,
      })
      const campaignId = createRes.data.id

      // 2. Upload image for A (if selected)
      if (imageFileA) {
        setImageUploading(true)
        try {
          await campaignsAPI.uploadImage(campaignId, imageFileA)
        } catch (uploadErr) {
          const msg = uploadErr.response?.data?.detail || 'Image A upload failed'
          setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
          setIsTestRunning(false); setImageUploading(false)
          return
        }
        setImageUploading(false)
      }

      // 3. Run A/B compare
      // Not: B seçeneğinin görseli şu an backend'de content_b_image olarak desteklenmiyor.
      // B görseli için ayrı bir kampanya oluşturup image yükleriz, ancak mevcut compare endpoint
      // sadece A'nın görselini kullanır. İleride B görseli de eklenebilir.
      const comparePayload = {
        content_b: contentB || '(Görsel kampanya B)',
        persona_count: personaCount,
        region: region,
        lang: i18n.language,
      }
      const cleanedFilters = cleanFiltersForAPI(filters)
      if (cleanedFilters) comparePayload.filters = cleanedFilters

      const compareRes = await campaignsAPI.abCompare(campaignId, comparePayload)

      const data = compareRes.data
      setTestResults({
        campaign_id: data.campaign_id || campaignId,
        option_a: data.option_a,
        option_b: data.option_b,
        total_personas: data.total_personas,
        a_votes: data.a_votes,
        b_votes: data.b_votes,
        neither_votes: data.neither_votes,
        a_percentage: data.a_percentage,
        b_percentage: data.b_percentage,
        avg_confidence: data.avg_confidence,
        credits_used: data.credits_used,
        winner: data.a_votes >= data.b_votes ? 'A' : 'B',
        results: data.results || [],
      })

      fetchBalance()
      fetchSubscription()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Comparison failed. Please try again.'
      setError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    } finally {
      setIsTestRunning(false)
      setImageUploading(false)
    }
  }

  return (
    <DashboardLayout>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <div style={{ marginBottom: '48px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '700', marginBottom: '8px' }}>A/B Comparison</h1>
          <p style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>Compare two campaign variants to find the winner</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ padding: '40px', marginBottom: '32px' }}>
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('abCompare.testName')}</label>
              <input type="text" value={testName} onChange={(e) => setTestName(e.target.value)} className="input" placeholder="e.g., Summer Sale A/B Test" />
            </div>

            {/* A ve B kampanya alanları */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
              {/* Campaign A */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '8px', background: 'var(--color-accent-cyan)', color: '#000', fontSize: '13px', fontWeight: '700' }}>A</span>
                  <label style={{ fontSize: '14px', fontWeight: '600' }}>Campaign A *</label>
                </div>
                <textarea value={contentA} onChange={(e) => setContentA(e.target.value)} className="input" style={{ minHeight: '150px', resize: 'vertical' }} placeholder={t("abCompare.campaignAPlaceholder")} required={!imageFileA} />

                {/* Image upload A */}
                {canUploadImage && (
                  <ImageUploadBox
                    imageFile={imageFileA}
                    imagePreview={imagePreviewA}
                    onSelect={handleImageSelectA}
                    onRemove={handleImageRemoveA}
                    fileInputRef={fileInputRefA}
                    label="Campaign A"
                  />
                )}
              </div>

              {/* Campaign B */}
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '28px', height: '28px', borderRadius: '8px', background: 'var(--color-accent-purple)', color: '#fff', fontSize: '13px', fontWeight: '700' }}>B</span>
                  <label style={{ fontSize: '14px', fontWeight: '600' }}>Campaign B *</label>
                </div>
                <textarea value={contentB} onChange={(e) => setContentB(e.target.value)} className="input" style={{ minHeight: '150px', resize: 'vertical' }} placeholder={t("abCompare.campaignBPlaceholder")} required={!imageFileB} />

                {/* Image upload B */}
                {canUploadImage && (
                  <ImageUploadBox
                    imageFile={imageFileB}
                    imagePreview={imagePreviewB}
                    onSelect={handleImageSelectB}
                    onRemove={handleImageRemoveB}
                    fileInputRef={fileInputRefB}
                    label="Campaign B"
                  />
                )}
              </div>
            </div>

            {/* Region */}
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

            {/* Persona count */}
            <div style={{ marginBottom: '32px' }}>
              <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', marginBottom: '12px' }}>{t('abCompare.personaCount')}: 
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

            {/* Cost / Balance */}
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '24px', background: 'var(--color-bg-tertiary)', borderRadius: '12px', marginBottom: '24px' }}>
              <div><div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('abCompare.totalCost')}</div><div style={{ fontSize: '28px', fontWeight: '700' }}>{personaCount} {t('common.credits')}</div></div>
              <div style={{ textAlign: 'right' }}><div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '4px' }}>{t('abCompare.yourBalance')}</div><div style={{ fontSize: '28px', fontWeight: '700', color: personaCount > balance ? 'var(--color-danger)' : 'var(--color-accent-cyan)' }}>{balance} {t('common.credits')}</div></div>
            </div>

            {error && <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '16px', borderRadius: '12px', background: 'rgba(239, 68, 68, 0.1)', marginBottom: '24px' }}><XCircle style={{ width: '20px', height: '20px', color: 'var(--color-danger)' }} /><span style={{ color: 'var(--color-danger)' }}>{error}</span></div>}

            <button type="submit" disabled={isTestRunning || (!contentA && !imageFileA) || (!contentB && !imageFileB) || personaCount > balance} className="btn btn-primary" style={{ width: '100%', padding: '18px', fontSize: '16px', opacity: (isTestRunning || (!contentA && !imageFileA) || (!contentB && !imageFileB) || personaCount > balance) ? 0.5 : 1 }}>
              {isTestRunning ? (
                <>
                  <Loader2 style={{ width: '20px', height: '20px', animation: 'spin 1s linear infinite' }} />
                  {imageUploading ? ' Uploading images...' : ' Comparing... (this may take a moment)'}
                </>
              ) : (
                <><Swords style={{ width: '20px', height: '20px' }} /> Compare A vs B{(imageFileA || imageFileB) ? ' (with images)' : ''}</>
              )}
            </button>
          </div>
        </form>

        {testResults && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '24px', fontWeight: '700' }}>{t('abCompare.comparisonResults')}</h2>
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
              <div style={{ fontSize: '18px', color: 'var(--color-text-muted)', marginBottom: '8px' }}>{t('abCompare.winner')}</div>
              <div className="gradient-text" style={{ fontSize: '48px', fontWeight: '800', marginBottom: '8px' }}>Option {testResults.winner}</div>
              <div style={{ fontSize: '16px', color: 'var(--color-text-muted)' }}>
                {testResults.winner === 'A' ? testResults.a_percentage : testResults.b_percentage}% {t('abCompare.preferredOption')}
              </div>
            </div>

            {/* A vs B Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '32px' }}>
              <div className="card" style={{ padding: '28px', textAlign: 'center', border: testResults.winner === 'A' ? '2px solid var(--color-warning)' : '1px solid var(--color-border)', position: 'relative' }}>
                {testResults.winner === 'A' && <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: 'var(--color-warning)', color: '#000', padding: '4px 16px', borderRadius: '12px', fontSize: '12px', fontWeight: '700' }}>WINNER</div>}
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '10px', background: 'var(--color-accent-cyan)', color: '#000', fontSize: '18px', fontWeight: '700', margin: '0 auto 16px auto' }}>A</div>
                <div style={{ fontSize: '42px', fontWeight: '800', marginBottom: '4px', color: testResults.winner === 'A' ? 'var(--color-warning)' : 'var(--color-text-primary)' }}>{testResults.a_percentage}%</div>
                <div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{testResults.a_votes} votes</div>
              </div>
              <div className="card" style={{ padding: '28px', textAlign: 'center', border: testResults.winner === 'B' ? '2px solid var(--color-warning)' : '1px solid var(--color-border)', position: 'relative' }}>
                {testResults.winner === 'B' && <div style={{ position: 'absolute', top: '-12px', left: '50%', transform: 'translateX(-50%)', background: 'var(--color-warning)', color: '#000', padding: '4px 16px', borderRadius: '12px', fontSize: '12px', fontWeight: '700' }}>WINNER</div>}
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '10px', background: 'var(--color-accent-purple)', color: '#fff', fontSize: '18px', fontWeight: '700', margin: '0 auto 16px auto' }}>B</div>
                <div style={{ fontSize: '42px', fontWeight: '800', marginBottom: '4px', color: testResults.winner === 'B' ? 'var(--color-warning)' : 'var(--color-text-primary)' }}>{testResults.b_percentage}%</div>
                <div style={{ fontSize: '14px', color: 'var(--color-text-muted)', marginBottom: '16px' }}>{testResults.b_votes} votes</div>
              </div>
            </div>

            {/* Stats Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '32px' }}>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><Users style={{ width: '28px', height: '28px', color: 'var(--color-accent-cyan)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '28px', fontWeight: '700' }}>{testResults.total_personas}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Total Personas</div></div>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><TrendingUp style={{ width: '28px', height: '28px', color: 'var(--color-accent-purple)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '28px', fontWeight: '700' }}>{testResults.avg_confidence.toFixed(1)}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Avg Confidence</div></div>
              <div className="card" style={{ padding: '24px', textAlign: 'center' }}><XCircle style={{ width: '28px', height: '28px', color: 'var(--color-text-muted)', margin: '0 auto 12px auto' }} /><div style={{ fontSize: '28px', fontWeight: '700' }}>{testResults.neither_votes}</div><div style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>Neither</div></div>
            </div>

            {/* Comparison Bar */}
            <div className="card" style={{ padding: '28px', marginBottom: '32px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('abCompare.headToHead')}</h3>
              <div style={{ display: 'flex', height: '48px', borderRadius: '12px', overflow: 'hidden' }}>
                <div style={{ width: `${testResults.a_percentage}%`, background: 'var(--color-accent-cyan)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '14px', color: '#000', transition: 'width 0.8s ease' }}>A: {testResults.a_percentage}%</div>
                <div style={{ width: `${testResults.b_percentage}%`, background: 'var(--color-accent-purple)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: '700', fontSize: '14px', color: '#fff', transition: 'width 0.8s ease' }}>B: {testResults.b_percentage}%</div>
              </div>
            </div>

            {/* Persona Details */}
            {testResults.results?.length > 0 && (
              <div className="card" style={{ padding: '28px' }}>
                <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>{t('abCompare.personaResponses')} ({testResults.results.length})</h3>
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
                            <span style={{ padding: '4px 12px', borderRadius: '12px', fontSize: '12px', fontWeight: '600', background: r.choice === 'A' ? 'rgba(6, 182, 212, 0.1)' : r.choice === 'B' ? 'rgba(168, 85, 247, 0.1)' : 'rgba(100,100,100,0.1)', color: r.choice === 'A' ? 'var(--color-accent-cyan)' : r.choice === 'B' ? 'var(--color-accent-purple)' : 'var(--color-text-muted)' }}>{r.choice}</span>
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

export default ABCompare
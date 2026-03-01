import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Filter, Lock, ChevronDown, ChevronUp } from 'lucide-react'

const FILTER_OPTIONS = {
  gender: [
    { value: 'Erkek', labelKey: 'filters.male', icon: '♂' },
    { value: 'Kadın', labelKey: 'filters.female', icon: '♀' },
  ],
  income: [
    { value: 'Düşük', labelKey: 'filters.incomeLow' },
    { value: 'Orta-Düşük', labelKey: 'filters.incomeLowerMid' },
    { value: 'Orta', labelKey: 'filters.incomeMiddle' },
    { value: 'Orta-Yüksek', labelKey: 'filters.incomeUpperMid' },
    { value: 'Yüksek', labelKey: 'filters.incomeHigh' },
  ],
  education: [
    { value: 'İlkokul', labelKey: 'filters.eduPrimary' },
    { value: 'Ortaokul', labelKey: 'filters.eduMiddle' },
    { value: 'Lise', labelKey: 'filters.eduHighSchool' },
    { value: 'Ön Lisans', labelKey: 'filters.eduAssociate' },
    { value: 'Üniversite', labelKey: 'filters.eduUniversity' },
    { value: 'Yüksek Lisans', labelKey: 'filters.eduMasters' },
    { value: 'Doktora', labelKey: 'filters.eduPhD' },
  ],
  buyingStyle: [
    { value: 'Planlı Alıcı', labelKey: 'filters.buyPlanner', icon: '📋' },
    { value: 'Anlık Alıcı', labelKey: 'filters.buyImpulsive', icon: '⚡' },
    { value: 'Araştırmacı', labelKey: 'filters.buyResearcher', icon: '🔍' },
    { value: 'Fırsat Avcısı', labelKey: 'filters.buyBargain', icon: '🏷️' },
    { value: 'Marka Bağımlısı', labelKey: 'filters.buyBrandLoyal', icon: '💎' },
  ],
  maritalStatus: [
    { value: 'Bekar', labelKey: 'filters.single' },
    { value: 'Evli', labelKey: 'filters.married' },
    { value: 'Boşanmış', labelKey: 'filters.divorced' },
  ],
  techAdoption: [
    { value: 'Erken Benimseyen', labelKey: 'filters.techEarlyAdopter' },
    { value: 'Erken Çoğunluk', labelKey: 'filters.techEarlyMajority' },
    { value: 'Geç Çoğunluk', labelKey: 'filters.techLateMajority' },
    { value: 'Gelenekçi', labelKey: 'filters.techTraditional' },
  ],
  onlineShopping: [
    { value: 'Hiç', labelKey: 'filters.shopNever' },
    { value: 'Ayda 1', labelKey: 'filters.shopMonthly' },
    { value: 'Haftada 1', labelKey: 'filters.shopWeekly' },
    { value: 'Her gün', labelKey: 'filters.shopDaily' },
  ],
  financialBehavior: [
    { value: 'Tasarrufçu', labelKey: 'filters.finSaver' },
    { value: 'Harcamacı', labelKey: 'filters.finSpender' },
    { value: 'Yatırımcı', labelKey: 'filters.finInvestor' },
    { value: 'Borç Kullanıcısı', labelKey: 'filters.finDebtUser' },
  ],
}

const PLAN_TIERS = {
  disposable: [],
  starter: [],
  pro: ['demographic'],
  business: ['demographic', 'behavioral'],
  enterprise: ['demographic', 'behavioral', 'advanced'],
}

function PersonaFilters({ planSlug, filters, onFiltersChange }) {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(false)
  const allowedGroups = PLAN_TIERS[planSlug] || []

  const hasDemographic = allowedGroups.includes('demographic')
  const hasBehavioral = allowedGroups.includes('behavioral')
  const hasAdvanced = allowedGroups.includes('advanced')

  const updateFilter = (key, value) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const toggleMulti = (key, value) => {
    const current = filters[key] || []
    const updated = current.includes(value)
      ? current.filter(v => v !== value)
      : [...current, value]
    updateFilter(key, updated.length > 0 ? updated : null)
  }

  const activeFilterCount = Object.values(filters).filter(v => v !== null && v !== undefined && (Array.isArray(v) ? v.length > 0 : true)).length

  if (planSlug === 'starter' || planSlug === 'disposable') {
    return (
      <div style={{ padding: '14px 20px', background: 'rgba(255,255,255,0.03)', borderRadius: '10px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px', border: '1px solid rgba(255,255,255,0.06)' }}>
        <Lock style={{ width: '16px', height: '16px', color: 'var(--color-text-muted)' }} />
        <span style={{ fontSize: '13px', color: 'var(--color-text-muted)' }}>
          <strong style={{ color: 'var(--color-text-secondary)' }}>{t('filters.title')}</strong> — {t('filters.upgradeToProDesc')}
        </span>
      </div>
    )
  }

  return (
    <div style={{ marginBottom: '24px' }}>
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex', alignItems: 'center', gap: '8px', width: '100%',
          padding: '12px 16px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)',
          borderRadius: isExpanded ? '10px 10px 0 0' : '10px', cursor: 'pointer',
          color: 'var(--color-text-primary)', fontSize: '14px', fontWeight: '600',
        }}
      >
        <Filter style={{ width: '15px', height: '15px', color: 'var(--color-accent-cyan)' }} />
        {t('filters.title')}
        {activeFilterCount > 0 && (
          <span style={{
            padding: '1px 8px', borderRadius: '10px', fontSize: '11px', fontWeight: '700',
            background: 'var(--color-accent-cyan)', color: '#000',
          }}>
            {activeFilterCount}
          </span>
        )}
        <span style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center' }}>
          {isExpanded
            ? <ChevronUp style={{ width: '16px', height: '16px', color: 'var(--color-text-muted)' }} />
            : <ChevronDown style={{ width: '16px', height: '16px', color: 'var(--color-text-muted)' }} />
          }
        </span>
      </button>

      {isExpanded && (
        <div style={{
          padding: '20px', background: 'rgba(255,255,255,0.03)',
          borderRadius: '0 0 10px 10px',
          border: '1px solid rgba(255,255,255,0.08)', borderTop: '1px solid rgba(255,255,255,0.04)',
        }}>

          {/* ── PRO: Demographic ── */}
          <FilterSection title={t('filters.demographic')} tier="Pro" unlocked={hasDemographic} t={t}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              {/* Left col */}
              <div>
                <Label text={t('filters.gender')} />
                <div style={{ display: 'flex', gap: '6px' }}>
                  <Chip active={!filters.gender} onClick={() => updateFilter('gender', null)} label={t('filters.all')} disabled={!hasDemographic} />
                  {FILTER_OPTIONS.gender.map(o => (
                    <Chip key={o.value} active={filters.gender === o.value} onClick={() => updateFilter('gender', o.value)} label={`${o.icon} ${t(o.labelKey)}`} disabled={!hasDemographic} />
                  ))}
                </div>
                <div style={{ marginTop: '14px' }}>
                  <Label text={`${t('filters.age')}: ${filters.min_age || 18} – ${filters.max_age || 80}`} />
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={rangeLabel}>{filters.min_age || 18}</span>
                    <input type="range" min="18" max="80" value={filters.min_age || 18}
                      onChange={(e) => { const v = Number(e.target.value); updateFilter('min_age', v > 18 ? v : null); if (filters.max_age && v > filters.max_age) updateFilter('max_age', v) }}
                      disabled={!hasDemographic} style={rangeStyle} />
                    <input type="range" min="18" max="80" value={filters.max_age || 80}
                      onChange={(e) => { const v = Number(e.target.value); updateFilter('max_age', v < 80 ? v : null); if (filters.min_age && v < filters.min_age) updateFilter('min_age', v) }}
                      disabled={!hasDemographic} style={rangeStyle} />
                    <span style={rangeLabel}>{filters.max_age || 80}</span>
                  </div>
                </div>
              </div>
              {/* Right col */}
              <div>
                <Label text={t('filters.incomeLevel')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.income.map(o => (
                    <Chip key={o.value} active={(filters.income_levels || []).includes(o.value)} onClick={() => toggleMulti('income_levels', o.value)} label={t(o.labelKey)} disabled={!hasDemographic} />
                  ))}
                </div>
              </div>
            </div>
          </FilterSection>

          {/* ── BUSINESS: Behavioral ── */}
          <FilterSection title={t('filters.behavioral')} tier="Business" unlocked={hasBehavioral} t={t}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
              <div>
                <Label text={t('filters.education')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.education.map(o => (
                    <Chip key={o.value} active={(filters.education_levels || []).includes(o.value)} onClick={() => toggleMulti('education_levels', o.value)} label={t(o.labelKey)} disabled={!hasBehavioral} />
                  ))}
                </div>
                <div style={{ marginTop: '12px' }}>
                  <Label text={t('filters.maritalStatus')} />
                  <div style={{ display: 'flex', gap: '5px' }}>
                    {FILTER_OPTIONS.maritalStatus.map(o => (
                      <Chip key={o.value} active={(filters.marital_statuses || []).includes(o.value)} onClick={() => toggleMulti('marital_statuses', o.value)} label={t(o.labelKey)} disabled={!hasBehavioral} />
                    ))}
                  </div>
                </div>
              </div>
              <div>
                <Label text={t('filters.buyingStyle')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.buyingStyle.map(o => (
                    <Chip key={o.value} active={(filters.buying_styles || []).includes(o.value)} onClick={() => toggleMulti('buying_styles', o.value)} label={`${o.icon} ${t(o.labelKey)}`} disabled={!hasBehavioral} />
                  ))}
                </div>
              </div>
            </div>
          </FilterSection>

          {/* ── ENTERPRISE: Advanced ── */}
          <FilterSection title={t('filters.advanced')} tier="Enterprise" unlocked={hasAdvanced} t={t}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
              <div>
                <Label text={t('filters.techAdoption')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.techAdoption.map(o => (
                    <Chip key={o.value} active={(filters.tech_adoptions || []).includes(o.value)} onClick={() => toggleMulti('tech_adoptions', o.value)} label={t(o.labelKey)} disabled={!hasAdvanced} />
                  ))}
                </div>
              </div>
              <div>
                <Label text={t('filters.shoppingFreq')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.onlineShopping.map(o => (
                    <Chip key={o.value} active={(filters.online_shopping_freqs || []).includes(o.value)} onClick={() => toggleMulti('online_shopping_freqs', o.value)} label={t(o.labelKey)} disabled={!hasAdvanced} />
                  ))}
                </div>
              </div>
              <div>
                <Label text={t('filters.financial')} />
                <div style={{ display: 'flex', gap: '5px', flexWrap: 'wrap' }}>
                  {FILTER_OPTIONS.financialBehavior.map(o => (
                    <Chip key={o.value} active={(filters.financial_behaviors || []).includes(o.value)} onClick={() => toggleMulti('financial_behaviors', o.value)} label={t(o.labelKey)} disabled={!hasAdvanced} />
                  ))}
                </div>
              </div>
            </div>
          </FilterSection>

          {activeFilterCount > 0 && (
            <div style={{ textAlign: 'right', marginTop: '8px' }}>
              <button type="button" onClick={() => onFiltersChange({})}
                style={{ padding: '5px 14px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.1)', background: 'transparent', color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: '12px' }}>
                {t('filters.clearAll')}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ── Shared Styles ──
const rangeLabel = { fontSize: '11px', color: 'var(--color-text-muted)', minWidth: '20px', textAlign: 'center' }
const rangeStyle = { flex: 1, accentColor: 'var(--color-accent-cyan)', height: '4px' }

// ── Sub-Components ──

function FilterSection({ title, tier, unlocked, children, t }) {
  return (
    <div style={{ marginBottom: '18px', position: 'relative' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
        <span style={{ fontSize: '11px', fontWeight: '700', color: 'var(--color-text-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>{title}</span>
        <span style={{
          padding: '1px 7px', borderRadius: '4px', fontSize: '10px', fontWeight: '600',
          background: unlocked ? 'rgba(16, 185, 129, 0.15)' : 'rgba(100, 100, 100, 0.15)',
          color: unlocked ? '#10b981' : 'var(--color-text-muted)',
        }}>
          {unlocked ? `✓ ${tier}` : `🔒 ${tier}`}
        </span>
      </div>
      <div style={{ opacity: unlocked ? 1 : 0.35, pointerEvents: unlocked ? 'auto' : 'none' }}>
        {children}
      </div>
      {!unlocked && (
        <div style={{
          position: 'absolute', top: '28px', left: 0, right: 0, bottom: 0,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          borderRadius: '6px', cursor: 'default',
        }}>
          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', background: 'var(--color-bg-primary)', padding: '4px 12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.08)' }}>
            {t('filters.upgradeToTier', { tier })}
          </span>
        </div>
      )}
    </div>
  )
}

function Label({ text }) {
  return <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: '6px', textTransform: 'uppercase', letterSpacing: '0.3px' }}>{text}</div>
}

function Chip({ active, onClick, label, disabled }) {
  return (
    <button type="button" onClick={disabled ? undefined : onClick}
      style={{
        padding: '4px 10px', borderRadius: '6px', fontSize: '11px', fontWeight: '500',
        border: active ? '1.5px solid var(--color-accent-cyan)' : '1px solid rgba(255,255,255,0.1)',
        background: active ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
        color: active ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)',
        cursor: disabled ? 'not-allowed' : 'pointer',
        transition: 'all 0.12s', lineHeight: '1.4',
      }}>
      {label}
    </button>
  )
}


export function cleanFiltersForAPI(filters) {
  const cleaned = {}
  if (filters.gender) cleaned.gender = filters.gender
  if (filters.min_age) cleaned.min_age = filters.min_age
  if (filters.max_age) cleaned.max_age = filters.max_age
  if (filters.income_levels?.length) cleaned.income_levels = filters.income_levels
  if (filters.education_levels?.length) cleaned.education_levels = filters.education_levels
  if (filters.buying_styles?.length) cleaned.buying_styles = filters.buying_styles
  if (filters.marital_statuses?.length) cleaned.marital_statuses = filters.marital_statuses
  if (filters.tech_adoptions?.length) cleaned.tech_adoptions = filters.tech_adoptions
  if (filters.online_shopping_freqs?.length) cleaned.online_shopping_freqs = filters.online_shopping_freqs
  if (filters.financial_behaviors?.length) cleaned.financial_behaviors = filters.financial_behaviors
  return Object.keys(cleaned).length > 0 ? cleaned : null
}

export default PersonaFilters
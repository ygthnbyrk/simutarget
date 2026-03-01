/**
 * Persona value translation utility.
 * DB always stores Turkish values (from persona factory).
 * This utility translates them to English when display language is EN.
 */

const TR_TO_EN = {
  // Income levels
  'Düşük': 'Low',
  'Orta-Düşük': 'Lower-Middle',
  'Orta': 'Middle',
  'Orta-Yüksek': 'Upper-Middle',
  'Yüksek': 'High',
  // Gender
  'Erkek': 'Male',
  'Kadın': 'Female',
  // Education
  'İlkokul': 'Primary School',
  'Ortaokul': 'Middle School',
  'Lise': 'High School',
  'Üniversite': 'University',
  'Yüksek Lisans': "Master's Degree",
  'Doktora': 'PhD',
  'Ön Lisans': 'Associate Degree',
  // Buying style
  'Planlı Alıcı': 'Planned Buyer',
  'Anlık Alıcı': 'Impulse Buyer',
  'Araştırmacı': 'Researcher',
  'Fırsat Avcısı': 'Deal Hunter',
  'Marka Bağımlısı': 'Brand Loyal',
  // Marital status
  'Bekar': 'Single',
  'Evli': 'Married',
  'Boşanmış': 'Divorced',
  'Dul': 'Widowed',
}

// Reverse map for EN → TR
const EN_TO_TR = Object.fromEntries(
  Object.entries(TR_TO_EN).map(([k, v]) => [v, k])
)

/**
 * Translate a persona field value based on current language.
 * @param {string} value - The raw value from DB (could be TR or EN)
 * @param {string} lang - Current UI language ('tr' or 'en')
 * @returns {string} Translated value
 */
export function translatePersonaValue(value, lang) {
  if (!value) return value

  if (lang === 'en') {
    // DB value is TR → translate to EN
    return TR_TO_EN[value] || value
  } else {
    // DB value might be EN (old data) → translate to TR
    return EN_TO_TR[value] || value
  }
}

/**
 * Shorthand: translate income level
 */
export function tIncome(value, lang) {
  return translatePersonaValue(value, lang)
}

/**
 * Shorthand: translate gender
 */
export function tGender(value, lang) {
  return translatePersonaValue(value, lang)
}

/**
 * Extract reasoning in the correct language.
 * DB stores reasoning as JSON: {"tr": "...", "en": "..."} or plain string (old data).
 * @param {string} reasoning - Raw reasoning from DB
 * @param {string} lang - Current UI language ('tr' or 'en')
 * @returns {string} Localized reasoning text
 */
export function getLocalizedReasoning(reasoning, lang) {
  if (!reasoning) return ''

  // Try parsing as JSON (new bilingual format)
  try {
    const parsed = typeof reasoning === 'string' ? JSON.parse(reasoning) : reasoning
    if (parsed && typeof parsed === 'object' && (parsed.tr || parsed.en)) {
      return parsed[lang] || parsed.tr || parsed.en || ''
    }
  } catch {
    // Not JSON — plain string (old data or already localized)
  }

  return reasoning
}

export default translatePersonaValue

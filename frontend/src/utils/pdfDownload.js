/**
 * PDF Report Download Utility
 * Downloads campaign PDF report via authenticated API call
 */

const API_BASE = import.meta.env.VITE_API_URL 
  ? `${import.meta.env.VITE_API_URL}/api/v1` 
  : '/api/v1'

export async function downloadCampaignPDF(campaignId, lang = 'en') {
  const token = localStorage.getItem('token')
  if (!token) {
    throw new Error('Not authenticated')
  }

  const response = await fetch(
    `${API_BASE}/campaigns/${campaignId}/download-pdf?lang=${lang}`,
    {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    }
  )

  if (response.status === 403) {
    throw new Error('PDF export requires Pro plan or higher.')
  }

  if (!response.ok) {
    const err = await response.json().catch(() => ({}))
    throw new Error(err.detail || 'PDF download failed')
  }

  // Get filename from header or generate one
  const disposition = response.headers.get('Content-Disposition')
  let filename = `SimuTarget_Report_${campaignId}.pdf`
  if (disposition) {
    const match = disposition.match(/filename="?([^"]+)"?/)
    if (match) filename = match[1]
  }

  // Trigger browser download
  const blob = await response.blob()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  window.URL.revokeObjectURL(url)

  return filename
}
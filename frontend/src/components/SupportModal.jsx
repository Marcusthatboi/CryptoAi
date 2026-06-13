import React, { useMemo, useState } from 'react'
import { cryptoAPI } from '../utils/api'
import { API_BASE } from '../utils/backendConfig'
import './SupportModal.css'

const ISSUE_CATEGORIES = [
  { value: 'billing', label: 'Billing and Payment' },
  { value: 'login', label: 'Login and Access' },
  { value: 'portfolio', label: 'Portfolio and Investments' },
  { value: 'ai_chat', label: 'AI Chat and Recommendations' },
  { value: 'other', label: 'Other' }
]

const CATEGORY_DEFAULT_SUBJECT = {
  billing: 'Billing Support Request',
  login: 'Login Support Request',
  portfolio: 'Portfolio Support Request',
  ai_chat: 'AI Chat Support Request',
  other: 'General Support Request'
}

const buildDiagnosticsText = ({ user, category }) => {
  const now = new Date().toISOString()
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || 'unknown'
  const onlineStatus = typeof navigator !== 'undefined' ? String(navigator.onLine) : 'unknown'
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent : 'unknown'
  const language = typeof navigator !== 'undefined' ? navigator.language : 'unknown'
  const currentUrl = typeof window !== 'undefined' ? window.location.href : 'unknown'

  return [
    'Auto Diagnostics',
    `- Timestamp (UTC): ${now}`,
    `- Timezone: ${timezone}`,
    `- Category: ${category}`,
    `- Username: ${user?.username || 'unknown'}`,
    `- User ID: ${user?.user_id || 'unknown'}`,
    `- Role: ${user?.role || 'unknown'}`,
    `- API Base: ${API_BASE}`,
    `- Current URL: ${currentUrl}`,
    `- Browser Language: ${language}`,
    `- Browser Online: ${onlineStatus}`,
    `- User Agent: ${userAgent}`
  ].join('\n')
}

export default function SupportModal({ visible, onClose, user, supportEmail }) {
  const [category, setCategory] = useState('billing')
  const [summary, setSummary] = useState('')
  const [details, setDetails] = useState('')
  const [copied, setCopied] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [statusMessage, setStatusMessage] = useState({ type: '', text: '' })

  const diagnostics = useMemo(() => buildDiagnosticsText({ user, category }), [user, category])

  const defaultSubject = CATEGORY_DEFAULT_SUBJECT[category] || CATEGORY_DEFAULT_SUBJECT.other

  const copyDiagnostics = async () => {
    try {
      await navigator.clipboard.writeText(diagnostics)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch (error) {
      console.warn('Could not copy diagnostics:', error)
    }
  }

  const submitSupportRequest = async () => {
    if (!summary.trim()) {
      setStatusMessage({ type: 'error', text: 'Please add a short summary before sending.' })
      return
    }

    try {
      setSubmitting(true)
      setStatusMessage({ type: '', text: '' })

      const response = await cryptoAPI.sendSupportRequest({
        category,
        summary: `${defaultSubject}: ${summary.trim()}`,
        details,
        diagnostics,
        current_url: window.location.href
      })

      setStatusMessage({
        type: 'success',
        text: response?.data?.message || 'Thanks, your message was sent successfully. Responses occur within 1-2 business days.'
      })
      setSummary('')
      setDetails('')
    } catch (error) {
      const status = error?.response?.status
      const detail = status === 404
        ? 'Support endpoint is unavailable. Please restart the backend to load latest routes, then try again.'
        : (error?.response?.data?.detail || `Could not send support request. You can still contact ${supportEmail} directly.`)
      setStatusMessage({ type: 'error', text: detail })
    } finally {
      setSubmitting(false)
    }
  }

  if (!visible) {
    return null
  }

  return (
    <div className="support-modal-overlay" onClick={onClose}>
      <div className="support-modal" onClick={(event) => event.stopPropagation()}>
        <div className="support-modal-header">
          <h3>Contact Support</h3>
          <button className="support-close-btn" onClick={onClose} aria-label="Close support modal">
            Close
          </button>
        </div>

        <p className="support-subtitle">
          Choose an issue type, add context, and send your request directly to support.
        </p>

        {statusMessage.text && (
          <div className={`support-status-message ${statusMessage.type}`}>
            {statusMessage.text}
          </div>
        )}

        <label className="support-label" htmlFor="support-category">
          Issue Category
        </label>
        <select
          id="support-category"
          className="support-select"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
        >
          {ISSUE_CATEGORIES.map((option) => (
            <option key={option.value} value={option.value}>{option.label}</option>
          ))}
        </select>

        <label className="support-label" htmlFor="support-summary">
          Short Summary
        </label>
        <input
          id="support-summary"
          className="support-input"
          type="text"
          value={summary}
          onChange={(event) => setSummary(event.target.value)}
          placeholder="Example: Charged twice but upgrade not visible"
        />

        <label className="support-label" htmlFor="support-details">
          Details
        </label>
        <textarea
          id="support-details"
          className="support-textarea"
          value={details}
          onChange={(event) => setDetails(event.target.value)}
          rows={4}
          placeholder="What happened, when it happened, and what you expected."
        />

        <div className="support-diagnostics-card">
          <div className="support-diagnostics-header">
            <strong>Auto Diagnostics</strong>
            <button className="support-copy-btn" onClick={copyDiagnostics}>
              {copied ? 'Copied' : 'Copy Diagnostics'}
            </button>
          </div>
          <pre className="support-diagnostics-text">{diagnostics}</pre>
        </div>

        <div className="support-actions">
          <button className="support-secondary-btn" onClick={onClose} disabled={submitting}>Cancel</button>
          <button
            className="support-primary-btn"
            onClick={submitSupportRequest}
            disabled={submitting || !summary.trim()}
          >
            {submitting ? 'Sending...' : 'Send Support Request'}
          </button>
        </div>
      </div>
    </div>
  )
}

import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import { useLanguage } from '../context/LanguageContext'
import './IntegrationsPage.css'

const PLATFORM_CONFIG = [
  { key: 'slack', label: 'Slack' },
  { key: 'teams', label: 'Microsoft Teams' },
  { key: 'google_chat', label: 'Google Chat (Google Workspace)' }
]

export default function IntegrationsPage() {
  const [platforms, setPlatforms] = useState({})
  const [configuredCount, setConfiguredCount] = useState(0)
  const { t } = useLanguage()
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [testLoadingKey, setTestLoadingKey] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const loadStatus = async ({ quiet = false } = {}) => {
    try {
      if (!quiet) {
        setLoading(true)
      } else {
        setRefreshing(true)
      }
      setError('')
      const response = await cryptoAPI.getIntegrationsStatus()
      setPlatforms(response?.data?.platforms || {})
      setConfiguredCount(Number(response?.data?.configured_count) || 0)
    } catch (statusError) {
      setError(statusError?.response?.data?.detail || 'Failed to load integrations status.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  const handleTest = async (platform) => {
    try {
      setTestLoadingKey(platform)
      setMessage('')
      setError('')
      const response = await cryptoAPI.sendIntegrationTest(platform)
      setMessage(response?.data?.message || `Test message sent to ${platform}.`)
      await loadStatus({ quiet: true })
    } catch (testError) {
      setError(testError?.response?.data?.detail || `Failed to send test message to ${platform}.`)
    } finally {
      setTestLoadingKey('')
    }
  }

  return (
    <div className="integrations-page">
      <header className="integrations-hero">
        <div>
          <p className="integrations-eyebrow">Collaboration Integrations</p>
          <h1>{t('integrations_title', 'Connect Slack, Teams, and Google Chat')}</h1>
          <p>
            {t('integrations_subtitle', 'Verify webhook readiness and send test notifications without leaving the app.')}
          </p>
        </div>
        <div className="integrations-hero-actions">
          <span className="integrations-pill">Configured: {configuredCount} / {PLATFORM_CONFIG.length}</span>
          <Link to="/dashboard" className="integrations-back-link">{t('integrations_back_dashboard', 'Back to dashboard')}</Link>
        </div>
      </header>

      {(message || error) && (
        <div className={`integrations-banner ${error ? 'error' : 'success'}`}>
          {error || message}
        </div>
      )}

      <section className="integrations-toolbar">
        <button
          className="refresh-btn"
          onClick={() => loadStatus({ quiet: true })}
          disabled={refreshing || loading}
        >
          {refreshing ? t('integrations_refreshing', 'Refreshing...') : t('integrations_refresh', 'Refresh Status')}
        </button>
      </section>

      <section className="integrations-grid">
        {PLATFORM_CONFIG.map((platform) => {
          const platformStatus = platforms?.[platform.key]
          const configured = Boolean(platformStatus?.configured)
          return (
            <article className="integration-card" key={platform.key}>
              <h2>{platform.label}</h2>
              <div className={`status-pill ${configured ? 'ready' : 'missing'}`}>
                {loading ? 'Loading...' : configured ? t('integrations_configured', 'Configured') : t('integrations_not_configured', 'Not configured')}
              </div>
              <p className="diagnostic-text">
                {configured
                  ? 'Webhook URL detected. Test send is available.'
                  : 'Missing webhook URL. Add environment variable on backend and restart.'}
              </p>
              <button
                className="test-btn"
                disabled={!configured || testLoadingKey === platform.key || loading}
                onClick={() => handleTest(platform.key)}
              >
                {testLoadingKey === platform.key ? t('integrations_sending', 'Sending...') : t('integrations_send_test', 'Send Test Message')}
              </button>
            </article>
          )
        })}
      </section>

      <section className="integrations-diagnostics">
        <h3>Diagnostics</h3>
        <p>If a platform shows not configured, set the related backend environment variable:</p>
        <ul>
          <li>SLACK_WEBHOOK_URL</li>
          <li>TEAMS_WEBHOOK_URL</li>
          <li>GOOGLE_CHAT_WEBHOOK_URL</li>
        </ul>
        <p>After updating environment values, restart the backend and refresh this page.</p>
      </section>
    </div>
  )
}
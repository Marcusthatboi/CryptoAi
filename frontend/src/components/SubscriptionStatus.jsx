import React, { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import { useLanguage } from '../context/LanguageContext'
import './SubscriptionStatus.css'

export default function SubscriptionStatus() {
  const { token, user } = useAuth()
  const { t } = useLanguage()
  const navigate = useNavigate()
  const [subscription, setSubscription] = useState(null)
  const [usageSummary, setUsageSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastSyncedAt, setLastSyncedAt] = useState(null)

  useEffect(() => {
    if (token && user?.user_id) {
      fetchSubscription()

      const handleUsageUpdated = () => {
        fetchSubscription()
      }
      window.addEventListener('subscription-usage-updated', handleUsageUpdated)

      const interval = setInterval(fetchSubscription, 45000)
      return () => {
        clearInterval(interval)
        window.removeEventListener('subscription-usage-updated', handleUsageUpdated)
      }
    }
  }, [token, user?.user_id])

  const fetchSubscription = async () => {
    try {
      const [statusResponse, usageResponse] = await Promise.all([
        cryptoAPI.getSubscriptionStatus(),
        cryptoAPI.getSubscriptionUsageSummary()
      ])

      setSubscription(statusResponse.data)
      setUsageSummary(usageResponse.data)
      setLastSyncedAt(new Date())
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch subscription:', err)
      setLoading(false)
    }
  }

  const getTierBadge = (tier) => {
    const badges = {
      free: { color: '#999', icon: '🟢', label: 'Free' },
      pro: { color: '#667eea', icon: '⭐', label: 'Pro' },
      premium: { color: '#e91e63', icon: '👑', label: 'Premium' }
    }
    return badges[tier] || badges.free
  }

  if (loading || !subscription) {
    return null
  }

  const badge = getTierBadge(subscription.tier)
  const daysLeft = subscription.current_period_end
    ? Math.ceil(
        (new Date(subscription.current_period_end) - new Date()) /
          (1000 * 60 * 60 * 24)
      )
    : null

  const hasUnlimitedSignals = usageSummary?.signals_daily_limit === null
  const signalsLimit = usageSummary?.signals_daily_limit || 0
  const signalsUsed = usageSummary?.signals_used_today || 0
  const usagePercent = hasUnlimitedSignals
    ? 0
    : Math.min((signalsUsed / Math.max(signalsLimit, 1)) * 100, 100)

  return (
    <div className="subscription-status-container">
      <div
        className="subscription-status"
        style={{ borderLeftColor: badge.color }}
      >
        <div className="status-header">
          <div className="tier-info">
            <span className="tier-icon">{badge.icon}</span>
            <div className="tier-details">
              <h3 className="tier-name">{badge.label} Plan</h3>
              <p className="tier-status">{subscription.status}</p>
            </div>
          </div>

          {subscription.tier !== 'free' && (
            <div className="renewal-info">
              <p className="renewal-text">{t('sub_renews_in', 'Renews in')} {daysLeft} {t('sub_days', 'days')}</p>
              <button
                className="manage-btn"
                onClick={() => navigate('/pricing')}
              >
                {t('sub_manage_plan', 'Manage Plan')}
              </button>
            </div>
          )}

          {subscription.tier === 'free' && (
            <button
              className="upgrade-btn-mini"
              onClick={() => navigate('/pricing')}
            >
              {t('sub_upgrade_plan', 'Upgrade Plan')} ↗
            </button>
          )}
        </div>

        {subscription.tier === 'free' && (
          <div className="upgrade-prompt">
            <p>🚀 {t('sub_upgrade_prompt', 'Upgrade to Pro or Premium to unlock advanced AI signals and real-time alerts')}</p>
          </div>
        )}
      </div>

      {usageSummary && (
        <div className="usage-summary-card">
          <div className="usage-summary-header">
            <h4>{t('sub_today_usage', "Today's Usage")}</h4>
            <div className="usage-summary-header-right">
              <span className="usage-date">{usageSummary.date}</span>
              <button className="usage-refresh-btn" onClick={fetchSubscription}>
                {t('common_refresh', 'Refresh')}
              </button>
            </div>
          </div>

          {lastSyncedAt && (
            <p className="usage-last-synced">
              {t('sub_updated', 'Updated')} {lastSyncedAt.toLocaleTimeString()}
            </p>
          )}

          <div className="usage-row">
            <span className="usage-label">Signals</span>
            <span className="usage-value">
              {hasUnlimitedSignals
                ? `${signalsUsed} used (unlimited)`
                : `${signalsUsed}/${signalsLimit} used`}
            </span>
          </div>

          {!hasUnlimitedSignals && (
            <div className="usage-progress-track">
              <div
                className="usage-progress-fill"
                style={{ width: `${usagePercent}%` }}
              ></div>
            </div>
          )}

          <div className="usage-meta-grid">
            <div className="usage-meta-item">
              <span className="usage-meta-label">Remaining</span>
              <span className="usage-meta-value">
                {hasUnlimitedSignals ? 'Unlimited' : usageSummary.signals_remaining_today}
              </span>
            </div>
            <div className="usage-meta-item">
              <span className="usage-meta-label">Alerts</span>
              <span className="usage-meta-value">{usageSummary.alerts_enabled ? 'Enabled' : 'Locked'}</span>
            </div>
            <div className="usage-meta-item">
              <span className="usage-meta-label">History</span>
              <span className="usage-meta-value">
                {usageSummary.history_days ? `${usageSummary.history_days}d` : 'Locked'}
              </span>
            </div>
            <div className="usage-meta-item">
              <span className="usage-meta-label">API / hour</span>
              <span className="usage-meta-value">
                {usageSummary.api_calls_used_this_hour}/{usageSummary.api_calls_per_hour}
              </span>
            </div>
            <div className="usage-meta-item">
              <span className="usage-meta-label">Signals Reset</span>
              <span className="usage-meta-value">
                {usageSummary.daily_reset_at
                  ? new Date(usageSummary.daily_reset_at).toLocaleTimeString()
                  : 'N/A'}
              </span>
            </div>
            <div className="usage-meta-item">
              <span className="usage-meta-label">API Reset</span>
              <span className="usage-meta-value">
                {usageSummary.hourly_reset_at
                  ? new Date(usageSummary.hourly_reset_at).toLocaleTimeString()
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Tier Benefits Preview */}
      <div className="tier-benefits">
        <div className="benefit-item">
          <span className="benefit-icon">
            {subscription.tier === 'premium'
              ? '∞'
              : subscription.tier === 'pro'
              ? '100'
              : '10'}
          </span>
          <span className="benefit-text">Signals/Day</span>
        </div>

        <div className="benefit-item">
          <span className="benefit-icon">
            {subscription.tier === 'premium' || subscription.tier === 'pro'
              ? '✓'
              : '✗'}
          </span>
          <span className="benefit-text">Real-time Alerts</span>
        </div>

        <div className="benefit-item">
          <span className="benefit-icon">
            {subscription.tier === 'premium'
              ? '1y'
              : subscription.tier === 'pro'
              ? '30d'
              : '-'}
          </span>
          <span className="benefit-text">Signal History</span>
        </div>

        <div className="benefit-item">
          <span className="benefit-icon">
            {subscription.tier === 'premium' ? '✓' : '✗'}
          </span>
          <span className="benefit-text">Premium Support</span>
        </div>
      </div>
    </div>
  )
}

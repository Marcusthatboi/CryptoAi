import React, { useState, useEffect, useRef } from 'react'
import { cryptoAPI } from '../utils/api'
import UpgradePrompt from './UpgradePrompt'
import './AlertPanel.css'

const NOTIFICATION_PROMPT_KEY = 'price-alert-notification-prompted'

const getAlertId = (alert) => {
  const ts = alert?.timestamp || ''
  return `${alert?.crypto_id || ''}:${alert?.direction || ''}:${ts}`
}

const formatAlertNotificationBody = (alert) => {
  const change = Number(alert?.price_change_percent || 0)
  const previous = Number(alert?.previous_price || 0)
  const current = Number(alert?.current_price || 0)
  const signedChange = `${change > 0 ? '+' : ''}${change.toFixed(2)}%`
  return `${signedChange} (${previous.toFixed(2)} -> ${current.toFixed(2)})`
}

export default function AlertPanel() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [upgradeRequired, setUpgradeRequired] = useState(false)
  const [threshold, setThreshold] = useState(5)
  const [lastCheckedAt, setLastCheckedAt] = useState(null)
  const [notificationPermission, setNotificationPermission] = useState(() => {
    if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported'
    return window.Notification.permission
  })
  const [autoBuyLoading, setAutoBuyLoading] = useState(false)
  const [autoBuyConfig, setAutoBuyConfig] = useState({
    enabled: false,
    direction: 'down',
    amount_per_order_usd: 50,
    max_orders_per_day: 3,
    cooldown_minutes: 30,
    orders_today: 0
  })
  const [autoBuyMessage, setAutoBuyMessage] = useState('')
  const [recentAutoBuys, setRecentAutoBuys] = useState([])
  const seenAlertIdsRef = useRef(new Set())

  useEffect(() => {
    fetchAlerts(5)
    loadAutoBuyConfig()
    const interval = setInterval(() => fetchAlerts(threshold), 60000) // Refresh every 60 seconds
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    fetchAlerts(threshold)
  }, [threshold])

  const askNotificationPermission = async () => {
    if (typeof window === 'undefined' || !('Notification' in window)) {
      setNotificationPermission('unsupported')
      return
    }

    try {
      const permission = await window.Notification.requestPermission()
      setNotificationPermission(permission)
      localStorage.setItem(NOTIFICATION_PROMPT_KEY, '1')
    } catch (permissionError) {
      console.error('Failed requesting notification permission:', permissionError)
    }
  }

  useEffect(() => {
    if (upgradeRequired) {
      return
    }

    if (notificationPermission !== 'default') {
      return
    }

    const alreadyPrompted = localStorage.getItem(NOTIFICATION_PROMPT_KEY)
    if (!alreadyPrompted) {
      askNotificationPermission()
    }
  }, [notificationPermission, upgradeRequired])

  const notifyNewAlerts = (incomingAlerts) => {
    const isNotificationsAllowed = notificationPermission === 'granted' && typeof window !== 'undefined' && 'Notification' in window
    const nextSeenIds = new Set(seenAlertIdsRef.current)

    for (const alert of incomingAlerts) {
      const alertId = getAlertId(alert)

      if (!alertId) {
        continue
      }

      const isNewAlert = !nextSeenIds.has(alertId)

      if (isNewAlert && isNotificationsAllowed) {
        const symbol = (alert.crypto_id || 'CRYPTO').toUpperCase()
        const direction = alert.direction === 'UP' ? 'Price Surge' : 'Price Drop'

        try {
          new window.Notification(`${symbol} ${direction}`, {
            body: formatAlertNotificationBody(alert),
            tag: alertId
          })
        } catch (notificationError) {
          console.error('Failed to send browser notification:', notificationError)
        }
      }

      nextSeenIds.add(alertId)
    }

    seenAlertIdsRef.current = nextSeenIds
  }

  const loadAutoBuyConfig = async () => {
    try {
      const response = await cryptoAPI.getAlertAutoBuyConfig()
      const payload = response?.data || {}
      setAutoBuyConfig((current) => ({
        ...current,
        ...payload
      }))
      setAutoBuyMessage('')
    } catch (configError) {
      if (configError?.response?.status !== 401) {
        console.error('Failed to load auto-buy config:', configError)
      }
    }
  }

  const loadRecentAutoBuyExecutions = async () => {
    try {
      const response = await cryptoAPI.getUserPortfolio({ timeout: 20000, retryAttempts: 0 })
      const portfolio = response?.data || {}
      const activityLog = Array.isArray(portfolio.activity_log) ? portfolio.activity_log : []

      const rows = activityLog
        .filter((entry) => entry?.event === 'auto_buy_alert')
        .sort((a, b) => new Date(b?.timestamp || 0).getTime() - new Date(a?.timestamp || 0).getTime())
        .slice(0, 8)

      setRecentAutoBuys(rows)
    } catch (executionError) {
      if (executionError?.response?.status !== 401) {
        console.error('Failed to load recent auto-buy executions:', executionError)
      }
      setRecentAutoBuys([])
    }
  }

  const saveAutoBuyConfig = async () => {
    try {
      setAutoBuyLoading(true)
      const payload = {
        enabled: !!autoBuyConfig.enabled,
        direction: String(autoBuyConfig.direction || 'down'),
        amount_per_order_usd: Number(autoBuyConfig.amount_per_order_usd || 0),
        max_orders_per_day: Number(autoBuyConfig.max_orders_per_day || 0),
        cooldown_minutes: Number(autoBuyConfig.cooldown_minutes || 0)
      }
      const response = await cryptoAPI.updateAlertAutoBuyConfig(payload)
      setAutoBuyConfig((current) => ({ ...current, ...(response?.data || {}) }))
      setAutoBuyMessage('Auto-buy settings saved.')
      await loadRecentAutoBuyExecutions()
    } catch (saveError) {
      const statusCode = saveError?.response?.status
      const detail = saveError?.response?.data?.detail || saveError?.message || 'Failed to save auto-buy settings.'

      if (statusCode === 401) {
        setAutoBuyMessage(`Save failed [HTTP ${statusCode}]: Authentication required. Please sign in again.`)
      } else if (statusCode) {
        setAutoBuyMessage(`Save failed [HTTP ${statusCode}]: ${detail}`)
      } else {
        setAutoBuyMessage(`Save failed: ${detail}`)
      }
    } finally {
      setAutoBuyLoading(false)
    }
  }

  const fetchAlerts = async (activeThreshold = threshold) => {
    try {
      setLoading(true)
      const response = await cryptoAPI.getAlerts(activeThreshold)
      const nextAlerts = Array.isArray(response.data) ? response.data : []
      setAlerts(nextAlerts)
      notifyNewAlerts(nextAlerts)
      setError(null)
      setUpgradeRequired(false)
      setLastCheckedAt(new Date())
      await loadRecentAutoBuyExecutions()
    } catch (err) {
      if (err?.response?.status === 403) {
        setUpgradeRequired(true)
        setError('Real-time alerts are available on Pro and Premium plans.')
        setAlerts([])
      } else {
        console.error(err)
        setUpgradeRequired(false)
        setError('Failed to fetch alerts')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="alert-panel">
      <div className="panel-header">
        <h3>🚨 Price Alerts</h3>
        <button onClick={() => fetchAlerts(threshold)} disabled={loading} className="refresh-btn">
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      <div className="alert-engine-status">
        <strong>Alert engine:</strong> Active • polling every 60s • threshold {Number(threshold).toFixed(1)}%
        {lastCheckedAt && <span> • last check {lastCheckedAt.toLocaleTimeString()}</span>}
      </div>

      <div className="threshold-controls">
        <label htmlFor="alert-threshold">Trigger Threshold (%)</label>
        <input
          id="alert-threshold"
          type="number"
          min="0.5"
          max="25"
          step="0.5"
          value={threshold}
          onChange={(e) => setThreshold(Math.min(25, Math.max(0.5, Number(e.target.value || 5))))}
        />
      </div>

      <div className="notification-controls">
        <span className="notification-status">
          Notifications: {notificationPermission === 'granted' ? 'Enabled' : notificationPermission === 'unsupported' ? 'Unsupported' : 'Disabled'}
        </span>
        {notificationPermission !== 'granted' && notificationPermission !== 'unsupported' && (
          <button className="notification-btn" onClick={askNotificationPermission}>
            Enable Browser Notifications
          </button>
        )}
      </div>

      <div className="auto-buy-controls">
        <div className="auto-buy-header">
          <h4>Auto-Buy On Alert (Practice Money)</h4>
          <label className="auto-buy-toggle">
            <input
              type="checkbox"
              checked={!!autoBuyConfig.enabled}
              onChange={(e) => setAutoBuyConfig((current) => ({ ...current, enabled: e.target.checked }))}
            />
            <span>{autoBuyConfig.enabled ? 'Enabled' : 'Disabled'}</span>
          </label>
        </div>

        <div className="auto-buy-grid">
          <label>
            Direction
            <select
              value={autoBuyConfig.direction || 'down'}
              onChange={(e) => setAutoBuyConfig((current) => ({ ...current, direction: e.target.value }))}
            >
              <option value="down">Buy Dips Only</option>
              <option value="up">Buy Breakouts Only</option>
              <option value="both">Both</option>
            </select>
          </label>

          <label>
            Amount per order ($)
            <input
              type="number"
              min="1"
              step="1"
              value={autoBuyConfig.amount_per_order_usd ?? 50}
              onChange={(e) => setAutoBuyConfig((current) => ({ ...current, amount_per_order_usd: Number(e.target.value || 0) }))}
            />
          </label>

          <label>
            Max orders / day
            <input
              type="number"
              min="1"
              max="100"
              step="1"
              value={autoBuyConfig.max_orders_per_day ?? 3}
              onChange={(e) => setAutoBuyConfig((current) => ({ ...current, max_orders_per_day: Number(e.target.value || 0) }))}
            />
          </label>

          <label>
            Cooldown (minutes)
            <input
              type="number"
              min="1"
              max="1440"
              step="1"
              value={autoBuyConfig.cooldown_minutes ?? 30}
              onChange={(e) => setAutoBuyConfig((current) => ({ ...current, cooldown_minutes: Number(e.target.value || 0) }))}
            />
          </label>
        </div>

        <div className="auto-buy-footer">
          <span>Orders placed today: {Number(autoBuyConfig.orders_today || 0)}</span>
          <button onClick={saveAutoBuyConfig} disabled={autoBuyLoading} className="auto-buy-save-btn">
            {autoBuyLoading ? 'Saving...' : 'Save Auto-Buy'}
          </button>
        </div>

        {autoBuyMessage && <div className="auto-buy-message">{autoBuyMessage}</div>}

        <div className="auto-buy-executions">
          <h5>Recent Auto-Buy Executions</h5>
          {recentAutoBuys.length === 0 ? (
            <p className="no-executions">No auto-buy executions yet.</p>
          ) : (
            <div className="execution-list">
              {recentAutoBuys.map((entry, index) => (
                <div key={`${entry.timestamp || index}-${entry.symbol || 'AUTO'}`} className="execution-item">
                  <span className="execution-symbol">{String(entry.symbol || 'UNKNOWN').toUpperCase()}</span>
                  <span className="execution-meta">
                    ${Number(entry.total_value || 0).toFixed(2)} @ ${Number(entry.price || 0).toFixed(2)}
                  </span>
                  <span className="execution-time">{new Date(entry.timestamp).toLocaleString()}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {upgradeRequired && (
        <UpgradePrompt
          title="Pro/Premium feature"
          message="Unlock instant alert notifications by upgrading your plan."
        />
      )}

      <div className="alerts-list">
        {alerts.length === 0 ? (
          <div className="no-alerts">
            <p>✓ No alerts triggered</p>
            <small>Threshold: {Number(threshold).toFixed(1)}% price change</small>
          </div>
        ) : (
          alerts.map((alert, idx) => (
            <div key={idx} className={`alert-item alert-${alert.direction.toLowerCase()}`}>
              <div className="alert-icon">
                {alert.direction === 'UP' ? '📈' : '📉'}
              </div>
              <div className="alert-content">
                <h4>{alert.crypto_id.toUpperCase()}</h4>
                <p className="change">
                  {alert.price_change_percent > 0 ? '+' : ''}{alert.price_change_percent.toFixed(2)}%
                </p>
                <p className="price-range">
                  ${alert.previous_price.toFixed(2)} → ${alert.current_price.toFixed(2)}
                </p>
                <small>{new Date(alert.timestamp).toLocaleString()}</small>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

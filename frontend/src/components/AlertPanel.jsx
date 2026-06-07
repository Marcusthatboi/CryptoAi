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
  const [notificationPermission, setNotificationPermission] = useState(() => {
    if (typeof window === 'undefined' || !('Notification' in window)) return 'unsupported'
    return window.Notification.permission
  })
  const seenAlertIdsRef = useRef(new Set())

  useEffect(() => {
    fetchAlerts()
    const interval = setInterval(fetchAlerts, 60000) // Refresh every 60 seconds
    return () => clearInterval(interval)
  }, [])

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

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const response = await cryptoAPI.getAlerts()
      const nextAlerts = Array.isArray(response.data) ? response.data : []
      setAlerts(nextAlerts)
      notifyNewAlerts(nextAlerts)
      setError(null)
      setUpgradeRequired(false)
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
        <button onClick={fetchAlerts} disabled={loading} className="refresh-btn">
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
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
            <small>Threshold: 5% price change</small>
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

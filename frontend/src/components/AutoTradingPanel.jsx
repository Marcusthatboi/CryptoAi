import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import './AutoTradingPanel.css'

const formatCurrency = (value) => `$${Number(value || 0).toFixed(2)}`
const AUTO_TRADING_REFRESH_MS = 45000

// Cache with 2-minute TTL
const CACHE_TTL = 120000
const autoTradeCache = {
  data: null,
  timestamp: 0,
  isValid() { return Date.now() - this.timestamp < CACHE_TTL }
}

export default function AutoTradingPanel() {
  const [autoTrades, setAutoTrades] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    fetchAutoTrades()
    const intervalId = setInterval(() => {
      fetchAutoTrades({ background: true })
    }, AUTO_TRADING_REFRESH_MS)
    return () => {
      mountedRef.current = false
      clearInterval(intervalId)
    }
  }, [])

  const fetchAutoTrades = async ({ background = false } = {}) => {
    try {
      const token = localStorage.getItem('token')
      if (!token) {
        if (mountedRef.current) {
          setAutoTrades([])
          setError('Please log in to view auto trading data.')
          setLoading(false)
        }
        return
      }

      // Return cached data if valid
      if (autoTradeCache.isValid() && autoTradeCache.data) {
        setAutoTrades(autoTradeCache.data)
        setLoading(false)
        return
      }

      if (!background) {
        setLoading(true)
      }

      const response = await cryptoAPI.getAllActiveAutoTradingCoins({ timeout: 30000, retryAttempts: 1 })
      const trades = response.data?.active_trades || []
      
      if (mountedRef.current) {
        // Update cache
        autoTradeCache.data = trades
        autoTradeCache.timestamp = Date.now()
        
        setAutoTrades(trades)
        setError(null)
      }
    } catch (err) {
      if (mountedRef.current) {
        console.error('Failed to fetch auto trades:', err)
        const detail = err?.response?.data?.detail
        if (err?.response?.status === 401) {
          setError('Please log in to view auto trading data.')
        } else if (detail && detail.includes('Premium')) {
          setError('Premium subscription required.')
        } else if (err?.code === 'ECONNABORTED' && autoTradeCache.data) {
          setAutoTrades(autoTradeCache.data)
          setError('Live refresh delayed. Showing last known auto trading data.')
        } else {
          setError('Failed to load auto trading data.')
        }
        if (!autoTradeCache.data) {
          setAutoTrades([])
        }
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false)
      }
    }
  }

  if (loading) {
    return (
      <div className="auto-trading-panel">
        <div className="loading">Loading auto trading data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="auto-trading-panel">
        <div className="error-message">{error}</div>
        <button className="setup-btn" onClick={() => fetchAutoTrades()}>
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="auto-trading-panel">
      <div className="panel-header">
        <h3>🤖 Auto Trading Status</h3>
        <button 
          className="manage-btn"
          onClick={() => navigate('/auto-trading')}
        >
          Manage
        </button>
      </div>

      {autoTrades && autoTrades.length > 0 ? (
        <div className="auto-trading-content">
          <div className="stats-row">
            <div className="stat-card">
              <span className="stat-label">Active Trades</span>
              <span className="stat-value">{autoTrades.length}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">Total P&L</span>
              <span className={`stat-value ${(autoTrades.reduce((sum, t) => sum + (t.total_profit_loss || 0), 0)) >= 0 ? 'positive' : 'negative'}`}>
                {formatCurrency(autoTrades.reduce((sum, t) => sum + (t.total_profit_loss || 0), 0))}
              </span>
            </div>
          </div>

          <div className="trades-list">
            <div className="trades-header">
              <span>Symbol</span>
              <span>Buy %</span>
              <span>Sell %</span>
              <span>Status</span>
            </div>
            {autoTrades.slice(0, 5).map((trade) => (
              <div key={trade.symbol} className="trade-row">
                <span className="trade-symbol">{trade.symbol || 'N/A'}</span>
                <span className="trade-buy">{(trade.buy_percentage || 0).toFixed(1)}%</span>
                <span className="trade-sell">{(trade.sell_percentage || 0).toFixed(1)}%</span>
                <span className="trade-status">
                  {trade.enabled ? <span className="status-active">🟢 Active</span> : <span className="status-inactive">⚫ Inactive</span>}
                </span>
              </div>
            ))}
          </div>

          {autoTrades.length > 5 && (
            <div className="trades-count">
              +{autoTrades.length - 5} more
            </div>
          )}

          <button 
            className="full-view-btn"
            onClick={() => navigate('/auto-trading')}
          >
            View Full Dashboard →
          </button>
        </div>
      ) : (
        <div className="empty-state">
          <p>No active auto trading configured yet.</p>
          <p>Enable auto trading on individual crypto pages or visit the auto trading dashboard to get started.</p>
          <button 
            className="setup-btn"
            onClick={() => navigate('/auto-trading')}
          >
            Set Up Auto Trading
          </button>
        </div>
      )}
    </div>
  )
}

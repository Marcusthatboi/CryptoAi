import React, { useState, useEffect } from 'react'
import { cryptoAPI } from '../utils/api'
import './PortfolioPanel.css'

const formatCurrency = (value) => `$${Number(value || 0).toFixed(2)}`

const normalizeType = (type) => {
  const value = String(type || '').toLowerCase()
  if (value === 'real_money') return 'real_money'
  return 'fake_money'
}

const buildSegment = (holdings) => {
  const holdingsValue = holdings.reduce((sum, holding) => sum + Number(holding.total_value || 0), 0)
  const topHoldings = [...holdings]
    .sort((a, b) => Number(b.total_value || 0) - Number(a.total_value || 0))
    .slice(0, 3)

  return {
    holdings,
    holdingsValue,
    topHoldings
  }
}

export default function PortfolioPanel() {
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchPortfolio()
  }, [])

  const fetchPortfolio = async () => {
    try {
      setLoading(true)
      const response = await cryptoAPI.getUserPortfolio()
      setPortfolio(response.data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)
      const detail = err?.response?.data?.detail
      setError(detail || 'Failed to load portfolio data. Please retry.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="portfolio-panel">Loading portfolio...</div>
  if (error) {
    return (
      <div className="portfolio-panel error">
        <h2>Portfolio Overview</h2>
        <p>{error}</p>
        <button className="portfolio-retry-btn" onClick={fetchPortfolio}>Retry</button>
      </div>
    )
  }
  if (!portfolio) return <div className="portfolio-panel">No portfolio data</div>

  const holdings = portfolio.holdings || []
  const fakeHoldings = holdings.filter((holding) => normalizeType(holding.investment_type) === 'fake_money')
  const realHoldings = holdings.filter((holding) => normalizeType(holding.investment_type) === 'real_money')

  const fakeSegment = buildSegment(fakeHoldings)
  const realSegment = buildSegment(realHoldings)

  const totalHoldingsValue = fakeSegment.holdingsValue + realSegment.holdingsValue
  const cash = Number(portfolio.cash || 0)
  const computedPortfolioValue = cash + totalHoldingsValue
  const totalPortfolioValue = Number(portfolio.total_value || computedPortfolioValue)

  const renderSegment = (title, typeClass, segment, icon) => (
    <div className={`portfolio-details portfolio-segment ${typeClass}`}>
      <h3>{icon} {title}</h3>
      <div className="segment-stats">
        <div className="segment-stat">
          <label>Holdings Value</label>
          <span className="segment-stat-value">{formatCurrency(segment.holdingsValue)}</span>
        </div>
        <div className="segment-stat">
          <label>Active Holdings</label>
          <span className="segment-stat-value">{segment.holdings.length}</span>
        </div>
      </div>

      <h4>Top Holdings by Value</h4>
      {segment.topHoldings.length > 0 ? (
        <ul>
          {segment.topHoldings.map((holding, index) => (
            <li key={`${holding.symbol}-${index}`}>
              <span>{holding.symbol || 'N/A'}</span>
              <span>{formatCurrency(holding.total_value)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p>No holdings yet in this segment.</p>
      )}
    </div>
  )

  return (
    <div className="portfolio-panel">
      <h2>Portfolio Overview</h2>
      <div className="portfolio-stats">
        <div className="stat-item">
          <label>Available Cash</label>
          <span className="stat-value">{formatCurrency(cash)}</span>
        </div>
        <div className="stat-item">
          <label>Total Holdings Value</label>
          <span className="stat-value">{formatCurrency(totalHoldingsValue)}</span>
        </div>
        <div className="stat-item">
          <label>Total Portfolio Value</label>
          <span className="stat-value">{formatCurrency(totalPortfolioValue)}</span>
        </div>
        <div className="stat-item">
          <label>Active Holdings</label>
          <span className="stat-value">{holdings.length}</span>
        </div>
      </div>

      <div className="portfolio-segments-grid">
        {renderSegment('Practice Money Overview', 'segment-fake', fakeSegment, '🎮')}
        {renderSegment('Real Money Overview', 'segment-real', realSegment, '💰')}
      </div>
    </div>
  )
}

import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import { useAuth } from '../hooks/useAuth'
import { useWebSocket } from '../hooks/useWebSocket'
import { API_BASE } from '../utils/backendConfig'
import PriceChart from '../components/PriceChart'
import InvestmentTypeSelector from '../components/InvestmentTypeSelector'
import UpgradePrompt from '../components/UpgradePrompt'
import ActivateAutoTradingBtn from '../components/ActivateAutoTradingBtn'
import './InvestmentDetailPage.css'

const normalizeSymbol = (value) => String(value || '').trim().toUpperCase()

const evaluateTimingSignal = (history, stats) => {
  if (!Array.isArray(history) || history.length < 10) {
    return {
      action: 'HOLD',
      confidence: 'LOW',
      rationale: 'Insufficient data for a reliable market valuation signal.'
    }
  }

  const prices = history.map((point) => Number(point.price || 0)).filter((price) => Number.isFinite(price) && price > 0)
  if (prices.length < 10) {
    return {
      action: 'HOLD',
      confidence: 'LOW',
      rationale: 'Price history is incomplete for proper valuation analysis.'
    }
  }

  // Calculate multiple indicators for market valuation
  const shortWindow = prices.slice(-7)
  const longWindow = prices.slice(-Math.min(30, prices.length))
  const shortAvg = shortWindow.reduce((sum, price) => sum + price, 0) / shortWindow.length
  const longAvg = longWindow.reduce((sum, price) => sum + price, 0) / longWindow.length
  
  const trendDelta = ((shortAvg - longAvg) / longAvg) * 100
  const changePercent = Number(stats?.changePercent || 0)
  const volatility = Math.sqrt(prices.reduce((sum, p, i) => {
    if (i === 0) return 0
    const change = (p - prices[i-1]) / prices[i-1]
    return sum + change * change
  }, 0) / prices.length) * 100

  // Evaluate market value: Is it undervalued, fairly valued, or overvalued?
  
  // Strong uptrend with positive momentum = potentially overheating/overvalued
  if (trendDelta >= 2.5 && changePercent >= 2) {
    return {
      action: 'HOLD',
      confidence: 'HIGH',
      rationale: `Asset is in strong uptrend (+${trendDelta.toFixed(2)}%). Price momentum is high - consider waiting for pullback or profit-taking opportunity rather than chasing.`
    }
  }

  // Moderate uptrend = good entry opportunity
  if (trendDelta >= 0.5 && trendDelta < 2.5 && changePercent >= 0) {
    return {
      action: 'BUY',
      confidence: 'MEDIUM',
      rationale: `Asset showing positive momentum (+${trendDelta.toFixed(2)}%). Valuation is attractive with upside potential.`
    }
  }

  // Downtrend with low volatility = undervalued, good buying opportunity
  if (trendDelta <= -2.5 && volatility < 3) {
    return {
      action: 'BUY',
      confidence: 'HIGH',
      rationale: `Asset is undervalued (${trendDelta.toFixed(2)}% below average). Low volatility (${volatility.toFixed(2)}%) makes this a strong accumulation opportunity.`
    }
  }

  // Downtrend with high volatility = risky
  if (trendDelta <= -2.5 && volatility >= 3) {
    return {
      action: 'HOLD',
      confidence: 'MEDIUM',
      rationale: `Asset is declining (${trendDelta.toFixed(2)}%) with high volatility (${volatility.toFixed(2)}%). Wait for stabilization before entering.`
    }
  }

  // Mild downtrend = consolidation/value zone
  if (trendDelta < 0 && trendDelta > -2.5 && volatility < 2) {
    return {
      action: 'BUY',
      confidence: 'MEDIUM',
      rationale: `Asset is consolidating at a discount (${trendDelta.toFixed(2)}%). Stable pricing (${volatility.toFixed(2)}% volatility) offers good entry point.`
    }
  }

  // Mixed signals = wait
  if (Math.abs(trendDelta) < 0.5) {
    return {
      action: 'HOLD',
      confidence: 'MEDIUM',
      rationale: `Market value is uncertain (${trendDelta.toFixed(2)}% trend). Wait for clearer directional signal before committing capital.`
    }
  }

  return {
    action: 'HOLD',
    confidence: 'LOW',
    rationale: `Unable to determine clear market valuation. Risk/reward ratio unclear - monitor for better entry point.`
  }
}

export default function InvestmentDetailPage() {
  const { cryptoId } = useParams()
  const navigate = useNavigate()
  const { token, logout } = useAuth()
  const { priceUpdates } = useWebSocket()
  const [crypto, setCrypto] = useState(null)
  const [priceHistory, setPriceHistory] = useState([])
  const [currentPrice, setCurrentPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [historyLocked, setHistoryLocked] = useState(false)
  const [sellQuantityInput, setSellQuantityInput] = useState({ fake: '', real: '' })
  const [sellLoadingType, setSellLoadingType] = useState('')
  const [sellMessage, setSellMessage] = useState('')
  const [analysisShareMessage, setAnalysisShareMessage] = useState('')
  const [portfolioPosition, setPortfolioPosition] = useState({
    fake: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 },
    real: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 }
  })

  // Auto-update chart with live WebSocket prices
  useEffect(() => {
    if (priceUpdates && priceUpdates.length > 0 && priceHistory.length > 0) {
      setPriceHistory((prevHistory) => {
        const updated = [...prevHistory]
        if (updated.length > 0) {
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            price: priceUpdates[0]?.price || updated[updated.length - 1].price,
            timestamp: new Date().toISOString()
          }
          setCurrentPrice(updated[updated.length - 1])
        }
        return updated
      })
    }
  }, [priceUpdates])

  useEffect(() => {
    fetchCryptoDetails()
    // Auto-refresh every 90 seconds for fresh historical data
    const interval = setInterval(() => fetchCryptoDetails(), 90000)
    return () => clearInterval(interval)
  }, [cryptoId])

  useEffect(() => {
    fetchUserPosition()
  }, [cryptoId])

  const fetchUserPosition = async () => {
    try {
      const response = await cryptoAPI.getUserPortfolio()
      const holdings = Array.isArray(response?.data?.holdings) ? response.data.holdings : []
      const symbolKey = normalizeSymbol(cryptoId)

      const matchedHoldings = holdings.filter((holding) => normalizeSymbol(holding.symbol) === symbolKey)

      const aggregatePosition = (rows) => {
        if (!rows.length) {
          return { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 }
        }

        const quantity = rows.reduce((sum, holding) => sum + Number(holding.quantity || 0), 0)
        const investedCost = rows.reduce((sum, holding) => {
          const entry = Number(holding.average_price || holding.price || 0)
          const qty = Number(holding.quantity || 0)
          const fallback = Number(holding.total_value || 0)
          return sum + (entry > 0 && qty > 0 ? entry * qty : fallback)
        }, 0)

        return {
          quantity,
          investedCost,
          averagePrice: quantity > 0 ? investedCost / quantity : 0,
          holdingCount: rows.length
        }
      }

      const fakeHoldings = matchedHoldings.filter((holding) => {
        const type = String(holding.investment_type || '').toLowerCase()
        return type === 'fake_money' || !type
      })

      const realHoldings = matchedHoldings.filter((holding) => String(holding.investment_type || '').toLowerCase() === 'real_money')

      if (!matchedHoldings.length) {
        setPortfolioPosition({
          fake: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 },
          real: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 }
        })
        return
      }
      setPortfolioPosition({
        fake: aggregatePosition(fakeHoldings),
        real: aggregatePosition(realHoldings)
      })
    } catch (positionErr) {
      console.warn('Failed to fetch user position for asset:', positionErr)
      setPortfolioPosition({
        fake: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 },
        real: { quantity: 0, investedCost: 0, averagePrice: 0, holdingCount: 0 }
      })
    }
  }

  const fetchCryptoDetails = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch current price history; if unavailable, fallback to a live spot quote.
      try {
        const priceResponse = await cryptoAPI.getHistory(cryptoId, 100)
        const records = priceResponse?.data?.records || []

        if (records.length > 0) {
          const historyData = records.map(item => ({
            timestamp: item.timestamp || new Date().toISOString(),
            price: item.price || item.usd || 0
          }))
          setPriceHistory(historyData)
          setCurrentPrice(historyData[historyData.length - 1])
          setHistoryLocked(false)
        } else {
          throw new Error('No price history available')
        }
      } catch (apiErr) {
        if (apiErr?.response?.status === 403) {
          setHistoryLocked(true)
          setPriceHistory([])
          setCurrentPrice(null)
        } else {
          console.warn('History API unavailable, trying live quote:', apiErr.message)
          const liveQuoteResponse = await cryptoAPI.getPrice(cryptoId)
          const liveQuote = liveQuoteResponse?.data
          if (!liveQuote || !Number.isFinite(Number(liveQuote.price))) {
            throw new Error('Live quote unavailable')
          }

          const syntheticHistory = [{
            timestamp: liveQuote.timestamp || new Date().toISOString(),
            price: Number(liveQuote.price)
          }]
          setPriceHistory(syntheticHistory)
          setCurrentPrice(syntheticHistory[0])
          setHistoryLocked(false)
        }
      }

      // Create crypto object with symbol
      const symbol = cryptoId.toUpperCase()
      setCrypto({
        id: cryptoId,
        symbol: symbol,
        name: cryptoId.charAt(0).toUpperCase() + cryptoId.slice(1)
      })
    } catch (err) {
      setError('Failed to load investment details')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  // Handle Fake Money Investment
  const handleFakeInvest = async (investData) => {
    try {
      if (!token) {
        throw new Error('Please sign in to place an investment.')
      }

      const response = await fetch(`${API_BASE}/api/user/portfolio/invest/fake`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol: investData.symbol,
          quantity: investData.quantity,
          price: investData.price,
          total_value: investData.totalValue
        })
      })

      if (!response.ok) {
        let detail = 'Failed to record fake investment'
        try {
          const error = await response.json()
          detail = error?.detail || detail
        } catch {
          // Keep fallback detail when response is not JSON.
        }

        if (response.status === 401) {
          logout()
          navigate('/login')
          throw new Error('Session expired. Please sign in again.')
        }

        throw new Error(detail)
      }

      return await response.json()
    } catch (err) {
      console.error('Fake investment error:', err)
      throw err
    } finally {
      fetchUserPosition()
    }
  }

  // Handle Real Money Investment
  const handleRealInvest = async (investData) => {
    try {
      if (!token) {
        throw new Error('Please sign in to place an investment.')
      }

      const response = await fetch(`${API_BASE}/api/user/portfolio/invest/real`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol: investData.symbol,
          quantity: investData.quantity,
          price: investData.price,
          total_value: investData.totalValue,
          encrypted_payment: investData.paymentData
        })
      })

      if (!response.ok) {
        let detail = 'Payment processing failed'
        try {
          const error = await response.json()
          detail = error?.detail || detail
        } catch {
          // Keep fallback detail when response is not JSON.
        }

        if (response.status === 401) {
          logout()
          navigate('/login')
          throw new Error('Session expired. Please sign in again.')
        }

        throw new Error(detail)
      }

      return await response.json()
    } catch (err) {
      console.error('Real investment error:', err)
      throw err
    } finally {
      fetchUserPosition()
    }
  }

  const handleSellPosition = async (positionType) => {
    if (!crypto?.symbol) {
      return
    }

    const investmentType = positionType === 'real' ? 'real_money' : 'fake_money'
    const ownedQuantity = Number(positionType === 'real' ? portfolioPosition.real.quantity : portfolioPosition.fake.quantity)
    const typedQuantity = Number(sellQuantityInput[positionType])
    const sellQuantity = Number.isFinite(typedQuantity) && typedQuantity > 0 ? typedQuantity : ownedQuantity
    const sellPrice = Number(currentPrice?.price || 0)

    if (!Number.isFinite(sellPrice) || sellPrice <= 0) {
      setSellMessage('Current price unavailable. Please wait for price update and try again.')
      return
    }

    if (!Number.isFinite(sellQuantity) || sellQuantity <= 0) {
      setSellMessage('Enter a valid quantity to sell.')
      return
    }

    if (sellQuantity > ownedQuantity) {
      setSellMessage(`Cannot sell ${sellQuantity}. You only own ${ownedQuantity.toFixed(8)} ${crypto.symbol}.`)
      return
    }

    try {
      setSellLoadingType(positionType)
      const response = await cryptoAPI.sellUserHolding({
        symbol: crypto.symbol,
        investment_type: investmentType,
        quantity: sellQuantity,
        price: sellPrice
      })
      setSellMessage(response?.data?.message || `Sold ${sellQuantity.toFixed(8)} ${crypto.symbol}.`)
      setSellQuantityInput((current) => ({ ...current, [positionType]: '' }))
      await fetchUserPosition()
    } catch (sellErr) {
      const detail = sellErr?.response?.data?.detail || 'Failed to sell position.'
      setSellMessage(detail)
    } finally {
      setSellLoadingType('')
    }
  }

  if (loading) {
    return (
      <div className="investment-detail-page">
        <button className="back-btn" onClick={() => navigate('/')}>← Back to Dashboard</button>
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading investment details...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="investment-detail-page">
        <button className="back-btn" onClick={() => navigate('/')}>← Back to Dashboard</button>
        <div className="error-state">
          <p>⚠️ {error}</p>
          <button onClick={fetchCryptoDetails} className="retry-btn">Try Again</button>
        </div>
      </div>
    )
  }

  // Calculate statistics from price history
  const stats = priceHistory.length > 0 ? {
    highPrice: Math.max(...priceHistory.map(p => p.price)),
    lowPrice: Math.min(...priceHistory.map(p => p.price)),
    avgPrice: priceHistory.reduce((sum, p) => sum + p.price, 0) / priceHistory.length,
    priceChange: currentPrice ? currentPrice.price - (priceHistory[0]?.price || currentPrice.price) : 0,
    changePercent: currentPrice && priceHistory[0] ? ((currentPrice.price - priceHistory[0].price) / priceHistory[0].price * 100) : 0
  } : {}

  const timingSignal = evaluateTimingSignal(priceHistory, stats)
  const currentAssetPrice = Number(currentPrice?.price || 0)

  const fakePositionValue = portfolioPosition.fake.quantity * currentAssetPrice
  const fakeProfitNow = fakePositionValue - portfolioPosition.fake.investedCost
  const fakeProfitPct = portfolioPosition.fake.investedCost > 0
    ? (fakeProfitNow / portfolioPosition.fake.investedCost) * 100
    : 0

  const realPositionValue = portfolioPosition.real.quantity * currentAssetPrice
  const realProfitNow = realPositionValue - portfolioPosition.real.investedCost
  const realProfitPct = portfolioPosition.real.investedCost > 0
    ? (realProfitNow / portfolioPosition.real.investedCost) * 100
    : 0

  const shareAnalysis = async (platform) => {
    const detailUrl = window.location.href
    const text = `CryptoAI analysis for ${crypto?.symbol}: ${timingSignal.action} signal, ${stats.changePercent?.toFixed(2)}% period change, current price $${currentPrice?.price?.toFixed(2) || 'N/A'}.`
    const encodedText = encodeURIComponent(text)
    const encodedUrl = encodeURIComponent(detailUrl)

    try {
      if (platform === 'copy') {
        await navigator.clipboard.writeText(`${text} ${detailUrl}`)
        setAnalysisShareMessage('Analysis link copied.')
      } else if (platform === 'native' && navigator.share) {
        await navigator.share({
          title: `${crypto?.symbol} analysis`,
          text,
          url: detailUrl
        })
      } else {
        const shareUrls = {
          x: `https://twitter.com/intent/tweet?text=${encodedText}&url=${encodedUrl}`,
          facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`,
          linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodedUrl}`
        }
        const targetUrl = shareUrls[platform]
        if (targetUrl) {
          window.open(targetUrl, '_blank', 'noopener,noreferrer')
        }
      }
    } catch (shareError) {
      console.warn('Analysis share failed:', shareError)
      setAnalysisShareMessage('Could not share right now.')
    }

    if (platform !== 'native') {
      setTimeout(() => setAnalysisShareMessage(''), 2200)
    }
  }

  return (
    <div className="investment-detail-page">
      <header className="detail-header">
        <div className="header-top">
          <button className="back-btn" onClick={() => navigate('/')}>← Back to Dashboard</button>
          <h1>{crypto?.name} ({crypto?.symbol})</h1>
        </div>
        <div className="header-bottom">
          <ActivateAutoTradingBtn
            symbol={crypto?.symbol}
            currentPrice={currentPrice?.price}
          />
        </div>
      </header>

      <main className="detail-main">
        <div className="detail-content">
          <section className="analysis-share-section">
            <div className="analysis-share-title">Share Analysis Results</div>
            <div className="analysis-share-actions">
              <button className="analysis-share-btn" onClick={() => shareAnalysis('x')}>Share on X</button>
              <button className="analysis-share-btn" onClick={() => shareAnalysis('facebook')}>Share on Facebook</button>
              <button className="analysis-share-btn" onClick={() => shareAnalysis('linkedin')}>Share on LinkedIn</button>
              <button className="analysis-share-btn" onClick={() => shareAnalysis('copy')}>Copy Link</button>
              {navigator.share && (
                <button className="analysis-share-btn" onClick={() => shareAnalysis('native')}>Share</button>
              )}
            </div>
            {analysisShareMessage && <div className="analysis-share-message">✅ {analysisShareMessage}</div>}
          </section>

          {/* Price Chart Section */}
          <section className="chart-section">
            <div className="chart-header">
              <h2>Price History & Trends</h2>
              <div className="price-summary">
                <div className="price-stat">
                  <span className="label">Current Price</span>
                  <span className="value">${currentPrice?.price?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="price-stat">
                  <span className="label">24h Change</span>
                  <span className={`value ${stats.priceChange >= 0 ? 'positive' : 'negative'}`}>
                    {stats.priceChange >= 0 ? '+' : ''}{stats.priceChange?.toFixed(2)} ({stats.changePercent?.toFixed(2)}%)
                  </span>
                </div>
                <div className="price-stat">
                  <span className="label">High</span>
                  <span className="value">${stats.highPrice?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="price-stat">
                  <span className="label">Low</span>
                  <span className="value">${stats.lowPrice?.toFixed(2) || 'N/A'}</span>
                </div>
              </div>
            </div>
            
            {priceHistory.length > 0 ? (
              <PriceChart data={priceHistory} />
            ) : historyLocked ? (
              <div className="history-lock-box">
                <UpgradePrompt
                  title="Pro/Premium feature"
                  message="Price history is available on Pro and Premium plans."
                />
              </div>
            ) : (
              <div className="no-chart-data">No price history available</div>
            )}
          </section>

          {/* Description Section */}
          <section className="description-section">
            <h2>Investment Details</h2>
            <div className="description-content">
              <div className="description-card ai-timing-card">
                <h3>AI Timing Signal</h3>
                <div className={`ai-action ${timingSignal.action.toLowerCase()}`}>
                  {timingSignal.action} NOW
                </div>
                <p>
                  Confidence: <strong>{timingSignal.confidence}</strong>
                </p>
                <p>{timingSignal.rationale}</p>
                <ul className="stats-list">
                  <li>7-period trend: {priceHistory.length >= 7 ? 'Available' : 'Insufficient data'}</li>
                  <li>Current momentum: {stats.changePercent >= 0 ? '+' : ''}{stats.changePercent?.toFixed(2)}%</li>
                </ul>
              </div>

              <div className="description-card position-card fake-position-card">
                <h3>Your Practice Position</h3>
                <p>
                  Quantity owned: <strong>{portfolioPosition.fake.quantity.toFixed(8)} {crypto?.symbol}</strong>
                </p>
                <p>
                  Average entry: <strong>${portfolioPosition.fake.averagePrice.toFixed(2)}</strong>
                </p>
                <p>
                  Value if sold now: <strong>${fakePositionValue.toFixed(2)}</strong>
                </p>
                <p>
                  Estimated P/L now:{' '}
                  <strong className={fakeProfitNow >= 0 ? 'positive' : 'negative'}>
                    {fakeProfitNow >= 0 ? '+' : ''}${fakeProfitNow.toFixed(2)} ({fakeProfitNow >= 0 ? '+' : ''}{fakeProfitPct.toFixed(2)}%)
                  </strong>
                </p>
                <ul className="stats-list">
                  <li>Lots in portfolio: {portfolioPosition.fake.holdingCount}</li>
                  <li>Cost basis: ${portfolioPosition.fake.investedCost.toFixed(2)}</li>
                </ul>
                <div className="sell-inline-controls">
                  <input
                    type="number"
                    min="0"
                    step="0.00000001"
                    className="sell-inline-input"
                    placeholder="Qty (blank = sell all)"
                    value={sellQuantityInput.fake}
                    onChange={(event) => setSellQuantityInput((current) => ({ ...current, fake: event.target.value }))}
                  />
                  <button
                    className="sell-inline-btn"
                    onClick={() => handleSellPosition('fake')}
                    disabled={sellLoadingType === 'fake' || portfolioPosition.fake.quantity <= 0}
                  >
                    {sellLoadingType === 'fake' ? 'Selling...' : 'Sell Practice'}
                  </button>
                </div>
              </div>

              <div className="description-card position-card real-position-card">
                <h3>Your Real Money Position</h3>
                <p>
                  Quantity owned: <strong>{portfolioPosition.real.quantity.toFixed(8)} {crypto?.symbol}</strong>
                </p>
                <p>
                  Average entry: <strong>${portfolioPosition.real.averagePrice.toFixed(2)}</strong>
                </p>
                <p>
                  Value if sold now: <strong>${realPositionValue.toFixed(2)}</strong>
                </p>
                <p>
                  Estimated P/L now:{' '}
                  <strong className={realProfitNow >= 0 ? 'positive' : 'negative'}>
                    {realProfitNow >= 0 ? '+' : ''}${realProfitNow.toFixed(2)} ({realProfitNow >= 0 ? '+' : ''}{realProfitPct.toFixed(2)}%)
                  </strong>
                </p>
                <ul className="stats-list">
                  <li>Lots in portfolio: {portfolioPosition.real.holdingCount}</li>
                  <li>Cost basis: ${portfolioPosition.real.investedCost.toFixed(2)}</li>
                </ul>
                <div className="sell-inline-controls">
                  <input
                    type="number"
                    min="0"
                    step="0.00000001"
                    className="sell-inline-input"
                    placeholder="Qty (blank = sell all)"
                    value={sellQuantityInput.real}
                    onChange={(event) => setSellQuantityInput((current) => ({ ...current, real: event.target.value }))}
                  />
                  <button
                    className="sell-inline-btn"
                    onClick={() => handleSellPosition('real')}
                    disabled={sellLoadingType === 'real' || portfolioPosition.real.quantity <= 0}
                  >
                    {sellLoadingType === 'real' ? 'Selling...' : 'Sell Real'}
                  </button>
                </div>
              </div>

              <div className="description-card">
                <h3>Market Overview</h3>
                <p>
                  {crypto?.symbol} represents one of the leading cryptocurrencies in the digital asset market. 
                  This detailed analysis shows the historical price trends and current market conditions 
                  to help you make informed investment decisions.
                </p>
              </div>

              <div className="description-card">
                <h3>Price Analysis</h3>
                <p>
                  Current Price: <strong>${currentPrice?.price?.toFixed(2) || 'N/A'}</strong>
                </p>
                <p>
                  Over the analyzed period, {crypto?.symbol} has shown a 
                  <strong className={stats.priceChange >= 0 ? 'positive' : 'negative'}>
                    {' '}{stats.priceChange >= 0 ? 'positive' : 'negative'}{' '}
                  </strong>
                  trend with a change of <strong>{stats.changePercent?.toFixed(2)}%</strong>.
                </p>
                <ul className="stats-list">
                  <li>Highest Price: ${stats.highPrice?.toFixed(2) || 'N/A'}</li>
                  <li>Lowest Price: ${stats.lowPrice?.toFixed(2) || 'N/A'}</li>
                  <li>Average Price: ${stats.avgPrice?.toFixed(2) || 'N/A'}</li>
                </ul>
              </div>

              <div className="description-card">
                <h3>Investment Strategy</h3>
                <p>
                  Consider your risk tolerance and investment horizon when deciding on {crypto?.symbol}. 
                  The cryptocurrency market is volatile, and diversification is recommended to manage risk effectively.
                </p>
              </div>
            </div>
          </section>
        </div>

        {/* Invest Module Sidebar */}
        <aside className="invest-sidebar">
          {sellMessage && (
            <div className="sell-message-banner">{sellMessage}</div>
          )}
          <InvestmentTypeSelector
            crypto={crypto}
            currentPrice={currentPrice}
            onFakeInvest={handleFakeInvest}
            onRealInvest={handleRealInvest}
          />
        </aside>
      </main>
    </div>
  )
}

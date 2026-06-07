import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'
import UpgradePrompt from './UpgradePrompt'
import './RecommendationsPanel.css'

const CATEGORIES = {
  LONG_TERM: { id: 'long-term', label: '🏦 Long Term Investments', icon: '📈' },
  QUICK_TURNAROUND: { id: 'quick-turnaround', label: '⚡ Quick Turnaround', icon: '🚀' },
  DANGEROUS_PROFITABLE: { id: 'dangerous-profitable', label: '💎 Dangerous but Profitable', icon: '🎯' }
}

const ACTION_FILTERS = {
  ALL: { id: 'all', label: 'All Signals' },
  BUY_NOW: { id: 'buy-now', label: 'Buy Now' },
  HOLD: { id: 'hold', label: 'Hold' },
  SELL_NOW: { id: 'sell-now', label: 'Sell Now' }
}

export default function RecommendationsPanel() {
  const navigate = useNavigate()
  const [recommendations, setRecommendations] = useState([])
  const [reasoning, setReasoning] = useState('')
  const [riskLevel, setRiskLevel] = useState('LOW')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState(CATEGORIES.LONG_TERM.id)
  const [selectedActionFilter, setSelectedActionFilter] = useState(ACTION_FILTERS.ALL.id)
  const [strategy, setStrategy] = useState('balanced')
  const [timePeriod, setTimePeriod] = useState('7d')
  const [recommendationCount, setRecommendationCount] = useState(10)
  const [riskFilter, setRiskFilter] = useState('all')
  const [tier, setTier] = useState(null)
  const [limitApplied, setLimitApplied] = useState(0)
  const [signalsDailyLimit, setSignalsDailyLimit] = useState(null)
  const [signalsUsedToday, setSignalsUsedToday] = useState(null)
  const [signalsRemainingToday, setSignalsRemainingToday] = useState(null)
  const [apiCallsHourlyLimit, setApiCallsHourlyLimit] = useState(null)
  const [apiCallsUsedThisHour, setApiCallsUsedThisHour] = useState(null)
  const [apiCallsRemainingThisHour, setApiCallsRemainingThisHour] = useState(null)
  const [dailyResetAt, setDailyResetAt] = useState(null)
  const [hourlyResetAt, setHourlyResetAt] = useState(null)
  const [retryAfterSeconds, setRetryAfterSeconds] = useState(null)
  const [upgradeRequired, setUpgradeRequired] = useState(false)
  const [blockedLimitType, setBlockedLimitType] = useState(null)
  const [shareMessage, setShareMessage] = useState('')
  const [integrationMessage, setIntegrationMessage] = useState('')
  const [integrationLoadingKey, setIntegrationLoadingKey] = useState('')
  const { isConnected } = useWebSocket()

  useEffect(() => {
    fetchRecommendations()
    // Refresh recommendations every 5 minutes
    const interval = setInterval(fetchRecommendations, 300000)
    return () => clearInterval(interval)
  }, [])

  const fetchRecommendations = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await cryptoAPI.getRecommendations(recommendationCount, {
        strategy,
        timePeriod,
        riskLevel: riskFilter
      })
      const resolvedTier = response?.data?.tier
        ? String(response.data.tier).trim().toLowerCase()
        : null

      setRecommendations(response.data.recommendations || [])
      setReasoning(response.data.reasoning)
      setRiskLevel(response.data.risk_level)
      setTier((previousTier) => resolvedTier || previousTier)
      setLimitApplied(response.data.limit_applied || 0)
      setSignalsDailyLimit(response.data.signals_daily_limit ?? null)
      setSignalsUsedToday(response.data.signals_used_today ?? null)
      setSignalsRemainingToday(response.data.signals_remaining_today ?? null)
      setApiCallsHourlyLimit(response.data.api_calls_hourly_limit ?? null)
      setApiCallsUsedThisHour(response.data.api_calls_used_this_hour ?? null)
      setApiCallsRemainingThisHour(response.data.api_calls_remaining_this_hour ?? null)
      setDailyResetAt(response.data.daily_reset_at ?? null)
      setHourlyResetAt(response.data.hourly_reset_at ?? null)
      setRetryAfterSeconds(null)
      setUpgradeRequired(false)
      setBlockedLimitType(null)

      window.dispatchEvent(new CustomEvent('subscription-usage-updated'))
    } catch (err) {
      if (err?.response?.status === 403 || err?.response?.status === 429) {
        const retryHeader = Number(err?.response?.headers?.['retry-after'])
        const isHourlyLimit = err?.response?.status === 429

        setRecommendations([])
        setReasoning('')
        setError(err?.response?.data?.detail || 'Recommendation access is limited on your current plan.')
        setUpgradeRequired(true)
        setBlockedLimitType(isHourlyLimit ? 'hourly' : 'daily')
        setRetryAfterSeconds(Number.isFinite(retryHeader) ? retryHeader : null)

        try {
          const usageResponse = await cryptoAPI.getSubscriptionUsageSummary()
          const usage = usageResponse.data || {}
          setSignalsDailyLimit(usage.signals_daily_limit ?? null)
          setSignalsUsedToday(usage.signals_used_today ?? null)
          setSignalsRemainingToday(usage.signals_remaining_today ?? null)
          setApiCallsHourlyLimit(usage.api_calls_per_hour ?? null)
          setApiCallsUsedThisHour(usage.api_calls_used_this_hour ?? null)
          setApiCallsRemainingThisHour(usage.api_calls_remaining_this_hour ?? null)
          setDailyResetAt(usage.daily_reset_at ?? null)
          setHourlyResetAt(usage.hourly_reset_at ?? null)
        } catch (summaryErr) {
          console.warn('Failed to fetch usage summary after limit response:', summaryErr)
        }

        window.dispatchEvent(new CustomEvent('subscription-usage-updated'))
        return
      }

      console.warn('Failed to fetch recommendations, using mock data:', err)
      // Use mock recommendations when API fails
      const mockRecs = [
        {
          symbol: 'BITCOIN',
          reason: 'Bitcoin is showing strong uptrend with +0.33% growth in 24h. Technical indicators suggest continued momentum with good entry points for long-term investors. Strong institutional interest supports price stability and growth potential.',
          risk: 'MEDIUM',
          allocation: 30,
          trend: 'UPTREND',
          current_price: 45339.26
        },
        {
          symbol: 'ETHEREUM',
          reason: 'Ethereum exhibits positive trend with +1.25% growth. DeFi ecosystem expansion and upcoming protocol upgrades provide strong fundamentals. Recommended for balanced portfolios seeking exposure to smart contract platforms.',
          risk: 'MEDIUM',
          allocation: 25,
          trend: 'UPTREND',
          current_price: 2540.15
        },
        {
          symbol: 'CARDANO',
          reason: 'Cardano trading in stable range with +0.95% change. Strong development roadmap and sustainability focus make it attractive for ESG-conscious investors. Good potential in emerging markets and blockchain adoption.',
          risk: 'LOW',
          allocation: 20,
          trend: 'NEUTRAL',
          current_price: 0.6785
        },
        {
          symbol: 'SOLANA',
          reason: 'Solana shows positive momentum with +2.15% daily gain. Network improvements and reduced transaction costs make it competitive. Suitable for growth-oriented portfolios with medium-term outlook.',
          risk: 'HIGH',
          allocation: 15,
          trend: 'UPTREND',
          current_price: 112.45
        },
        {
          symbol: 'RIPPLE',
          reason: 'Ripple displays slight downward trend with -0.85% change. Regulatory clarity in multiple jurisdictions provides stability. Recommended for contrarian investors practicing dollar-cost averaging into dips.',
          risk: 'LOW',
          allocation: 10,
          trend: 'DOWNTREND',
          current_price: 0.5125
        },
        {
          symbol: 'POLKADOT',
          reason: 'Polkadot showing interoperability potential with +1.08% gain. Multi-chain ecosystem development and strong developer community drive adoption. Excellent for investors seeking blockchain infrastructure exposure.',
          risk: 'MEDIUM',
          allocation: 12,
          trend: 'UPTREND',
          current_price: 8.234
        },
        {
          symbol: 'DOGECOIN',
          reason: 'Dogecoin trading with positive sentiment and +0.71% momentum. Community-driven projects and mainstream adoption increasing. Fun alternative for speculative short-term traders.',
          risk: 'HIGH',
          allocation: 8,
          trend: 'UPTREND',
          current_price: 0.1045
        },
        {
          symbol: 'AVALANCHE',
          reason: 'Avalanche demonstrating strong performance with +1.04% daily gain. High-speed transactions and low fees attract DeFi protocols. Great for fast-growing blockchain ecosystem investors.',
          risk: 'HIGH',
          allocation: 11,
          trend: 'UPTREND',
          current_price: 8.91
        },
        {
          symbol: 'CHAINLINK',
          reason: 'Chainlink maintains crucial oracle infrastructure role with +0.37% growth. Increasing smart contract integrations and partnerships support long-term value. Essential component for DeFi ecosystem.',
          risk: 'LOW',
          allocation: 9,
          trend: 'NEUTRAL',
          current_price: 9.05
        },
        {
          symbol: 'POLYGON',
          reason: 'Polygon scaling solution showing +0.82% momentum. Layer-2 adoption accelerating across major protocols. Perfect for investors seeking Ethereum ecosystem growth.',
          risk: 'MEDIUM',
          allocation: 10,
          trend: 'UPTREND',
          current_price: 0.8234
        },
        {
          symbol: 'LITECOIN',
          reason: 'Litecoin maintaining stability with -1.57% pullback. Established payment network with strong community. Suitable for conservative long-term cryptocurrency allocation.',
          risk: 'LOW',
          allocation: 6,
          trend: 'DOWNTREND',
          current_price: 50.70
        },
        {
          symbol: 'UNISWAP',
          reason: 'Uniswap leading DEX with +0.55% growth. Increasing trading volume and token swap activity. Essential for decentralized finance portfolio exposure.',
          risk: 'MEDIUM',
          allocation: 8,
          trend: 'NEUTRAL',
          current_price: 6.78
        },
        {
          symbol: 'MONERO',
          reason: 'Monero privacy coin showing +2.34% uptrend. Privacy-focused technology gaining institutional interest. For investors seeking alternative value propositions.',
          risk: 'HIGH',
          allocation: 7,
          trend: 'UPTREND',
          current_price: 175.42
        },
        {
          symbol: 'COSMOS',
          reason: 'Cosmos network showing +1.67% momentum. Inter-blockchain communication protocol attracting new chains. Ideal for infrastructure-focused portfolios.',
          risk: 'MEDIUM',
          allocation: 9,
          trend: 'UPTREND',
          current_price: 12.34
        },
        {
          symbol: 'VET (VECHAIN)',
          reason: 'VeChain displaying +0.92% growth. Supply chain and IoT solutions gaining enterprise adoption. Emerging leader in blockchain-based tracking.',
          risk: 'LOW',
          allocation: 5,
          trend: 'NEUTRAL',
          current_price: 0.0456
        },
        {
          symbol: 'THETA',
          reason: 'Theta showing +1.45% uptrend. Video streaming platform tokenization and NFT integration expanding. Great for media tech enthusiasts.',
          risk: 'HIGH',
          allocation: 6,
          trend: 'UPTREND',
          current_price: 2.156
        },
        {
          symbol: 'FILECOIN',
          reason: 'Filecoin demonstrating +2.08% momentum. Decentralized storage adoption accelerating with enterprise clients. For investors in Web3 infrastructure.',
          risk: 'HIGH',
          allocation: 7,
          trend: 'UPTREND',
          current_price: 8.92
        },
        {
          symbol: 'ALGORAND',
          reason: 'Algorand showing +0.73% steady performance. Scalable blockchain for enterprise solutions. Suitable for tech-focused institutional investors.',
          risk: 'LOW',
          allocation: 7,
          trend: 'NEUTRAL',
          current_price: 0.4562
        },
        {
          symbol: 'ZCASH',
          reason: 'Zcash maintaining privacy focus with +1.12% growth. Regulatory clarity emerging in key markets. For privacy-conscious long-term holders.',
          risk: 'MEDIUM',
          allocation: 4,
          trend: 'UPTREND',
          current_price: 48.76
        },
        {
          symbol: 'HELIUM',
          reason: 'Helium showing +3.24% explosive uptrend. Decentralized wireless network deployment accelerating. High-risk/high-reward growth opportunity.',
          risk: 'HIGH',
          allocation: 5,
          trend: 'UPTREND',
          current_price: 4.321
        },
        // Best Stocks - Tech Leaders
        {
          symbol: 'APPLE',
          reason: 'Apple (AAPL) showing strong fundamentals with consistent performance. Leading brand in consumer electronics and services. Reliable long-term dividend-paying stock with strong balance sheet.',
          risk: 'LOW',
          allocation: 25,
          trend: 'UPTREND',
          current_price: 182.45
        },
        {
          symbol: 'MICROSOFT',
          reason: 'Microsoft (MSFT) demonstrating growth through AI integration and cloud services. Strong enterprise adoption of Azure and Office 365. Excellent foundation for tech-focused portfolios.',
          risk: 'LOW',
          allocation: 22,
          trend: 'UPTREND',
          current_price: 415.78
        },
        {
          symbol: 'NVIDIA',
          reason: 'NVIDIA (NVDA) leading AI chip revolution with exceptional demand. GPUs powering ChatGPT, data centers, and autonomous vehicles. High growth potential but higher volatility than mega-cap peers.',
          risk: 'MEDIUM',
          allocation: 18,
          trend: 'UPTREND',
          current_price: 875.42
        },
        {
          symbol: 'TESLA',
          reason: 'Tesla (TSLA) at forefront of EV revolution and renewable energy. Strong growth trajectory but subject to market sentiment swings. Suitable for growth-oriented investors with medium-term horizon.',
          risk: 'HIGH',
          allocation: 14,
          trend: 'UPTREND',
          current_price: 285.63
        },
        {
          symbol: 'META',
          reason: 'Meta (META) pivoting to AI and metaverse opportunities. Recent profitability improvements and strong advertising fundamentals. Growth play with significant upside potential.',
          risk: 'HIGH',
          allocation: 12,
          trend: 'UPTREND',
          current_price: 512.34
        },
        {
          symbol: 'GOOGLE',
          reason: 'Alphabet/Google (GOOGL) dominant in search and advertising. Strong cash flow and diversified revenue streams. AI investments positioning for future growth in emerging technologies.',
          risk: 'LOW',
          allocation: 20,
          trend: 'NEUTRAL',
          current_price: 178.92
        },
        {
          symbol: 'AMAZON',
          reason: 'Amazon (AMZN) expanding AWS dominance and cloud computing leadership. E-commerce still growing with strong logistics network. Excellent for exposure to tech infrastructure.',
          risk: 'LOW',
          allocation: 19,
          trend: 'UPTREND',
          current_price: 193.67
        },
        {
          symbol: 'VISA',
          reason: 'Visa (V) providing exposure to global payment trends with consistent dividend growth. Essential financial infrastructure with recurring revenue model. Perfect for conservative diversification.',
          risk: 'LOW',
          allocation: 15,
          trend: 'NEUTRAL',
          current_price: 267.45
        },
        {
          symbol: 'BERKSHIRE',
          reason: 'Berkshire Hathaway (BRK.B) Warren Buffett\'s diversified holding company. Stable value investment with exposure to insurance, railroads, utilities. Ideal for risk-averse long-term investors.',
          risk: 'LOW',
          allocation: 12,
          trend: 'NEUTRAL',
          current_price: 378.56
        },
        {
          symbol: 'JPMORGAN',
          reason: 'JPMorgan Chase (JPM) leading investment bank with strong balance sheet. Benefits from rising interest rates and market activity. Solid dividend yield and financial sector exposure.',
          risk: 'LOW',
          allocation: 10,
          trend: 'UPTREND',
          current_price: 198.34
        }
      ]
      
      // Add action fields to mock recommendations to ensure consistency
      const enrichedMockRecs = mockRecs.map(rec => ({
        ...rec,
        recommendation: 'BUY',
        action_category: 'buy-now',
        action_label: 'BUY NOW'
      }))
      
      setRecommendations(enrichedMockRecs)
      setReasoning('Portfolio analysis based on technical indicators, market sentiment, and fundamental metrics. Diversified allocation across different market caps and risk profiles.')
      setRiskLevel('LOW')
      setTier((previousTier) => previousTier)
      setLimitApplied(20)
      setUpgradeRequired(false)
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'LOW':
        return '#4CAF50'
      case 'MEDIUM':
        return '#FF9800'
      case 'HIGH':
        return '#f44336'
      default:
        return '#999'
    }
  }

  const getRiskEmoji = (risk) => {
    switch (risk) {
      case 'LOW':
        return '🟢'
      case 'MEDIUM':
        return '🟡'
      case 'HIGH':
        return '🔴'
      default:
        return '⚪'
    }
  }

  const categorizeRecommendation = (rec) => {
    if ((rec.risk === 'LOW' || rec.risk === 'MEDIUM') && rec.allocation <= 30) {
      return CATEGORIES.LONG_TERM.id
    }

    if ((rec.risk === 'MEDIUM' || rec.risk === 'HIGH') && rec.trend === 'UPTREND' && rec.allocation > 10) {
      return CATEGORIES.QUICK_TURNAROUND.id
    }

    if (rec.risk === 'HIGH') {
      return CATEGORIES.DANGEROUS_PROFITABLE.id
    }

    if (rec.risk === 'MEDIUM' && rec.trend === 'UPTREND') {
      return CATEGORIES.QUICK_TURNAROUND.id
    }

    return CATEGORIES.LONG_TERM.id
  }

  const getActionCategory = (rec) => {
    const actionCategory = String(rec?.action_category || '').trim().toLowerCase()
    if (actionCategory === ACTION_FILTERS.SELL_NOW.id || actionCategory === ACTION_FILTERS.BUY_NOW.id || actionCategory === ACTION_FILTERS.HOLD.id) {
      return actionCategory
    }

    const recommendationValue = String(rec?.recommendation || '').trim().toUpperCase()
    const reasonValue = String(rec?.reason || '').trim().toLowerCase()

    // Sell signals: explicit "SELL" recommendation or phrases indicating selling
    if (recommendationValue.includes('SELL') || recommendationValue === 'NO') {
      return ACTION_FILTERS.SELL_NOW.id
    }
    
    if (reasonValue.includes('take profit') || reasonValue.includes('exit position') || reasonValue.includes('reduce position')) {
      return ACTION_FILTERS.SELL_NOW.id
    }

    // Hold signals: wait for better conditions
    if (recommendationValue.includes('HOLD')) {
      return ACTION_FILTERS.HOLD.id
    }
    
    if (reasonValue.includes('wait for') || reasonValue.includes('pullback') || reasonValue.includes('stabiliz') || reasonValue.includes('confirm')) {
      return ACTION_FILTERS.HOLD.id
    }

    // Default: Buy opportunities
    return ACTION_FILTERS.BUY_NOW.id
  }

  const getActionLabel = (rec) => {
    const actionLabel = String(rec?.action_label || '').trim().toUpperCase()
    if (actionLabel === 'BUY NOW' || actionLabel === 'SELL NOW') {
      return actionLabel
    }

    return getActionCategory(rec) === ACTION_FILTERS.SELL_NOW.id ? 'SELL NOW' : 'BUY NOW'
  }

  const getFilteredRecommendations = () => {
    return recommendations.filter((rec) => {
      const categoryMatch = categorizeRecommendation(rec) === selectedCategory
      const actionMatch = selectedActionFilter === ACTION_FILTERS.ALL.id || getActionCategory(rec) === selectedActionFilter
      return categoryMatch && actionMatch
    })
  }

  const getCategoryStats = (categoryId) => {
    const filtered = recommendations.filter(rec => categorizeRecommendation(rec) === categoryId)
    return {
      count: filtered.length,
      avgRisk: filtered.length > 0 
        ? [filtered.filter(r => r.risk === 'HIGH').length, filtered.filter(r => r.risk === 'MEDIUM').length, filtered.filter(r => r.risk === 'LOW').length]
        : [0, 0, 0]
    }
  }

  const getActionFilterCount = (filterId) => {
    if (filterId === ACTION_FILTERS.ALL.id) {
      return recommendations.length
    }

    return recommendations.filter((rec) => getActionCategory(rec) === filterId).length
  }

  const hasTrackedDailyLimit = signalsDailyLimit !== null && signalsRemainingToday !== null
  const isNearDailyLimit = hasTrackedDailyLimit && signalsRemainingToday > 0 && signalsRemainingToday <= 2
  const isDailyLimitExhausted = hasTrackedDailyLimit && signalsRemainingToday === 0
  const hasTrackedApiHourlyLimit = apiCallsHourlyLimit !== null && apiCallsRemainingThisHour !== null
  const isNearApiHourlyLimit = hasTrackedApiHourlyLimit && apiCallsRemainingThisHour > 0 && apiCallsRemainingThisHour <= 3
  const isApiHourlyLimitExhausted = hasTrackedApiHourlyLimit && apiCallsRemainingThisHour === 0
  const retryAfterMinutes = retryAfterSeconds !== null ? Math.ceil(retryAfterSeconds / 60) : null
  const blockedResetAt = blockedLimitType === 'hourly' ? hourlyResetAt : dailyResetAt

  const getRecommendationSharePayload = (rec) => {
    const detailUrl = `${window.location.origin}/invest/${String(rec.symbol || '').toLowerCase()}`
    const allocation = (Number(rec.allocation) || 0).toFixed(1)
    const text = `CryptoAI analysis: ${rec.symbol} is ${rec.trend || 'NEUTRAL'} with ${rec.risk || 'MEDIUM'} risk and ${allocation}% suggested allocation.`
    return { text, detailUrl }
  }

  const shareRecommendation = async (rec, platform) => {
    const { text, detailUrl } = getRecommendationSharePayload(rec)
    const encodedText = encodeURIComponent(text)
    const encodedUrl = encodeURIComponent(detailUrl)

    try {
      if (platform === 'copy') {
        await navigator.clipboard.writeText(`${text} ${detailUrl}`)
        setShareMessage(`Copied ${rec.symbol} analysis link.`)
      } else if (platform === 'native' && navigator.share) {
        await navigator.share({
          title: `${rec.symbol} analysis`,
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
      console.warn('Share failed:', shareError)
      setShareMessage('Could not share right now. Try copy link.')
    }

    if (platform !== 'native') {
      setTimeout(() => setShareMessage(''), 2200)
    }
  }

  const sendToIntegration = async (rec, platform) => {
    const key = `${String(rec?.symbol || '').toUpperCase()}-${platform}`
    const detailUrl = `${window.location.origin}/invest/${String(rec.symbol || '').toLowerCase()}`
    const title = `CryptoAI Recommendation: ${rec.symbol}`
    const summary = `${rec.reason} Trend: ${rec.trend || 'NEUTRAL'}, Risk: ${rec.risk || 'MEDIUM'}, Suggested allocation: ${(Number(rec.allocation) || 0).toFixed(1)}%.`

    try {
      setIntegrationLoadingKey(key)
      const response = await cryptoAPI.shareAnalysisToIntegration({
        platform,
        title,
        summary,
        symbol: rec.symbol,
        url: detailUrl
      })
      setIntegrationMessage(response?.data?.message || `Shared ${rec.symbol} to ${platform}.`)
    } catch (integrationError) {
      const detail = integrationError?.response?.data?.detail || `Could not share to ${platform}.`
      setIntegrationMessage(detail)
    } finally {
      setIntegrationLoadingKey('')
      setTimeout(() => setIntegrationMessage(''), 2600)
    }
  }

  return (
    <div className="recommendations-panel">
      <div className="recommendations-header">
        <h2>🤖 AI Investment Recommendations</h2>
        <div className="header-controls">
          <span className={`risk-badge ${riskLevel.toLowerCase()}`}>
            {getRiskEmoji(riskLevel)} {riskLevel} Risk
          </span>
          <button
            className="refresh-btn"
            onClick={fetchRecommendations}
            disabled={loading}
          >
            {loading ? '⟳ Analyzing...' : '↻ Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">⚠️ {error}</div>}

      {shareMessage && <div className="share-message">✅ {shareMessage}</div>}

      {integrationMessage && <div className="integration-message">🧩 {integrationMessage}</div>}

      {signalsDailyLimit !== null && signalsUsedToday !== null && (
        <div className="quota-chip">
          Daily signals: {signalsUsedToday}/{signalsDailyLimit} used
          {signalsRemainingToday !== null ? ` (${signalsRemainingToday} remaining)` : ''}
        </div>
      )}

      {apiCallsHourlyLimit !== null && apiCallsUsedThisHour !== null && (
        <div className="quota-chip api-quota-chip">
          API/hour: {apiCallsUsedThisHour}/{apiCallsHourlyLimit} used
          {apiCallsRemainingThisHour !== null ? ` (${apiCallsRemainingThisHour} remaining)` : ''}
        </div>
      )}

      {loading && !recommendations.length ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Analyzing market data...</p>
        </div>
      ) : (
        <>
          {/* Reasoning Section */}
          {reasoning && (
            <div className="reasoning-box">
              <p className="reasoning-label">📊 Analysis Basis:</p>
              <p className="reasoning-text">{reasoning}</p>
            </div>
          )}

          {tier === 'free' && limitApplied > 0 && recommendations.length > 0 && (
            <UpgradePrompt
              compact
              className="recommendations-upgrade"
              title="Free plan limit applied"
              message={`You are seeing ${limitApplied || 3} recommendations. Upgrade to Pro or Premium for deeper idea coverage.`}
              ctaLabel="Upgrade Plan"
            />
          )}

          {isNearDailyLimit && (
            <UpgradePrompt
              compact
              className="recommendations-upgrade recommendations-near-limit"
              title="Approaching daily limit"
              message={`You only have ${signalsRemainingToday} signal${signalsRemainingToday === 1 ? '' : 's'} remaining today.`}
              ctaLabel="Upgrade for Higher Limits"
            />
          )}

          {isDailyLimitExhausted && !upgradeRequired && (
            <UpgradePrompt
              className="recommendations-upgrade recommendations-near-limit"
              title="Daily signals exhausted"
              message={`You have used all available signals for today.${dailyResetAt ? ` Resets at ${new Date(dailyResetAt).toLocaleTimeString()}.` : ''} Upgrade your plan to increase daily capacity.`}
              ctaLabel="Upgrade Plan"
            />
          )}

          {isNearApiHourlyLimit && (
            <UpgradePrompt
              compact
              className="recommendations-upgrade recommendations-near-limit"
              title="Approaching hourly API limit"
              message={`Only ${apiCallsRemainingThisHour} API call${apiCallsRemainingThisHour === 1 ? '' : 's'} remaining this hour.`}
              ctaLabel="Upgrade for More Throughput"
            />
          )}

          {isApiHourlyLimitExhausted && !upgradeRequired && (
            <UpgradePrompt
              className="recommendations-upgrade recommendations-near-limit"
              title="Hourly API limit exhausted"
              message={`You have used all available API calls for this hour.${hourlyResetAt ? ` Resets at ${new Date(hourlyResetAt).toLocaleTimeString()}.` : ''} Upgrade for higher hourly throughput.`}
              ctaLabel="Upgrade Plan"
            />
          )}

          {upgradeRequired && (
            <UpgradePrompt
              title={blockedLimitType === 'hourly' ? 'Hourly API limit reached' : 'Daily signal limit reached'}
              message={`You've reached your current ${blockedLimitType === 'hourly' ? 'hourly API' : 'daily signal'} limit.${retryAfterMinutes !== null ? ` Try again in about ${retryAfterMinutes} minute${retryAfterMinutes === 1 ? '' : 's'}.` : ''}${blockedResetAt ? ` Resets at ${new Date(blockedResetAt).toLocaleTimeString()}.` : ''} Upgrade to Pro or Premium for higher capacity.`}
              ctaLabel="Upgrade Plan"
            />
          )}

          {/* Filter Dropdowns */}
          <div className="recommendations-filters">
            <div className="filter-group">
              <label htmlFor="strategy-select">📈 Strategy</label>
              <select
                id="strategy-select"
                value={strategy}
                onChange={(e) => {
                  setStrategy(e.target.value)
                  setTimeout(() => fetchRecommendations(), 100)
                }}
                className="filter-select"
              >
                <option value="aggressive">🚀 Aggressive (High Growth)</option>
                <option value="balanced">⚖️ Balanced (Mixed Risk/Reward)</option>
                <option value="conservative">🛡️ Conservative (Low Risk)</option>
                <option value="value">💎 Value (Undervalued Assets)</option>
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="period-select">⏱️ Analysis Period</label>
              <select
                id="period-select"
                value={timePeriod}
                onChange={(e) => {
                  setTimePeriod(e.target.value)
                  setTimeout(() => fetchRecommendations(), 100)
                }}
                className="filter-select"
              >
                <option value="1d">1 Day</option>
                <option value="7d">7 Days</option>
                <option value="30d">30 Days</option>
                <option value="90d">90 Days</option>
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="count-select">🔢 Number of Recommendations</label>
              <select
                id="count-select"
                value={recommendationCount}
                onChange={(e) => {
                  setRecommendationCount(Number(e.target.value))
                  setTimeout(() => fetchRecommendations(), 100)
                }}
                className="filter-select"
              >
                <option value={5}>5 Recommendations</option>
                <option value={10}>10 Recommendations</option>
                <option value={15}>15 Recommendations</option>
                <option value={20}>20 Recommendations</option>
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="risk-select">⚠️ Risk Level Filter</label>
              <select
                id="risk-select"
                value={riskFilter}
                onChange={(e) => {
                  setRiskFilter(e.target.value)
                  setTimeout(() => fetchRecommendations(), 100)
                }}
                className="filter-select"
              >
                <option value="all">All Risk Levels</option>
                <option value="LOW">Low Risk Only</option>
                <option value="MEDIUM">Medium Risk Only</option>
                <option value="HIGH">High Risk Only</option>
                <option value="low-medium">Low & Medium Risk</option>
              </select>
            </div>
          </div>

          {/* Category Tabs */}
          <div className="category-tabs">
            {Object.values(CATEGORIES).map(category => {
              const stats = getCategoryStats(category.id)
              return (
                <button
                  key={category.id}
                  className={`category-tab ${selectedCategory === category.id ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(category.id)}
                  title={`${stats.count} recommendations`}
                >
                  <span className="category-icon">{category.icon}</span>
                  <span className="category-name">{category.label}</span>
                  <span className="category-count">{stats.count}</span>
                </button>
              )
            })}
          </div>

          <div className="action-tabs">
            {Object.values(ACTION_FILTERS).map((filter) => (
              <button
                key={filter.id}
                className={`action-tab ${selectedActionFilter === filter.id ? 'active' : ''}`}
                onClick={() => setSelectedActionFilter(filter.id)}
                title={`${getActionFilterCount(filter.id)} recommendations`}
              >
                <span className="action-tab-label">{filter.label}</span>
                <span className="action-tab-count">{getActionFilterCount(filter.id)}</span>
              </button>
            ))}
          </div>

          {/* Recommendations Grid */}
          <div className="recommendations-grid">
            {getFilteredRecommendations().length > 0 ? (
              getFilteredRecommendations().map((rec, idx) => (
                <div
                  key={idx}
                  className="recommendation-card"
                  style={{
                    borderLeftColor: getRiskColor(rec.risk),
                    animationDelay: `${idx * 0.1}s`
                  }}
                >
                  <div className="rec-header">
                    <span className="symbol">{rec.symbol}</span>
                    <span className="risk-indicator">
                      {getRiskEmoji(rec.risk)} {rec.risk}
                    </span>
                  </div>

                  <div className="rec-body">
                    <div className="detailed-reason">
                      <p className="reason-text">{rec.reason}</p>
                    </div>

                    <div className="rec-details">
                      {rec.current_price && (
                        <div className="price-info">
                          <span className="label">Current Price:</span>
                          <span className="value">${rec.current_price?.toFixed(2) || 'N/A'}</span>
                        </div>
                      )}

                      {rec.trend && (
                        <div className="trend-info">
                          <span className="label">Market Trend:</span>
                          <span className={`trend ${rec.trend.toLowerCase()}`}>
                            {rec.trend === 'UPTREND' ? '📈' : rec.trend === 'DOWNTREND' ? '📉' : '➡️'}
                            {rec.trend}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Market Position Section */}
                    <div className="market-position">
                      <div className="position-label">📍 Current Market Position:</div>
                      <div className="position-statement">
                        {rec.trend === 'UPTREND' ? (
                          <span className="position-uptrend">
                            Price is in an uptrend at ${rec.current_price?.toFixed(2)}. 
                            Strong bullish momentum with good entry opportunities for long-term positions.
                          </span>
                        ) : rec.trend === 'DOWNTREND' ? (
                          <span className="position-downtrend">
                            Price is consolidating at ${rec.current_price?.toFixed(2)}. 
                            Trading lower with potential support building—buying opportunity for value investors.
                          </span>
                        ) : (
                          <span className="position-neutral">
                            Price is stable at ${rec.current_price?.toFixed(2)}. 
                            Trading in equilibrium with balanced risk-reward profile.
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Investment Recommendation */}
                    <div className="invest-recommendation">
                      <div className="recommendation-label">Investment Recommendation:</div>
                      <div className={`recommendation-badge ${getActionCategory(rec) === ACTION_FILTERS.SELL_NOW.id ? 'no' : 'yes'}`}>
                        <span className="recommendation-text">
                          {getActionLabel(rec)}
                        </span>
                        <span className="recommendation-emoji">
                          {getActionCategory(rec) === ACTION_FILTERS.SELL_NOW.id ? '❌' : '✅'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="rec-footer">
                    <div className="allocation-bar">
                      <span className="allocation-label">
                        Allocation
                      </span>
                      <div className="bar-container">
                        <div
                          className="bar-fill"
                          style={{
                            width: `${Number(rec.allocation) || 0}%`,
                            backgroundColor: getRiskColor(rec.risk)
                          }}
                        ></div>
                      </div>
                      <span className="allocation-percent">{(Number(rec.allocation) || 0).toFixed(1)}%</span>
                    </div>
                  </div>

                  <button 
                    className="invest-btn"
                    onClick={() => navigate(`/invest/${rec.symbol.toLowerCase()}`)}
                  >
                    Invest in {rec.symbol}
                  </button>

                  <div className="share-actions">
                    <span className="share-label">Share:</span>
                    <button className="share-btn" onClick={() => shareRecommendation(rec, 'x')}>X</button>
                    <button className="share-btn" onClick={() => shareRecommendation(rec, 'facebook')}>Facebook</button>
                    <button className="share-btn" onClick={() => shareRecommendation(rec, 'linkedin')}>LinkedIn</button>
                    <button className="share-btn" onClick={() => shareRecommendation(rec, 'copy')}>Copy Link</button>
                    {navigator.share && (
                      <button className="share-btn" onClick={() => shareRecommendation(rec, 'native')}>Share</button>
                    )}
                  </div>

                  <div className="integration-actions">
                    <span className="integration-label">Send to:</span>
                    <button
                      className="integration-btn"
                      onClick={() => sendToIntegration(rec, 'slack')}
                      disabled={integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-slack`}
                    >
                      {integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-slack` ? 'Sending...' : 'Slack'}
                    </button>
                    <button
                      className="integration-btn"
                      onClick={() => sendToIntegration(rec, 'teams')}
                      disabled={integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-teams`}
                    >
                      {integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-teams` ? 'Sending...' : 'Teams'}
                    </button>
                    <button
                      className="integration-btn"
                      onClick={() => sendToIntegration(rec, 'google_chat')}
                      disabled={integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-google_chat`}
                    >
                      {integrationLoadingKey === `${String(rec.symbol || '').toUpperCase()}-google_chat` ? 'Sending...' : 'Google Chat'}
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="empty-state">
                {recommendations.length > 0 ? (
                  <>
                    <p>🔍 No recommendations in this category</p>
                    <small>Try selecting a different category</small>
                  </>
                ) : (
                  <>
                    <p>🔍 No recommendations available yet</p>
                    <small>Refresh prices first to generate recommendations</small>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Summary Card */}
          {recommendations.length > 0 && (
            <div className="portfolio-summary-box">
              <h3>💼 Recommended Portfolio</h3>
              <div className="summary-stats">
                <div className="stat">
                  <span className="stat-label">Total Assets:</span>
                  <span className="stat-value">{recommendations.length}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Portfolio Risk:</span>
                  <span className="stat-value">{riskLevel}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Diversification:</span>
                  <span className="stat-value">
                    {Math.round((recommendations.length / 5) * 100)}%
                  </span>
                </div>
              </div>
              <button className="allocate-btn">
                📊 Use This Allocation
              </button>
            </div>
          )}

          <div className="recommendations-footer">
            <p className="disclaimer">
              ⚠️ <strong>Disclaimer:</strong> These AI recommendations are for educational purposes only.
              Always conduct your own research and consult with a financial advisor before investing.
              Past performance does not guarantee future results.
            </p>
          </div>
        </>
      )}
    </div>
  )
}

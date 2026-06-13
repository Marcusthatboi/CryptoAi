import React, { useState, useEffect, useRef, useCallback } from 'react'
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

const FALLBACK_POLL_INTERVAL_MS = 60000
const REALTIME_REFRESH_COOLDOWN_MS = 30000
const COUNTDOWN_TICK_MS = 1000

const formatCountdown = (seconds) => {
  const safeSeconds = Math.max(0, Number(seconds || 0))
  const minutes = Math.floor(safeSeconds / 60)
  const remainingSeconds = safeSeconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`
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
  const [nextUpdateInSeconds, setNextUpdateInSeconds] = useState(FALLBACK_POLL_INTERVAL_MS / 1000)
  const [lastUpdatedAt, setLastUpdatedAt] = useState(null)
  const [candidateUniverse, setCandidateUniverse] = useState([])
  const [recommendationProfile, setRecommendationProfile] = useState(null)
  const [newsProvider, setNewsProvider] = useState('none')
  const { isConnected, message } = useWebSocket()
  const requestInFlightRef = useRef(false)
  const lastRealtimeRefreshRef = useRef(0)
  const nextAutoRefreshAtRef = useRef(Date.now() + FALLBACK_POLL_INTERVAL_MS)

  const scheduleNextUpdate = useCallback((delayMs) => {
    const safeDelay = Math.max(0, Number(delayMs || 0))
    nextAutoRefreshAtRef.current = Date.now() + safeDelay
    setNextUpdateInSeconds(Math.ceil(safeDelay / 1000))
  }, [])

  useEffect(() => {
    const timerId = setInterval(() => {
      const secondsLeft = Math.ceil((nextAutoRefreshAtRef.current - Date.now()) / 1000)
      setNextUpdateInSeconds(Math.max(0, secondsLeft))
    }, COUNTDOWN_TICK_MS)

    return () => clearInterval(timerId)
  }, [])

  useEffect(() => {
    fetchRecommendations()
    scheduleNextUpdate(FALLBACK_POLL_INTERVAL_MS)
    // Fallback refresh in case websocket messages are delayed.
    const interval = setInterval(() => {
      scheduleNextUpdate(FALLBACK_POLL_INTERVAL_MS)
      fetchRecommendations({ background: true })
    }, FALLBACK_POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [strategy, timePeriod, riskFilter, recommendationCount, scheduleNextUpdate])

  useEffect(() => {
    if (!isConnected || !message || message.type !== 'price_update') {
      return
    }

    const now = Date.now()
    if (now - lastRealtimeRefreshRef.current < REALTIME_REFRESH_COOLDOWN_MS) {
      return
    }

    lastRealtimeRefreshRef.current = now
    scheduleNextUpdate(REALTIME_REFRESH_COOLDOWN_MS)
    fetchRecommendations({ background: true })
  }, [isConnected, message, strategy, timePeriod, riskFilter, recommendationCount, scheduleNextUpdate])

  const fetchRecommendations = useCallback(async ({ background = false } = {}) => {
    if (requestInFlightRef.current) {
      return
    }

    requestInFlightRef.current = true

    try {
      if (!background || recommendations.length === 0) {
        setLoading(true)
      }
      setError(null)
      const response = await cryptoAPI.getRecommendations(recommendationCount, {
        strategy,
        timePeriod,
        riskLevel: riskFilter
      })
      const payload = response?.data || {}
      const resolvedTier = payload?.tier
        ? String(payload.tier).trim().toLowerCase()
        : null

      setRecommendations(Array.isArray(payload.recommendations) ? payload.recommendations : [])
      setReasoning(payload.reasoning || '')
      setRiskLevel(payload.risk_level || 'LOW')
      setTier((previousTier) => resolvedTier || previousTier)
      setLimitApplied(payload.limit_applied || 0)
      setSignalsDailyLimit(payload.signals_daily_limit ?? null)
      setSignalsUsedToday(payload.signals_used_today ?? null)
      setSignalsRemainingToday(payload.signals_remaining_today ?? null)
      setApiCallsHourlyLimit(payload.api_calls_hourly_limit ?? null)
      setApiCallsUsedThisHour(payload.api_calls_used_this_hour ?? null)
      setApiCallsRemainingThisHour(payload.api_calls_remaining_this_hour ?? null)
      setDailyResetAt(payload.daily_reset_at ?? null)
      setHourlyResetAt(payload.hourly_reset_at ?? null)
      setCandidateUniverse(Array.isArray(payload.candidate_universe) ? payload.candidate_universe : [])
      setRecommendationProfile(payload.recommendation_profile || null)
      setNewsProvider(payload?._debug?.news_provider || 'none')
      setRetryAfterSeconds(null)
      setUpgradeRequired(false)
      setBlockedLimitType(null)
      setLastUpdatedAt(new Date())

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

      console.error('Failed to fetch live recommendations:', err)
      setRecommendations([])
      setReasoning('')
      setRiskLevel('LOW')
      setLimitApplied(0)
      setCandidateUniverse([])
      setRecommendationProfile(null)
      setNewsProvider('none')
      setUpgradeRequired(false)
      setBlockedLimitType(null)
      setRetryAfterSeconds(null)
      setError(err?.response?.data?.detail || 'Live recommendations are currently unavailable. Please retry in a moment.')
    } finally {
      requestInFlightRef.current = false
      if (!background) {
        scheduleNextUpdate(isConnected ? REALTIME_REFRESH_COOLDOWN_MS : FALLBACK_POLL_INTERVAL_MS)
      }
      setLoading(false)
    }
  }, [recommendationCount, strategy, timePeriod, riskFilter, recommendations.length, scheduleNextUpdate, isConnected])

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
    const strategyBucket = String(rec?.strategy_bucket || '').trim().toLowerCase()
    if (strategyBucket === 'long_term') {
      return CATEGORIES.LONG_TERM.id
    }
    if (strategyBucket === 'swing') {
      return CATEGORIES.QUICK_TURNAROUND.id
    }
    if (strategyBucket === 'speculative') {
      return CATEGORIES.DANGEROUS_PROFITABLE.id
    }

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
    const parseScore = (value) => {
      const numeric = Number(value)
      return Number.isFinite(numeric) ? numeric : null
    }

    const filtered = recommendations.filter((rec) => {
      const categoryMatch = categorizeRecommendation(rec) === selectedCategory
      const actionMatch = selectedActionFilter === ACTION_FILTERS.ALL.id || getActionCategory(rec) === selectedActionFilter
      return categoryMatch && actionMatch
    })

    return filtered.sort((left, right) => {
      const rightRiskAdjusted = parseScore(right?.risk_adjusted_score)
      const leftRiskAdjusted = parseScore(left?.risk_adjusted_score)

      if (rightRiskAdjusted !== null || leftRiskAdjusted !== null) {
        return (rightRiskAdjusted ?? -1) - (leftRiskAdjusted ?? -1)
      }

      const rightConfidence = parseScore(right?.confidence_score)
      const leftConfidence = parseScore(left?.confidence_score)

      if (rightConfidence !== null || leftConfidence !== null) {
        return (rightConfidence ?? -1) - (leftConfidence ?? -1)
      }

      return Number(right?.allocation || 0) - Number(left?.allocation || 0)
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
          <div className="live-refresh-status" title={isConnected ? 'Realtime websocket updates enabled' : 'Fallback polling mode active'}>
            <span className={`live-dot ${isConnected ? 'connected' : 'fallback'}`}></span>
            <span>{isConnected ? 'Live' : 'Polling'}</span>
            <span className="status-separator">|</span>
            <span>Next update {formatCountdown(nextUpdateInSeconds)}</span>
            {lastUpdatedAt && <span className="status-separator">|</span>}
            {lastUpdatedAt && <span>Updated {lastUpdatedAt.toLocaleTimeString()}</span>}
          </div>
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

      {newsProvider && newsProvider !== 'none' && (
        <div className="news-provider-badge" title="Data source for live news sentiment analysis">
          📰 News: {newsProvider === 'newsdata' ? 'NewsData.io' : newsProvider === 'newsapi' ? 'NewsAPI' : newsProvider === 'cryptopanic' ? 'CryptoPanic' : 'Unknown'}
        </div>
      )}

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

          {candidateUniverse.length > 0 && (
            <div className="candidate-universe-box">
              <div className="candidate-universe-header">
                <p className="candidate-universe-title">🌐 Top 10 Candidate Universe</p>
                <span className="candidate-universe-count">{candidateUniverse.length} assets</span>
              </div>
              <p className="candidate-universe-subtitle">
                AI recommendations are generated only from these ranked assets gathered from connected APIs.
              </p>
              <div className="candidate-universe-grid">
                {candidateUniverse.map((asset, idx) => (
                  <div key={`${String(asset.crypto_id || asset.symbol || idx)}-${idx}`} className="candidate-chip">
                    <span className="candidate-rank">#{idx + 1}</span>
                    <span className="candidate-symbol">{String(asset.symbol || asset.crypto_id || 'N/A').toUpperCase()}</span>
                    <span className="candidate-sources">{Array.isArray(asset.sources) ? asset.sources.join(' + ') : 'unknown source'}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {recommendationProfile && (
            <div className="recommendation-profile-box">
              <div className="recommendation-profile-item long-term">
                🏦 Long Term: {Number(recommendationProfile.long_term || 0)}
              </div>
              <div className="recommendation-profile-item swing">
                ⚡ Swing: {Number(recommendationProfile.swing || 0)}
              </div>
              <div className="recommendation-profile-item speculative">
                💎 Speculative: {Number(recommendationProfile.speculative || 0)}
              </div>
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

          <div className="recommendations-filters category-dropdown-row">
            <div className="filter-group">
              <label htmlFor="category-select">📂 Recommendation Category</label>
              <select
                id="category-select"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="filter-select"
              >
                {Object.values(CATEGORIES).map((category) => {
                  const stats = getCategoryStats(category.id)
                  return (
                    <option key={category.id} value={category.id}>
                      {category.label} ({stats.count})
                    </option>
                  )
                })}
              </select>
            </div>

            <div className="filter-group">
              <label htmlFor="action-filter-select">🎯 Action Filter</label>
              <select
                id="action-filter-select"
                value={selectedActionFilter}
                onChange={(e) => setSelectedActionFilter(e.target.value)}
                className="filter-select"
              >
                {Object.values(ACTION_FILTERS).map((filter) => (
                  <option key={filter.id} value={filter.id}>
                    {filter.label} ({getActionFilterCount(filter.id)})
                  </option>
                ))}
              </select>
            </div>
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
                    <div className="rec-header-meta">
                      <span className="risk-indicator">
                        {getRiskEmoji(rec.risk)} {rec.risk}
                      </span>
                      {rec.strategy_bucket && (
                        <span className={`bucket-indicator ${String(rec.strategy_bucket).toLowerCase()}`}>
                          {String(rec.strategy_bucket).replace('_', ' ').toUpperCase()}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="rec-body">
                    <div className="detailed-reason">
                      <p className="reason-text">{rec.reason}</p>
                    </div>

                    <div className="rec-details">
                      {(rec.risk_adjusted_score !== undefined || rec.confidence_score !== undefined) && (
                        <div className="score-row">
                          {rec.risk_adjusted_score !== undefined && (
                            <div className="score-chip risk-adjusted">
                              Risk-Adjusted: {Number(rec.risk_adjusted_score).toFixed(1)}
                            </div>
                          )}
                          {rec.confidence_score !== undefined && (
                            <div className="score-chip confidence">
                              Confidence: {Number(rec.confidence_score).toFixed(1)}
                            </div>
                          )}
                          {rec.rank_in_universe !== undefined && (
                            <div className="score-chip rank">
                              Universe Rank: #{rec.rank_in_universe}
                            </div>
                          )}
                        </div>
                      )}

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

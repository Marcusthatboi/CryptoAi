import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import { cryptoAPI } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'
import './UserInvestmentsPanel.css'

const SYMBOL_TO_CRYPTO_ID = {
  BITCOIN: 'bitcoin',
  ETHEREUM: 'ethereum',
  TETHER: 'tether',
  BNB: 'binancecoin',
  USDC: 'usd-coin',
  CARDANO: 'cardano',
  SOLANA: 'solana',
  RIPPLE: 'ripple',
  TRON: 'tron',
  TONCOIN: 'toncoin',
  POLKADOT: 'polkadot',
  DOGECOIN: 'dogecoin',
  'SHIBA INU': 'shiba-inu',
  AVALANCHE: 'avalanche-2',
  CHAINLINK: 'chainlink',
  POLYGON: 'polygon',
  LITECOIN: 'litecoin',
  UNISWAP: 'uniswap',
  'BITCOIN CASH': 'bitcoin-cash',
  NEAR: 'near',
  STELLAR: 'stellar',
  FILECOIN: 'filecoin',
  HEDERA: 'hedera-hashgraph',
  COSMOS: 'cosmos',
  ALGORAND: 'algorand',
  APTOS: 'aptos',
  ARBITRUM: 'arbitrum',
  OPTIMISM: 'optimism',
  RENDER: 'render-token',
  IMX: 'immutable-x'
}

const SYMBOL_ALIAS_TO_CANONICAL = {
  BTC: 'BITCOIN',
  XBT: 'BITCOIN',
  ETH: 'ETHEREUM',
  ADA: 'CARDANO',
  SOL: 'SOLANA',
  XRP: 'RIPPLE',
  DOT: 'POLKADOT',
  DOGE: 'DOGECOIN',
  AVAX: 'AVALANCHE',
  LINK: 'CHAINLINK',
  MATIC: 'POLYGON',
  LTC: 'LITECOIN',
  UNI: 'UNISWAP',
  BCH: 'BITCOIN CASH',
  XLM: 'STELLAR',
  FIL: 'FILECOIN',
  ALGO: 'ALGORAND',
  APT: 'APTOS',
  OP: 'OPTIMISM'
}

const CANONICAL_TO_TICKER = {
  BITCOIN: 'BTC',
  ETHEREUM: 'ETH',
  CARDANO: 'ADA',
  SOLANA: 'SOL',
  RIPPLE: 'XRP',
  POLKADOT: 'DOT',
  DOGECOIN: 'DOGE',
  AVALANCHE: 'AVAX',
  CHAINLINK: 'LINK',
  POLYGON: 'MATIC',
  LITECOIN: 'LTC',
  UNISWAP: 'UNI',
  'BITCOIN CASH': 'BCH',
  STELLAR: 'XLM',
  FILECOIN: 'FIL',
  ALGORAND: 'ALGO',
  APTOS: 'APT',
  OPTIMISM: 'OP'
}

const PORTFOLIO_FETCH_TIMEOUT_MS = 35000

const normalizeSymbol = (symbol) => {
  const normalized = String(symbol || '').trim().toUpperCase()
  if (!normalized) {
    return ''
  }
  return SYMBOL_ALIAS_TO_CANONICAL[normalized] || normalized
}

const getCryptoIdForSymbol = (symbol) => {
  const canonicalSymbol = normalizeSymbol(symbol)
  return SYMBOL_TO_CRYPTO_ID[canonicalSymbol]
}

const getLivePriceForSymbol = (symbol, livePrices) => {
  const normalized = String(symbol || '').trim().toUpperCase()
  const canonical = normalizeSymbol(symbol)
  const ticker = CANONICAL_TO_TICKER[canonical]

  return Number(
    livePrices[normalized]?.price
    ?? livePrices[canonical]?.price
    ?? (ticker ? livePrices[ticker]?.price : undefined)
  )
}

const getHoldingQuantity = (holding) => Number(holding?.quantity || 0)

const getHoldingCostBasis = (holding) => {
  const quantity = getHoldingQuantity(holding)
  const averagePrice = Number(holding?.average_price)
  const totalValue = Number(holding?.total_value)
  const entryPrice = Number(holding?.price)

  if (!(Number.isFinite(quantity) && quantity > 0)) {
    return 0
  }

  if (Number.isFinite(averagePrice) && averagePrice > 0) {
    return quantity * averagePrice
  }

  if (Number.isFinite(totalValue) && totalValue > 0) {
    return totalValue
  }

  if (Number.isFinite(entryPrice) && entryPrice > 0) {
    return quantity * entryPrice
  }

  return 0
}

const getScopedRealizedProfit = (portfolio, investmentType) => {
  const realized = portfolio?.realized_pnl || {}

  if (investmentType === 'fake') {
    return Number(realized.fake_money || 0)
  }

  if (investmentType === 'real') {
    return Number(realized.real_money || 0)
  }

  return Number(realized.overall || 0)
}

const getScopedRealizedCostBasis = (portfolio, investmentType) => {
  const activityLog = Array.isArray(portfolio?.activity_log) ? portfolio.activity_log : []

  return activityLog.reduce((sum, entry) => {
    if (entry?.event !== 'sell') {
      return sum
    }

    const type = String(entry?.investment_type || 'real_money')
    const shouldInclude = investmentType === 'all'
      || (investmentType === 'fake' && type === 'fake_money')
      || (investmentType === 'real' && type === 'real_money')

    if (!shouldInclude) {
      return sum
    }

    return sum + Number(entry?.cost_basis || 0)
  }, 0)
}

export default function UserInvestmentsPanel() {
  const navigate = useNavigate()
  const [portfolio, setPortfolio] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [investmentType, setInvestmentType] = useState('all')
  const [livePrices, setLivePrices] = useState({})
  const [actionMessage, setActionMessage] = useState('')
  const [actionLoadingKey, setActionLoadingKey] = useState('')
  const [withdrawAmount, setWithdrawAmount] = useState('')
  const [sellPercentByKey, setSellPercentByKey] = useState({})
  const [sellQuantityByKey, setSellQuantityByKey] = useState({})
  const [profitTimeRange, setProfitTimeRange] = useState('7d') // 'd', '7d', '30d'
  const [practiceLastTickAt, setPracticeLastTickAt] = useState(null)
  const isRefreshingRef = useRef(false)
  const isMountedRef = useRef(true)
  const { isConnected, message, subscribe, unsubscribe } = useWebSocket()
  const holdingsSymbolKey = [...new Set((portfolio?.holdings || []).map((holding) => holding.symbol?.toUpperCase()).filter(Boolean))]
    .sort()
    .join(',')
  const practiceSymbolKey = [
    ...new Set(
      (portfolio?.holdings || [])
        .filter((holding) => holding.investment_type === 'fake_money')
        .map((holding) => normalizeSymbol(holding.symbol))
        .filter(Boolean)
    )
  ]
    .sort()
    .join(',')

  useEffect(() => {
    isMountedRef.current = true
    refreshPortfolioData(true)

    // Auto-refresh: window focus listener
    const handleFocus = () => refreshPortfolioData(true)
    window.addEventListener('focus', handleFocus)

    // Refresh holdings/cash every 10 seconds; live prices come from the websocket feed.
    const interval = setInterval(() => refreshPortfolioData(false), 10000)

    return () => {
      isMountedRef.current = false
      window.removeEventListener('focus', handleFocus)
      clearInterval(interval)
    }
  }, [])

  useEffect(() => {
    if (!holdingsSymbolKey) {
      return
    }

    refreshHoldingPrices(portfolio?.holdings || [])
  }, [holdingsSymbolKey])

  useEffect(() => {
    if (!isConnected || !portfolio?.holdings?.length) {
      return
    }

    const symbols = [
      ...new Set(
        portfolio.holdings
          .map((holding) => String(holding.symbol || '').toUpperCase())
          .filter(Boolean)
          .flatMap((symbol) => {
            const canonical = normalizeSymbol(symbol)
            return canonical && canonical !== symbol ? [symbol, canonical] : [symbol]
          })
      )
    ]
    symbols.forEach((symbol) => subscribe(symbol))

    return () => {
      symbols.forEach((symbol) => unsubscribe(symbol))
    }
  }, [isConnected, portfolio, subscribe, unsubscribe])

  useEffect(() => {
    if (message?.type !== 'price_update' || !message?.symbol || !message?.data) {
      return
    }

    const normalizedSymbol = String(message.symbol || '').toUpperCase()
    const canonicalSymbol = normalizeSymbol(normalizedSymbol)
    const tickerSymbol = CANONICAL_TO_TICKER[canonicalSymbol]
    const normalizedPrice = Number(message.data?.price)
    const normalizedData = Number.isFinite(normalizedPrice)
      ? { ...message.data, price: normalizedPrice }
      : message.data
    const practiceSymbols = practiceSymbolKey ? new Set(practiceSymbolKey.split(',')) : null
    const isPracticeTick = Boolean(
      practiceSymbols && (practiceSymbols.has(normalizedSymbol) || practiceSymbols.has(canonicalSymbol))
    )

    setLivePrices((currentPrices) => ({
      ...currentPrices,
      [normalizedSymbol]: normalizedData,
      ...(canonicalSymbol ? { [canonicalSymbol]: normalizedData } : {}),
      ...(tickerSymbol ? { [tickerSymbol]: normalizedData } : {})
    }))

    if (isPracticeTick) {
      setPracticeLastTickAt(normalizedData?.timestamp || new Date().toISOString())
    }
  }, [message, practiceSymbolKey])

  const refreshHoldingPrices = async (holdings) => {
    const symbols = [...new Set((holdings || []).map((holding) => holding.symbol?.toUpperCase()).filter(Boolean))]
    const symbolMappings = symbols
      .map((symbol) => ({ symbol, cryptoId: getCryptoIdForSymbol(symbol) }))
      .filter((item) => item.cryptoId)
    const trackedCryptoIds = [...new Set(symbolMappings.map((item) => item.cryptoId))]

    if (!trackedCryptoIds.length) {
      return
    }

    let response
    try {
      response = await cryptoAPI.getPrices(trackedCryptoIds)
    } catch (priceError) {
      console.warn('Failed to refresh holding prices:', priceError)
      return
    }

    const pricesBySymbol = symbolMappings.reduce((result, item) => {
      const { symbol, cryptoId } = item
      const canonicalSymbol = normalizeSymbol(symbol)
      const tickerSymbol = CANONICAL_TO_TICKER[canonicalSymbol]
      const priceData = response.data?.[cryptoId]
      if (priceData) {
        result[symbol] = priceData
        result[canonicalSymbol] = priceData
        if (tickerSymbol) {
          result[tickerSymbol] = priceData
        }
      }
      return result
    }, {})

    if (Object.keys(pricesBySymbol).length) {
      setLivePrices((currentPrices) => ({
        ...currentPrices,
        ...pricesBySymbol
      }))

      const hasPracticeHoldings = (holdings || []).some((holding) => holding.investment_type === 'fake_money')
      if (hasPracticeHoldings) {
        setPracticeLastTickAt(new Date().toISOString())
      }
    }
  }

  const refreshPortfolioData = async (includePrices = false) => {
    if (isRefreshingRef.current) {
      return
    }

    isRefreshingRef.current = true

    try {
      const response = await cryptoAPI.getUserPortfolio({
        timeout: PORTFOLIO_FETCH_TIMEOUT_MS,
        retryAttempts: 1
      })

      if (!isMountedRef.current) {
        return
      }

      setPortfolio(response.data)
      setError(null)
      if (includePrices) {
        await refreshHoldingPrices(response.data?.holdings || [])
      }
    } catch (err) {
      console.error('Failed to fetch portfolio:', err)

      if (!isMountedRef.current) {
        return
      }

      if (!portfolio) {
        const isTimeout =
          err?.code === 'ECONNABORTED' ||
          String(err?.message || '').toLowerCase().includes('timeout')

        setError(
          isTimeout
            ? 'Portfolio request timed out. Please retry in a moment.'
            : 'Failed to load portfolio'
        )
      }
    } finally {
      isRefreshingRef.current = false
      if (isMountedRef.current) {
        setLoading(false)
      }
    }
  }

  const getHoldingKey = (holding) => `${String(holding?.symbol || '').toUpperCase()}-${holding?.investment_type || 'real_money'}`

  const getSelectedSellQuantity = (holding) => {
    const key = getHoldingKey(holding)
    const totalQuantity = Number(holding?.quantity || 0)
    const customQuantity = Number(sellQuantityByKey[key])

    if (Number.isFinite(customQuantity) && customQuantity > 0) {
      return customQuantity
    }

    const selectedPercent = Number(sellPercentByKey[key] ?? 100)
    const normalizedPercent = Number.isFinite(selectedPercent) && selectedPercent > 0 ? selectedPercent : 100
    return totalQuantity * (normalizedPercent / 100)
  }

  const handleSellHolding = async (holding) => {
    if (!holding?.symbol) {
      return
    }

    const symbol = String(holding.symbol).toUpperCase()
    const totalQuantity = Number(holding.quantity || 0)
    const quantity = getSelectedSellQuantity(holding)
    const type = holding.investment_type || 'real_money'
    const livePrice = Number(livePrices[symbol]?.price || 0)
    const fallbackPrice = Number(holding.current_price ?? holding.average_price ?? holding.price ?? 0)
    const price = livePrice > 0 ? livePrice : fallbackPrice

    if (quantity <= 0 || price <= 0 || totalQuantity <= 0) {
      setActionMessage(`Unable to sell ${symbol}: invalid quantity or price.`)
      return
    }

    if (quantity > totalQuantity) {
      setActionMessage(`Unable to sell ${symbol}: quantity exceeds your holding.`)
      return
    }

    const actionKey = `${symbol}-${type}`
    try {
      setActionLoadingKey(actionKey)
      const response = await cryptoAPI.sellUserHolding({
        symbol,
        quantity,
        price,
        investment_type: type
      })
      setActionMessage(response?.data?.message || `Sold ${symbol} successfully.`)
      setSellQuantityByKey((current) => ({ ...current, [actionKey]: '' }))
      setSellPercentByKey((current) => ({ ...current, [actionKey]: 100 }))
      await refreshPortfolioData(true)
    } catch (sellError) {
      const detail = sellError?.response?.data?.detail || `Failed to sell ${symbol}`
      setActionMessage(detail)
    } finally {
      setActionLoadingKey('')
    }
  }

  const handleWithdraw = async () => {
    const amount = Number(withdrawAmount)
    if (!Number.isFinite(amount) || amount <= 0) {
      setActionMessage('Enter a valid withdrawal amount.')
      return
    }

    try {
      setActionLoadingKey('withdraw')
      const response = await cryptoAPI.withdrawBuyingPower({ amount })
      setActionMessage(response?.data?.message || `Withdrawal of $${amount.toFixed(2)} completed.`)
      setWithdrawAmount('')
      await refreshPortfolioData(true)
    } catch (withdrawError) {
      const detail = withdrawError?.response?.data?.detail || 'Withdrawal failed'
      setActionMessage(detail)
    } finally {
      setActionLoadingKey('')
    }
  }

  const calculateProfitData = (holdings) => {
    return holdings.map(holding => {
      const symbol = holding.symbol?.toUpperCase()
      const cryptoId = getCryptoIdForSymbol(symbol) || symbol?.toLowerCase()
      const livePrice = getLivePriceForSymbol(symbol, livePrices)
      const currentPrice = Number(livePrice ?? holding.current_price ?? holding.price)
      const quantity = getHoldingQuantity(holding)
      const investmentValue = getHoldingCostBasis(holding)
      const currentValue = quantity * currentPrice
      const profitLoss = currentValue - investmentValue
      const profitPercentage = investmentValue > 0 ? (profitLoss / investmentValue) * 100 : 0

      return {
        symbol: holding.symbol,
        cryptoId,
        entryPrice: Number(holding.average_price ?? holding.price ?? 0),
        currentPrice,
        quantity,
        investmentValue,
        currentValue,
        profitLoss,
        profitPercentage,
        type: holding.investment_type
      }
    })
  }

  const generateProfitHistory = (timeRange, totalProfit, portfolioData) => {
    const now = new Date()
    const dayMap = { d: 1, '7d': 7, '30d': 30 }
    const labelMap = { d: '24 Hours', '7d': '7 Days', '30d': '30 Days' }
    const days = dayMap[timeRange] || 7
    const label = labelMap[timeRange] || '7 Days'
    const startTime = now.getTime() - (days * 24 * 60 * 60 * 1000)

    const activityLog = Array.isArray(portfolioData?.activity_log) ? portfolioData.activity_log : []
    const realizedEvents = activityLog
      .filter((entry) => entry?.event === 'sell')
      .map((entry) => {
        const timestampMs = Date.parse(entry?.timestamp || '')
        return {
          timestampMs,
          realizedProfit: Number(entry?.realized_profit || 0)
        }
      })
      .filter((entry) => Number.isFinite(entry.timestampMs))
      .sort((a, b) => a.timestampMs - b.timestampMs)

    const pointCount = days === 1 ? 24 : days
    const data = []

    for (let i = 0; i <= pointCount; i++) {
      const pointTime = startTime + ((now.getTime() - startTime) * (i / pointCount))
      const realizedToPoint = realizedEvents
        .filter((entry) => entry.timestampMs <= pointTime)
        .reduce((sum, entry) => sum + entry.realizedProfit, 0)

      const progress = i / pointCount
      const interpolatedTotal = totalProfit * progress
      const pointProfit = (interpolatedTotal * 0.65) + (realizedToPoint * 0.35)
      const pointDate = new Date(pointTime)

      const dateStr = days === 1
        ? pointDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
        : pointDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })

      data.push({
        name: dateStr,
        profit: Number(pointProfit.toFixed(2)),
        timestamp: pointTime
      })
    }

    if (data.length) {
      data[data.length - 1].profit = Number(totalProfit.toFixed(2))
    }

    return { data, label }
  }

  const getTotalProfit = (profitData) => {
    return profitData.reduce((sum, item) => sum + item.profitLoss, 0)
  }

  const getTotalProfitPercentage = (profitData, totalInvested) => {
    const totalProfit = getTotalProfit(profitData)
    return totalInvested > 0 ? (totalProfit / totalInvested) * 100 : 0
  }

  const getProfitByType = (allProfitData) => {
    const fake = allProfitData.filter(p => p.type === 'fake_money')
    const real = allProfitData.filter(p => p.type === 'real_money')

    return {
      fake: {
        profit: getTotalProfit(fake),
        percentage: fake.length > 0 ? getTotalProfitPercentage(fake, fake.reduce((sum, p) => sum + p.investmentValue, 0)) : 0
      },
      real: {
        profit: getTotalProfit(real),
        percentage: real.length > 0 ? getTotalProfitPercentage(real, real.reduce((sum, p) => sum + p.investmentValue, 0)) : 0
      }
    }
  }

  const openHoldingDetails = (symbol) => {
    const cryptoId = SYMBOL_TO_CRYPTO_ID[symbol?.toUpperCase()] || symbol?.toLowerCase()
    if (!cryptoId) {
      return
    }

    navigate(`/invest/${cryptoId}`)
  }

  const getHoldingSuggestion = (holding) => {
    const symbol = String(holding?.symbol || '').toUpperCase()
    const livePrice = Number(livePrices[symbol]?.price || 0)
    const currentPrice = livePrice > 0
      ? livePrice
      : Number(holding?.current_price ?? holding?.price ?? 0)
    const entryPrice = Number(holding?.average_price ?? holding?.price ?? 0)

    if (!Number.isFinite(currentPrice) || currentPrice <= 0 || !Number.isFinite(entryPrice) || entryPrice <= 0) {
      return {
        label: 'HOLD',
        reason: 'Waiting for clearer price data.',
        className: 'hold'
      }
    }

    const changePercent = ((currentPrice - entryPrice) / entryPrice) * 100

    if (changePercent >= 8) {
      return {
        label: 'SELL',
        reason: `Up ${changePercent.toFixed(1)}% from entry.`,
        className: 'sell'
      }
    }

    if (changePercent <= -6) {
      return {
        label: 'BUY',
        reason: `Down ${Math.abs(changePercent).toFixed(1)}% from entry.`,
        className: 'buy'
      }
    }

    return {
      label: 'HOLD',
      reason: `${Math.abs(changePercent).toFixed(1)}% from entry, mixed momentum.`,
      className: 'hold'
    }
  }

  if (loading) return <div className="user-investments-panel">Loading investments...</div>
  if (error) return <div className="user-investments-panel error">{error}</div>
  if (!portfolio) return <div className="user-investments-panel">No portfolio data</div>

  const holdings = portfolio.holdings || []
  const filteredHoldings = investmentType === 'all'
    ? holdings
    : holdings.filter(h => h.investment_type === (investmentType === 'fake' ? 'fake_money' : 'real_money'))

  const allProfitData = calculateProfitData(holdings)
  const filteredProfitData = calculateProfitData(filteredHoldings)
  const scopedProfitData = investmentType === 'all' ? allProfitData : filteredProfitData
  const unrealizedProfit = getTotalProfit(scopedProfitData)
  const realizedProfit = getScopedRealizedProfit(portfolio, investmentType)
  const totalProfit = unrealizedProfit + realizedProfit
  const totalInvested = scopedProfitData.reduce((sum, item) => sum + item.investmentValue, 0)
  const realizedCostBasis = getScopedRealizedCostBasis(portfolio, investmentType)
  const totalTrackedCostBasis = totalInvested + realizedCostBasis
  const totalProfitPercentage = totalTrackedCostBasis > 0 ? (totalProfit / totalTrackedCostBasis) * 100 : 0
  const scopedCurrentValue = scopedProfitData.reduce((sum, item) => sum + item.currentValue, 0)
  const profitByType = getProfitByType(allProfitData)
  const profitScopeLabel = investmentType === 'all'
    ? 'Overall'
    : investmentType === 'fake'
      ? 'Practice Money'
      : 'Real Money'

  const scopedPortfolioValue = investmentType === 'all'
    ? Number(portfolio.cash || 0) + Number(portfolio.personal_buying_power || 0) + scopedCurrentValue
    : investmentType === 'real'
      ? Number(portfolio.personal_buying_power || 0) + scopedCurrentValue
      : Number(portfolio.cash || 0) + scopedCurrentValue
  const personalBuyingPower = Number(portfolio.personal_buying_power || 0)
  const totalWithdrawn = (portfolio.withdrawals || []).reduce((sum, item) => sum + Number(item?.amount || 0), 0)

  const moneyInMarket = scopedCurrentValue

  const topHoldings = allProfitData
    .sort((a, b) => b.profitLoss - a.profitLoss)
    .slice(0, 5)

  const openHoldingDetail = (holding) => {
    if (!holding?.cryptoId) {
      return
    }

    navigate(`/invest/${holding.cryptoId}`)
  }

  const chartData = [
    {
      name: 'Practice Money',
      profit: profitByType.fake.profit + Number(portfolio?.realized_pnl?.fake_money || 0)
    },
    {
      name: 'Real Money',
      profit: profitByType.real.profit + Number(portfolio?.realized_pnl?.real_money || 0)
    }
  ].filter(item => item.profit !== 0)

  const { data: profitHistory, label: rangeLabel } = generateProfitHistory(profitTimeRange, totalProfit, portfolio)

  const positivePositions = scopedProfitData.filter((item) => item.profitLoss > 0)
  const negativePositions = scopedProfitData.filter((item) => item.profitLoss < 0)
  const neutralPositions = scopedProfitData.filter((item) => item.profitLoss === 0)

  const bestPerformer = scopedProfitData.length
    ? [...scopedProfitData].sort((a, b) => b.profitLoss - a.profitLoss)[0]
    : null
  const biggestDrag = scopedProfitData.length
    ? [...scopedProfitData].sort((a, b) => a.profitLoss - b.profitLoss)[0]
    : null

  const profitNarrative = totalProfit >= 0
    ? `${profitScopeLabel} total P&L is up ${totalProfit.toFixed(2)} USD (${unrealizedProfit.toFixed(2)} unrealized, ${realizedProfit.toFixed(2)} realized).`
    : `${profitScopeLabel} total P&L is down ${Math.abs(totalProfit).toFixed(2)} USD (${unrealizedProfit.toFixed(2)} unrealized, ${realizedProfit.toFixed(2)} realized).`

  return (
    <div className="user-investments-panel">
      <div className="panel-header">
        <h2>💼 Your Investments</h2>
        <button className="refresh-btn" onClick={() => refreshPortfolioData(true)}>↻ Refresh</button>
      </div>

      <div className="investment-tabs">
        <button
          className={`tab ${investmentType === 'all' ? 'active' : ''}`}
          onClick={() => setInvestmentType('all')}
        >
          📊 All Investments <span>{holdings.length}</span>
        </button>
        <button
          className={`tab ${investmentType === 'fake' ? 'active' : ''}`}
          onClick={() => setInvestmentType('fake')}
        >
          🎮 Practice Money <span>{holdings.filter(h => h.investment_type === 'fake_money').length}</span>
        </button>
        <button
          className={`tab ${investmentType === 'real' ? 'active' : ''}`}
          onClick={() => setInvestmentType('real')}
        >
          💰 Real Money <span>{holdings.filter(h => h.investment_type === 'real_money').length}</span>
        </button>
      </div>

      <div className="portfolio-summary">
        <div className="summary-card">
          <div className="summary-label">Available Cash</div>
          <div className="summary-value">${portfolio.cash?.toFixed(2) || '0.00'}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Money in Market</div>
          <div className="summary-value">${moneyInMarket.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Total Invested</div>
          <div className="summary-value">${totalInvested.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Portfolio Value</div>
          <div className="summary-value">${scopedPortfolioValue.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Personal Buying Power</div>
          <div className="summary-value">${personalBuyingPower.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Total Withdrawn</div>
          <div className="summary-value">${totalWithdrawn.toFixed(2)}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Unrealized P&L</div>
          <div className="summary-value" style={{ color: unrealizedProfit >= 0 ? '#4caf50' : '#f44336' }}>
            {unrealizedProfit >= 0 ? '+' : ''}{unrealizedProfit.toFixed(2)}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Realized P&L</div>
          <div className="summary-value" style={{ color: realizedProfit >= 0 ? '#4caf50' : '#f44336' }}>
            {realizedProfit >= 0 ? '+' : ''}{realizedProfit.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="withdraw-section">
        <div className="withdraw-label">Withdraw from Personal Buying Power</div>
        <div className="withdraw-controls">
          <input
            type="number"
            min="0"
            step="0.01"
            value={withdrawAmount}
            onChange={(event) => setWithdrawAmount(event.target.value)}
            placeholder="Enter amount"
            className="withdraw-input"
          />
          <button
            className="withdraw-btn"
            onClick={handleWithdraw}
            disabled={actionLoadingKey === 'withdraw'}
          >
            {actionLoadingKey === 'withdraw' ? 'Processing...' : 'Withdraw'}
          </button>
        </div>
      </div>

      {actionMessage && <div className="action-message">{actionMessage}</div>}

      {/* Profit Visualization Section */}
      <div className="profit-summary">
        <h3>📊 {profitScopeLabel} Profit/Loss</h3>
        <div className={`practice-tick ${isConnected ? 'live' : 'polling'}`}>
          <span className="practice-tick-label">Practice Tick</span>
          <span className="practice-tick-value">
            {practiceLastTickAt
              ? new Date(practiceLastTickAt).toLocaleTimeString()
              : 'Waiting for live practice updates'}
          </span>
        </div>
        <div className={`profit-card ${totalProfit >= 0 ? 'positive' : 'negative'}`}>
          <div className="profit-amount">{totalProfit >= 0 ? '+' : ''}{totalProfit.toFixed(2)} USD</div>
          <div className="profit-percentage">{totalProfitPercentage >= 0 ? '+' : ''}{totalProfitPercentage.toFixed(2)}%</div>
          <div className="profit-breakdown-badges">
            <span className={`profit-breakdown-badge ${unrealizedProfit >= 0 ? 'positive' : 'negative'}`}>
              Unrealized: {unrealizedProfit >= 0 ? '+' : ''}{unrealizedProfit.toFixed(2)} USD
            </span>
            <span className={`profit-breakdown-badge ${realizedProfit >= 0 ? 'positive' : 'negative'}`}>
              Realized: {realizedProfit >= 0 ? '+' : ''}{realizedProfit.toFixed(2)} USD
            </span>
          </div>
          <div className="profit-emoji">{totalProfit >= 0 ? '📈' : '📉'}</div>
        </div>

        <div className="profit-explainer">
          <h4>How this profit/loss is calculated</h4>
          <p className="profit-narrative">{profitNarrative}</p>

          <div className="profit-explainer-grid">
            <div className="explainer-item">
              <span className="explainer-label">Cost Basis</span>
              <span className="explainer-value">${totalInvested.toFixed(2)}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Realized Cost Basis</span>
              <span className="explainer-value">${realizedCostBasis.toFixed(2)}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Current Market Value</span>
              <span className="explainer-value">${scopedCurrentValue.toFixed(2)}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Winning Positions</span>
              <span className="explainer-value">{positivePositions.length}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Losing Positions</span>
              <span className="explainer-value">{negativePositions.length}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Flat Positions</span>
              <span className="explainer-value">{neutralPositions.length}</span>
            </div>
            <div className="explainer-item">
              <span className="explainer-label">Formula</span>
              <span className="explainer-value explainer-formula">Market Value - Cost Basis</span>
            </div>
          </div>

          <div className="profit-highlights">
            <div className="highlight-card positive">
              <span className="highlight-title">Top Contributor</span>
              {bestPerformer ? (
                <span className="highlight-value">{bestPerformer.symbol}: {bestPerformer.profitLoss >= 0 ? '+' : ''}{bestPerformer.profitLoss.toFixed(2)} USD</span>
              ) : (
                <span className="highlight-value">No data</span>
              )}
            </div>
            <div className="highlight-card negative">
              <span className="highlight-title">Biggest Drag</span>
              {biggestDrag ? (
                <span className="highlight-value">{biggestDrag.symbol}: {biggestDrag.profitLoss >= 0 ? '+' : ''}{biggestDrag.profitLoss.toFixed(2)} USD</span>
              ) : (
                <span className="highlight-value">No data</span>
              )}
            </div>
          </div>
        </div>

        {chartData.length > 0 && (
          <div className="profit-chart-container">
            <div className="chart-header-live">
              <span>Profit by Investment Type</span>
              <span className="live-indicator">{isConnected ? '🔴 LIVE' : '⏱️ REFRESHING'}</span>
            </div>
            
            <div className="profit-time-range-selector">
              <button
                className={`time-range-btn ${profitTimeRange === 'd' ? 'active' : ''}`}
                onClick={() => setProfitTimeRange('d')}
              >
                📅 1 Day
              </button>
              <button
                className={`time-range-btn ${profitTimeRange === '7d' ? 'active' : ''}`}
                onClick={() => setProfitTimeRange('7d')}
              >
                📊 7 Days
              </button>
              <button
                className={`time-range-btn ${profitTimeRange === '30d' ? 'active' : ''}`}
                onClick={() => setProfitTimeRange('30d')}
              >
                📈 30 Days
              </button>
            </div>
            
            <div className="chart-metrics">
              <div className="metric-box live-metric">
                <div className="metric-header">
                  <div className="metric-label">Total Invested</div>
                  <span className="metric-live-badge">🔴 LIVE</span>
                </div>
                <div className="metric-value">${totalInvested.toFixed(2)}</div>
              </div>
              <div className="metric-box live-metric">
                <div className="metric-header">
                  <div className="metric-label">Total Account Value</div>
                  <span className="metric-live-badge">🔴 LIVE</span>
                </div>
                <div className="metric-value" style={{color: '#ffc107'}}>
                  ${scopedPortfolioValue.toFixed(2)}
                </div>
              </div>
              <div className="metric-box live-metric">
                <div className="metric-header">
                  <div className="metric-label">Overall Profit</div>
                  <span className="metric-live-badge">🔴 LIVE</span>
                </div>
                <div className="metric-value" style={{color: totalProfit >= 0 ? '#4caf50' : '#f44336'}}>
                  {totalProfit >= 0 ? '+' : ''}{totalProfit.toFixed(2)} USD
                </div>
              </div>
            </div>
            
            <div>
              <div className="profit-chart-label">{rangeLabel} Profit Progress</div>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={profitHistory} margin={{ top: 20, right: 30, left: 0, bottom: 20 }} isAnimationActive={true}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                  <XAxis dataKey="name" stroke="#888" fontSize={12} />
                  <YAxis stroke="#888" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #ffc107' }}
                    formatter={(value) => `$${Number(value || 0).toFixed(2)}`}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="profit" 
                    stroke={totalProfit >= 0 ? '#4caf50' : '#f44336'} 
                    strokeWidth={3} 
                    dot={{ fill: totalProfit >= 0 ? '#4caf50' : '#f44336', r: 5 }} 
                    activeDot={{ r: 8 }} 
                    animationDuration={300}
                    name="Profit"
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="top-performers">
          <div className="chart-header">Top Holdings by Profit</div>
          <div className="performers-list">
            {topHoldings.map((holding, idx) => (
              <button
                key={idx}
                type="button"
                className={`performer-item ${holding.profitLoss >= 0 ? 'gain' : 'loss'}`}
                onClick={() => openHoldingDetail(holding)}
                aria-label={`Open ${holding.symbol} investment details`}
                style={{ width: '100%', cursor: 'pointer', font: 'inherit', color: 'inherit', textAlign: 'left' }}
              >
                <div className="performer-symbol">{holding.symbol}</div>
                <div className="performer-details">
                  <div className="performer-profit">{holding.profitLoss >= 0 ? '📈' : '📉'} {holding.profitLoss >= 0 ? '+' : ''}{holding.profitLoss.toFixed(2)} USD</div>
                  <div className="performer-percentage">{holding.profitPercentage >= 0 ? '+' : ''}{holding.profitPercentage.toFixed(2)}%</div>
                </div>
                <div className="performer-price">${holding.currentPrice.toFixed(2)}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Holdings Table */}
      <div className="holdings-section">
        <div className="holdings-header">
          <h3>🎮 Practice Investments</h3>
          <span>${holdings.filter(h => h.investment_type === 'fake_money').reduce((sum, h) => sum + getHoldingCostBasis(h), 0).toFixed(2)}</span>
        </div>

        {filteredHoldings.filter(h => h.investment_type === 'fake_money').length > 0 ? (
          <div className="holdings-table">
            <div className="table-header">
              <div>Cryptocurrency</div>
              <div>Quantity</div>
              <div>Price</div>
              <div>Total Value</div>
              <div>Date</div>
              <div>AI Suggestion</div>
              <div>Sell Controls</div>
            </div>
            {filteredHoldings.filter(h => h.investment_type === 'fake_money').map((holding, idx) => (
              <div key={idx} className="table-row">
                {(() => {
                  const suggestion = getHoldingSuggestion(holding)
                  return (
                    <>
                <div>🎮 {holding.symbol}</div>
                <div>{holding.quantity.toFixed(8)}</div>
                <div>${holding.price.toFixed(2)}</div>
                <div>${(holding.quantity * holding.price).toFixed(2)}</div>
                <div>{new Date(holding.timestamp || holding.updated_at || holding.created_at || Date.now()).toLocaleDateString()}</div>
                <div className="holding-suggestion-cell">
                  <span className={`holding-suggestion-badge ${suggestion.className}`}>{suggestion.label}</span>
                  <small>{suggestion.reason}</small>
                </div>
                <div className="sell-controls-cell">
                  <select
                    className="sell-percent-select"
                    value={sellPercentByKey[getHoldingKey(holding)] ?? 100}
                    onChange={(event) => setSellPercentByKey((current) => ({
                      ...current,
                      [getHoldingKey(holding)]: Number(event.target.value)
                    }))}
                  >
                    <option value={25}>25%</option>
                    <option value={50}>50%</option>
                    <option value={100}>100%</option>
                  </select>
                  <input
                    className="sell-qty-input"
                    type="number"
                    min="0"
                    step="0.00000001"
                    placeholder="Qty"
                    value={sellQuantityByKey[getHoldingKey(holding)] ?? ''}
                    onChange={(event) => setSellQuantityByKey((current) => ({
                      ...current,
                      [getHoldingKey(holding)]: event.target.value
                    }))}
                  />
                  <button
                    className="sell-btn"
                    onClick={() => handleSellHolding(holding)}
                    disabled={actionLoadingKey === `${String(holding.symbol || '').toUpperCase()}-${holding.investment_type}`}
                  >
                    {actionLoadingKey === `${String(holding.symbol || '').toUpperCase()}-${holding.investment_type}` ? 'Selling...' : 'Sell'}
                  </button>
                </div>
                    </>
                  )
                })()}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-holdings">No practice investments yet. Start with fake money!</div>
        )}

      </div>

      <div className="holdings-section">
        <div className="holdings-header">
          <h3>💰 Real Money Investments</h3>
          <span>${holdings.filter(h => h.investment_type === 'real_money').reduce((sum, h) => sum + getHoldingCostBasis(h), 0).toFixed(2)}</span>
        </div>
        {filteredHoldings.filter(h => h.investment_type === 'real_money').length > 0 ? (
          <div className="holdings-table">
            <div className="table-header">
              <div>Cryptocurrency</div>
              <div>Quantity</div>
              <div>Price</div>
              <div>Total Value</div>
              <div>Date</div>
              <div>AI Suggestion</div>
              <div>Sell Controls</div>
            </div>
            {filteredHoldings.filter(h => h.investment_type === 'real_money').map((holding, idx) => (
              <div key={idx} className="table-row">
                {(() => {
                  const suggestion = getHoldingSuggestion(holding)
                  return (
                    <>
                <div>💰 {holding.symbol}</div>
                <div>{holding.quantity.toFixed(8)}</div>
                <div>${holding.price.toFixed(2)}</div>
                <div>${(holding.quantity * holding.price).toFixed(2)}</div>
                <div>{new Date(holding.timestamp || holding.updated_at || holding.created_at || Date.now()).toLocaleDateString()}</div>
                <div className="holding-suggestion-cell">
                  <span className={`holding-suggestion-badge ${suggestion.className}`}>{suggestion.label}</span>
                  <small>{suggestion.reason}</small>
                </div>
                <div className="sell-controls-cell">
                  <select
                    className="sell-percent-select"
                    value={sellPercentByKey[getHoldingKey(holding)] ?? 100}
                    onChange={(event) => setSellPercentByKey((current) => ({
                      ...current,
                      [getHoldingKey(holding)]: Number(event.target.value)
                    }))}
                  >
                    <option value={25}>25%</option>
                    <option value={50}>50%</option>
                    <option value={100}>100%</option>
                  </select>
                  <input
                    className="sell-qty-input"
                    type="number"
                    min="0"
                    step="0.00000001"
                    placeholder="Qty"
                    value={sellQuantityByKey[getHoldingKey(holding)] ?? ''}
                    onChange={(event) => setSellQuantityByKey((current) => ({
                      ...current,
                      [getHoldingKey(holding)]: event.target.value
                    }))}
                  />
                  <button
                    className="sell-btn"
                    onClick={() => handleSellHolding(holding)}
                    disabled={actionLoadingKey === `${String(holding.symbol || '').toUpperCase()}-${holding.investment_type}`}
                  >
                    {actionLoadingKey === `${String(holding.symbol || '').toUpperCase()}-${holding.investment_type}` ? 'Selling...' : 'Sell'}
                  </button>
                </div>
                    </>
                  )
                })()}
              </div>
            ))}
          </div>
        ) : (
          <div className="no-holdings">No real money investments yet. Start investing to grow your portfolio!</div>
        )}
      </div>
    </div>
  )
}

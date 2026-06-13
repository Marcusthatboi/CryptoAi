import axios from 'axios'
import { API_BASE } from './backendConfig'

const RETRYABLE_METHODS = new Set(['get', 'head', 'options'])
const DEFAULT_MAX_RETRY_ATTEMPTS = 2
const RETRY_BASE_DELAY_MS = 400
const RETRY_LOG_ENABLED = import.meta.env.DEV && import.meta.env.VITE_API_RETRY_DEBUG === 'true'

const sleep = (delayMs) => new Promise((resolve) => {
  setTimeout(resolve, delayMs)
})

const getRetryDelayMs = (error, retryCount) => {
  const retryAfter = Number(error?.response?.headers?.['retry-after'])
  if (Number.isFinite(retryAfter) && retryAfter > 0) {
    return retryAfter * 1000
  }

  return RETRY_BASE_DELAY_MS * Math.pow(2, Math.max(0, retryCount - 1))
}

const isRetryableError = (error) => {
  // Axios timeout errors use ECONNABORTED; retrying these usually amplifies latency.
  if (error?.code === 'ECONNABORTED') {
    return false
  }

  const status = error?.response?.status
  if (!status) {
    return true
  }

  return status >= 500
}

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,  // 30 second timeout for slow database queries and AI processing
  headers: {
    'Content-Type': 'application/json'
  }
})

// Add Authorization header to all requests if token exists
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const status = error?.response?.status
    const config = error?.config || {}
    const method = String(config.method || 'get').toLowerCase()
    const requestUrl = config.url || ''
    const currentRetry = config.__retryCount || 0
    const maxRetryAttempts = Number.isFinite(config.retryAttempts)
      ? Math.max(0, Number(config.retryAttempts))
      : DEFAULT_MAX_RETRY_ATTEMPTS
    const shouldLogRetry = typeof config.retryLog === 'boolean' ? config.retryLog : RETRY_LOG_ENABLED
    const shouldRetry =
      RETRYABLE_METHODS.has(method) &&
      currentRetry < maxRetryAttempts &&
      isRetryableError(error)

    if (shouldRetry) {
      config.__retryCount = currentRetry + 1
      const delayMs = getRetryDelayMs(error, config.__retryCount)
      if (shouldLogRetry) {
        console.warn(
          `Transient API failure for ${method.toUpperCase()} ${requestUrl}. ` +
          `Retrying (${config.__retryCount}/${maxRetryAttempts}) in ${delayMs}ms.`
        )
      }
      await sleep(delayMs)
      return api(config)
    }

    if (status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    if (status === 429) {
      const retryAfter = error?.response?.headers?.['retry-after']
      console.warn(`Request rate limited${retryAfter ? `, retry after ${retryAfter}s` : ''}`)
    }

    return Promise.reject(error)
  }
)

export const cryptoAPI = {
  // Health check
  health: () => api.get('/health'),
  
  // Price endpoints
  getPrice: (cryptoId) => api.get(`/api/price/${cryptoId}`, { timeout: 25000 }),
  getPrices: (cryptoIds) => api.post('/api/prices', cryptoIds, { timeout: 25000 }),
  refreshPrices: () => api.get('/api/prices/refresh', { timeout: 20000 }),
  
  // Analysis endpoints
  getTrendAnalysis: (cryptoId, smaWindow = 5) => 
    api.get(`/api/analysis/${cryptoId}`, { params: { sma_window: smaWindow }, timeout: 25000 }),
  getAllTrends: (smaWindow = 5) => 
    api.get('/api/analysis', { params: { sma_window: smaWindow }, timeout: 25000 }),
  
  // Alert endpoints
  getAlerts: (threshold = 5.0) => 
    api.get('/api/alerts', { params: { threshold }, retryAttempts: 0, timeout: 20000 }),
  getAlertAutoBuyConfig: () =>
    api.get('/api/alerts/auto-buy', { timeout: 15000 }),
  updateAlertAutoBuyConfig: (payload) =>
    api.post('/api/alerts/auto-buy', payload, { timeout: 15000 }),
  
  // History endpoints
  getHistory: (cryptoId, limit = 50) => 
    api.get(`/api/history/${cryptoId}`, { params: { limit }, timeout: 25000 }),
  
  // ML endpoints
  getMLData: (cryptoId) => api.get(`/api/ml-data/${cryptoId}`, { timeout: 25000 }),
  
  // Stats endpoints
  getStats: () => api.get('/api/stats', { timeout: 25000 }),
  
  // Config endpoints
  getConfig: () => api.get('/api/config'),
  getLiveReadiness: () => api.get('/api/system/live-readiness', { timeout: 12000, retryAttempts: 0 }),
  getAssets: (limit = 250) => api.get('/api/assets', { params: { limit } }),
  
  // Chat endpoint
  sendChat: (message, context = 'crypto') => 
    api.post('/api/chat', { message, context }),
  fixGrammar: (text) =>
    api.post('/api/text/grammar', { text }, { timeout: 30000 }),
  
  // Recommendations endpoint
  getRecommendations: (count = 5, filters = {}) => 
    api.get('/api/recommendations', { 
      params: { 
        count,
        strategy: filters.strategy || 'balanced',
        timePeriod: filters.timePeriod || '7d',
        riskLevel: filters.riskLevel || 'all'
      },
      timeout: 30000  // AI analysis can be slow
    }),
  shareAnalysisToIntegration: (payload) =>
    api.post('/api/integrations/share-analysis', payload, { timeout: 12000 }),
  getIntegrationsStatus: () => api.get('/api/integrations/status', { timeout: 8000 }),
  sendIntegrationTest: (platform) => api.post('/api/integrations/test', { platform }, { timeout: 12000 }),

  // Subscription usage summary endpoint
  getSubscriptionStatus: () => api.get('/api/subscription/status'),
  getSubscriptionUsageSummary: () => api.get('/api/subscription/usage-summary'),
  getAdCampaigns: () => api.get('/api/ads/campaigns', { timeout: 15000 }),
  getAdPlacements: (placement = 'home', limit = 2) =>
    api.get(`/api/ads/placements/${placement}`, { params: { limit }, timeout: 15000 }),
  createAdCampaign: (payload) => api.post('/api/ads/campaigns', payload, { timeout: 20000 }),
  createAdCheckoutSession: (campaignId, payload) =>
    api.post(`/api/ads/campaigns/${campaignId}/stripe-checkout-session`, payload, { timeout: 20000 }),
  
  // User Portfolio endpoints
  getUserPortfolio: (options = {}) =>
    api.get('/api/user/portfolio', {
      timeout: options.timeout ?? 30000,  // Database queries can be slow
      retryAttempts: options.retryAttempts
    }),
  verifyProfitCalculation: (options = {}) =>
    api.get('/api/profit-verification', {
      timeout: options.timeout ?? 30000,
      retryAttempts: options.retryAttempts
    }),
  sellUserHolding: (payload) => api.post('/api/user/portfolio/sell', payload),
  addBuyingPower: (payload) => api.post('/api/user/portfolio/add-buying-power', payload),
  withdrawBuyingPower: (payload) => api.post('/api/user/portfolio/withdraw', payload),
  sendSupportRequest: (payload) => api.post('/api/support/contact', payload, { timeout: 12000 }),
  investFakeMoney: (investData) => api.post('/api/user/portfolio/invest/fake', investData),
  precheckRealMoneyInvest: (investData) => api.post('/api/user/portfolio/invest/real/precheck', investData),
  createTradePaymentIntent: (payload) => api.post('/api/payments/trade/create-intent', payload),
  investRealMoney: (investData) => api.post('/api/user/portfolio/invest/real', investData),
  
  // Ollama endpoints
  ollamaStatus: (options = {}) =>
    api.get('/api/ollama/status', { timeout: options.timeout ?? 15000, retryAttempts: 0 }),  // Ollama might be slow to initialize
  switchModel: (modelName) => api.post(`/api/ollama/switch-model/${modelName}`),

  // Alpaca Trading endpoints
  getAlpacaAccount: () => api.get('/alpaca/account'),
  getAlpacaHoldings: () => api.get('/alpaca/holdings'),
  getAlpacaOrders: (status = 'all') => api.get('/alpaca/orders', { params: { status } }),
  getAlpacaQuote: (symbol) => api.get(`/alpaca/quote/${symbol}`),
  placeAlpacaOrder: (orderData) => api.post('/alpaca/order', orderData),
  cancelAlpacaOrder: (orderId) => api.delete(`/alpaca/order/${orderId}`),
  getAlpacaOrderStatus: (orderId) => api.get(`/alpaca/order/${orderId}`),

  // Binance endpoints
  getBinanceStatus: () => api.get('/api/binance/status'),
  getBinanceAccount: () => api.get('/api/binance/account'),
  getBinanceBalance: (asset = null) => 
    api.get('/api/binance/balance', { params: asset ? { asset } : {} }),
  getBinancePortfolio: (baseCurrency = 'USDT') => 
    api.get('/api/binance/portfolio', { params: { base_currency: baseCurrency } }),
  getBinanceTicker: (symbol) => api.get(`/api/binance/ticker/${symbol}`),
  getBinanceKlines: (symbol, interval = '1h', limit = 100) => 
    api.get(`/api/binance/klines/${symbol}`, { params: { interval, limit } }),
  getBinanceGainers: (limit = 10) => 
    api.get('/api/binance/gainers', { params: { limit } }),
  placeBinanceTrade: (tradeData) => api.post('/api/binance/trade', tradeData),
  cancelBinanceOrder: (symbol, orderId) => 
    api.post('/api/binance/cancel-order', null, { params: { symbol, order_id: orderId } }),
  getBinanceOrderStatus: (symbol, orderId) => 
    api.get('/api/binance/order-status', { params: { symbol, order_id: orderId } }),
  getBinanceOpenOrders: (symbol = null) => 
    api.get('/api/binance/open-orders', { params: symbol ? { symbol } : {} }),
  getBinanceOrderHistory: (symbol = null, limit = 20) => 
    api.get('/api/binance/order-history', { params: { symbol, limit } }),
  getBinanceTradingPairs: (quoteAsset = 'USDT', limit = 100) => 
    api.get('/api/binance/trading-pairs', { params: { quote_asset: quoteAsset, limit } }),
  searchBinanceSymbol: (query) => api.get(`/api/binance/search/${query}`),

  // Auth endpoints
  getProfile: () => api.get('/auth/profile'),
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (username, password, email) => api.post('/auth/register', { username, password, email }),
  forgotPassword: (payload) => api.post('/auth/forgot-password', payload),
  resetPassword: (payload) => api.post('/auth/reset-password', payload),
  updateAccountSettings: (encryptedPayload) => 
    api.post('/auth/update-settings', encryptedPayload, { timeout: 10000 }),

  // Admin endpoints
  getAdminAnalyticsOverview: (days = 7) => api.get('/api/subscription/analytics/overview', { params: { days } }),
  getAdminCustomers: (params = {}) => api.get('/api/admin/customers', { params }),
  updateAdminCustomerSubscription: (userId, payload) =>
    api.patch(`/api/admin/customers/${userId}/subscription`, payload),

  // Auto Trading endpoints
  getAutoTradingWarnings: () => api.get('/api/auto-trading/warnings'),
  generateTradingSignal: (symbol) => 
    api.post(`/api/auto-trading/generate-signal/${symbol}`, {}, { timeout: 15000 }),
  assessAutoTradeRisk: (payload) =>
    api.post('/api/auto-trading/assess-risk', payload, { timeout: 15000 }),
  previewAutoTrade: (payload) =>
    api.post('/api/auto-trading/preview', payload, { timeout: 15000 }),
  executeAutoTrade: (payload) =>
    api.post('/api/auto-trading/execute', payload, { timeout: 20000 }),
  getActiveAutoTrades: () => api.get('/api/auto-trading/user/active-trades', { timeout: 15000 }),
  runBacktest: (payload) =>
    api.post('/api/auto-trading/backtest', payload, { timeout: 30000 }),

  // Per-Cryptocurrency Auto Trading endpoints
  enableAutoTradingCoin: (symbol, buyPercentage, sellPercentage, referencePrice) =>
    api.post(`/api/auto-trading-per-coin/enable/${symbol}`, null, {
      params: {
        buy_percentage: buyPercentage,
        sell_percentage: sellPercentage,
        reference_price: referencePrice
      },
      timeout: 8000
    }),
  disableAutoTradingCoin: (symbol) =>
    api.post(`/api/auto-trading-per-coin/disable/${symbol}`, null, { timeout: 8000 }),
  getAutoTradingCoinSettings: (symbol) =>
    api.get(`/api/auto-trading-per-coin/settings/${symbol}`, { timeout: 7000 }),
  getAllActiveAutoTradingCoins: (options = {}) =>
    api.get('/api/auto-trading-per-coin/active', {
      timeout: options.timeout ?? 15000,
      retryAttempts: options.retryAttempts
    }),
  getAutoTradingCoinHistory: (symbol, limit = 50) =>
    api.get(`/api/auto-trading-per-coin/history/${symbol}`, { params: { limit }, timeout: 7000 }),
  getAutoTradingCoinStats: (symbol) =>
    api.get(`/api/auto-trading-per-coin/stats/${symbol}`, { timeout: 7000 }),
  updateAutoTradingCoinSettings: (symbol, buyPercentage, sellPercentage, referencePrice) =>
    api.put(`/api/auto-trading-per-coin/update/${symbol}`, null, {
      params: {
        buy_percentage: buyPercentage,
        sell_percentage: sellPercentage,
        reference_price: referencePrice
      },
      timeout: 8000
    }),
  getAutoTradingAIRecommendations: (symbol) =>
    api.get(`/api/auto-trading-per-coin/recommendations/${symbol}`, { timeout: 7000 })
}

export default api

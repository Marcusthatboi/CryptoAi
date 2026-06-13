import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import PriceCard from './components/PriceCard'
import AlertPanel from './components/AlertPanel'
import AIChatSidePanel from './components/AIChatSidePanel'
import RecommendationsPanel from './components/RecommendationsPanel'
import PortfolioPanel from './components/PortfolioPanel'
import UserInvestmentsPanel from './components/UserInvestmentsPanel'
import SubscriptionStatus from './components/SubscriptionStatus'
import SupportModal from './components/SupportModal'
import AutoTradingPanel from './components/AutoTradingPanel'
import BrandMark from './components/BrandMark'
import InvestmentDetailPage from './pages/InvestmentDetailPage'
import PricingPage from './pages/PricingPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ResetPasswordPage from './pages/ResetPasswordPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import AutoTradingPage from './pages/AutoTradingPage'
import SettingsPage from './pages/SettingsPage'
import AffiliateToolsPage from './pages/AffiliateToolsPage'
import AllCryptosPage from './pages/AllCryptosPage'
import LanguageSelector from './components/LanguageSelector'
import DashboardDirectory from './components/DashboardDirectory'
import AdPanel from './components/AdPanel'
import { useLanguage } from './context/LanguageContext'
import { useAuth } from './hooks/useAuth.jsx'
import { cryptoAPI } from './utils/api'
import { BACKEND_HEALTH_URL } from './utils/backendConfig'
import './App.css'

const BUILD_STAMP = typeof __BUILD_STAMP__ !== 'undefined' ? __BUILD_STAMP__ : 'local-dev'

const DEFAULT_CRYPTO_IDS = [
  'bitcoin',
  'ethereum',
  'tether',
  'binancecoin',
  'usd-coin',
  'cardano',
  'solana',
  'ripple',
  'tron',
  'toncoin',
  'polkadot',
  'dogecoin',
  'shiba-inu',
  'avalanche-2',
  'chainlink',
  'polygon',
  'litecoin',
  'uniswap',
  'bitcoin-cash',
  'near',
  'stellar',
  'filecoin',
  'hedera-hashgraph',
  'cosmos',
  'algorand',
  'aptos',
  'arbitrum',
  'optimism',
  'render-token',
  'immutable-x'
]
const PRICE_PANEL_LIMIT = 250

const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || 'cryptosupport74@gmail.com'

const normalizeIds = (ids = []) => {
  const normalized = ids
    .map((value) => String(value || '').trim().toLowerCase())
    .filter(Boolean)

  return [...new Set(normalized)]
}

function Dashboard() {
  const { user, logout } = useAuth()
  const { t } = useLanguage()
  const location = useLocation()
  const navigate = useNavigate()
  const [cryptoIds, setCryptoIds] = useState(DEFAULT_CRYPTO_IDS)
  const [priceSearch, setPriceSearch] = useState('')
  const [priceSearchError, setPriceSearchError] = useState('')
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [statsError, setStatsError] = useState('')
  const [upgradeBanner, setUpgradeBanner] = useState({ visible: false, tier: '' })
  const [supportModalOpen, setSupportModalOpen] = useState(false)

  useEffect(() => {
    fetchStats()
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const upgrade = params.get('upgrade')
    const tier = params.get('tier')

    if (upgrade === 'success' && tier) {
      setUpgradeBanner({ visible: true, tier })
      navigate('/dashboard', { replace: true })
    }
  }, [location.search, navigate])

  const fetchStats = async () => {
    try {
      setStatsError('')
      const response = await cryptoAPI.getStats()
      setStats(response.data)

      const assetsResponse = await cryptoAPI.getAssets(250)
      const idsFromAssets = normalizeIds((assetsResponse?.data?.assets || []).map((asset) => asset.id))

      if (idsFromAssets.length > 0) {
        setCryptoIds(idsFromAssets)
      } else {
        // Assets endpoint returned empty; use DEFAULT_CRYPTO_IDS as reliable baseline.
        setCryptoIds(DEFAULT_CRYPTO_IDS)
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err)
      setStatsError(t('stats_load_failed', 'Live market stats are temporarily unavailable.'))
      setStats(null)
      setCryptoIds(DEFAULT_CRYPTO_IDS)
    } finally {
      setLoading(false)
    }
  }

  const priceSearchTerm = priceSearch.trim().toLowerCase()
  const visibleCryptoIds = cryptoIds.filter((id) => {
    if (!priceSearchTerm) {
      return true
    }

    const normalized = id.toLowerCase()
    const readable = normalized.replace(/-/g, ' ')
    return normalized.includes(priceSearchTerm) || readable.includes(priceSearchTerm)
  })

  const displayedCryptoIds = visibleCryptoIds.slice(0, PRICE_PANEL_LIMIT)

  const openPriceDetails = (cryptoId) => {
    if (!cryptoId) {
      return
    }
    navigate(`/invest/${cryptoId}`)
  }

  const resolveSearchCandidate = (rawTerm) => {
    const sanitized = String(rawTerm || '').trim().toLowerCase()
    if (!sanitized) {
      return ''
    }

    const normalizedCandidate = sanitized
      .replace(/[_\s]+/g, '-')
      .replace(/[^a-z0-9-]/g, '')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')

    if (!normalizedCandidate) {
      return ''
    }

    const exactId = cryptoIds.find((id) => id === normalizedCandidate)
    if (exactId) {
      return exactId
    }

    const friendlyMatch = cryptoIds.find((id) => id.replace(/-/g, ' ') === sanitized)
    if (friendlyMatch) {
      return friendlyMatch
    }

    return normalizedCandidate
  }

  const handlePriceSearchSubmit = async () => {
    const candidateId = resolveSearchCandidate(priceSearch)
    if (!candidateId) {
      setPriceSearchError(t('prices_search_enter_term', 'Enter a crypto name or ID to search.'))
      return
    }

    setPriceSearchError('')

    try {
      const response = await cryptoAPI.getPrice(candidateId)
      if (response?.data) {
        openPriceDetails(candidateId)
        return
      }
      throw new Error('No price data returned')
    } catch (searchErr) {
      console.warn('Price search failed:', searchErr)
      setPriceSearchError(t('prices_search_not_found', 'Crypto not found in API. Try a different name or ID.'))
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <div className="brand-title-row">
            <BrandMark className="brand-mark header-brand-mark" />
            <h1>DaCryptoBeast</h1>
          </div>
          <p>{t('app_dashboard_subtitle', 'Real-time Cryptocurrency Tracking & Analysis')}</p>
        </div>
        <div className="header-user">
          <a href="/pricing" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#fff', fontWeight: '500' }}>
            💳 {t('nav_pricing', 'Pricing')}
          </a>
          <a href="/tools" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#ffe08a', fontWeight: '500' }}>
            🛍 {t('nav_tools', 'Tools')}
          </a>
          <a href="/all-cryptos" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#9be9ff', fontWeight: '500' }}>
            🌐 {t('nav_all_cryptos', 'All 250')}
          </a>
          <button className="support-btn" onClick={() => setSupportModalOpen(true)}>
            🛟 {t('nav_support', 'Support')}
          </button>
          <a href="/auto-trading" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#ff6600', fontWeight: '500' }}>
            🤖 {t('nav_auto_trading', 'Auto Trading')}
          </a>
          {user?.is_admin && (
            <a href="/admin" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#fff', fontWeight: '500' }}>
              🛡 {t('nav_admin', 'Admin')}
            </a>
          )}
          <a href="/settings" className="pricing-link" style={{ marginRight: '15px', textDecoration: 'none', color: '#00d4ff', fontWeight: '500' }}>
            ⚙️ {t('nav_settings', 'Settings')}
          </a>
          <span className="username">👤 {user?.username}</span>
          <button className="logout-btn" onClick={logout}>{t('auth_logout', 'Logout')}</button>
        </div>
      </header>

      <div className="dashboard-layout-outer">
      <div className="dashboard-layout">
        <aside className="dashboard-sidebar-left">
          <DashboardDirectory />
        </aside>

      <main className="main-content dashboard-main-col">
        {upgradeBanner.visible && (
          <section className="upgrade-success-banner">
            <div>
              <strong>{t('upgrade_success_title', 'Payment successful.')}</strong> {t('upgrade_success_body', 'Your')} {upgradeBanner.tier.toUpperCase()} {t('upgrade_success_body_suffix', 'plan is now active.')}
            </div>
            <button
              className="upgrade-banner-close"
              onClick={() => setUpgradeBanner({ visible: false, tier: '' })}
            >
              {t('common_dismiss', 'Dismiss')}
            </button>
          </section>
        )}

        {/* Subscription Status */}
        <section id="section-subscription" className="subscription-section">
          <SubscriptionStatus />
        </section>

        {/* Stats Section */}
        <section id="section-stats" className="stats-section">
          <div className="stat-card">
            <span className="stat-label">{t('stats_total_records', 'Total Records')}</span>
            <span className="stat-value">{stats?.total_records || 0}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">{t('stats_cryptocurrencies', 'Cryptocurrencies')}</span>
            <span className="stat-value">{stats?.unique_cryptos || 0}</span>
          </div>
          <div className="stat-card">
            <span className="stat-label">{t('stats_last_update', 'Last Update')}</span>
            <span className="stat-value">
              {stats?.last_update ? new Date(stats.last_update).toLocaleTimeString() : t('common_na', 'N/A')}
            </span>
          </div>
        </section>
        {statsError && (
          <section className="stats-section" style={{ marginTop: '10px' }}>
            <div className="stat-card" style={{ gridColumn: '1 / -1', color: '#fca5a5' }}>
              {statsError}
            </div>
          </section>
        )}

        {/* AI Recommendations Section */}
        <section id="section-recommendations" className="recommendations-section">
          <RecommendationsPanel />
        </section>

        {/* Auto Trading Section */}
        <section id="section-auto-trading" className="auto-trading-section">
          <AutoTradingPanel />
        </section>

        {/* Portfolio Section */}
        <section id="section-portfolio" className="portfolio-section">
          <PortfolioPanel />
        </section>

        {/* User Investments Section */}
        <section id="section-investments" className="user-investments-section">
          <UserInvestmentsPanel />
        </section>

        {/* Price Cards Section */}
        <section id="section-prices" className="prices-section">
          <div className="prices-header">
            <h2>{t('prices_heading', 'Current Prices')}</h2>
            <div className="prices-search-wrap">
              <div className="prices-search-controls">
                <input
                  type="text"
                  className="prices-search"
                  placeholder={t('prices_search_placeholder', 'Search asset (e.g. dogecoin, bitcoin)')}
                  value={priceSearch}
                  onChange={(event) => {
                    setPriceSearch(event.target.value)
                    if (priceSearchError) {
                      setPriceSearchError('')
                    }
                  }}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') {
                      event.preventDefault()
                      handlePriceSearchSubmit()
                    }
                  }}
                />
                <button
                  type="button"
                  className="prices-search-btn"
                  onClick={handlePriceSearchSubmit}
                >
                  {t('common_search', 'Search')}
                </button>
              </div>
              {priceSearchError && <small className="prices-search-error">{priceSearchError}</small>}
              <small className="prices-count">{t('prices_showing', 'Showing')} {Math.min(PRICE_PANEL_LIMIT, visibleCryptoIds.length)} {t('prices_of', 'of')} {visibleCryptoIds.length} {t('prices_matches', 'matches')} ({cryptoIds.length} {t('prices_total_assets', 'total assets')})</small>
            </div>
          </div>
          <div className="price-cards-container">
            {displayedCryptoIds.map((id) => (
              <div
                key={id}
                className="card-wrapper"
                role="button"
                tabIndex={0}
                aria-label={`Open ${id} details`}
                onClick={() => openPriceDetails(id)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' || event.key === ' ') {
                    event.preventDefault()
                    openPriceDetails(id)
                  }
                }}
              >
                <PriceCard cryptoId={id} />
              </div>
            ))}
            {visibleCryptoIds.length === 0 && (
              <div className="prices-empty">{t('prices_no_matches', 'No assets match your search.')}</div>
            )}
          </div>
        </section>

        {/* Alerts Section */}
        <section id="section-alerts" className="alerts-section">
          <AlertPanel />
        </section>
      </main>

        <aside className="dashboard-sidebar-right">
          <AdPanel />
        </aside>
      </div>
      </div>

      <footer className="footer">
        <p>{t('footer_tagline', 'CryptoAI © 2026 | Real-time cryptocurrency analytics powered by CoinGecko API')}</p>
        <p>
          {t('footer_support_text', 'Need help with billing or account issues? Contact support at')}{' '}
          <a href={`mailto:${SUPPORT_EMAIL}?subject=CryptoAI%20Support%20Request`}>
            {SUPPORT_EMAIL}
          </a>
          {' '}or{' '}
          <button className="support-footer-btn" onClick={() => setSupportModalOpen(true)}>
            {t('footer_support_form', 'open support form')}
          </button>
        </p>
        <p className="build-stamp">Build: {BUILD_STAMP}</p>
      </footer>

      <SupportModal
        visible={supportModalOpen}
        onClose={() => setSupportModalOpen(false)}
        user={user}
        supportEmail={SUPPORT_EMAIL}
      />

      {/* AI Chat Side Panel - Only on Dashboard */}
      <AIChatSidePanel />
    </div>
  )
}

// Protected Route Component
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  const { t } = useLanguage()

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>{t('common_loading', 'Loading...')}</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return children
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth()
  const { t } = useLanguage()

  if (loading) {
    return <div style={{ padding: '40px', textAlign: 'center' }}>{t('common_loading', 'Loading...')}</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  if (!user.is_admin) {
    return <Navigate to="/dashboard" replace />
  }

  return children
}

export default function App() {
  const { loading } = useAuth()
  const { t } = useLanguage()
  const [backendStatus, setBackendStatus] = useState('checking')
  const [backendFailureCount, setBackendFailureCount] = useState(0)

  useEffect(() => {
    let active = true

    const checkBackendHealth = async () => {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 2500)

      try {
        const response = await fetch(BACKEND_HEALTH_URL, {
          method: 'GET',
          cache: 'no-store',
          signal: controller.signal
        })

        if (!active) {
          return
        }

        if (response.ok) {
          setBackendStatus('online')
          setBackendFailureCount(0)
          return
        }

        setBackendStatus('offline')
        setBackendFailureCount((count) => count + 1)
      } catch (err) {
        if (!active) {
          return
        }
        setBackendStatus('offline')
        setBackendFailureCount((count) => count + 1)
      } finally {
        clearTimeout(timeoutId)
      }
    }

    checkBackendHealth()
    const intervalId = setInterval(checkBackendHealth, 8000)

    return () => {
      active = false
      clearInterval(intervalId)
    }
  }, [])

  const showBackendBanner = backendStatus !== 'online'
  const backendBannerText = backendStatus === 'checking'
    ? t('backend_status_checking', 'Checking backend status...')
    : backendFailureCount >= 2
      ? t('backend_status_waking', 'Server waking up. Some modules may load slowly until backend is ready.')
      : t('backend_status_reconnecting', 'Trying to reconnect to backend...')

  if (loading) {
    return (
      <>
        {showBackendBanner && (
          <div className="backend-status-banner warning" role="status" aria-live="polite">
            {backendBannerText}
          </div>
        )}
        <div style={{ padding: '40px', textAlign: 'center' }}>{t('common_loading', 'Loading...')}</div>
      </>
    )
  }

  return (
    <>
      {showBackendBanner && (
        <div className="backend-status-banner warning" role="status" aria-live="polite">
          {backendBannerText}
        </div>
      )}
      <div className="global-language-switcher">
        <LanguageSelector />
      </div>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/pricing" element={<PricingPage />} />
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/" element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        } />
        <Route path="/invest/:cryptoId" element={
          <ProtectedRoute>
            <InvestmentDetailPage />
          </ProtectedRoute>
        } />
        <Route path="/auto-trading" element={
          <ProtectedRoute>
            <AutoTradingPage />
          </ProtectedRoute>
        } />
        <Route path="/admin" element={
          <AdminRoute>
            <AdminDashboardPage />
          </AdminRoute>
        } />
        <Route path="/settings" element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        } />
        <Route path="/tools" element={<AffiliateToolsPage />} />
        <Route path="/all-cryptos" element={
          <ProtectedRoute>
            <AllCryptosPage />
          </ProtectedRoute>
        } />
      </Routes>
    </>
  )
}

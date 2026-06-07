import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { cryptoAPI } from '../utils/api'
import { encryptAESGCM } from '../utils/encryption'
import './SettingsPage.css'

const formatDate = (dateString) => {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatCurrency = (value) => {
  if (!value) return '$0.00'
  return `$${Number(value).toFixed(2)}`
}

export default function SettingsPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [profile, setProfile] = useState(null)
  const [portfolio, setPortfolio] = useState(null)
  const [buyHistory, setBuyHistory] = useState([])
  const [sellHistory, setSellHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('profile')
  const [settingsForm, setSettingsForm] = useState({
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [settingsMessage, setSettingsMessage] = useState({ type: '', text: '' })

  useEffect(() => {
    fetchAllData()
  }, [])

  const fetchAllData = async () => {
    try {
      setLoading(true)
      setError(null)

      // Fetch user profile
      const profileRes = await cryptoAPI.getProfile()
      setProfile(profileRes.data)

      // Fetch portfolio data
      const portfolioRes = await cryptoAPI.getUserPortfolio()
      setPortfolio(portfolioRes.data)

      // Extract trading history from portfolio
      if (portfolioRes.data?.holdings) {
        const buys = []
        const sells = []

        portfolioRes.data.holdings.forEach(holding => {
          const investmentType = holding.investment_type || 'real_money'
          if (holding.transactions) {
            holding.transactions.forEach(tx => {
              if (tx.type === 'BUY') {
                buys.push({
                  ...tx,
                  symbol: holding.symbol,
                  cryptoName: holding.name,
                  investment_type: investmentType
                })
              } else if (tx.type === 'SELL') {
                sells.push({
                  ...tx,
                  symbol: holding.symbol,
                  cryptoName: holding.name,
                  investment_type: investmentType
                })
              }
            })
          }
        })

        // Sort by date descending
        setBuyHistory(buys.sort((a, b) => new Date(b.date) - new Date(a.date)))
        setSellHistory(sells.sort((a, b) => new Date(b.date) - new Date(a.date)))
      }
    } catch (err) {
      console.error('Error fetching data:', err)
      setError('Failed to load settings data. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSettingsChange = (e) => {
    const { name, value } = e.target
    setSettingsForm(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSaveSettings = async () => {
    try {
      // Validate inputs
      if (!settingsForm.email && !settingsForm.password) {
        setSettingsMessage({ type: 'error', text: 'Please provide at least an email or password' })
        return
      }

      if (settingsForm.password && settingsForm.password !== settingsForm.confirmPassword) {
        setSettingsMessage({ type: 'error', text: 'Passwords do not match' })
        return
      }

      if (settingsForm.password && settingsForm.password.length < 6) {
        setSettingsMessage({ type: 'error', text: 'Password must be at least 6 characters' })
        return
      }

      if (settingsForm.email && (!settingsForm.email.includes('@') || !settingsForm.email.includes('.'))) {
        setSettingsMessage({ type: 'error', text: 'Please enter a valid email address' })
        return
      }

      setSettingsMessage({ type: 'info', text: 'Encrypting and saving settings...' })
      
      // Prepare data to encrypt
      const settingsData = {
        email: settingsForm.email || '',
        password: settingsForm.password || ''
      }

      // Encrypt the settings data
      const encryptedPayload = await encryptAESGCM(settingsData)

      // Send encrypted data to backend
      const response = await cryptoAPI.updateAccountSettings(encryptedPayload)

      if (response.status === 200) {
        setSettingsMessage({ type: 'success', text: 'Settings updated successfully!' })
        // Clear form
        setSettingsForm({ email: '', password: '', confirmPassword: '' })
        // Refresh profile data
        setTimeout(() => {
          fetchAllData()
        }, 1500)
      }
    } catch (err) {
      console.error('Error saving settings:', err)
      setSettingsMessage({ 
        type: 'error', 
        text: err.response?.data?.detail || 'Failed to save settings. Please try again.' 
      })
    }
  }

  if (!user) {
    navigate('/login')
    return null
  }

  if (loading) {
    return (
      <div className="settings-page">
        <div className="loading">Loading settings...</div>
      </div>
    )
  }

  return (
    <div className="settings-page">
      <div className="settings-container">
        {/* Header */}
        <div className="settings-header">
          <button className="back-btn" onClick={() => navigate('/')} title="Back to Home">
            ← Back to Home
          </button>
          <h1>⚙️ Account Settings</h1>
          <p className="subtitle">Manage your profile and view your trading history</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="alert alert-error">
            <span>⚠️ {error}</span>
            <button onClick={fetchAllData}>Retry</button>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="tabs-nav">
          <button
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            👤 Profile
          </button>
          <button
            className={`tab-btn ${activeTab === 'account' ? 'active' : ''}`}
            onClick={() => setActiveTab('account')}
          >
            🔐 Account Settings
          </button>
          <button
            className={`tab-btn ${activeTab === 'buyhistory' ? 'active' : ''}`}
            onClick={() => setActiveTab('buyhistory')}
          >
            📈 Buy History
          </button>
          <button
            className={`tab-btn ${activeTab === 'sellhistory' ? 'active' : ''}`}
            onClick={() => setActiveTab('sellhistory')}
          >
            📉 Sell History
          </button>
          <button
            className={`tab-btn ${activeTab === 'portfolio' ? 'active' : ''}`}
            onClick={() => setActiveTab('portfolio')}
          >
            💼 Portfolio
          </button>
        </div>

        {/* Profile Tab */}
        {activeTab === 'profile' && profile && (
          <div className="tab-content">
            <div className="profile-card">
              <div className="profile-header">
                <div className="avatar">
                  <span>{profile.username?.[0]?.toUpperCase() || 'U'}</span>
                </div>
                <div className="profile-info">
                  <h2>{profile.username}</h2>
                  <p className="role-badge">{profile.role?.toUpperCase() || 'USER'}</p>
                </div>
              </div>

              <div className="profile-details">
                <div className="detail-row">
                  <span className="label">Email:</span>
                  <span className="value">{profile.email || 'Not provided'}</span>
                </div>
                <div className="detail-row">
                  <span className="label">User ID:</span>
                  <span className="value code">{profile.user_id}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Account Created:</span>
                  <span className="value">{formatDate(profile.created_at)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Last Updated:</span>
                  <span className="value">{formatDate(profile.updated_at)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Account Status:</span>
                  <span className="value status-active">✅ Active</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Account Settings Tab */}
        {activeTab === 'account' && (
          <div className="tab-content">
            <div className="settings-card">
              <h3>Update Account Settings</h3>

              {settingsMessage.text && (
                <div className={`message message-${settingsMessage.type}`}>
                  {settingsMessage.type === 'success' && '✅ '}
                  {settingsMessage.type === 'error' && '❌ '}
                  {settingsMessage.type === 'info' && 'ℹ️ '}
                  {settingsMessage.text}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email">Email Address</label>
                <input
                  id="email"
                  type="email"
                  name="email"
                  placeholder="your@email.com"
                  value={settingsForm.email || profile?.email || ''}
                  onChange={handleSettingsChange}
                />
                <small>Your current email: {profile?.email || 'Not set'}</small>
              </div>

              <div className="form-group">
                <label htmlFor="password">New Password</label>
                <input
                  id="password"
                  type="password"
                  name="password"
                  placeholder="Enter new password"
                  value={settingsForm.password}
                  onChange={handleSettingsChange}
                />
                <small>Leave blank to keep current password</small>
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword">Confirm Password</label>
                <input
                  id="confirmPassword"
                  type="password"
                  name="confirmPassword"
                  placeholder="Confirm password"
                  value={settingsForm.confirmPassword}
                  onChange={handleSettingsChange}
                />
              </div>

              <div className="button-group">
                <button className="btn btn-primary" onClick={handleSaveSettings}>
                  💾 Save Changes
                </button>
                <button className="btn btn-secondary" onClick={() => setSettingsForm({ email: '', password: '', confirmPassword: '' })}>
                  🔄 Reset
                </button>
              </div>

              <div className="danger-zone">
                <h4>⚠️ Danger Zone</h4>
                <button className="btn btn-logout" onClick={logout}>
                  🚪 Logout
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Buy History Tab */}
        {activeTab === 'buyhistory' && (
          <div className="tab-content">
            <h3>📈 Buy History</h3>
            {buyHistory && buyHistory.length > 0 ? (
              <div className="history-table">
                <div className="table-header">
                  <div className="col col-crypto">Cryptocurrency</div>
                  <div className="col col-amount">Amount</div>
                  <div className="col col-price">Price per Unit</div>
                  <div className="col col-total">Total Cost</div>
                  <div className="col col-type">Type</div>
                  <div className="col col-date">Date</div>
                </div>
                {buyHistory.map((buy, index) => (
                  <div key={index} className="table-row">
                    <div className="col col-crypto">
                      <span className="crypto-badge">{buy.symbol}</span>
                      <span className="crypto-name">{buy.cryptoName}</span>
                    </div>
                    <div className="col col-amount">{Number(buy.quantity || 0).toFixed(8)} {buy.symbol}</div>
                    <div className="col col-price">{formatCurrency(buy.price)}</div>
                    <div className="col col-total">{formatCurrency((buy.quantity || 0) * (buy.price || 0))}</div>
                    <div className="col col-type">
                      <span className={`investment-type ${buy.investment_type === 'fake_money' ? 'fake' : 'real'}`}>
                        {buy.investment_type === 'fake_money' ? '📋 Fake' : '💰 Real'}
                      </span>
                    </div>
                    <div className="col col-date">{formatDate(buy.date)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>📋 No buy history yet. Start investing to see your purchases here!</p>
              </div>
            )}
          </div>
        )}

        {/* Sell History Tab */}
        {activeTab === 'sellhistory' && (
          <div className="tab-content">
            <h3>📉 Sell History</h3>
            {sellHistory && sellHistory.length > 0 ? (
              <div className="history-table">
                <div className="table-header">
                  <div className="col col-crypto">Cryptocurrency</div>
                  <div className="col col-amount">Amount</div>
                  <div className="col col-price">Price per Unit</div>
                  <div className="col col-total">Total Revenue</div>
                  <div className="col col-profit">Profit/Loss</div>
                  <div className="col col-type">Type</div>
                  <div className="col col-date">Date</div>
                </div>
                {sellHistory.map((sell, index) => (
                  <div key={index} className="table-row sell-row">
                    <div className="col col-crypto">
                      <span className="crypto-badge">{sell.symbol}</span>
                      <span className="crypto-name">{sell.cryptoName}</span>
                    </div>
                    <div className="col col-amount">{Number(sell.quantity || 0).toFixed(8)} {sell.symbol}</div>
                    <div className="col col-price">{formatCurrency(sell.price)}</div>
                    <div className="col col-total positive">{formatCurrency((sell.quantity || 0) * (sell.price || 0))}</div>
                    <div className={`col col-profit ${sell.profit >= 0 ? 'positive' : 'negative'}`}>
                      {sell.profit >= 0 ? '✅ ' : '❌ '}{formatCurrency(Math.abs(sell.profit || 0))}
                    </div>
                    <div className="col col-type">
                      <span className={`investment-type ${sell.investment_type === 'fake_money' ? 'fake' : 'real'}`}>
                        {sell.investment_type === 'fake_money' ? '📋 Fake' : '💰 Real'}
                      </span>
                    </div>
                    <div className="col col-date">{formatDate(sell.date)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>📋 No sell history yet. Start trading to see your sales here!</p>
              </div>
            )}
          </div>
        )}

        {/* Portfolio Tab */}
        {activeTab === 'portfolio' && portfolio && (
          <div className="tab-content">
            <h3>💼 Portfolio Overview</h3>
            <div className="portfolio-stats">
              <div className="stat-card">
                <span className="stat-label">Total Holdings Value</span>
                <span className="stat-value">{formatCurrency(portfolio.total_holdings_value)}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Available Cash</span>
                <span className="stat-value cash">{formatCurrency(portfolio.available_cash)}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total Portfolio</span>
                <span className="stat-value total">{formatCurrency(portfolio.total_portfolio_value)}</span>
              </div>
              <div className="stat-card">
                <span className="stat-label">Total P&L</span>
                <span className={`stat-value ${(portfolio.total_profit_loss || 0) >= 0 ? 'positive' : 'negative'}`}>
                  {formatCurrency(portfolio.total_profit_loss)}
                </span>
              </div>
            </div>

            {portfolio.holdings && portfolio.holdings.length > 0 ? (
              <div className="holdings-section">
                <h4>Current Holdings</h4>
                <div className="holdings-grid">
                  {portfolio.holdings.map((holding) => (
                    <div key={holding.symbol} className="holding-card">
                      <div className="holding-header">
                        <h5>{holding.name} ({holding.symbol})</h5>
                        <span className="qty-badge">{Number(holding.quantity).toFixed(8)}</span>
                      </div>
                      <div className="holding-details">
                        <div className="detail">
                          <span>Current Price:</span>
                          <strong>{formatCurrency(holding.current_price)}</strong>
                        </div>
                        <div className="detail">
                          <span>Total Value:</span>
                          <strong>{formatCurrency(holding.total_value)}</strong>
                        </div>
                        <div className="detail">
                          <span>Average Cost:</span>
                          <strong>{formatCurrency(holding.average_cost)}</strong>
                        </div>
                        <div className="detail">
                          <span>Profit/Loss:</span>
                          <strong className={holding.profit_loss >= 0 ? 'positive' : 'negative'}>
                            {formatCurrency(holding.profit_loss)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="empty-state">
                <p>💼 No holdings yet. Start investing to build your portfolio!</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

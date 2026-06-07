import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useLanguage } from '../context/LanguageContext'
import BrandMark from '../components/BrandMark'
import { cryptoAPI } from '../utils/api'
import './LoginPage.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const { t } = useLanguage()
  const [formData, setFormData] = useState({
    username: '',
    password: ''
  })
  const [loading, setLoading] = useState(false)
  const [forgotLoading, setForgotLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [forgotIdentifier, setForgotIdentifier] = useState('')
  const [forgotNotice, setForgotNotice] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setError('')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      await login(formData.username, formData.password)

      setSuccess('✅ Login successful! Redirecting...')
      setTimeout(() => {
        navigate('/dashboard')
      }, 1500)
    } catch (err) {
      setError(err.message || 'Login failed')
      setLoading(false)
    }
  }

  const handleForgotPassword = async () => {
    const identifier = forgotIdentifier.trim()
    if (!identifier) {
      setError('Enter your username or email to request a reset link.')
      return
    }

    setForgotLoading(true)
    setError('')
    setForgotNotice('')

    const isEmail = identifier.includes('@')
    const payload = isEmail
      ? { email: identifier }
      : { username: identifier }

    try {
      await cryptoAPI.forgotPassword(payload)
      setForgotNotice('If the account exists, we emailed a secure reset link.')
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to submit forgot password request')
    } finally {
      setForgotLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-brand-row">
            <BrandMark className="brand-mark auth-brand-mark" />
            <h1>DaCryptoBeast</h1>
          </div>
          <p>{t('app_dashboard_subtitle', 'Real-time Cryptocurrency Tracking and Analysis')}</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2>{t('login_heading', 'Login to Your Account')}</h2>

          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}

          {success && (
            <div className="success-message">
              {success}
            </div>
          )}

          <div className="form-group">
            <label htmlFor="username">{t('auth_username', 'Username')}</label>
            <input
              id="username"
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder={t('auth_username', 'Username')}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('auth_password', 'Password')}</label>
            <input
              id="password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder={t('auth_password', 'Password')}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? t('login_loading', 'Logging in...') : t('login_button', 'Login')}
          </button>

          <div className="forgot-password-row">
            <label htmlFor="forgotIdentifier">Forgot Password?</label>
            <input
              id="forgotIdentifier"
              type="text"
              value={forgotIdentifier}
              onChange={(event) => setForgotIdentifier(event.target.value)}
              placeholder="Username or email"
              disabled={forgotLoading}
            />
          </div>

          <button
            type="button"
            className="forgot-password-btn"
            onClick={handleForgotPassword}
            disabled={forgotLoading}
          >
            {forgotLoading ? 'Sending reset link...' : 'Send Reset Link'}
          </button>

          {forgotNotice && (
            <p className="forgot-password-note">{forgotNotice}</p>
          )}
        </form>

        <div className="auth-footer">
          <p>
            {t('login_no_account', "Don't have an account?")}{' '}
            <Link to="/register" className="auth-link">
              {t('login_register_here', 'Register here')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

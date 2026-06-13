import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useLanguage } from '../context/LanguageContext'
import BrandMark from '../components/BrandMark'
import './LoginPage.css'
import axios from 'axios'
import { API_BASE } from '../utils/backendConfig'

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const { t } = useLanguage()
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [showVerifyNudge, setShowVerifyNudge] = useState(false)
  const [sendingVerify, setSendingVerify] = useState(false)
  const [verifyMessage, setVerifyMessage] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    setError('')
  }

  const validateForm = () => {
    if (!formData.username || !formData.password) {
      setError('Username and password are required')
      return false
    }

    if (formData.username.length < 3) {
      setError('Username must be at least 3 characters')
      return false
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters')
      return false
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return false
    }

    return true
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (!validateForm()) {
      setLoading(false)
      return
    }

    try {
      await register(formData.username, formData.password, formData.email)

      setSuccess('✅ Registration successful! Redirecting...')
      if (formData.email) {
        setShowVerifyNudge(true)
      } else {
        setTimeout(() => navigate('/dashboard'), 1500)
      }
    } catch (err) {
      setError(err.message || 'Registration failed')
      setLoading(false)
    }
  }

  const handleSendVerify = async () => {
    setSendingVerify(true)
    try {
      const token = localStorage.getItem('token')
      const r = await axios.post(`${API_BASE}/api/auth/send-verification-email`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      })
      setVerifyMessage(r.data?.message || 'Verification email sent. Check your inbox.')
    } catch (err) {
      setVerifyMessage(err.response?.data?.detail || 'Failed to send verification email.')
    } finally {
      setSendingVerify(false)
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
          <h2>{t('register_heading', 'Create Your Account')}</h2>

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

          {showVerifyNudge && (
            <div className="success-message" style={{ background: '#1d4ed8', padding: '16px', borderRadius: '8px', marginTop: '8px' }}>
              <p style={{ margin: '0 0 8px', fontWeight: 600 }}>🎉 Welcome! Would you like to verify your email now?</p>
              <p style={{ margin: '0 0 10px', fontSize: '0.9em', opacity: 0.9 }}>Verification is required for the launch promo and helps protect your account.</p>
              {verifyMessage && <p style={{ margin: '0 0 8px', fontSize: '0.85em' }}>{verifyMessage}</p>}
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <button type="button" onClick={handleSendVerify} disabled={sendingVerify}
                  style={{ background: 'white', color: '#1d4ed8', border: 'none', borderRadius: '6px', padding: '8px 16px', fontWeight: 600, cursor: 'pointer' }}>
                  {sendingVerify ? 'Sending...' : 'Send Verification Email'}
                </button>
                <button type="button" onClick={() => navigate('/dashboard')}
                  style={{ background: 'rgba(255,255,255,0.2)', color: 'white', border: '1px solid rgba(255,255,255,0.4)', borderRadius: '6px', padding: '8px 16px', cursor: 'pointer' }}>
                  Skip for now
                </button>
              </div>
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
            <label htmlFor="email">{t('auth_email_optional', 'Email (Optional)')}</label>
            <input
              id="email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="Enter your email"
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

          <div className="form-group">
            <label htmlFor="confirmPassword">{t('auth_confirm_password', 'Confirm Password')}</label>
            <input
              id="confirmPassword"
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              placeholder={t('auth_confirm_password', 'Confirm Password')}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="auth-button"
            disabled={loading}
          >
            {loading ? t('register_loading', 'Creating Account...') : t('register_button', 'Register')}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            {t('register_have_account', 'Already have an account?')}{' '}
            <Link to="/login" className="auth-link">
              {t('register_login_here', 'Login here')}
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

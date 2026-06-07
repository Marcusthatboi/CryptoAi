import React, { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import BrandMark from '../components/BrandMark'
import './LoginPage.css'

export default function ResetPasswordPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const token = useMemo(() => new URLSearchParams(location.search).get('token') || '', [location.search])

  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!token) {
      setError('Missing reset token. Open the reset link from your email again.')
      return
    }

    if (newPassword.length < 10) {
      setError('New password must be at least 10 characters.')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    setLoading(true)

    try {
      await cryptoAPI.resetPassword({ token, new_password: newPassword })
      setSuccess('Password reset successful. Redirecting to login...')
      setTimeout(() => navigate('/login'), 1500)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to reset password')
    } finally {
      setLoading(false)
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
          <p>Set your new account password</p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <h2>Reset Password</h2>

          {error && <div className="error-message">⚠️ {error}</div>}
          {success && <div className="success-message">{success}</div>}

          <div className="form-group">
            <label htmlFor="newPassword">New Password</label>
            <input
              id="newPassword"
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="Enter new password"
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm New Password</label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="Confirm new password"
              required
              disabled={loading}
            />
          </div>

          <button type="submit" className="auth-button" disabled={loading}>
            {loading ? 'Resetting password...' : 'Reset Password'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            Back to{' '}
            <Link to="/login" className="auth-link">Login</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

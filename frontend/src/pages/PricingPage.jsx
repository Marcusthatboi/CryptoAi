import React, { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'
import { QRCodeSVG } from 'qrcode.react'
import { API_BASE } from '../utils/backendConfig'
import './PricingPage.css'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '')
const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || 'cryptosupport74@gmail.com'

const SUBSCRIPTION_PRICES = { pro: 999, premium: 2999 }

function CheckoutModal({
  visible,
  clientSecret,
  selectedPlan,
  checkoutAmount,
  applePayCheckoutUrl,
  user,
  onClose,
  onConfirm,
  onError
}) {
  const stripe = useStripe()
  const elements = useElements()
  const [submitting, setSubmitting] = useState(false)

  if (!visible) return null

  const submitPayment = async (e) => {
    e.preventDefault()

    if (!stripe || !elements || !clientSecret) {
      onError('Stripe is not ready yet. Please try again.')
      return
    }

    const card = elements.getElement(CardElement)
    if (!card) {
      onError('Card input is not available.')
      return
    }

    try {
      setSubmitting(true)
      const result = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card,
          billing_details: {
            name: user?.username || 'CryptoAI User',
            email: user?.email || undefined
          }
        }
      })

      if (result.error) {
        onError(result.error.message || 'Payment failed. Please try again.')
        return
      }

      if (result.paymentIntent?.status === 'succeeded') {
        onConfirm(result.paymentIntent)
      } else {
        onError('Payment was not completed. Please try again.')
      }
    } catch (err) {
      onError(err?.message || 'Unexpected payment error occurred.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="checkout-modal-overlay">
      <div className="checkout-modal">
        <h3>Complete Your {selectedPlan?.toUpperCase()} Upgrade</h3>
        <p className="checkout-amount">Amount: ${checkoutAmount}</p>
        {applePayCheckoutUrl && (
          <div className="wallet-checkout-card">
            <div>
              <h4>Apple Pay QR</h4>
              <p>Scan with your iPhone camera to open a Stripe-hosted checkout page that can present Apple Pay on supported devices.</p>
              <a
                className="wallet-link"
                href={applePayCheckoutUrl}
                target="_blank"
                rel="noreferrer"
              >
                Open mobile checkout
              </a>
            </div>
            <div className="wallet-qr-code" aria-label="Apple Pay checkout QR code">
              <QRCodeSVG value={applePayCheckoutUrl} size={152} includeMargin />
            </div>
          </div>
        )}
        <div className="checkout-divider">
          <span>Or pay with card</span>
        </div>
        <form onSubmit={submitPayment}>
          <div className="card-element-wrapper">
            <CardElement
              options={{
                hidePostalCode: true,
                style: {
                  base: {
                    fontSize: '16px',
                    color: '#1f2937',
                    fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
                    '::placeholder': { color: '#9ca3af' }
                  },
                  invalid: { color: '#dc2626' }
                }
              }}
            />
          </div>
          <div className="checkout-modal-actions">
            <button type="button" className="action-btn" onClick={onClose} disabled={submitting}>
              Cancel
            </button>
            <button type="submit" className="action-btn upgrade-btn" disabled={submitting || !stripe}>
              {submitting ? 'Processing...' : `Pay $${checkoutAmount}`}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function PricingPage() {
  const { token, user } = useAuth()
  const navigate = useNavigate()
  const [plans, setPlans] = useState([])
  const [currentTier, setCurrentTier] = useState('free')
  const [loading, setLoading] = useState(true)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [processingTier, setProcessingTier] = useState(null)
  const [checkoutMessage, setCheckoutMessage] = useState(null)
  const [clientSecret, setClientSecret] = useState('')
  const [checkoutAmount, setCheckoutAmount] = useState('0.00')
  const [stripeCustomerId, setStripeCustomerId] = useState('')
  const [showCheckoutModal, setShowCheckoutModal] = useState(false)
  const [applePayCheckoutUrl, setApplePayCheckoutUrl] = useState('')
  const [redirectingTier, setRedirectingTier] = useState(null)
  const [manualCheckoutUrl, setManualCheckoutUrl] = useState('')
  const [liveReadiness, setLiveReadiness] = useState({
    stripe: { ready: null, live_mode: false, message: 'Checking checkout readiness...' }
  })
  const [promoStatus, setPromoStatus] = useState(null)
  const [applyPromo, setApplyPromo] = useState(false)
  const [emailVerified, setEmailVerified] = useState(null)
  const [sendingVerification, setSendingVerification] = useState(false)
  const normalizedCurrentTier = String(currentTier || 'free').toLowerCase()
  const isProcessingCheckout = processingTier !== null

  const getPlanByTier = (tier, fallback) => {
    const matched = plans.find((plan) => String(plan?.tier || '').toLowerCase() === tier)
    if (!matched) {
      return fallback
    }

    return {
      ...fallback,
      ...matched,
      priceDisplay: matched.price_display || fallback.priceDisplay,
      features: Array.isArray(matched.features) && matched.features.length ? matched.features : fallback.features
    }
  }

  const proPlan = getPlanByTier('pro', {
    name: 'Pro',
    priceDisplay: '$9.99/mo',
    features: [
      'Everything in Free +',
      'Advanced AI signals',
      'Real-time price alerts',
      'Signal confidence scoring',
      'Signal history (30 days)',
      'Portfolio optimization tips'
    ]
  })

  const premiumPlan = getPlanByTier('premium', {
    name: 'Premium',
    priceDisplay: '$29.99/mo',
    features: [
      'Everything in Pro +',
      'Exclusive high-accuracy signals',
      'Unlimited alerts',
      'Signal history (1 year)',
      'Advanced portfolio analytics',
      'Early access to new features',
      'Priority support',
      'Performance tracking'
    ]
  })

  const shouldUseMobileHostedCheckout = () => {
    if (typeof window === 'undefined') return false
    const compactViewport = window.matchMedia && window.matchMedia('(max-width: 768px)').matches
    const touchDevice = typeof navigator !== 'undefined' && (
      /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent || '') ||
      (navigator.maxTouchPoints || 0) > 1
    )
    return compactViewport || touchDevice
  }

  useEffect(() => {
    fetchPlans()
    fetchLiveReadiness()
    if (user?.user_id) {
      fetchUserSubscription()
    }
  }, [user])

  useEffect(() => {
    fetchPromoStatus()
  }, [])

  useEffect(() => {
    if (token) fetchVerificationStatus()
  }, [token])

  const fetchLiveReadiness = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/system/live-readiness`)
      const stripe = response?.data?.stripe || {}
      setLiveReadiness({
        stripe: {
          ready: Boolean(stripe.ready),
          live_mode: Boolean(stripe.live_mode),
          message: String(stripe.message || 'Stripe readiness unavailable')
        }
      })
    } catch (err) {
      setLiveReadiness({
        stripe: {
          ready: false,
          live_mode: false,
          message: 'Unable to verify checkout readiness. Backend may be unavailable.'
        }
      })
      console.error('Failed to fetch live readiness:', err)
    }
  }

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/subscription/pricing/plans`)
      setPlans(response.data.plans || [])
      setLoading(false)
    } catch (err) {
      console.error('Failed to fetch pricing plans:', err)
      setLoading(false)
    }
  }

  const fetchUserSubscription = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/api/subscription/status`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setCurrentTier(response.data.tier)
    } catch (err) {
      console.error('Failed to fetch subscription:', err)
    }
  }

  const fetchPromoStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/promo/status`)
      setPromoStatus(response.data)
    } catch (err) {
      setPromoStatus(null)
    }
  }

  const fetchVerificationStatus = async () => {
    try {
      const r = await axios.get(`${API_BASE}/api/auth/verification-status`, { headers: { Authorization: `Bearer ${token}` } })
      setEmailVerified(r.data.email_verified)
    } catch { setEmailVerified(null) }
  }

  const handleSendVerificationEmail = async () => {
    setSendingVerification(true)
    try {
      const r = await axios.post(`${API_BASE}/api/auth/send-verification-email`, {}, { headers: { Authorization: `Bearer ${token}` } })
      setCheckoutMessage({ type: 'success', text: r.data?.message || 'Verification email sent. Check your inbox.' })
    } catch (err) {
      setCheckoutMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to send verification email.' })
    } finally {
      setSendingVerification(false)
    }
  }

  const handleUpgrade = async (tier) => {
    if (!token) {
      navigate('/login')
      return
    }

    if (!liveReadiness?.stripe?.ready) {
      setCheckoutMessage({
        type: 'error',
        text: `${liveReadiness?.stripe?.message || 'Stripe checkout is unavailable.'} Please configure Stripe keys and try again.`
      })
      return
    }

    try {
      setProcessingTier(tier)
      setCheckoutMessage(null)

      const response = await axios.post(
        `${API_BASE}/api/subscription/create-payment-intent`,
        null,
        {
          params: { tier, apply_promo: applyPromo },
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setSelectedPlan(tier)
      setClientSecret(response.data?.client_secret || '')
      setStripeCustomerId(response.data?.stripe_customer_id || '')
      const amountUsd = ((response.data?.promo_applied ? response.data.promo_discounted_cents : response.data?.amount || 0) / 100).toFixed(2)
      setCheckoutAmount(amountUsd)
      if (response.data?.promo_applied) {
        setCheckoutMessage({ type: 'success', text: `🎉 Launch deal applied! ${response.data.promo_discount_pct}% off — you pay $${amountUsd} today.` })
        fetchPromoStatus()
      }

      try {
        const checkoutSessionResponse = await axios.post(
          `${API_BASE}/api/subscription/create-checkout-session`,
          null,
          {
            params: { tier, origin: window.location.origin },
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        const hostedCheckoutUrl = checkoutSessionResponse.data?.url || ''
        setApplePayCheckoutUrl(hostedCheckoutUrl)

        if (hostedCheckoutUrl && shouldUseMobileHostedCheckout()) {
          setRedirectingTier(tier)
          setManualCheckoutUrl('')
          window.location.assign(hostedCheckoutUrl)
          window.setTimeout(() => {
            setRedirectingTier(null)
            setManualCheckoutUrl(hostedCheckoutUrl)
            setCheckoutMessage({
              type: 'error',
              text: 'Checkout did not open automatically. Use the manual checkout button below.'
            })
          }, 1500)
          return
        }
      } catch (checkoutSessionError) {
        console.error('Failed to create Apple Pay checkout session:', checkoutSessionError)
        setApplePayCheckoutUrl('')
      }

      setShowCheckoutModal(true)
      setCheckoutMessage({
        type: 'success',
        text: `Checkout initialized for ${tier.toUpperCase()} ($${amountUsd}). Use the Apple Pay QR or enter card details to complete upgrade.`
      })
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Failed to initialize checkout. Please try again.'
      setCheckoutMessage({ type: 'error', text: detail })
      console.error('Failed to initialize checkout:', err)
    } finally {
      setRedirectingTier(null)
      setProcessingTier(null)
    }
  }

  const closeCheckoutModal = () => {
    setShowCheckoutModal(false)
    setApplePayCheckoutUrl('')
  }

  const clearManualCheckoutPrompt = () => {
    setManualCheckoutUrl('')
  }

  const onPaymentError = (message) => {
    setCheckoutMessage({ type: 'error', text: message })
  }

  const onPaymentConfirmed = async (paymentIntent) => {
    if (!selectedPlan) {
      setCheckoutMessage({ type: 'error', text: 'No plan selected for upgrade.' })
      return
    }

    try {
      setProcessingTier(selectedPlan)
      await axios.post(
        `${API_BASE}/api/subscription/upgrade`,
        null,
        {
          params: {
            tier: selectedPlan,
            stripe_customer_id: stripeCustomerId,
            stripe_subscription_id: paymentIntent.id,
            payment_method_id: paymentIntent.payment_method || ''
          },
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setCheckoutMessage({
        type: 'success',
        text: `Payment confirmed. You are now on the ${selectedPlan.toUpperCase()} plan.`
      })
      setShowCheckoutModal(false)
      await fetchUserSubscription()
      navigate(`/dashboard?upgrade=success&tier=${selectedPlan}`)
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Payment succeeded but subscription update failed.'
      setCheckoutMessage({ type: 'error', text: detail })
    } finally {
      setProcessingTier(null)
    }
  }

  const handleDowngradeToPro = async () => {
    if (!token || normalizedCurrentTier !== 'premium') {
      return
    }

    try {
      setProcessingTier('pro')
      const response = await axios.post(
        `${API_BASE}/api/subscription/downgrade`,
        null,
        {
          params: { tier: 'pro' },
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setCheckoutMessage({
        type: 'success',
        text: response?.data?.message || 'Downgrade to Pro scheduled for your next billing cycle.'
      })
      await fetchUserSubscription()
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Failed to schedule downgrade.'
      setCheckoutMessage({ type: 'error', text: detail })
    } finally {
      setProcessingTier(null)
    }
  }

  const handleCancelToFree = async () => {
    if (!token || normalizedCurrentTier === 'free') {
      return
    }

    try {
      setProcessingTier('free')
      const response = await axios.post(
        `${API_BASE}/api/subscription/cancel`,
        null,
        { headers: { Authorization: `Bearer ${token}` } }
      )

      setCheckoutMessage({
        type: 'success',
        text: response?.data?.message || 'Subscription cancelled successfully.'
      })
      await fetchUserSubscription()
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Failed to cancel subscription.'
      setCheckoutMessage({ type: 'error', text: detail })
    } finally {
      setProcessingTier(null)
    }
  }

  if (loading) {
    return (
      <div className="pricing-page">
        <div className="loading-spinner">Loading pricing...</div>
      </div>
    )
  }

  return (
    <div className="pricing-page">
      <div className="pricing-header">
        <h1>🚀 Choose Your Plan</h1>
        <p>Unlock advanced AI signals and profit-tracking features</p>
      </div>

      {/* Launch sale banner */}
      {promoStatus?.active && (
        <div className="launch-promo-banner" role="alert">
          <div className="promo-banner-content">
            <span className="promo-fire">🔥</span>
            <div className="promo-text">
              <strong>LAUNCH DEAL — {promoStatus.discount_pct}% OFF</strong>
              <span> · First-100 users only · {promoStatus.claims_remaining} spot{promoStatus.claims_remaining !== 1 ? 's' : ''} left out of {promoStatus.total_slots}</span>
            </div>
          </div>
          <label className="promo-toggle-label">
            <input
              type="checkbox"
              checked={applyPromo}
              onChange={e => setApplyPromo(e.target.checked)}
              className="promo-toggle-input"
            />
            <span className="promo-toggle-text">Apply {promoStatus.discount_pct}% discount to my upgrade</span>
          </label>
        </div>
      )}
      {promoStatus && !promoStatus.active && (
        <div className="launch-promo-banner promo-ended" role="status">
          🏁 Launch deal ended — all 100 discounted spots claimed. Regular pricing applies.
        </div>
      )}

      <div className={`checkout-readiness-banner ${liveReadiness?.stripe?.ready ? 'ready' : 'blocked'}`}>
        <strong>Checkout status:</strong> {liveReadiness?.stripe?.message}
        {liveReadiness?.stripe?.ready && !liveReadiness?.stripe?.live_mode && (
          <span className="checkout-readiness-note"> • Test mode</span>
        )}
      </div>

      {!import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY && (
        <div className="checkout-message error">
          Stripe publishable key is missing. Set VITE_STRIPE_PUBLISHABLE_KEY in frontend/.env.local.
        </div>
      )}

      {/* Current Plan Badge */}
      {currentTier !== 'free' && (
        <div className="current-plan-banner">
          <span>✅ Currently on <strong>{currentTier.toUpperCase()}</strong> Plan</span>
        </div>
      )}

      {/* Email verification nudge */}
      {token && emailVerified === false && (
        <div className="verify-email-notice">
          <span>⚠️ Your email is not verified. Verify to protect your account and unlock promo eligibility.</span>
          <button className="verify-email-btn" onClick={handleSendVerificationEmail} disabled={sendingVerification}>
            {sendingVerification ? 'Sending...' : 'Verify Email'}
          </button>
        </div>
      )}
      {token && emailVerified === true && (
        <div className="verify-email-notice" style={{ borderColor: '#4ade80', color: '#4ade80', background: 'rgba(74,222,128,0.08)' }}>
          ✅ Email verified
        </div>
      )}

      {checkoutMessage && (
        <div className={`checkout-message ${checkoutMessage.type}`}>
          {checkoutMessage.text}
          {selectedPlan && checkoutMessage.type === 'success' && (
            <div className="checkout-note">Selected plan: {selectedPlan.toUpperCase()}</div>
          )}
        </div>
      )}

      {manualCheckoutUrl && (
        <div className="manual-checkout-toast" role="status" aria-live="polite">
          <span>Checkout did not open automatically.</span>
          <a href={manualCheckoutUrl} className="manual-checkout-link" target="_blank" rel="noreferrer">
            Open checkout manually
          </a>
          <button type="button" className="manual-checkout-dismiss" onClick={clearManualCheckoutPrompt}>
            Dismiss
          </button>
        </div>
      )}

      <div className="pricing-grid">
        {/* Free Plan */}
        <div className={`pricing-card free ${currentTier === 'free' ? 'current' : ''}`}>
          <div className="card-header">
            <h2>Free</h2>
            <p className="price">$0<span>/month</span></p>
          </div>

          <div className="features-list">
            <div className="feature">✓ Basic investment tracking</div>
            <div className="feature">✓ General AI recommendations</div>
            <div className="feature">✓ Standard buy/sell lines</div>
            <div className="feature">✓ Portfolio dashboard</div>
            <div className="feature limit">⚡ 10 signals/day</div>
          </div>

          <button
            className={`action-btn ${normalizedCurrentTier === 'free' ? 'current-plan' : ''}`}
            onClick={handleCancelToFree}
            disabled={isProcessingCheckout || processingTier === 'free' || normalizedCurrentTier === 'free'}
          >
            {processingTier === 'free'
              ? 'Processing...'
              : normalizedCurrentTier === 'free'
                ? '✓ Current Plan'
                : 'Cancel to Free'}
          </button>
        </div>

        {/* Pro Plan */}
        <div className={`pricing-card pro ${currentTier === 'pro' ? 'current' : ''} popular`}>
          <div className="popular-badge">Most Popular</div>
          <div className="card-header">
            <h2>Pro</h2>
            {applyPromo && promoStatus?.active ? (
              <p className="price">
                <span className="price-original">{proPlan.priceDisplay.replace('/mo', '')}</span>
                <span className="price-discounted"> ${(SUBSCRIPTION_PRICES.pro * (1 - promoStatus.discount_pct / 100) / 100).toFixed(2)}</span>
                <span>/month</span>
              </p>
            ) : (
              <p className="price">{proPlan.priceDisplay.replace('/mo', '')}<span>/month</span></p>
            )}
          </div>

          <div className="features-list">
            {proPlan.features.map((feature) => (
              <div key={`pro-${feature}`} className="feature">✓ {feature}</div>
            ))}
            <div className="feature limit">⚡ 100 signals/day</div>
            <div className="feature limit">⚡ 20 alerts/day</div>
          </div>

          <button
            className={`action-btn upgrade-btn ${normalizedCurrentTier === 'pro' ? 'current-plan' : ''}`}
            onClick={() => {
              if (normalizedCurrentTier === 'premium') {
                handleDowngradeToPro()
                return
              }
              if (normalizedCurrentTier !== 'pro') {
                handleUpgrade('pro')
              }
            }}
            disabled={isProcessingCheckout}
          >
            {redirectingTier === 'pro'
              ? 'Opening checkout...'
              : processingTier === 'pro'
              ? normalizedCurrentTier === 'premium' ? 'Scheduling downgrade...' : 'Creating checkout...'
              : normalizedCurrentTier === 'pro'
                ? '✓ Current Plan'
                : normalizedCurrentTier === 'premium'
                  ? 'Schedule Downgrade to Pro'
                  : 'Upgrade to Pro'}
          </button>
        </div>

        {/* Premium Plan */}
        <div className={`pricing-card premium ${currentTier === 'premium' ? 'current' : ''}`}>
          <div className="elite-badge">Elite</div>
          <div className="card-header">
            <h2>Premium</h2>
            {applyPromo && promoStatus?.active ? (
              <p className="price">
                <span className="price-original">{premiumPlan.priceDisplay.replace('/mo', '')}</span>
                <span className="price-discounted"> ${(SUBSCRIPTION_PRICES.premium * (1 - promoStatus.discount_pct / 100) / 100).toFixed(2)}</span>
                <span>/month</span>
              </p>
            ) : (
              <p className="price">{premiumPlan.priceDisplay.replace('/mo', '')}<span>/month</span></p>
            )}
          </div>

          <div className="features-list">
            {premiumPlan.features.map((feature) => (
              <div key={`premium-${feature}`} className="feature">✓ {feature}</div>
            ))}
            <div className="feature limit">⚡ Unlimited signals</div>
          </div>

          <button
            className={`action-btn premium-btn ${normalizedCurrentTier === 'premium' ? 'current-plan' : ''}`}
            onClick={() => handleUpgrade('premium')}
            disabled={isProcessingCheckout || normalizedCurrentTier === 'premium'}
          >
            {redirectingTier === 'premium'
              ? 'Opening checkout...'
              : processingTier === 'premium'
              ? 'Creating checkout...'
              : normalizedCurrentTier === 'premium'
                ? '✓ Current Plan'
                : 'Upgrade to Premium'}
          </button>
        </div>
      </div>

      <section className="support-help-card">
        <h3>Need Help With Payment or Subscription?</h3>
        <p>
          If checkout fails, your upgrade does not appear, or you need account assistance,
          contact our support team and include your username plus approximate payment time.
        </p>
        <a
          className="support-email-link"
          href={`mailto:${SUPPORT_EMAIL}?subject=CryptoAI%20Billing%20Support`}
        >
          Contact Support: {SUPPORT_EMAIL}
        </a>
      </section>

      <Elements stripe={stripePromise}>
        <CheckoutModal
          visible={showCheckoutModal}
          clientSecret={clientSecret}
          selectedPlan={selectedPlan}
          checkoutAmount={checkoutAmount}
          applePayCheckoutUrl={applePayCheckoutUrl}
          user={user}
          onClose={closeCheckoutModal}
          onConfirm={onPaymentConfirmed}
          onError={onPaymentError}
        />
      </Elements>

      {/* FAQ Section */}
      <div className="pricing-faq">
        <h3>❓ Frequently Asked Questions</h3>

        <div className="faq-item">
          <h4>Can I change my plan anytime?</h4>
          <p>Yes! You can upgrade or downgrade your plan at any time. Changes take effect on your next billing cycle.</p>
        </div>

        <div className="faq-item">
          <h4>Is there a free trial?</h4>
          <p>You can use the Free plan indefinitely. Start with Free and upgrade whenever you're ready to unlock advanced features.</p>
        </div>

        <div className="faq-item">
          <h4>What payment methods do you accept?</h4>
          <p>We accept all major credit/debit cards through Stripe for secure payments.</p>
        </div>

        <div className="faq-item">
          <h4>Can I cancel anytime?</h4>
          <p>Yes! Cancel your subscription anytime with no questions asked. Your access continues until the end of your billing period.</p>
        </div>

        <div className="faq-item">
          <h4>Do you offer refunds?</h4>
          <p>We offer a 7-day money-back guarantee. If you're not satisfied, contact support for a full refund.</p>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="pricing-comparison">
        <h3>📊 Detailed Feature Comparison</h3>
        
        <table className="comparison-table">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Free</th>
              <th>Pro</th>
              <th>Premium</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Investment Tracking</td>
              <td>✓</td>
              <td>✓</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>AI Recommendations</td>
              <td>Basic</td>
              <td>Advanced</td>
              <td>Exclusive</td>
            </tr>
            <tr>
              <td>Real-time Alerts</td>
              <td>✗</td>
              <td>✓ (20/day)</td>
              <td>✓ Unlimited</td>
            </tr>
            <tr>
              <td>Signal History</td>
              <td>✗</td>
              <td>30 days</td>
              <td>1 year</td>
            </tr>
            <tr>
              <td>Portfolio Analytics</td>
              <td>Basic</td>
              <td>Advanced</td>
              <td>Premium</td>
            </tr>
            <tr>
              <td>API Access</td>
              <td>Limited</td>
              <td>Standard</td>
              <td>Priority</td>
            </tr>
            <tr>
              <td>Early Access Features</td>
              <td>✗</td>
              <td>✗</td>
              <td>✓</td>
            </tr>
            <tr>
              <td>Priority Support</td>
              <td>✗</td>
              <td>✗</td>
              <td>✓</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}

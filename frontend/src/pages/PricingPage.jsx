import React, { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'
import { QRCodeSVG } from 'qrcode.react'
import './PricingPage.css'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '')
const SUPPORT_EMAIL = import.meta.env.VITE_SUPPORT_EMAIL || 'cryptosupport74@gmail.com'

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
  const API_BASE = `http://${window.location.hostname || 'localhost'}:8002`
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

  useEffect(() => {
    fetchPlans()
    if (user?.user_id) {
      fetchUserSubscription()
    }
  }, [user])

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

  const handleUpgrade = async (tier) => {
    if (!token) {
      navigate('/login')
      return
    }

    try {
      setProcessingTier(tier)
      setCheckoutMessage(null)

      const response = await axios.post(
        `${API_BASE}/api/subscription/create-payment-intent`,
        null,
        {
          params: { tier },
          headers: { Authorization: `Bearer ${token}` }
        }
      )

      setSelectedPlan(tier)
      setClientSecret(response.data?.client_secret || '')
      setStripeCustomerId(response.data?.stripe_customer_id || '')
      const amountUsd = ((response.data?.amount || 0) / 100).toFixed(2)
      setCheckoutAmount(amountUsd)

      try {
        const checkoutSessionResponse = await axios.post(
          `${API_BASE}/api/subscription/create-checkout-session`,
          null,
          {
            params: { tier, origin: window.location.origin },
            headers: { Authorization: `Bearer ${token}` }
          }
        )
        setApplePayCheckoutUrl(checkoutSessionResponse.data?.url || '')
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
      setProcessingTier(null)
    }
  }

  const closeCheckoutModal = () => {
    setShowCheckoutModal(false)
    setApplePayCheckoutUrl('')
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

      {checkoutMessage && (
        <div className={`checkout-message ${checkoutMessage.type}`}>
          {checkoutMessage.text}
          {selectedPlan && checkoutMessage.type === 'success' && (
            <div className="checkout-note">Selected plan: {selectedPlan.toUpperCase()}</div>
          )}
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
            className={`action-btn ${currentTier === 'free' ? 'current-plan' : ''}`}
            disabled={currentTier === 'free' || processingTier !== null}
          >
            {currentTier === 'free' ? '✓ Current Plan' : 'Downgrade'}
          </button>
        </div>

        {/* Pro Plan */}
        <div className={`pricing-card pro ${currentTier === 'pro' ? 'current' : ''} popular`}>
          <div className="popular-badge">Most Popular</div>
          <div className="card-header">
            <h2>Pro</h2>
            <p className="price">$9.99<span>/month</span></p>
          </div>

          <div className="features-list">
            <div className="feature">✓ Everything in Free +</div>
            <div className="feature">✓ Advanced AI signals</div>
            <div className="feature">✓ Real-time price alerts</div>
            <div className="feature">✓ Signal confidence scoring</div>
            <div className="feature">✓ Signal history (30 days)</div>
            <div className="feature">✓ Portfolio optimization tips</div>
            <div className="feature limit">⚡ 100 signals/day</div>
            <div className="feature limit">⚡ 20 alerts/day</div>
          </div>

          <button
            className={`action-btn upgrade-btn ${currentTier === 'pro' ? 'current-plan' : ''}`}
            onClick={() => handleUpgrade('pro')}
            disabled={currentTier === 'pro' || processingTier !== null}
          >
            {processingTier === 'pro' ? 'Creating checkout...' : currentTier === 'pro' ? '✓ Current Plan' : 'Upgrade to Pro'}
          </button>
        </div>

        {/* Premium Plan */}
        <div className={`pricing-card premium ${currentTier === 'premium' ? 'current' : ''}`}>
          <div className="elite-badge">Elite</div>
          <div className="card-header">
            <h2>Premium</h2>
            <p className="price">$29.99<span>/month</span></p>
          </div>

          <div className="features-list">
            <div className="feature">✓ Everything in Pro +</div>
            <div className="feature">✓ Exclusive high-accuracy signals</div>
            <div className="feature">✓ Unlimited alerts</div>
            <div className="feature">✓ Signal history (1 year)</div>
            <div className="feature">✓ Advanced portfolio analytics</div>
            <div className="feature">✓ Early access to new features</div>
            <div className="feature">✓ Priority support</div>
            <div className="feature">✓ Performance tracking</div>
            <div className="feature limit">⚡ Unlimited signals</div>
          </div>

          <button
            className={`action-btn premium-btn ${currentTier === 'premium' ? 'current-plan' : ''}`}
            onClick={() => handleUpgrade('premium')}
            disabled={currentTier === 'premium' || processingTier !== null}
          >
            {processingTier === 'premium' ? 'Creating checkout...' : currentTier === 'premium' ? '✓ Current Plan' : 'Upgrade to Premium'}
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

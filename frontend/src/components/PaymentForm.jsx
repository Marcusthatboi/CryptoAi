import React, { useEffect, useMemo, useState } from 'react'
import { Elements, CardElement, PaymentRequestButtonElement, useElements, useStripe } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'
import { cryptoAPI } from '../utils/api'
import './PaymentForm.css'

const stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '')

function TradePaymentFormInner({
  onSubmit,
  amount,
  displaySymbol,
  quantity,
  assetClass = 'crypto',
  executionProvider = 'auto',
  loading
}) {
  const stripe = useStripe()
  const elements = useElements()
  const [cardholderName, setCardholderName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [showPurchaseConfirm, setShowPurchaseConfirm] = useState(false)
  const [errors, setErrors] = useState({})
  const [paymentRequest, setPaymentRequest] = useState(null)
  const [applePayReady, setApplePayReady] = useState(false)
  const [applePayChecked, setApplePayChecked] = useState(false)
  const [applePayStatus, setApplePayStatus] = useState('checking')
  const amountLabel = useMemo(() => Number(amount || 0).toFixed(2), [amount])

  useEffect(() => {
    if (!stripe || Number(amount || 0) <= 0) {
      setPaymentRequest(null)
      setApplePayReady(false)
      setApplePayChecked(false)
      setApplePayStatus('checking')
      return
    }

    const host = typeof window !== 'undefined' ? window.location.hostname : ''
    const isLocalhost = host === 'localhost' || host === '127.0.0.1' || host === '::1'
    const isSecure = typeof window !== 'undefined'
      ? (window.isSecureContext || window.location.protocol === 'https:' || isLocalhost)
      : false

    if (!isSecure) {
      setPaymentRequest(null)
      setApplePayReady(false)
      setApplePayChecked(true)
      setApplePayStatus('https_required')
      return
    }

    const pr = stripe.paymentRequest({
      country: 'US',
      currency: 'usd',
      total: {
        label: `CryptoAI ${displaySymbol || 'Trade'}`,
        amount: Math.max(1, Math.round(Number(amount || 0) * 100))
      },
      requestPayerName: true,
      requestPayerEmail: true
    })

    setApplePayChecked(false)
    pr.canMakePayment()
      .then((result) => {
        if (result?.applePay) {
          setPaymentRequest(pr)
          setApplePayReady(true)
          setApplePayStatus('available')
        } else {
          setPaymentRequest(null)
          setApplePayReady(false)
          setApplePayStatus('unavailable')
        }
        setApplePayChecked(true)
      })
      .catch(() => {
        setPaymentRequest(null)
        setApplePayReady(false)
        setApplePayChecked(true)
        setApplePayStatus('unavailable')
      })

    pr.on('paymentmethod', async (event) => {
      try {
        setSubmitting(true)
        setErrors({})

        const intentResponse = await cryptoAPI.createTradePaymentIntent({
          amount: Number(amount || 0),
          symbol: displaySymbol,
          asset_class: assetClass,
          quantity: Number(quantity || 0)
        })

        const clientSecret = intentResponse?.data?.client_secret
        if (!clientSecret) {
          throw new Error('Missing Stripe client secret for trade payment.')
        }

        const confirmResult = await stripe.confirmCardPayment(
          clientSecret,
          { payment_method: event.paymentMethod.id },
          { handleActions: false }
        )

        if (confirmResult.error) {
          event.complete('fail')
          throw new Error(confirmResult.error.message || 'Apple Pay payment failed.')
        }

        let paymentIntent = confirmResult.paymentIntent

        if (paymentIntent?.status === 'requires_action') {
          const actionResult = await stripe.confirmCardPayment(clientSecret)
          if (actionResult.error) {
            event.complete('fail')
            throw new Error(actionResult.error.message || 'Payment authentication failed.')
          }
          paymentIntent = actionResult.paymentIntent
        }

        if (paymentIntent?.status !== 'succeeded') {
          event.complete('fail')
          throw new Error('Payment was not completed. Please try again.')
        }

        event.complete('success')

        await onSubmit({
          paymentIntentId: paymentIntent.id,
          paymentStatus: paymentIntent.status
        })
      } catch (error) {
        console.error('Apple Pay submission error:', error)
        setErrors({ submit: error?.message || 'Failed to process Apple Pay payment.' })
      } finally {
        setSubmitting(false)
      }
    })
  }, [amount, assetClass, displaySymbol, onSubmit, quantity, stripe])

  const validateForm = () => {
    const newErrors = {}

    if (!cardholderName || cardholderName.trim().length < 3) {
      newErrors.cardholderName = 'Please enter cardholder name'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const submitTradePayment = async () => {
    try {
      setSubmitting(true)
      setErrors({})

      const intentResponse = await cryptoAPI.createTradePaymentIntent({
        amount: Number(amount || 0),
        symbol: displaySymbol,
        asset_class: assetClass,
        quantity: Number(quantity || 0)
      })

      const clientSecret = intentResponse?.data?.client_secret
      if (!clientSecret) {
        throw new Error('Missing Stripe client secret for trade payment.')
      }

      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error('Card input is unavailable.')
      }

      const confirmResult = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            name: cardholderName.trim()
          }
        }
      })

      if (confirmResult.error) {
        throw new Error(confirmResult.error.message || 'Payment failed. Please try again.')
      }

      if (confirmResult.paymentIntent?.status !== 'succeeded') {
        throw new Error('Payment was not completed. Please try again.')
      }

      await onSubmit({
        paymentIntentId: confirmResult.paymentIntent.id,
        paymentStatus: confirmResult.paymentIntent.status
      })
      setCardholderName('')
      cardElement.clear()
      setShowPurchaseConfirm(false)
    } catch (error) {
      console.error('Payment submission error:', error)
      setErrors({ submit: error?.message || 'Failed to process payment. Please try again.' })
    } finally {
      setSubmitting(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    if (!stripe || !elements) {
      setErrors({ submit: 'Stripe is not ready yet. Please try again.' })
      return
    }

    setErrors({})
    setShowPurchaseConfirm(true)
  }

  return (
    <form className="payment-form" onSubmit={handleSubmit}>
      <div className="form-header">
        <h3>💳 Secure Checkout</h3>
        <p className="security-badge">🔒 Card details are handled directly by Stripe</p>
      </div>

      <div className={`wallet-availability ${applePayReady ? 'available' : 'unavailable'}`}>
        {!applePayChecked
          ? 'Checking Apple Pay availability on this device...'
          : applePayStatus === 'https_required'
            ? 'Apple Pay requires HTTPS. Open this app over https:// (or localhost) to enable wallet checkout.'
            : applePayReady
            ? 'Apple Pay is available on this device.'
            : 'Apple Pay is not available on this device/browser. You can still pay by card.'}
      </div>

      {applePayReady && paymentRequest && (
        <div className="wallet-method">
          <label>Apple Pay</label>
          <div className="wallet-button-wrap">
            <PaymentRequestButtonElement
              options={{
                paymentRequest,
                style: {
                  paymentRequestButton: {
                    type: 'buy',
                    theme: 'dark',
                    height: '44px'
                  }
                }
              }}
            />
          </div>
          <div className="wallet-divider"><span>or pay with card</span></div>
        </div>
      )}

      {/* Cardholder Name */}
      <div className="form-group">
        <label htmlFor="cardholderName">Cardholder Name</label>
        <input
          id="cardholderName"
          type="text"
          placeholder="John Doe"
          value={cardholderName}
          onChange={(e) => setCardholderName(e.target.value)}
          disabled={loading || submitting}
          className={errors.cardholderName ? 'error' : ''}
        />
        {errors.cardholderName && (
          <span className="error-text">{errors.cardholderName}</span>
        )}
      </div>

      <div className="form-group">
        <label>Card Details</label>
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
      </div>

      {/* Investment Summary */}
      <div className="investment-summary-card">
        <div className="summary-row">
          <span>Investment Amount:</span>
          <strong>${amountLabel}</strong>
        </div>
        <div className="summary-row">
          <span>Symbol:</span>
          <strong>{displaySymbol || 'N/A'}</strong>
        </div>
        <div className="summary-row">
          <span>Asset Class:</span>
          <strong>{String(assetClass || 'crypto').toUpperCase()}</strong>
        </div>
        <div className="summary-row">
          <span>Execution:</span>
          <strong>{String(executionProvider || 'auto').toUpperCase()}</strong>
        </div>
      </div>

      {/* Warnings */}
      <div className="payment-warnings">
        <p>⚠️ Please ensure all information is correct before submitting.</p>
        <p>Your card will be charged ${amountLabel} upon confirmation.</p>
      </div>

      {/* Error Message */}
      {errors.submit && (
        <div className="error-message">
          <span>❌ {errors.submit}</span>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        className="payment-submit-btn"
        disabled={loading || submitting || !stripe}
      >
        {loading || submitting ? (
          <>
            <span className="spinner"></span>
            Processing Secure Payment...
          </>
        ) : (
          `Invest $${amountLabel} Now`
        )}
      </button>

      {showPurchaseConfirm && (
        <div className="purchase-confirm-box" role="alertdialog" aria-live="assertive">
          <p className="purchase-confirm-title">Are you sure you are okay with this purchase?</p>
          <p className="purchase-confirm-amount">Purchase amount: ${amountLabel}</p>
          <div className="purchase-confirm-actions">
            <button
              type="button"
              className="purchase-confirm-btn no"
              onClick={() => setShowPurchaseConfirm(false)}
              disabled={submitting}
            >
              No
            </button>
            <button
              type="button"
              className="purchase-confirm-btn yes"
              onClick={submitTradePayment}
              disabled={submitting}
            >
              Yes
            </button>
          </div>
        </div>
      )}

      <p className="terms-text">
        By clicking "Invest", you agree to our Terms of Service and confirm that this is a real money investment.
      </p>
    </form>
  )
}

export default function PaymentForm(props) {
  return (
    <Elements stripe={stripePromise}>
      <TradePaymentFormInner {...props} />
    </Elements>
  )
}

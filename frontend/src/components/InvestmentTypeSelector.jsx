import React, { useEffect, useState } from 'react'
import PaymentForm from './PaymentForm'
import { cryptoAPI } from '../utils/api'
import './InvestmentTypeSelector.css'

const MIN_SHARES = 1
const MAX_SHARES = 20
const SHARE_OPTIONS = Array.from({ length: MAX_SHARES }, (_, idx) => String(idx + 1))

export default function InvestmentTypeSelector({
  crypto,
  currentPrice,
  onFakeInvest,
  onRealInvest
}) {
  const [investmentType, setInvestmentType] = useState('fake') // 'fake' or 'real'
  const [amount, setAmount] = useState('')
  const [quantity, setQuantity] = useState('')
  const [inputType, setInputType] = useState('amount') // 'amount' or 'quantity'
  const [showPaymentForm, setShowPaymentForm] = useState(false)
  const [showFakeConfirm, setShowFakeConfirm] = useState(false)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [assetClass, setAssetClass] = useState('crypto') // 'crypto' or 'stock'
  const [executionProvider, setExecutionProvider] = useState('auto') // 'auto', 'binance', 'alpaca'
  const [stockTicker, setStockTicker] = useState('')
  const [stockUnitPrice, setStockUnitPrice] = useState('')
  const [providerReadiness, setProviderReadiness] = useState({
    binance: { ready: null, message: 'Checking...' },
    alpaca: { ready: null, message: 'Checking...' }
  })
  const [checkoutReadiness, setCheckoutReadiness] = useState({
    stripe: { ready: null, live_mode: false, message: 'Checking...' }
  })
  const [applePayCtaReady, setApplePayCtaReady] = useState(false)
  const [applePayCtaStatus, setApplePayCtaStatus] = useState('checking')

  useEffect(() => {
    try {
      if (typeof window === 'undefined') {
        setApplePayCtaReady(false)
        setApplePayCtaStatus('unavailable')
        return
      }

      const host = window.location.hostname
      const isLocalhost = host === 'localhost' || host === '127.0.0.1' || host === '::1'
      const isSecure = window.isSecureContext || window.location.protocol === 'https:' || isLocalhost
      if (!isSecure) {
        setApplePayCtaReady(false)
        setApplePayCtaStatus('https_required')
        return
      }

      if (window.ApplePaySession && typeof window.ApplePaySession.canMakePayments === 'function') {
        const canPay = Boolean(window.ApplePaySession.canMakePayments())
        setApplePayCtaReady(canPay)
        setApplePayCtaStatus(canPay ? 'ready' : 'unavailable')
        return
      }

      setApplePayCtaReady(false)
      setApplePayCtaStatus('unavailable')
    } catch (error) {
      console.error('Apple Pay capability detection failed:', error)
      setApplePayCtaReady(false)
      setApplePayCtaStatus('unavailable')
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    const checkProviders = async () => {
      if (investmentType !== 'real') {
        return
      }

      setProviderReadiness({
        binance: { ready: null, message: 'Checking...' },
        alpaca: { ready: null, message: 'Checking...' }
      })

      const [binanceResult, alpacaResult, readinessResult] = await Promise.allSettled([
        cryptoAPI.getBinanceStatus(),
        cryptoAPI.getAlpacaAccount(),
        cryptoAPI.getLiveReadiness()
      ])

      if (cancelled) {
        return
      }

      setProviderReadiness({
        binance: binanceResult.status === 'fulfilled' && Boolean(binanceResult.value?.data?.connected)
          ? { ready: true, message: 'Connected' }
          : { ready: false, message: 'Not connected' },
        alpaca: alpacaResult.status === 'fulfilled'
          ? { ready: true, message: 'Authenticated' }
          : { ready: false, message: 'Not authenticated' }
      })

      const liveReadiness = readinessResult?.status === 'fulfilled' ? readinessResult.value?.data : null
      setCheckoutReadiness({
        stripe: {
          ready: Boolean(liveReadiness?.stripe?.ready),
          live_mode: Boolean(liveReadiness?.stripe?.live_mode),
          message: String(liveReadiness?.stripe?.message || 'Stripe not configured for checkout')
        }
      })
    }

    checkProviders()

    return () => {
      cancelled = true
    }
  }, [investmentType])

  const cryptoPrice = Number(currentPrice?.price || 0)
  const stockPrice = Number(stockUnitPrice || 0)
  const effectivePrice = assetClass === 'stock' ? stockPrice : cryptoPrice
  const selectedSymbol = assetClass === 'stock'
    ? stockTicker.trim().toUpperCase()
    : String(crypto?.symbol || '').trim().toUpperCase()

  const isQuantityMode = inputType === 'quantity'
  const parsedQuantity = Number(quantity)
  const isShareQuantityValid =
    Number.isInteger(parsedQuantity) && parsedQuantity >= MIN_SHARES && parsedQuantity <= MAX_SHARES
  const isStockTickerValid = /^[A-Z][A-Z0-9.-]{0,9}$/.test(selectedSymbol)
  const assetUnitLabel = assetClass === 'stock' ? 'shares' : (crypto?.symbol || 'units')
  const isBinanceReady = providerReadiness.binance.ready === true
  const isAlpacaReady = providerReadiness.alpaca.ready === true
  const availableProviders = assetClass === 'stock'
    ? { auto: isAlpacaReady, alpaca: isAlpacaReady, binance: false }
    : { auto: isBinanceReady || isAlpacaReady, alpaca: isAlpacaReady, binance: isBinanceReady }
  const canSubmitRealOrder =
    availableProviders[executionProvider] === true ||
    (executionProvider === 'auto' && availableProviders.auto === true)
  const canStartCheckout = checkoutReadiness.stripe.ready === true

  useEffect(() => {
    if (investmentType !== 'real') {
      return
    }

    if (!availableProviders[executionProvider]) {
      if (availableProviders.auto) {
        setExecutionProvider('auto')
      } else if (assetClass === 'crypto' && availableProviders.binance) {
        setExecutionProvider('binance')
      } else if (availableProviders.alpaca) {
        setExecutionProvider('alpaca')
      }
    }
  }, [investmentType, assetClass, executionProvider, availableProviders.auto, availableProviders.binance, availableProviders.alpaca])

  const calculatedQuantity =
    inputType === 'amount' && amount && effectivePrice > 0
      ? (Number(amount) / effectivePrice).toFixed(8)
      : quantity

  const totalCost =
    inputType === 'amount' ? Number(amount) : Number(quantity) * effectivePrice

  const handleAmountChange = (e) => {
    setAmount(e.target.value)
    if (inputType !== 'amount') setInputType('amount')
  }

  const handleQuantityChange = (e) => {
    setQuantity(e.target.value)
    if (inputType !== 'quantity') setInputType('quantity')
  }

  const handleShareQuickPick = (shareCount) => {
    setQuantity(shareCount)
    if (inputType !== 'quantity') setInputType('quantity')
  }

  const handleFakeInvestSubmit = async () => {
    if (!amount && !quantity) {
      setMessage({
        type: 'error',
        text: 'Please enter an investment amount or quantity'
      })
      return
    }

    if (isQuantityMode && !isShareQuantityValid) {
      setMessage({
        type: 'error',
        text: `Please choose a share quantity between ${MIN_SHARES} and ${MAX_SHARES}.`
      })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const investAmount = inputType === 'amount' ? Number(amount) : totalCost
      const investQty = Number(calculatedQuantity)

      // Call parent handler
      await onFakeInvest({
        symbol: crypto?.symbol,
        quantity: investQty,
        price: cryptoPrice,
        totalValue: investAmount
      })

      setMessage({
        type: 'success',
        text: `✅ Fake money investment recorded! ${investQty.toFixed(8)} ${crypto?.symbol} @ $${cryptoPrice.toFixed(2)} = $${investAmount.toFixed(2)}`
      })
      setShowFakeConfirm(false)

      // Reset form
      setTimeout(() => {
        setAmount('')
        setQuantity('')
        setMessage(null)
      }, 3000)
    } catch (err) {
      setMessage({
        type: 'error',
        text: '❌ Failed to process fake investment. Please try again.'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleFakeCheckoutPrecheck = () => {
    if (!amount && !quantity) {
      setMessage({
        type: 'error',
        text: 'Please enter an investment amount or quantity'
      })
      return
    }

    if (isQuantityMode && !isShareQuantityValid) {
      setMessage({
        type: 'error',
        text: `Please choose a share quantity between ${MIN_SHARES} and ${MAX_SHARES}.`
      })
      return
    }

    setMessage(null)
    setShowFakeConfirm(true)
  }

  const handleRealInvestSubmit = async (paymentData) => {
    if (!selectedSymbol) {
      setMessage({
        type: 'error',
        text: 'Please enter a symbol before placing a real order.'
      })
      return
    }

    if (!canStartCheckout) {
      setMessage({
        type: 'error',
        text: `${checkoutReadiness.stripe.message}. Configure Stripe credentials before attempting real-money checkout.`
      })
      return
    }

    if (assetClass === 'stock' && !isStockTickerValid) {
      setMessage({
        type: 'error',
        text: 'Enter a valid stock ticker (for example AAPL or MSFT).'
      })
      return
    }

    if (!Number.isFinite(effectivePrice) || effectivePrice <= 0) {
      setMessage({
        type: 'error',
        text: 'Enter a valid unit price before checkout.'
      })
      return
    }

    if (!canSubmitRealOrder) {
      setMessage({
        type: 'error',
        text: 'No execution provider is currently ready. Please reconnect Alpaca/Binance and try again.'
      })
      return
    }

    if (isQuantityMode && !isShareQuantityValid) {
      setMessage({
        type: 'error',
        text: `Please choose a share quantity between ${MIN_SHARES} and ${MAX_SHARES}.`
      })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const investAmount = inputType === 'amount' ? Number(amount) : totalCost
      const investQty = Number(calculatedQuantity)

      // Call parent handler with encrypted payment data
      const response = await onRealInvest({
        symbol: selectedSymbol,
        quantity: investQty,
        price: effectivePrice,
        totalValue: investAmount,
        assetClass,
        executionProvider,
        paymentIntentId: paymentData?.paymentIntentId
      })

      const executedProvider = response?.execution?.provider || executionProvider
      const executionLabel = String(executedProvider || 'auto').toUpperCase()

      setMessage({
        type: 'success',
        text: `✅ Live order executed via ${executionLabel}! ${investQty.toFixed(8)} ${selectedSymbol} purchased for $${investAmount.toFixed(2)}.`
      })

      // Reset form
      setTimeout(() => {
        setAmount('')
        setQuantity('')
        setShowPaymentForm(false)
        setMessage(null)
      }, 3000)
    } catch (err) {
      const backendMessage = err?.response?.data?.detail
      setMessage({
        type: 'error',
        text: backendMessage || '❌ Payment or order execution failed. Please verify payment details and broker/exchange setup, then try again.'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleRealCheckoutPrecheck = async () => {
    if (!selectedSymbol) {
      setMessage({
        type: 'error',
        text: 'Please enter a symbol before checkout.'
      })
      return
    }

    if (assetClass === 'stock' && !isStockTickerValid) {
      setMessage({
        type: 'error',
        text: 'Enter a valid stock ticker (for example AAPL or MSFT).'
      })
      return
    }

    if (!Number.isFinite(effectivePrice) || effectivePrice <= 0) {
      setMessage({
        type: 'error',
        text: 'Enter a valid unit price before checkout.'
      })
      return
    }

    if (!amount && !quantity) {
      setMessage({
        type: 'error',
        text: 'Please enter an investment amount or quantity'
      })
      return
    }

    if (isQuantityMode && !isShareQuantityValid) {
      setMessage({
        type: 'error',
        text: `Please choose a share quantity between ${MIN_SHARES} and ${MAX_SHARES}.`
      })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      const investAmount = inputType === 'amount' ? Number(amount) : totalCost
      const investQty = Number(calculatedQuantity)
      const precheckResponse = await cryptoAPI.precheckRealMoneyInvest({
        symbol: selectedSymbol,
        quantity: investQty,
        price: effectivePrice,
        total_value: investAmount,
        asset_class: assetClass,
        execution_provider: executionProvider
      })

      if (!precheckResponse?.data?.can_execute) {
        throw new Error('Live execution precheck did not pass.')
      }

      setShowPaymentForm(true)
    } catch (err) {
      const backendMessage = err?.response?.data?.detail
      setMessage({
        type: 'error',
        text: backendMessage || 'Unable to validate live order route. Check Alpaca/Binance connectivity and try again.'
      })
    } finally {
      setLoading(false)
    }
  }

  const presetAmounts = [100, 500, 1000, 5000]

  return (
    <div className="investment-type-selector">
      <div className="selector-header">
        <h3>💼 Invest in {selectedSymbol || crypto?.symbol}</h3>
        <div className="current-price">
          <span className="label">{assetClass === 'stock' ? 'Unit Price' : 'Current Price'}</span>
          <span className="price">${effectivePrice.toFixed(2)}</span>
        </div>
      </div>

      {/* Investment Type Toggle */}
      <div className="investment-type-toggle">
        <button
          className={`type-btn ${investmentType === 'fake' ? 'active' : ''}`}
          onClick={() => {
            setInvestmentType('fake')
            setShowPaymentForm(false)
            setShowFakeConfirm(false)
            setMessage(null)
          }}
          disabled={loading}
        >
          <span className="type-icon">🎮</span>
          <span className="type-label">
            <span className="type-title">Fake Money</span>
            <span className="type-desc">Practice with portfolio</span>
          </span>
        </button>

        <button
          className={`type-btn ${investmentType === 'real' ? 'active' : ''}`}
          onClick={() => {
            setInvestmentType('real')
            setShowPaymentForm(false)
            setShowFakeConfirm(false)
            setMessage(null)
          }}
          disabled={loading}
        >
          <span className="type-icon">💳</span>
          <span className="type-label">
            <span className="type-title">Real Money</span>
            <span className="type-desc">Live investment</span>
          </span>
        </button>
      </div>

      {/* Investment Amount/Quantity Section */}
      {!showPaymentForm || investmentType === 'fake' ? (
        <div className="investment-input-section">
          {investmentType === 'real' && (
            <div className="execution-settings">
              <div className="input-group">
                <label>Asset Class</label>
                <div className="input-wrapper">
                  <select
                    value={assetClass}
                    onChange={(e) => {
                      const nextAssetClass = e.target.value
                      setAssetClass(nextAssetClass)
                      if (nextAssetClass === 'stock' && executionProvider === 'binance') {
                        setExecutionProvider('auto')
                      }
                      if (nextAssetClass === 'crypto') {
                        setStockTicker('')
                        setStockUnitPrice('')
                      }
                    }}
                    disabled={loading}
                  >
                    <option value="crypto">Crypto</option>
                    <option value="stock">Stock</option>
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label>Execution Provider</label>
                <div className="input-wrapper">
                  <select
                    value={executionProvider}
                    onChange={(e) => setExecutionProvider(e.target.value)}
                    disabled={loading}
                  >
                    <option value="auto" disabled={!availableProviders.auto}>Auto (recommended)</option>
                    {assetClass === 'crypto' && <option value="binance" disabled={!availableProviders.binance}>Binance</option>}
                    <option value="alpaca" disabled={!availableProviders.alpaca}>Alpaca</option>
                  </select>
                </div>
              </div>

              {assetClass === 'stock' && (
                <>
                  <div className="input-group">
                    <label>Stock Ticker</label>
                    <div className="input-wrapper">
                      <input
                        type="text"
                        placeholder="AAPL"
                        value={stockTicker}
                        onChange={(e) => setStockTicker(e.target.value.toUpperCase().replace(/\s+/g, ''))}
                        maxLength={10}
                        disabled={loading}
                      />
                    </div>
                  </div>

                  <div className="input-group">
                    <label>Estimated Price per Share ($)</label>
                    <div className="input-wrapper">
                      <span className="currency-symbol">$</span>
                      <input
                        type="number"
                        placeholder="190.25"
                        value={stockUnitPrice}
                        onChange={(e) => setStockUnitPrice(e.target.value)}
                        min="0"
                        step="0.01"
                        disabled={loading}
                      />
                    </div>
                  </div>
                </>
              )}

              <p className="execution-settings-hint">
                Auto uses Binance-first for crypto (with Alpaca fallback) and Alpaca for stocks.
              </p>

              <div className="provider-readiness-row">
                <span className={`provider-pill ${providerReadiness.binance.ready === true ? 'ready' : providerReadiness.binance.ready === false ? 'down' : 'checking'}`}>
                  Binance: {providerReadiness.binance.message}
                </span>
                <span className={`provider-pill ${providerReadiness.alpaca.ready === true ? 'ready' : providerReadiness.alpaca.ready === false ? 'down' : 'checking'}`}>
                  Alpaca: {providerReadiness.alpaca.message}
                </span>
                <span className={`provider-pill ${checkoutReadiness.stripe.ready === true ? 'ready' : checkoutReadiness.stripe.ready === false ? 'down' : 'checking'}`}>
                  Stripe: {checkoutReadiness.stripe.message}
                </span>
              </div>

              {!canSubmitRealOrder && (
                <p className="execution-settings-warning">
                  No provider route is currently available for this asset class.
                </p>
              )}
            </div>
          )}

          {/* Input Type Toggle */}
          <div className="input-type-toggle">
            <button
              className={`toggle-btn ${inputType === 'amount' ? 'active' : ''}`}
              onClick={() => {
                setInputType('amount')
                setQuantity('')
              }}
              disabled={loading}
            >
              By Amount
            </button>
            <button
              className={`toggle-btn ${inputType === 'quantity' ? 'active' : ''}`}
              onClick={() => {
                setInputType('quantity')
                setAmount('')
              }}
              disabled={loading}
            >
              By Whole Units
            </button>
          </div>

          {/* Input Fields */}
          {inputType === 'amount' ? (
            <div className="input-group">
              <label>Investment Amount ($)</label>
              <div className="input-wrapper">
                <span className="currency-symbol">$</span>
                <input
                  type="number"
                  placeholder="Enter amount"
                  value={amount}
                  onChange={handleAmountChange}
                  min="0"
                  step="10"
                  disabled={loading}
                />
              </div>

              {/* Preset Amounts */}
              <div className="preset-amounts">
                {presetAmounts.map((preset) => (
                  <button
                    key={preset}
                    className="preset-btn"
                    onClick={() => {
                      setAmount(preset.toString())
                      setInputType('amount')
                    }}
                    disabled={loading}
                  >
                    ${preset}
                  </button>
                ))}
              </div>

              {amount && (
                <div className="calculation-result">
                  <span className="label">You will receive:</span>
                  <span className="value">
                    {calculatedQuantity} {assetUnitLabel}
                  </span>
                </div>
              )}
            </div>
          ) : (
            <div className="input-group">
              <label>Whole Units ({assetUnitLabel})</label>
              <div className="share-options-grid" role="group" aria-label="Select shares">
                {SHARE_OPTIONS.map((shareCount) => (
                  <button
                    key={shareCount}
                    type="button"
                    className={`share-option-btn ${quantity === shareCount ? 'active' : ''}`}
                    onClick={() => handleShareQuickPick(shareCount)}
                    disabled={loading}
                  >
                    {shareCount}
                  </button>
                ))}
              </div>

              <p className="share-selector-hint">
                Choose {MIN_SHARES} to {MAX_SHARES} whole {assetUnitLabel} units per order.
              </p>

              {quantity && (
                <div className="calculation-result">
                  <span className="label">Investment Cost:</span>
                  <span className="value">${totalCost.toFixed(2)}</span>
                </div>
              )}
            </div>
          )}

          {/* Summary */}
          {(amount || quantity) && (
            <div className="investment-summary">
              <h4>Order Summary</h4>
              <div className="summary-row">
                <span>Price per {selectedSymbol || assetUnitLabel}</span>
                <span>${effectivePrice.toFixed(2)}</span>
              </div>
              <div className="summary-row">
                <span>{isQuantityMode ? 'Whole Units' : 'Quantity'}</span>
                <span>{calculatedQuantity} {assetUnitLabel}</span>
              </div>
              <div className="summary-row total">
                <span>Total Investment</span>
                <span>${totalCost.toFixed(2)}</span>
              </div>
            </div>
          )}

          {/* Message */}
          {message && (
            <div className={`message ${message.type}`}>
              {message.text}
            </div>
          )}

          {/* Submit Button */}
          <button
            className={`invest-btn ${investmentType === 'real' ? 'real-money-btn' : 'fake-money-btn'}`}
            onClick={() => {
              if (investmentType === 'real') {
                handleRealCheckoutPrecheck()
              } else {
                handleFakeCheckoutPrecheck()
              }
            }}
            disabled={loading || (!amount && !quantity) || (isQuantityMode && !isShareQuantityValid) || (investmentType === 'real' && !canSubmitRealOrder)}
          >
            {investmentType === 'real'
              ? `Proceed to Payment ($${totalCost.toFixed(2)})`
              : `Invest $${totalCost.toFixed(2)} (Fake Money)`}
          </button>

          {investmentType === 'real' && (
            <div className={`apple-pay-cta-badge ${applePayCtaStatus === 'ready' ? 'ready' : applePayCtaStatus === 'https_required' ? 'https-required' : 'card-only'}`}>
              {applePayCtaStatus === 'ready'
                ? 'Apple Pay ready on this device'
                : applePayCtaStatus === 'https_required'
                  ? 'Apple Pay requires HTTPS'
                  : 'Card checkout available'}
            </div>
          )}

          {showFakeConfirm && investmentType === 'fake' && (
            <div className="fake-confirm-box" role="alertdialog" aria-live="assertive">
              <p className="fake-confirm-title">Are you sure you are okay with this purchase?</p>
              <p className="fake-confirm-amount">Purchase amount: ${totalCost.toFixed(2)} (Fake Money)</p>
              <div className="fake-confirm-actions">
                <button
                  type="button"
                  className="fake-confirm-btn no"
                  onClick={() => setShowFakeConfirm(false)}
                  disabled={loading}
                >
                  No
                </button>
                <button
                  type="button"
                  className="fake-confirm-btn yes"
                  onClick={handleFakeInvestSubmit}
                  disabled={loading}
                >
                  Yes
                </button>
              </div>
            </div>
          )}
        </div>
      ) : null}

      {/* Payment Form for Real Money */}
      {showPaymentForm && investmentType === 'real' && (
        <div className="payment-section">
          <button
            className="back-to-amount-btn"
            onClick={() => setShowPaymentForm(false)}
            disabled={loading}
          >
            ← Back to Amount
          </button>
          <PaymentForm
            onSubmit={handleRealInvestSubmit}
            amount={totalCost}
            crypto={crypto}
            displaySymbol={selectedSymbol || crypto?.symbol}
            quantity={Number(calculatedQuantity || 0)}
            assetClass={assetClass}
            executionProvider={executionProvider}
            loading={loading}
          />
        </div>
      )}
    </div>
  )
}

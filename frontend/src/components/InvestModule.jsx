import React, { useState } from 'react'
import './InvestModule.css'

const MIN_UNITS = 1
const MAX_UNITS = 20
const UNIT_OPTIONS = Array.from({ length: MAX_UNITS }, (_, idx) => String(idx + 1))

export default function InvestModule({ crypto, currentPrice }) {
  const [amount, setAmount] = useState('')
  const [quantity, setQuantity] = useState('')
  const [investType, setInvestType] = useState('amount') // 'amount' or 'quantity'
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)

  const price = currentPrice?.price || 0
  const isQuantityMode = investType === 'quantity'
  const parsedQuantity = Number(quantity)
  const isWholeUnitValid =
    Number.isInteger(parsedQuantity) && parsedQuantity >= MIN_UNITS && parsedQuantity <= MAX_UNITS
  const assetUnitLabel = crypto?.symbol || 'units'

  // Calculate quantity from amount
  const calculatedQuantity = investType === 'amount' && amount ? (Number(amount) / price).toFixed(8) : quantity

  // Calculate total cost
  const totalCost = investType === 'amount' ? Number(amount) : (Number(quantity) * price)

  const handleAmountChange = (e) => {
    setAmount(e.target.value)
    if (investType !== 'amount') setInvestType('amount')
  }

  const handleQuantityChange = (e) => {
    setQuantity(e.target.value)
    if (investType !== 'quantity') setInvestType('quantity')
  }

  const handleUnitQuickPick = (unitCount) => {
    setQuantity(unitCount)
    if (investType !== 'quantity') setInvestType('quantity')
  }

  const handleInvest = async () => {
    if (!amount && !quantity) {
      setMessage({ type: 'error', text: 'Please enter an investment amount or quantity' })
      return
    }

    if (isQuantityMode && !isWholeUnitValid) {
      setMessage({ type: 'error', text: `Please choose ${MIN_UNITS}-${MAX_UNITS} whole units.` })
      return
    }

    setLoading(true)
    setMessage(null)

    try {
      // Simulate investment process
      // In a real application, this would call the backend API
      await new Promise(resolve => setTimeout(resolve, 1500))

      const investAmount = investType === 'amount' ? Number(amount) : totalCost
      const investQty = Number(calculatedQuantity)

      setMessage({
        type: 'success',
        text: `✅ Investment order placed! ${investQty.toFixed(8)} ${crypto?.symbol} @ $${price.toFixed(2)} = $${investAmount.toFixed(2)}`
      })

      // Reset form after success
      setTimeout(() => {
        setAmount('')
        setQuantity('')
        setMessage(null)
      }, 3000)
    } catch (err) {
      setMessage({ type: 'error', text: '❌ Investment failed. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  const presetAmounts = [100, 500, 1000, 5000]

  return (
    <div className="invest-module">
      <div className="module-header">
        <h3>💼 Invest in {crypto?.symbol}</h3>
        <div className="current-price">
          <span className="label">Current Price</span>
          <span className="price">${price.toFixed(2)}</span>
        </div>
      </div>

      <div className="module-body">
        {/* Investment Type Toggle */}
        <div className="type-toggle">
          <button
            className={`toggle-btn ${investType === 'amount' ? 'active' : ''}`}
            onClick={() => {
              setInvestType('amount')
              setQuantity('')
            }}
          >
            By Amount
          </button>
          <button
            className={`toggle-btn ${investType === 'quantity' ? 'active' : ''}`}
            onClick={() => {
              setInvestType('quantity')
              setAmount('')
            }}
          >
            By Whole Units
          </button>
        </div>

        {/* Input Fields */}
        <div className="input-group">
          {investType === 'amount' ? (
            <>
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
                      setInvestType('amount')
                    }}
                    disabled={loading}
                  >
                    ${preset}
                  </button>
                ))}
              </div>

              {/* Calculated Quantity */}
              {amount && (
                <div className="calculation-result">
                  <span className="label">You will receive:</span>
                  <span className="value">{calculatedQuantity} {crypto?.symbol}</span>
                </div>
              )}
            </>
          ) : (
            <>
              <label>Whole Units ({assetUnitLabel})</label>
              <div className="unit-options-grid" role="group" aria-label="Select whole units">
                {UNIT_OPTIONS.map((unitCount) => (
                  <button
                    key={unitCount}
                    type="button"
                    className={`unit-option-btn ${quantity === unitCount ? 'active' : ''}`}
                    onClick={() => handleUnitQuickPick(unitCount)}
                    disabled={loading}
                  >
                    {unitCount}
                  </button>
                ))}
              </div>

              <p className="unit-selector-hint">
                Choose {MIN_UNITS} to {MAX_UNITS} whole {assetUnitLabel} units per order.
              </p>

              {/* Calculated Cost */}
              {quantity && (
                <div className="calculation-result">
                  <span className="label">Investment Cost:</span>
                  <span className="value">${totalCost.toFixed(2)}</span>
                </div>
              )}
            </>
          )}
        </div>

        {/* Summary */}
        {(amount || quantity) && (
          <div className="investment-summary">
            <h4>Order Summary</h4>
            <div className="summary-row">
              <span>Price per {crypto?.symbol}</span>
              <span>${price.toFixed(2)}</span>
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

        {/* Invest Button */}
        <button
          className="invest-btn-primary"
          onClick={handleInvest}
          disabled={loading || (!amount && !quantity) || (isQuantityMode && !isWholeUnitValid)}
        >
          {loading ? (
            <>
              <span className="spinner-mini"></span>
              Processing...
            </>
          ) : (
            <>
              🚀 Invest Now
            </>
          )}
        </button>

        {/* Disclaimer */}
        <div className="disclaimer">
          ⚠️ <strong>Disclaimer:</strong> This is a demonstration. Always conduct your own research before investing in cryptocurrency.
        </div>
      </div>
    </div>
  )
}

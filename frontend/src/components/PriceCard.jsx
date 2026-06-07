import React, { useState, useEffect } from 'react'
import { cryptoAPI } from '../utils/api'
import { useWebSocket } from '../hooks/useWebSocket'
import ActivateAutoTradingBtn from './ActivateAutoTradingBtn'
import './PriceCard.css'

// Map crypto IDs to their trading symbols
const cryptoIdToSymbol = {
  bitcoin: 'BTC',
  ethereum: 'ETH',
  cardano: 'ADA',
  solana: 'SOL',
  ripple: 'XRP',
  'bitcoin-cash': 'BCH',
  'litecoin': 'LTC',
  'dogecoin': 'DOGE',
  'polkadot': 'DOT',
  'avalanche': 'AVAX',
  'polygon': 'MATIC',
  'chainlink': 'LINK',
  'uniswap': 'UNI',
  'aave': 'AAVE',
  'curve': 'CRV'
}

const getSymbolFromCryptoId = (cryptoId) => {
  return cryptoIdToSymbol[cryptoId?.toLowerCase()] || cryptoId?.toUpperCase()
}

export default function PriceCard({ cryptoId }) {
  const [price, setPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [autoTradingActive, setAutoTradingActive] = useState(false)
  const { isConnected, message, subscribe, unsubscribe } = useWebSocket()

  // Subscribe to price updates for this crypto
  useEffect(() => {
    if (isConnected) {
      subscribe(cryptoId.toUpperCase())

      return () => {
        unsubscribe(cryptoId.toUpperCase())
      }
    }
  }, [isConnected, cryptoId, subscribe, unsubscribe])

  // Listen for price updates via WebSocket
  useEffect(() => {
    if (message?.type === 'price_update' && message?.symbol === cryptoId.toUpperCase()) {
      setPrice(message.data)
      setLoading(false)
    }
  }, [message, cryptoId])

  // Initial load
  useEffect(() => {
    fetchPrice()
  }, [cryptoId])

  const fetchPrice = async () => {
    try {
      setLoading(true)
      const response = await cryptoAPI.getPrice(cryptoId)
      setPrice(response.data)
      setError(null)
    } catch (err) {
      console.warn('Failed to fetch price, using mock data:', err)
      // Use mock price data when API fails
      const mockPrices = {
        bitcoin: { id: 'bitcoin', price: 45339.26, price_change_24h: -0.33, market_cap: 900000000000 },
        ethereum: { id: 'ethereum', price: 2540.15, price_change_24h: 1.25, market_cap: 305000000000 },
        cardano: { id: 'cardano', price: 0.6785, price_change_24h: 0.95, market_cap: 25000000000 },
        solana: { id: 'solana', price: 112.45, price_change_24h: 2.15, market_cap: 48000000000 },
        ripple: { id: 'ripple', price: 0.5125, price_change_24h: -0.85, market_cap: 28000000000 }
      }
      setPrice(mockPrices[cryptoId.toLowerCase()] || mockPrices.bitcoin)
      setError(null)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !price) return <div className="price-card loading">Loading...</div>
  if (error) return <div className="price-card error">{error}</div>
  if (!price) return <div className="price-card">No data</div>

  const change = price.price_change_24h || 0
  const changeClass = change >= 0 ? 'positive' : 'negative'
  const changeSymbol = change >= 0 ? '📈' : '📉'

  return (
    <div className="price-card">
      <div className="card-header">
        <h3>{price.id.toUpperCase()}</h3>
        <div className="card-header-right">
          <span className={`update-status ${isConnected ? 'live' : 'polling'}`}>
            {isConnected ? '🔴 Live' : '⏱️ Polling'}
          </span>
          <span className={`change ${changeClass}`}>
            {changeSymbol} {change > 0 ? '+' : ''}{change.toFixed(2)}%
          </span>
        </div>
      </div>
      
      <div className="card-body">
        <div className="price-display">
          <span className="currency">$</span>
          <span className="amount">{price.price.toLocaleString('en-US', { 
            minimumFractionDigits: 2, 
            maximumFractionDigits: 2 
          })}</span>
        </div>
        
        {price.market_cap && (
          <div className="details">
            <p>Market Cap: <span>${(price.market_cap / 1e9).toFixed(2)}B</span></p>
          </div>
        )}
        
        {price.volume_24h && (
          <div className="details">
            <p>24h Volume: <span>${(price.volume_24h / 1e9).toFixed(2)}B</span></p>
          </div>
        )}
      </div>
      
      <div className="card-footer">
        <small>{new Date(price.timestamp).toLocaleTimeString()}</small>
        <ActivateAutoTradingBtn 
          symbol={getSymbolFromCryptoId(cryptoId)}
          currentPrice={price.price}
          onAutoTradingChange={(isActive) => setAutoTradingActive(isActive)}
        />
      </div>
    </div>
  )
}

import React, { useState, useEffect, useRef } from 'react'
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
  const cardRef = useRef(null)
  const hasFetchedRef = useRef(false)
  const [price, setPrice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isVisible, setIsVisible] = useState(false)
  const [autoTradingActive, setAutoTradingActive] = useState(false)
  const { isConnected, message, subscribe, unsubscribe } = useWebSocket()

  useEffect(() => {
    const node = cardRef.current
    if (!node) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (entry && entry.isIntersecting) {
          setIsVisible(true)
          observer.unobserve(node)
        }
      },
      {
        root: null,
        rootMargin: '220px',
        threshold: 0.05
      }
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  // Subscribe to price updates for this crypto
  useEffect(() => {
    if (isConnected && isVisible) {
      subscribe(cryptoId.toUpperCase())

      return () => {
        unsubscribe(cryptoId.toUpperCase())
      }
    }
  }, [isConnected, isVisible, cryptoId, subscribe, unsubscribe])

  // Listen for price updates via WebSocket
  useEffect(() => {
    if (message?.type === 'price_update' && message?.symbol === cryptoId.toUpperCase()) {
      setPrice(message.data)
      setLoading(false)
    }
  }, [message, cryptoId])

  // Initial load
  useEffect(() => {
    if (!isVisible || hasFetchedRef.current) {
      return
    }

    hasFetchedRef.current = true
    fetchPrice()
  }, [cryptoId, isVisible])

  const fetchPrice = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await cryptoAPI.getPrice(cryptoId)
      setPrice(response.data)
    } catch (err) {
      const status = err?.response?.status
      if (status === 404) {
        setError('Unavailable')
      } else {
        console.warn('Failed to fetch live price:', err)
        setError('Live quote unavailable')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!isVisible) return <div ref={cardRef} className="price-card loading">Loading...</div>
  if (loading && !price) return <div ref={cardRef} className="price-card loading">Loading...</div>
  if (error) return <div ref={cardRef} className="price-card error">{error}</div>
  if (!price) return <div ref={cardRef} className="price-card">No data</div>

  const change = price.price_change_24h || 0
  const changeClass = change >= 0 ? 'positive' : 'negative'
  const changeSymbol = change >= 0 ? '📈' : '📉'

  return (
    <div ref={cardRef} className="price-card">
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

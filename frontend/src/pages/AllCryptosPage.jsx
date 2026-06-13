import React, { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import PriceCard from '../components/PriceCard'
import { cryptoAPI } from '../utils/api'
import './AllCryptosPage.css'

const PAGE_SIZE = 250

const normalizeIds = (assets = []) => {
  const ids = assets
    .map((asset) => String(asset?.id || '').trim().toLowerCase())
    .filter(Boolean)

  return [...new Set(ids)]
}

export default function AllCryptosPage() {
  const navigate = useNavigate()
  const [cryptoIds, setCryptoIds] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true

    const loadAllCryptos = async () => {
      setLoading(true)
      setError('')

      try {
        const response = await cryptoAPI.getAssets(PAGE_SIZE)
        const normalized = normalizeIds(response?.data?.assets || [])

        if (!active) {
          return
        }

        if (!normalized.length) {
          setError('No assets returned from API. Ensure backend is running and market source is available.')
          setCryptoIds([])
          return
        }

        setCryptoIds(normalized.slice(0, PAGE_SIZE))
      } catch (err) {
        if (!active) {
          return
        }

        setError('Failed to load all 250 cryptocurrencies. Please try again after backend reconnects.')
        setCryptoIds([])
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadAllCryptos()

    return () => {
      active = false
    }
  }, [])

  const filteredIds = useMemo(() => {
    const term = search.trim().toLowerCase()
    if (!term) {
      return cryptoIds
    }

    return cryptoIds.filter((id) => {
      const readable = id.replace(/-/g, ' ')
      return id.includes(term) || readable.includes(term)
    })
  }, [cryptoIds, search])

  return (
    <div className="all-cryptos-page">
      <header className="all-cryptos-header">
        <div>
          <p className="eyebrow">Market Universe</p>
          <h1>All 250 Cryptocurrencies</h1>
          <p>One page with live cards for the full 250-asset set.</p>
        </div>
        <button type="button" className="back-btn" onClick={() => navigate('/dashboard')}>
          Back to Dashboard
        </button>
      </header>

      <div className="all-cryptos-toolbar">
        <input
          type="text"
          className="all-cryptos-search"
          placeholder="Search by asset id (e.g. bitcoin, dogecoin)"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <div className="all-cryptos-count">Showing {filteredIds.length} of {cryptoIds.length}</div>
      </div>

      {loading && <div className="state-note">Loading 250 assets...</div>}
      {!loading && error && <div className="state-note error">{error}</div>}

      {!loading && !error && (
        <section className="all-cryptos-grid">
          {filteredIds.map((id) => (
            <div
              key={id}
              className="card-wrapper"
              role="button"
              tabIndex={0}
              aria-label={`Open ${id} details`}
              onClick={() => navigate(`/invest/${id}`)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  navigate(`/invest/${id}`)
                }
              }}
            >
              <PriceCard cryptoId={id} />
            </div>
          ))}
        </section>
      )}
    </div>
  )
}

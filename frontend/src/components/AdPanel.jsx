import React, { useEffect, useState } from 'react'
import { cryptoAPI } from '../utils/api'
import './AdPanel.css'

function AdSlot({ ad, index }) {
  if (ad) {
    const clickUrl = ad.tracking_url || ad.url || '#'

    return (
      <a
        href={clickUrl}
        target="_blank"
        rel="noopener noreferrer sponsored"
        className="ad-slot-link"
        aria-label={ad.title || `Sponsored ad ${index + 1}`}
      >
        {ad.image && (
          <img src={ad.image} alt={ad.title || 'Sponsored'} className="ad-slot-img" />
        )}
        {ad.title && <p className="ad-slot-title">{ad.title}</p>}
        {ad.description && <p className="ad-slot-desc">{ad.description}</p>}
      </a>
    )
  }

  return (
    <div className="ad-slot-placeholder">
      <div className="ad-slot-placeholder-icon">📢</div>
      <p className="ad-slot-placeholder-text">Ad Space {index + 1}</p>
      <small className="ad-slot-placeholder-hint">
        Loading sponsored placements...
      </small>
    </div>
  )
}

export default function AdPanel() {
  const [ads, setAds] = useState([null, null])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setLoading(true)
    cryptoAPI.getAdPlacements('home', 2)
      .then((response) => {
        const list = Array.isArray(response?.data?.ads) ? response.data.ads : []
        setAds([list[0] || null, list[1] || null])
      })
      .catch((error) => {
        console.warn('Failed to load ad placements:', error)
        setAds([null, null])
      })
      .finally(() => setLoading(false))
  }, [])

  return (
    <aside className="ad-panel">
      <div className="ad-panel-header">Sponsored</div>

      <div className={`ad-slot ad-slot-primary${loading ? ' loading' : ''}`}>
        <AdSlot ad={ads[0]} index={0} />
      </div>

      <div className={`ad-slot ad-slot-secondary${loading ? ' loading' : ''}`}>
        <AdSlot ad={ads[1]} index={1} />
      </div>

      <div className="ad-panel-footer">
        <small>Pay-per-click campaigns powered by Stripe</small>
      </div>
    </aside>
  )
}

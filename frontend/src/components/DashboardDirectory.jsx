import React, { useState, useEffect } from 'react'
import './DashboardDirectory.css'

const MODULES = [
  { id: 'section-subscription', label: 'Subscription', icon: '📋' },
  { id: 'section-stats', label: 'Market Stats', icon: '📊' },
  { id: 'section-recommendations', label: 'AI Picks', icon: '🤖' },
  { id: 'section-auto-trading', label: 'Auto Trading', icon: '⚡' },
  { id: 'section-portfolio', label: 'Portfolio', icon: '💼' },
  { id: 'section-investments', label: 'My Investments', icon: '📈' },
  { id: 'section-prices', label: 'Live Prices', icon: '💰' },
  { id: 'section-alerts', label: 'Price Alerts', icon: '🚨' },
]

export default function DashboardDirectory() {
  const [active, setActive] = useState('')

  // Highlight the closest visible section as user scrolls
  useEffect(() => {
    const handler = () => {
      for (let i = MODULES.length - 1; i >= 0; i--) {
        const el = document.getElementById(MODULES[i].id)
        if (el) {
          const rect = el.getBoundingClientRect()
          if (rect.top <= 120) {
            setActive(MODULES[i].id)
            return
          }
        }
      }
      setActive(MODULES[0].id)
    }
    window.addEventListener('scroll', handler, { passive: true })
    handler()
    return () => window.removeEventListener('scroll', handler)
  }, [])

  const scrollTo = (id) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
      setActive(id)
    }
  }

  return (
    <nav className="dashboard-directory" aria-label="Page modules">
      <div className="dashboard-directory-title">Modules</div>
      <ul className="dashboard-directory-list">
        {MODULES.map((mod) => (
          <li key={mod.id}>
            <button
              className={`dashboard-directory-item${active === mod.id ? ' active' : ''}`}
              onClick={() => scrollTo(mod.id)}
              aria-current={active === mod.id ? 'true' : undefined}
            >
              <span className="directory-icon">{mod.icon}</span>
              <span className="directory-label">{mod.label}</span>
            </button>
          </li>
        ))}
      </ul>
    </nav>
  )
}

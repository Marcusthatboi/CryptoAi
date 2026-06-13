import React, { useEffect } from 'react'
import './AffiliateToolsPage.css'

const AMAZON_ASSOCIATE_TAG = (import.meta.env.VITE_AMAZON_ASSOCIATE_TAG || '').trim()

const PRODUCT_GUIDES = [
  {
    id: 'hardware-wallets',
    title: 'Hardware Wallet Shortlist',
    description: 'Cold-storage options for long-term holdings and safer key management.',
    searchTerm: 'hardware wallet crypto',
    category: 'Security'
  },
  {
    id: 'trading-desk',
    title: 'Trader Desk Essentials',
    description: 'Monitors, laptop stands, and ergonomics gear for active chart sessions.',
    searchTerm: 'ultrawide monitor trading desk setup',
    category: 'Workspace'
  },
  {
    id: 'two-factor',
    title: 'Two-Factor Security Keys',
    description: 'Physical security keys that add a stronger second factor than SMS.',
    searchTerm: 'fido2 security key usb',
    category: 'Security'
  },
  {
    id: 'education',
    title: 'Trading and Risk Books',
    description: 'Reading picks focused on risk management, sizing, and discipline.',
    searchTerm: 'trading psychology risk management books',
    category: 'Education'
  }
]

const COMPARISON_ROWS = [
  {
    productType: 'Hardware wallet',
    bestFor: 'Long-term holders and self-custody',
    budgetRange: '$50 - $250',
    setupTime: '10 - 20 minutes'
  },
  {
    productType: 'Security key',
    bestFor: 'Account hardening and 2FA protection',
    budgetRange: '$20 - $90',
    setupTime: '5 - 10 minutes'
  },
  {
    productType: 'Desk monitor gear',
    bestFor: 'Active charting and multi-panel workflows',
    budgetRange: '$120 - $800',
    setupTime: '20 - 40 minutes'
  },
  {
    productType: 'Risk management books',
    bestFor: 'Improving process and discipline',
    budgetRange: '$15 - $60',
    setupTime: 'Self-paced'
  }
]

function buildAmazonLink(searchTerm, placementId) {
  const params = new URLSearchParams({
    k: searchTerm,
    tag: AMAZON_ASSOCIATE_TAG || 'yourtag-20',
    linkCode: 'll2',
    language: 'en_US',
    ref_: `as_li_ss_tl`,
    ascsubtag: placementId,
    utm_source: 'cryptoai',
    utm_medium: 'affiliate',
    utm_campaign: 'tools_page'
  })

  return `https://www.amazon.com/s?${params.toString()}`
}

function trackAffiliateClick(item) {
  const eventPayload = {
    event: 'affiliate_click',
    network: 'amazon',
    placement: `tools_${item.id}`,
    category: item.category,
    title: item.title,
    timestamp: new Date().toISOString()
  }

  if (typeof window !== 'undefined' && typeof window.gtag === 'function') {
    window.gtag('event', 'affiliate_click', {
      event_category: 'monetization',
      event_label: item.id,
      network: 'amazon',
      page_path: '/tools',
      value: 1
    })
  }

  if (typeof window !== 'undefined' && Array.isArray(window.dataLayer)) {
    window.dataLayer.push(eventPayload)
  }

  try {
    const storageKey = 'affiliate_click_events'
    const existing = JSON.parse(localStorage.getItem(storageKey) || '[]')
    existing.push(eventPayload)
    localStorage.setItem(storageKey, JSON.stringify(existing.slice(-100)))
  } catch (_err) {
    // Ignore localStorage failures in restricted browser contexts.
  }
}

export default function AffiliateToolsPage() {
  const hasRealTag = AMAZON_ASSOCIATE_TAG && AMAZON_ASSOCIATE_TAG !== 'yourtag-20'

  useEffect(() => {
    document.title = 'Trader Tools | CryptoAI'

    const description = 'Affiliate picks for hardware wallets, account security keys, and trader desk tools.'
    let meta = document.querySelector('meta[name="description"]')
    if (!meta) {
      meta = document.createElement('meta')
      meta.setAttribute('name', 'description')
      document.head.appendChild(meta)
    }
    meta.setAttribute('content', description)
  }, [])

  return (
    <div className="affiliate-tools-page">
      <header className="affiliate-hero">
        <p className="eyebrow">Affiliate Picks</p>
        <h1>Trader Tools and Security Gear</h1>
        <p>
          Curated resources for crypto users who want better setup hygiene, stronger security,
          and practical learning materials.
        </p>
      </header>

      <section className="affiliate-disclosure" aria-label="affiliate disclosure">
        <strong>Disclosure:</strong> Some links on this page are affiliate links. If you buy through
        these links, we may earn a commission at no extra cost to you. This content is educational
        and not financial advice.
      </section>

      {!hasRealTag && (
        <section className="affiliate-warning" aria-label="setup warning">
          Amazon tag is not configured. Set VITE_AMAZON_ASSOCIATE_TAG in your frontend env to replace
          placeholder tracking.
        </section>
      )}

      <section className="affiliate-grid" aria-label="affiliate products">
        {PRODUCT_GUIDES.map((item) => (
          <article key={item.id} className="affiliate-card">
            <div className="affiliate-card-top">
              <span className="category-pill">{item.category}</span>
              <h2>{item.title}</h2>
              <p>{item.description}</p>
            </div>

            <a
              href={buildAmazonLink(item.searchTerm, `tools_${item.id}`)}
              target="_blank"
              rel="noreferrer sponsored"
              className="affiliate-cta"
              onClick={() => trackAffiliateClick(item)}
            >
              View on Amazon
            </a>
          </article>
        ))}
      </section>

      <section className="comparison-section" aria-label="comparison guide">
        <h2>Quick Comparison Guide</h2>
        <div className="comparison-table-wrap">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Product Type</th>
                <th>Best For</th>
                <th>Typical Budget</th>
                <th>Setup Time</th>
              </tr>
            </thead>
            <tbody>
              {COMPARISON_ROWS.map((row) => (
                <tr key={row.productType}>
                  <td>{row.productType}</td>
                  <td>{row.bestFor}</td>
                  <td>{row.budgetRange}</td>
                  <td>{row.setupTime}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

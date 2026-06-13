import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { cryptoAPI } from '../utils/api'
import { useAuth } from '../hooks/useAuth'
import './AdminDashboardPage.css'

const TIER_OPTIONS = ['free', 'pro', 'premium']
const STATUS_OPTIONS = ['active', 'cancelled', 'expired']

const formatCount = (value) => Number(value || 0).toLocaleString('en-US')
const formatCurrency = (value) => `$${Number(value || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const formatDate = (value) => value ? new Date(value).toLocaleString() : 'N/A'

export default function AdminDashboardPage() {
  const { user } = useAuth()
  const [days, setDays] = useState(7)
  const [analytics, setAnalytics] = useState(null)
  const [customers, setCustomers] = useState([])
  const [campaigns, setCampaigns] = useState([])
  const [filters, setFilters] = useState({ search: '', tier: '', status: '' })
  const [loading, setLoading] = useState(true)
  const [adsLoading, setAdsLoading] = useState(true)
  const [savingUserId, setSavingUserId] = useState(null)
  const [savingCampaignId, setSavingCampaignId] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [campaignError, setCampaignError] = useState('')
  const [campaignSuccess, setCampaignSuccess] = useState('')
  const [campaignForm, setCampaignForm] = useState({
    title: '',
    description: '',
    url: '',
    image: '',
    placement: 'home',
    sponsor_name: user?.username || 'CryptoAI Ads',
    cpc_cents: 25,
    budget_cents: 2500,
  })

  useEffect(() => {
    loadAdminData(days, filters)
  }, [days])

  useEffect(() => {
    loadCampaigns()
  }, [])

  const loadAdminData = async (windowDays = days, activeFilters = filters) => {
    try {
      setLoading(true)
      setError('')

      const [analyticsResponse, customersResponse] = await Promise.all([
        cryptoAPI.getAdminAnalyticsOverview(windowDays),
        cryptoAPI.getAdminCustomers({ ...activeFilters, limit: 100, status_filter: activeFilters.status || undefined })
      ])

      setAnalytics(analyticsResponse.data)
      setCustomers(customersResponse.data?.customers || [])
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to load admin dashboard')
    } finally {
      setLoading(false)
    }
  }

  const filteredSummary = useMemo(() => {
    const paidUsers = customers.filter((customer) => ['pro', 'premium'].includes(customer.subscription?.tier)).length
    const adminUsers = customers.filter((customer) => customer.is_admin).length

    return {
      total: customers.length,
      paidUsers,
      adminUsers
    }
  }, [customers])

  const handleFilterChange = (event) => {
    const { name, value } = event.target
    setFilters((current) => ({ ...current, [name]: value }))
  }

  const applyFilters = async (event) => {
    event.preventDefault()
    await loadAdminData(days, filters)
  }

  const loadCampaigns = async () => {
    try {
      setAdsLoading(true)
      setCampaignError('')
      const response = await cryptoAPI.getAdCampaigns()
      setCampaigns(response.data?.campaigns || [])
    } catch (err) {
      setCampaignError(err?.response?.data?.detail || 'Failed to load ad campaigns')
    } finally {
      setAdsLoading(false)
    }
  }

  const handleCampaignFieldChange = (event) => {
    const { name, value } = event.target
    setCampaignForm((current) => ({
      ...current,
      [name]: name === 'cpc_cents' || name === 'budget_cents' ? Number(value) : value,
    }))
  }

  const createCampaign = async (event) => {
    event.preventDefault()

    try {
      setSavingCampaignId('create')
      setCampaignError('')
      setCampaignSuccess('')

      const response = await cryptoAPI.createAdCampaign(campaignForm)
      const campaign = response.data?.campaign
      if (!campaign?.id) {
        throw new Error('Campaign was not created')
      }

      setCampaignSuccess(`Created campaign "${campaign.title}". Open Stripe checkout to fund it.`)
      await loadCampaigns()

      const checkoutResponse = await cryptoAPI.createAdCheckoutSession(campaign.id, {
        success_url: `${window.location.origin}/admin?ad_checkout=success`,
        cancel_url: `${window.location.origin}/admin?ad_checkout=cancel`,
        amount_cents: campaignForm.budget_cents,
      })

      const checkoutUrl = checkoutResponse.data?.url
      if (checkoutUrl) {
        window.open(checkoutUrl, '_blank', 'noopener,noreferrer')
      }

      setCampaignForm((current) => ({
        ...current,
        title: '',
        description: '',
        url: '',
        image: '',
        sponsor_name: user?.username || 'CryptoAI Ads',
      }))
    } catch (err) {
      setCampaignError(err?.response?.data?.detail || 'Failed to create or fund campaign')
    } finally {
      setSavingCampaignId(null)
    }
  }

  const updateCustomer = async (customer, patch) => {
    try {
      setSavingUserId(customer.user_id)
      setSuccess('')
      const response = await cryptoAPI.updateAdminCustomerSubscription(customer.user_id, patch)
      const updatedCustomer = response.data?.customer

      setCustomers((currentCustomers) => currentCustomers.map((entry) => (
        entry.user_id === customer.user_id ? updatedCustomer : entry
      )))
      setSuccess(`Updated ${customer.username}'s subscription successfully.`)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update customer subscription')
    } finally {
      setSavingUserId(null)
    }
  }

  return (
    <div className="admin-page">
      <header className="admin-hero">
        <div>
          <p className="eyebrow">Admin Control Center</p>
          <h1>Operations, monetization, and customer management</h1>
          <p className="hero-copy">
            Monitor subscription growth, watch quota pressure, and make support-side plan changes without leaving the product.
          </p>
        </div>
        <div className="hero-actions">
          <span className="admin-pill">Signed in as {user?.username}</span>
          <Link className="back-link" to="/dashboard">Return to dashboard</Link>
        </div>
      </header>

      {(error || success) && (
        <div className={`admin-banner ${error ? 'error' : 'success'}`}>
          {error || success}
        </div>
      )}

      <section className="admin-toolbar">
        <div className="window-switcher">
          {[7, 14, 30].map((windowOption) => (
            <button
              key={windowOption}
              className={days === windowOption ? 'active' : ''}
              onClick={() => setDays(windowOption)}
            >
              Last {windowOption} days
            </button>
          ))}
        </div>
        <button className="refresh-button" onClick={() => loadAdminData(days, filters)}>
          Refresh data
        </button>
      </section>

      <section className="admin-grid summary-grid">
        <article className="stat-panel accent-gold">
          <span className="stat-label">Tracked customers</span>
          <strong>{formatCount(filteredSummary.total)}</strong>
          <small>Current filtered customer set</small>
        </article>
        <article className="stat-panel accent-coral">
          <span className="stat-label">Paid subscribers</span>
          <strong>{formatCount(analytics?.subscriptions?.active_paid ?? filteredSummary.paidUsers)}</strong>
          <small>Pro and Premium accounts</small>
        </article>
        <article className="stat-panel accent-sky">
          <span className="stat-label">Signals generated</span>
          <strong>{formatCount(analytics?.usage?.signals?.total_generated)}</strong>
          <small>Across the last {analytics?.usage?.signals?.window_days || days} days</small>
        </article>
        <article className="stat-panel accent-mint">
          <span className="stat-label">API calls</span>
          <strong>{formatCount(analytics?.usage?.api?.total_calls)}</strong>
          <small>Across the last {analytics?.usage?.api?.window_hours || 24} hours</small>
        </article>
      </section>

      <section className="admin-grid insight-grid">
        <article className="panel-card analytics-card">
          <div className="panel-card-header">
            <div>
              <h2>Subscription mix</h2>
              <p>Tier distribution and monetization pressure</p>
            </div>
            <span className="generated-at">Generated {formatDate(analytics?.generated_at)}</span>
          </div>
          <div className="tier-breakdown">
            {TIER_OPTIONS.map((tier) => (
              <div className="tier-chip" key={tier}>
                <span>{tier.toUpperCase()}</span>
                <strong>{formatCount(analytics?.subscriptions?.by_tier?.[tier])}</strong>
              </div>
            ))}
          </div>
          <div className="analytics-metrics">
            <div>
              <span>Signal limit hits</span>
              <strong>{formatCount(analytics?.usage?.signals?.limit_hits)}</strong>
            </div>
            <div>
              <span>API limit hits</span>
              <strong>{formatCount(analytics?.usage?.api?.limit_hits)}</strong>
            </div>
            <div>
              <span>Active signal users</span>
              <strong>{formatCount(analytics?.usage?.signals?.active_users)}</strong>
            </div>
            <div>
              <span>Active API users</span>
              <strong>{formatCount(analytics?.usage?.api?.active_users)}</strong>
            </div>
          </div>
        </article>

        <article className="panel-card support-card">
          <div className="panel-card-header">
            <div>
              <h2>Support quick read</h2>
              <p>Useful customer health signals for account management</p>
            </div>
          </div>
          <ul className="support-list">
            <li>
              <span>Admin accounts in result set</span>
              <strong>{formatCount(filteredSummary.adminUsers)}</strong>
            </li>
            <li>
              <span>Accounts filtered right now</span>
              <strong>{formatCount(filteredSummary.total)}</strong>
            </li>
            <li>
              <span>Requested by</span>
              <strong>{analytics?.requested_by || user?.username}</strong>
            </li>
            <li>
              <span>Recommended action</span>
              <strong>{(analytics?.usage?.api?.limit_hits || 0) > 0 ? 'Review throttled customers' : 'Quota pressure looks healthy'}</strong>
            </li>
          </ul>
        </article>
      </section>

      <section className="panel-card customer-section">
        <div className="panel-card-header">
          <div>
            <h2>Customer management</h2>
            <p>Search accounts, inspect quota usage, and apply subscription changes.</p>
          </div>
        </div>

        <form className="customer-filters" onSubmit={applyFilters}>
          <input
            type="text"
            name="search"
            value={filters.search}
            onChange={handleFilterChange}
            placeholder="Search by username or email"
          />
          <select name="tier" value={filters.tier} onChange={handleFilterChange}>
            <option value="">All tiers</option>
            {TIER_OPTIONS.map((tier) => <option key={tier} value={tier}>{tier.toUpperCase()}</option>)}
          </select>
          <select name="status" value={filters.status} onChange={handleFilterChange}>
            <option value="">All statuses</option>
            {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
          <button type="submit">Apply filters</button>
        </form>

        <div className="customer-table-wrapper">
          <table className="customer-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th>Tier</th>
                <th>Status</th>
                <th>Signals</th>
                <th>API/hr</th>
                <th>Portfolio</th>
                <th>Support actions</th>
              </tr>
            </thead>
            <tbody>
              {!loading && customers.length === 0 && (
                <tr>
                  <td colSpan="7" className="empty-state">No customers matched the current filters.</td>
                </tr>
              )}
              {customers.map((customer) => {
                const signals = customer.usage?.signals_daily_limit === null
                  ? `${formatCount(customer.usage?.signals_used_today)} / unlimited`
                  : `${formatCount(customer.usage?.signals_used_today)} / ${formatCount(customer.usage?.signals_daily_limit)}`
                const apiCalls = customer.usage?.api_calls_per_hour === null
                  ? `${formatCount(customer.usage?.api_calls_used_this_hour)} / unlimited`
                  : `${formatCount(customer.usage?.api_calls_used_this_hour)} / ${formatCount(customer.usage?.api_calls_per_hour)}`

                return (
                  <tr key={customer.user_id}>
                    <td>
                      <div className="customer-identity">
                        <strong>{customer.username}</strong>
                        <span>{customer.email || 'No email on file'}</span>
                        <small>{customer.is_admin ? 'Admin account' : `Created ${formatDate(customer.created_at)}`}</small>
                      </div>
                    </td>
                    <td>
                      <span className={`tier-badge tier-${customer.subscription?.tier}`}>{customer.subscription?.tier || 'free'}</span>
                    </td>
                    <td>
                      <span className={`status-badge status-${customer.subscription?.status}`}>{customer.subscription?.status || 'active'}</span>
                    </td>
                    <td>
                      <div className="usage-cell">
                        <strong>{signals}</strong>
                        <small>Reset {formatDate(customer.usage?.daily_reset_at)}</small>
                      </div>
                    </td>
                    <td>
                      <div className="usage-cell">
                        <strong>{apiCalls}</strong>
                        <small>Reset {formatDate(customer.usage?.hourly_reset_at)}</small>
                      </div>
                    </td>
                    <td>
                      <div className="usage-cell">
                        <strong>{formatCurrency(customer.portfolio?.cash)}</strong>
                        <small>{formatCount(customer.portfolio?.holdings_count)} holdings</small>
                      </div>
                    </td>
                    <td>
                      <div className="action-stack">
                        <select
                          value={customer.subscription?.tier || 'free'}
                          onChange={(event) => updateCustomer(customer, { tier: event.target.value })}
                          disabled={savingUserId === customer.user_id}
                        >
                          {TIER_OPTIONS.map((tier) => <option key={tier} value={tier}>{tier.toUpperCase()}</option>)}
                        </select>
                        <select
                          value={customer.subscription?.status || 'active'}
                          onChange={(event) => updateCustomer(customer, { status: event.target.value })}
                          disabled={savingUserId === customer.user_id}
                        >
                          {STATUS_OPTIONS.map((status) => <option key={status} value={status}>{status}</option>)}
                        </select>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="panel-card ad-section">
        <div className="panel-card-header">
          <div>
            <h2>Sponsored campaigns</h2>
            <p>Create PPC placements and fund them through Stripe.</p>
          </div>
          <button className="refresh-button" onClick={loadCampaigns} disabled={adsLoading}>
            {adsLoading ? 'Refreshing...' : 'Refresh campaigns'}
          </button>
        </div>

        {(campaignError || campaignSuccess) && (
          <div className={`admin-banner ${campaignError ? 'error' : 'success'}`}>
            {campaignError || campaignSuccess}
          </div>
        )}

        <form className="ad-campaign-form" onSubmit={createCampaign}>
          <input name="title" value={campaignForm.title} onChange={handleCampaignFieldChange} placeholder="Campaign title" required />
          <input name="url" value={campaignForm.url} onChange={handleCampaignFieldChange} placeholder="Landing page URL" required />
          <textarea name="description" value={campaignForm.description} onChange={handleCampaignFieldChange} placeholder="Short ad description" rows="3" required />
          <input name="image" value={campaignForm.image} onChange={handleCampaignFieldChange} placeholder="Optional image URL" />
          <div className="ad-campaign-grid">
            <input name="placement" value={campaignForm.placement} onChange={handleCampaignFieldChange} placeholder="Placement (home)" />
            <input name="sponsor_name" value={campaignForm.sponsor_name} onChange={handleCampaignFieldChange} placeholder="Sponsor name" />
            <label>
              CPC cents
              <input name="cpc_cents" type="number" min="1" value={campaignForm.cpc_cents} onChange={handleCampaignFieldChange} />
            </label>
            <label>
              Budget cents
              <input name="budget_cents" type="number" min="1" value={campaignForm.budget_cents} onChange={handleCampaignFieldChange} />
            </label>
          </div>
          <button type="submit" disabled={savingCampaignId === 'create'}>
            {savingCampaignId === 'create' ? 'Creating campaign...' : 'Create campaign and open Stripe'}
          </button>
        </form>

        <div className="campaign-list">
          {campaigns.map((campaign) => (
            <article className="campaign-card" key={campaign.id}>
              <div className="campaign-card-top">
                <div>
                  <strong>{campaign.title}</strong>
                  <p>{campaign.description}</p>
                </div>
                <span className={`campaign-status status-${campaign.status}`}>{campaign.status}</span>
              </div>
              <div className="campaign-metrics">
                <span>Placement: {campaign.placement}</span>
                <span>CPC: ${((campaign.cpc_cents || 0) / 100).toFixed(2)}</span>
                <span>Budget: ${((campaign.budget_cents || 0) / 100).toFixed(2)}</span>
                <span>Remaining: ${((campaign.remaining_budget_cents || 0) / 100).toFixed(2)}</span>
                <span>Clicks: {campaign.clicks || 0}</span>
              </div>
            </article>
          ))}
          {!adsLoading && campaigns.length === 0 && (
            <div className="empty-state">No campaigns found yet.</div>
          )}
        </div>
      </section>
    </div>
  )
}

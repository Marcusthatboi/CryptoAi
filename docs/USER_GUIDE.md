# User Guide

This guide helps end users register, log in, explore the dashboard, and manage subscriptions.

## 1) Getting Started

### Create account
1. Open login page.
2. Click register.
3. Enter username, email (optional), and password.
4. Submit registration to receive an authenticated session.

### Log in
1. Enter username/password.
2. On success, you are redirected to dashboard.

## 2) Dashboard Features

Main dashboard sections:
- Subscription status
- Market stats
- AI recommendations
- Portfolio panel
- Investments panel with live profit/loss
- Price cards
- Alerts panel
- Chat assistant

## 3) Portfolio and Investments

You can:
- view available cash
- view holdings and performance
- invest via fake-money or real-money lanes (when configured)
- open investment detail pages from holdings

Live updates:
- dashboard uses shared WebSocket connection for realtime price updates
- portfolio refresh cadence includes periodic REST sync

## 4) AI Features

### Chat assistant
- ask about crypto prices, trends, and summaries
- endpoint may return 429 when request rate is exceeded

### Recommendations
- recommendations are tier-aware
- free tier can hit daily and hourly limits
- responses include usage/reset metadata when available

## 5) Subscription and Billing

Open Pricing page to compare tiers.

Tier summary:
- Free: basic tracking and limited AI usage
- Pro: expanded signals/alerts/history
- Premium: highest limits and advanced analytics

Upgrade flow:
1. choose plan on Pricing page
2. checkout modal opens
3. pay by card or wallet flow (including Apple Pay QR where supported)
4. after successful payment, plan is upgraded

## 6) Account and Session Behavior

- your JWT token is stored in browser local storage
- expired/invalid tokens trigger redirect to login
- protected routes require active authentication

## 7) Troubleshooting

### Cannot log in / connection refused
- backend is likely not running on `localhost:8002`
- start backend and retry

### Realtime disconnected (`/ws` errors)
- backend WebSocket endpoint unavailable
- check backend health (`/health`) and retry

### Upgrade did not reflect immediately
- refresh pricing/subscription sections
- verify webhook processing and backend availability

### Too many requests
- wait for `Retry-After` duration if provided
- reduce request burst frequency

## 8) Safety Notes

- do not treat AI recommendations as financial advice
- use real-money trading features cautiously
- secure your credentials and avoid shared devices

## 9) Support Contacts

For billing, upgrade, account access, or technical issues:
- open the Pricing page and use the Contact Support email link
- or use the support email shown in the dashboard footer

When contacting support, include:
- username/account email
- time of issue and timezone
- what action failed (checkout, login, upgrade, portfolio load, etc.)
- screenshot of any visible error message

## 10) Collaboration Integrations

You can share AI analysis directly from recommendation cards to collaboration platforms:
- Slack
- Microsoft Teams
- Google Chat (Google Workspace)

How to use:
1. Open AI recommendations.
2. Choose a recommendation card.
3. Click Slack, Teams, or Google Chat in the Send to actions.

If sharing fails, your workspace webhook URL for that platform is likely not configured.

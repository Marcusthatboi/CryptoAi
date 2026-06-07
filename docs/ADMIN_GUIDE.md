# Admin Guide

This guide explains how to operate the admin surface for subscriptions, customer support, and quota monitoring.

## 1) Admin Access Model

Admin UI route:
- `/admin` in frontend

Admin API protection:
- Backend enforces admin access for admin-only endpoints.
- Admin is recognized by one of:
  - `is_admin: true`
  - `role: "admin"`
  - username fallback (`admin`) for legacy compatibility

## 2) Admin Dashboard Overview

The admin dashboard includes:
- Subscription mix metrics
- Usage pressure metrics (signals + API calls)
- Customer management table with filters
- Inline customer subscription update actions

Primary data sources:
- `GET /api/subscription/analytics/overview`
- `GET /api/admin/customers`
- `PATCH /api/admin/customers/{user_id}/subscription`

## 3) Customer Management Workflows

### Find customers
Use filter controls:
- Search by username/email
- Filter by tier
- Filter by status
- Limit result size

### Update customer plan
From a customer row:
- Change tier (`free`, `pro`, `premium`)
- Change status (`active`, `cancelled`, `expired`)

Support notes:
- Tier and status updates are immediate at database level.
- Cancelled status sets `cancel_at_period_end` behavior in the subscription record.

### Verify quota state
For each customer, review:
- signals used vs daily limit
- API calls used vs hourly limit
- next reset timestamps

## 4) Subscription Analytics Interpretation

Key fields in overview payload:
- `subscriptions.by_tier`
- `subscriptions.active_paid`
- `usage.signals.total_generated`
- `usage.signals.limit_hits`
- `usage.api.total_calls`
- `usage.api.limit_hits`

How to use it:
- rising `limit_hits` on free tier indicates upgrade pressure and potential UX friction
- high API usage concentration can require tighter rate controls or caching

## 5) Billing Operations

Billing lifecycle endpoints:
- create payment intent
- create checkout session
- upgrade subscription
- cancel subscription
- webhook sync

Admin responsibility:
- ensure Stripe keys are configured correctly
- monitor webhook processing success
- reconcile support tickets where checkout succeeded but tier did not update

## 6) Security and Compliance Checklist for Admins

- Never share admin credentials.
- Use strong unique passwords and rotate regularly.
- Keep environment secrets out of source control.
- Restrict production dashboard access by network and identity controls.
- Audit admin actions through logs and change history.

## 7) Troubleshooting

### Dashboard shows no data
- confirm backend is running on port 8002
- verify admin account metadata (`is_admin` / `role`)
- inspect browser network responses for 401/403/500

### Customer update fails
- check request payload values for valid tier/status enums
- ensure target user exists
- inspect backend logs for Mongo or validation errors

### WebSocket failures while viewing admin
- admin dashboard itself is primarily REST-driven; realtime issues usually indicate backend availability problems

## 8) Operational Best Practices

- Review quota pressure daily.
- Review active paid counts weekly.
- Keep Stripe webhook events monitored continuously.
- Use staged changes for subscription policy updates.

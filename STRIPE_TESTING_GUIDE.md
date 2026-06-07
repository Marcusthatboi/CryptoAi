# 🧪 Stripe Testing Guide

Complete reference for testing your subscription system in development.

---

## Test Cards

Use these cards in **test mode** (when using `sk_test_` and `pk_test_` keys).

### ✅ Successful Payment Cards

| Card Number | Brand | Expected Result |
|------------|-------|-----------------|
| `4242 4242 4242 4242` | Visa | ✅ Payment succeeds |
| `5555 5555 5555 4444` | Mastercard | ✅ Payment succeeds |
| `3782 822463 10005` | American Express | ✅ Payment succeeds |
| `6011 1111 1111 1117` | Discover | ✅ Payment succeeds |

### ❌ Test Decline Cards

| Card Number | Reason | Use Case |
|------------|--------|----------|
| `4000 0000 0000 0002` | Generic decline | Test error handling |
| `4000 0000 0000 0069` | Expired card | Test expired card handling |
| `4000 0000 0000 0127` | Lost card | Test fraud prevention |
| `4000 0000 0000 0341` | Authentication required | Test 3D Secure |

### 🎯 Always Use:

- **Any future expiry date**: `12/25`, `06/26`, etc.
- **Any 3-digit CVC**: `123`, `999`, etc.
- **Any valid email**: `test@example.com`

---

## Test Scenarios

### Scenario 1: Basic Subscription

**Goal**: Create a free user and upgrade to Pro

#### Steps:
1. Sign up with test email: `testuser@example.com`
2. Navigate to `/pricing`
3. Click "Upgrade to Pro"
4. Enter card: `4242 4242 4242 4242`
5. Submit payment

#### Expected:
- ✅ Payment processes without errors
- ✅ Status updates to "Pro"
- ✅ Dashboard shows "Pro Plan"
- ✅ Renewal date displayed

---

### Scenario 2: Premium Upgrade

**Goal**: Test upgrading from Pro to Premium

#### Steps:
1. Have existing Pro subscription
2. Go to `/pricing`
3. Click "Upgrade to Premium"
4. Complete payment with `5555 5555 5555 4444`

#### Expected:
- ✅ Upgrade succeeds
- ✅ New price charged ($29.99 instead of $9.99)
- ✅ Tier changes to "Premium"
- ✅ Premium features now visible

---

### Scenario 3: Payment Decline

**Goal**: Test error handling

#### Steps:
1. Go to `/pricing`
2. Click "Upgrade to Pro"
3. Use card: `4000 0000 0000 0002` (decline)
4. Try to submit

#### Expected:
- ✅ Clear error message: "Your card was declined"
- ✅ User can retry with different card
- ✅ Subscription not created
- ✅ User stays on Free tier

---

### Scenario 4: Multiple Users

**Goal**: Test concurrent subscriptions

#### Steps:
1. Sign up as User 1: `user1@example.com`
   - Upgrade to Pro
2. Sign up as User 2: `user2@example.com`
   - Upgrade to Premium
3. Sign up as User 3: `user3@example.com`
   - Stay on Free

#### Expected:
- ✅ Each user has separate subscription
- ✅ Dashboard shows correct tier for each
- ✅ Database has 3 subscription records

---

### Scenario 5: Cancellation

**Goal**: Test downgrading subscription

#### Steps:
1. Have Pro/Premium subscription
2. Click "Manage Plan" on dashboard
3. Click "Cancel Subscription"
4. Confirm

#### Expected:
- ✅ Subscription cancelled
- ✅ Tier reverts to Free
- ✅ Dashboard updates
- ✅ Current period still active (if mid-billing)

---

## Stripe Dashboard Checks

### View Test Payments

1. Log into https://dashboard.stripe.com
2. Go to **Payments** section
3. Should see test charges from your tests
4. Each should show:
   - Amount ($9.99 or $29.99)
   - Card used (Visa, Mastercard, etc.)
   - Status: Succeeded/Failed

### View Test Customers

1. Go to **Customers** section
2. Should see customers created during tests
3. Each customer should have:
   - Email
   - Payment methods
   - Subscriptions

### View Test Subscriptions

1. Go to **Subscriptions** section
2. Should see active/inactive subscriptions
3. Each should show:
   - Customer
   - Plan (Pro/Premium)
   - Status
   - Next billing date

---

## Testing Checklist

Complete these tests before launching:

### Payment Processing
- [ ] Successful payment with Visa card
- [ ] Successful payment with Mastercard
- [ ] Declined card shows error message
- [ ] Expired card shows error message
- [ ] User can retry after decline
- [ ] Amount charged is correct ($9.99 or $29.99)

### Subscription State
- [ ] Free tier user can upgrade
- [ ] Pro user can upgrade to Premium
- [ ] Premium user can't upgrade further (or show placeholder)
- [ ] User tier updates in database
- [ ] User tier updates on dashboard
- [ ] Renewal date calculated correctly

### User Experience
- [ ] Pricing page loads fast
- [ ] Payment form is clear
- [ ] Error messages are helpful
- [ ] Success feedback given
- [ ] Dashboard updates immediately
- [ ] Mobile responsive works

### Data Integrity
- [ ] Subscription saved in MongoDB
- [ ] Stripe customer created
- [ ] Subscription linked to user
- [ ] Email saved with subscription
- [ ] Tier saved correctly
- [ ] Status saved correctly

### Edge Cases
- [ ] Same user upgrades twice (updates subscription)
- [ ] Same email different users (separate accounts)
- [ ] Network latency (retry works)
- [ ] Double-click upgrade (doesn't create duplicate)
- [ ] Session expires during payment (user redirected)

---

## Common Test Data

### Test Users

```javascript
// User 1: Free
{
  email: "free@example.com",
  password: "Test123!",
  tier: "free"
}

// User 2: Pro
{
  email: "pro@example.com",
  password: "Test123!",
  tier: "pro",
  stripe_customer_id: "cus_123456",
  current_period_end: "2024-02-01"
}

// User 3: Premium
{
  email: "premium@example.com",
  password: "Test123!",
  tier: "premium",
  stripe_customer_id: "cus_789012",
  current_period_end: "2024-02-15"
}
```

### Test Prices

```python
{
  "free": {
    "amount": 0,
    "currency": "usd",
    "interval": "month"
  },
  "pro": {
    "amount": 999,  # $9.99 in cents
    "currency": "usd",
    "interval": "month"
  },
  "premium": {
    "amount": 2999,  # $29.99 in cents
    "currency": "usd",
    "interval": "month"
  }
}
```

---

## Debugging Tips

### Check Payment Intent

When payment form doesn't work:

1. Open browser DevTools (F12)
2. Go to **Network** tab
3. Look for request to `/api/subscription/create-payment-intent`
4. Check response for errors
5. Verify `client_secret` returned

### Check Subscription API

Test the API directly:

```bash
# Get pricing plans
curl http://localhost:8002/api/subscription/pricing/plans

# Get user subscription (with token)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8002/api/subscription/status

# Check MongoDB
mongo
> use crypto_ai
> db.subscriptions.find()
```

### Check Stripe Logs

1. Go to https://dashboard.stripe.com/logs
2. Look for API requests
3. Check for errors or warnings
4. Verify payment method accepted

---

## Simulating Webhook Events (Optional)

For testing cancellations and renewals:

1. Go to https://dashboard.stripe.com
2. Click **Developers** → **Webhooks**
3. Click **Add an endpoint**
4. Enter your webhook URL: `http://localhost:8002/api/subscription/webhook/stripe`
5. Subscribe to events:
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
6. Use "Send test event" to simulate

---

## Performance Testing

### Test High Load

```python
# Create multiple test users quickly
import requests

for i in range(100):
    # Register user
    # Upgrade to Pro
    # Measure response time
```

### Expected Times
- Pricing page load: < 500ms
- Payment form render: < 1s
- Payment processing: 1-3s
- Dashboard update: < 500ms

---

## Security Testing

### Test Authorization

- [ ] Can't access status without token
- [ ] Can't upgrade other user's subscription
- [ ] Can't use invalid token
- [ ] Token expiration works

### Test Data Privacy

- [ ] Payment info never logged
- [ ] Stripe keys not in code
- [ ] Email not exposed in API
- [ ] Only user can see their subscription

---

## Before Going Live

1. [ ] All test scenarios pass
2. [ ] Error handling works
3. [ ] Database has test data cleaned
4. [ ] Logs reviewed for errors
5. [ ] Mobile tested on real device
6. [ ] Payment times acceptable
7. [ ] SSL certificate ready (for production)
8. [ ] Stripe live keys obtained
9. [ ] Production environment set up

---

## Quick Command Reference

```bash
# Test stripe key validity
curl https://api.stripe.com/v1/charges \
  -u sk_test_YOUR_KEY: \
  -d amount=100 \
  -d currency=usd \
  -d source=tok_visa

# View test database
mongodump --out /backup --db crypto_ai

# Clear test data
mongo --eval "db.dropDatabase()" crypto_ai

# Restart services
pkill -f "uvicorn"
cd frontend && npm run dev &
python -m uvicorn backend.main:app --reload
```

---

## 🎯 You're Ready to Test!

Use these tools and scenarios to thoroughly test before launch.

**Remember**: Test mode is separate from production. Test freely without charging real money! 💰

# 💰 CryptoAI Subscription & Monetization System

## Overview

This implementation adds a **Subscription Tier System** with Stripe integration to turn your CryptoAI platform into a profitable SaaS. Users can access premium features by upgrading from Free → Pro → Premium tiers.

---

## 📋 What Was Created

### Backend Components

1. **`backend/subscription.py`** - Core subscription logic
   - Subscription tier definitions (Free, Pro, Premium)
   - Stripe integration for payment processing
   - Database operations for managing subscriptions
   - Feature access control utilities
   - Usage quota management

2. **`backend/subscription_routes.py`** - API endpoints
   - `GET /api/subscription/pricing/plans` - Get all pricing plans
   - `GET /api/subscription/benefits/{tier}` - Get tier benefits
   - `GET /api/subscription/status` - Get user's subscription (requires auth)
   - `POST /api/subscription/create-payment-intent` - Create payment (requires auth)
   - `POST /api/subscription/upgrade` - Upgrade subscription (requires auth)
   - `POST /api/subscription/cancel` - Cancel subscription (requires auth)
   - `POST /api/subscription/webhook/stripe` - Stripe webhook handler

### Frontend Components

1. **`frontend/src/pages/PricingPage.jsx`** & **`PricingPage.css`**
   - Full pricing page with all three tiers
   - Plan comparison table
   - FAQ section
   - Upgrade/downgrade buttons

2. **`frontend/src/components/SubscriptionStatus.jsx`** & **`SubscriptionStatus.css`**
   - Dashboard subscription status widget
   - Shows current tier, renewal date, benefits
   - Quick upgrade button
   - Plan management link

---

## 🔧 Integration Steps

### Step 1: Update Requirements

Already done! `stripe>=7.0.0` has been added to `requirements.txt`

Install the dependency:
```bash
pip install stripe
```

### Step 2: Environment Setup

Add these to your `.env` file:

```env
# Stripe Keys (get from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here

# Optional: Webhook Secret (for production)
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
```

### Step 3: Update Backend Main App

Add subscription routes to `backend/main.py`:

```python
# At the top with other imports
from backend.subscription_routes import router as subscription_router
from backend.subscription import init_subscription_collection

# In the FastAPI app setup (around line 100+)
app.include_router(subscription_router)

# In the startup event
@app.on_event("startup")
async def startup_event():
    db = await get_db()
    await init_subscription_collection(db)
    logger.info("✅ Subscription collection initialized")
```

### Step 4: Add to Frontend Navigation

Update `frontend/src/App.jsx` to add the pricing page route:

```jsx
import PricingPage from './pages/PricingPage'

// In your router setup:
<Route path="/pricing" element={<PricingPage />} />
```

### Step 5: Add Subscription Status to Dashboard

Update `frontend/src/components/UserInvestmentsPanel.jsx`:

```jsx
import SubscriptionStatus from './SubscriptionStatus'

// In the render:
export default function UserInvestmentsPanel() {
  return (
    <div className="user-investments-panel">
      <SubscriptionStatus />
      {/* Rest of component */}
    </div>
  )
}
```

---

## 💳 Stripe Setup for Development

1. **Create Stripe Account**: https://stripe.com
2. **Get API Keys**:
   - Go to https://dashboard.stripe.com/apikeys
   - Copy Test Publishable Key and Test Secret Key
   - Add to `.env`

3. **Create Products (Optional for testing)**:
   - Dashboard → Products
   - Create products for Pro ($9.99/mo) and Premium ($29.99/mo)
   - Copy the `price_xxx` IDs to `SUBSCRIPTION_PLANS` in `subscription.py`

4. **Test Mode**:
   - Use test card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any CVC

---

## 🎯 Subscription Tiers Breakdown

### Free Plan
- **Price**: $0/month
- **Signals/Day**: 10
- **Features**: Basic tracking, general recommendations
- **Alerts**: No
- **History**: None

### Pro Plan ($9.99/month)
- **Signals/Day**: 100
- **Features**: Advanced signals, real-time alerts, confidence scoring
- **Signal History**: 30 days
- **Alerts**: 20/day limit
- **Portfolio Optimization**: Yes

### Premium Plan ($29.99/month)
- **Signals/Day**: Unlimited
- **Features**: All Pro features +
- **Signal History**: 1 year
- **Alerts**: Unlimited
- **Early Access**: New features first
- **Priority Support**: Yes
- **Performance Analytics**: Yes

---

## 🔐 Feature Access Control

### In Backend

Use the access control functions in `subscription.py`:

```python
from backend.subscription import check_feature_access, has_quota_available

# Check if tier has feature
if not check_feature_access(user_tier, "alerts"):
    raise HTTPException(status_code=403, detail="Feature not available in your plan")

# Check usage quota
if not has_quota_available(user_tier, signal_count, "signals_per_day"):
    raise HTTPException(status_code=429, detail="Daily signal limit reached")
```

### In Frontend

Conditionally show features:

```jsx
import { useAuth } from '../hooks/useAuth'

function AdvancedFeature() {
  const { user } = useAuth()
  const [subscription, setSubscription] = useState(null)

  useEffect(() => {
    if (user?.user_id && token) {
      fetchSubscription()
    }
  }, [user, token])

  if (!subscription) return null

  // Show alert settings only for Pro+
  if (subscription.tier === 'pro' || subscription.tier === 'premium') {
    return <AlertSettings />
  }

  // Show upgrade prompt
  return <UpgradePrompt feature="Real-time Alerts" />
}
```

---

## 📊 Revenue Model

### Monthly Recurring Revenue (MRR)

**Formula**: (Pro Users × $9.99) + (Premium Users × $29.99)

**Example Projections**:
- 100 Pro + 50 Premium users = **$2,496/month**
- 500 Pro + 200 Premium users = **$10,480/month**
- 1000 Pro + 500 Premium users = **$24,960/month**

### Stripe Fees
- Standard: 2.9% + $0.30 per transaction
- Example: $9.99 transaction = $9.40 to you

---

## 🚀 Next Steps to Complete Implementation

1. **Set Stripe Environment Variables** in your `.env`
2. **Add subscription routes to backend** main.py
3. **Add pricing page route** to frontend App.jsx
4. **Add SubscriptionStatus widget** to dashboard
5. **Test the flow**:
   - Navigate to `/pricing`
   - Click upgrade to Pro
   - Use test Stripe card `4242 4242 4242 4242`
   - Verify subscription updates in dashboard
6. **Set Stripe webhook** in production (optional now)

---

## 🧪 Testing Checklist

- [ ] Pricing page loads with all 3 tiers visible
- [ ] Free tier is marked as current for new users
- [ ] Upgrade button opens payment modal
- [ ] Stripe payment succeeds with test card
- [ ] Subscription status updates to Pro/Premium
- [ ] SubscriptionStatus widget shows on dashboard
- [ ] Feature gating works (Pro features hidden on Free tier)
- [ ] Alerts show usage quotas
- [ ] Cancel subscription downgrades to Free

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| `backend/subscription.py` | Core subscription logic & Stripe |
| `backend/subscription_routes.py` | API endpoints |
| `frontend/src/pages/PricingPage.jsx` | Pricing page UI |
| `frontend/src/components/SubscriptionStatus.jsx` | Dashboard widget |
| `requirements.txt` | Dependencies (Stripe added) |

---

## 💡 Future Enhancements

1. **Performance-Based Commission**
   - Track user profits from trades
   - Earn 1-3% commission on realized gains
   - Display in dashboard analytics

2. **Signal Confidence Scoring**
   - Pro tier gets 0-100% confidence scores
   - Premium gets early access to high-confidence signals

3. **Affiliate Program**
   - Referral links to exchanges (Binance, Kraken)
   - Earn from user trades through referrals
   - Display referral earnings on dashboard

4. **API Access Tier**
   - Allow developers to access your signals via API
   - Price based on request volume
   - Create B2B revenue stream

5. **Annual Billing Discount**
   - Annual Pro: $99/year (vs $120 monthly) = 17% savings
   - Annual Premium: $299/year (vs $360 monthly) = 17% savings
   - Increase LTV (Lifetime Value)

---

## 🆘 Troubleshooting

**Stripe key not working?**
- Verify keys are in `.env` with correct prefix (sk_test_ or sk_live_)
- Restart Python server after adding .env

**Payment intent fails?**
- Check Stripe Dashboard for error logs
- Ensure customer email is valid
- Verify amount is in cents (9.99 = 999)

**Subscription not updating?**
- Check MongoDB connection is active
- Verify subscription collection was initialized
- Check auth token is valid

---

## 📞 Support

For issues with:
- **Stripe Integration**: https://stripe.com/docs
- **Backend**: Check `backend/subscription.py` and `subscription_routes.py`
- **Frontend**: Check React components and auth hooks

---

## ✅ Implementation Status

- ✅ Backend subscription system created
- ✅ Stripe integration setup
- ✅ API endpoints created
- ✅ Frontend pricing page created
- ✅ Subscription status widget created
- ✅ Feature access control utilities ready
- ⏳ **Next**: Integrate into main app and test

**Ready to make money from your users! 💰**

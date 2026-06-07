# 🔌 Integration Code Snippets

Use these exact code snippets to wire up the subscription system into your main app.

---

## 1️⃣ Backend Integration (`backend/main.py`)

### Add Import at Top

```python
from backend.subscription_routes import router as subscription_router
from backend.subscription import init_subscription_collection
```

### Add Router to App

Add this line after all other `app.include_router()` calls:

```python
# Subscription management routes
app.include_router(subscription_router)
```

### Initialize Subscription Collection on Startup

Find your startup event (or create one) and add:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("🚀 Server starting up...")
    
    # Initialize database
    db = await get_db()
    
    # ✅ ADD THIS LINE:
    await init_subscription_collection(db)
    
    logger.info("✅ Subscription collection initialized")
```

### Complete Example of Router Setup

```python
# Line ~50-70 (adjust for your file)
app.include_router(router)  # Your existing routes
app.include_router(recommendations_router)  # Other routers...

# ✅ ADD THIS:
app.include_router(subscription_router)  # Subscription routes
```

---

## 2️⃣ Frontend Integration (`frontend/src/App.jsx`)

### Add Import at Top

```jsx
import PricingPage from './pages/PricingPage'
```

### Add Route in Router

In your router setup (usually around line 40+), add:

```jsx
<Route path="/pricing" element={<PricingPage />} />
```

### Complete Example

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import PricingPage from './pages/PricingPage'  // ✅ ADD THIS

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/portfolio" element={<Portfolio />} />
        <Route path="/recommendations" element={<Recommendations />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/pricing" element={<PricingPage />} />  {/* ✅ ADD THIS */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
```

### Add Navigation Link

In your header/navbar component, add a link to pricing:

```jsx
<nav className="navbar">
  {/* Other links */}
  <a href="/pricing" className="nav-link">💰 Pricing</a>
</nav>
```

---

## 3️⃣ Dashboard Integration

### Add Subscription Status Widget

In `frontend/src/components/UserInvestmentsPanel.jsx`, add at the top of the component:

```jsx
import SubscriptionStatus from './SubscriptionStatus'

export default function UserInvestmentsPanel() {
  return (
    <div className="user-investments-panel">
      <SubscriptionStatus />  {/* ✅ ADD THIS LINE */}
      
      {/* Rest of your component... */}
      <div className="portfolio-stats">
        {/* existing content */}
      </div>
    </div>
  )
}
```

---

## 4️⃣ Environment Variables (`.env`)

Add to your `.env` file in project root:

```env
# ===============================
# Stripe Configuration
# ===============================
# Get these from: https://dashboard.stripe.com/apikeys

# Test Keys (use these for development)
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_SECRET_KEY_HERE
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_PUBLISHABLE_KEY_HERE

# Production keys (swap after testing)
# STRIPE_SECRET_KEY=sk_live_YOUR_LIVE_SECRET_KEY_HERE
# STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_LIVE_PUBLISHABLE_KEY_HERE

# Optional: Webhook signing secret
STRIPE_WEBHOOK_SECRET=whsec_YOUR_WEBHOOK_SECRET_HERE
```

### How to Get Stripe Keys

1. Go to https://dashboard.stripe.com
2. Sign in or create account
3. Click "Developers" → "API Keys"
4. Copy "Secret key" → paste as `STRIPE_SECRET_KEY`
5. Copy "Publishable key" → paste as `STRIPE_PUBLISHABLE_KEY`
6. Restart your backend server after adding `.env`

---

## 5️⃣ Test the Integration

### Run Backend
```bash
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8002
```

### Run Frontend
```bash
cd frontend
npm run dev
```

### Test Workflow

1. Open http://localhost:3002/pricing
2. Should see three pricing cards (Free, Pro, Premium)
3. Click "Upgrade to Pro" button
4. Should see payment form
5. Use test card: `4242 4242 4242 4242`
6. Fill any future expiry date, any CVC
7. Click submit
8. Should succeed and redirect to dashboard
9. Check subscription status on dashboard

---

## 🎯 Quick Checklist

After adding all code above:

- [ ] Stripe dependencies installed: `pip install stripe`
- [ ] Subscription routes added to main.py
- [ ] Init function called in startup event
- [ ] PricingPage route added to App.jsx
- [ ] Pricing page accessible at `/pricing`
- [ ] SubscriptionStatus widget visible on dashboard
- [ ] `.env` has Stripe keys
- [ ] Backend server restarted
- [ ] Frontend server restarted
- [ ] Test payment flow works

---

## 🚀 You're Ready!

Once all integrations complete, your monetization system is live! 💰

### What's Now Working:
✅ Users can view pricing at `/pricing`
✅ Users can upgrade with credit card
✅ Stripe processes payments securely
✅ Dashboard shows current subscription tier
✅ Ready for feature gating implementation

### Next Phase:
- [ ] Add feature gating to RecommendationsPanel
- [ ] Lock alerts behind Pro tier
- [ ] Enforce API rate limits by subscription
- [ ] Add usage tracking and notifications

---

## 📞 Common Issues & Fixes

**Issue**: "No module named subscription_routes"
- **Fix**: Make sure `backend/subscription_routes.py` exists
- **Fix**: Restart Python server after file creation

**Issue**: Stripe keys not loading
- **Fix**: Restart Python server after adding to `.env`
- **Fix**: Check `.env` is in project root, not in subdirectory
- **Fix**: Use correct format: `STRIPE_SECRET_KEY=sk_test_...`

**Issue**: "Cannot import subscription"
- **Fix**: Make sure both files exist:
  - `backend/subscription.py` ✅
  - `backend/subscription_routes.py` ✅
- **Fix**: Check import path matches your project structure

**Issue**: PricingPage not showing
- **Fix**: Verify route added to App.jsx
- **Fix**: Check browser console for errors
- **Fix**: Verify React Router is setup correctly

---

## 💾 Files You Should Have Now

```
backend/
├── main.py (UPDATE with routes)
├── subscription.py ✅
├── subscription_routes.py ✅
└── ... other files

frontend/src/
├── App.jsx (UPDATE with route)
├── components/
│   ├── SubscriptionStatus.jsx ✅
│   ├── SubscriptionStatus.css ✅
│   └── ... other components
├── pages/
│   ├── PricingPage.jsx ✅
│   ├── PricingPage.css ✅
│   └── ... other pages
└── ... other files

.env (UPDATE with Stripe keys)
requirements.txt (UPDATE with stripe package)
MONETIZATION_SETUP.md ✅
INTEGRATION_GUIDE.md ✅
```

---

**You've got this! 🚀**

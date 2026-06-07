# 🤖 AI Investment Recommendations Feature

## What's New

A **smart investment recommendation engine** that analyzes market data and provides AI-powered investment suggestions with risk assessments and allocation recommendations.

---

## Features

### 1. **AI-Powered Recommendations**
- Uses your local Ollama model to generate intelligent recommendations
- Falls back to smart pattern matching if Ollama is unavailable
- Analyzes market trends, momentum, and volatility

### 2. **Risk Assessment**
- Each recommendation gets a **LOW, MEDIUM, or HIGH** risk rating
- Considers price volatility and trend stability
- Overall portfolio risk level calculated

### 3. **Smart Allocation Suggestions**
- AI recommends allocation percentages for each asset
- Diversification strategy built-in
- Visual allocation bar for each recommendation

### 4. **Market Analysis Basis**
- Shows the reasoning behind recommendations
- Cites market trends and data points
- Transparent decision-making

### 5. **Real-Time Status**
- Live connection indicator (🟢 Live / 🔴 Connecting)
- Automatic refresh every 5 minutes
- Manual refresh button

---

## Component Structure

### Backend: `/api/recommendations`

```python
GET /api/recommendations?count=5
```

**Response:**
```json
{
  "status": "success",
  "recommendations": [
    {
      "symbol": "BTC",
      "reason": "UPTREND - Price change: +15.42%",
      "risk": "MEDIUM",
      "allocation": 20.0,
      "current_price": 73720.50,
      "trend": "UPTREND"
    }
  ],
  "reasoning": "Based on current market trends and analysis...",
  "risk_level": "MEDIUM",
  "timestamp": "2026-05-31T12:00:00"
}
```

### Frontend: `RecommendationsPanel.jsx`

```jsx
import RecommendationsPanel from './components/RecommendationsPanel'

export default function App() {
  return (
    <main>
      <RecommendationsPanel />
    </main>
  )
}
```

---

## How It Works

### Step 1: Data Analysis
- Backend loads historical price data
- Analyzes trends for each cryptocurrency using SMA (Simple Moving Average)
- Calculates price changes and volatility

### Step 2: AI Generation (if Ollama available)
- Sends market summary to Ollama AI model
- Model generates personalized recommendations
- Returns risk levels and allocation suggestions

### Step 3: Fallback Pattern Matching
- If Ollama unavailable, uses trend analysis
- Ranks cryptos by performance
- Assigns risk based on volatility
- Calculates fair allocations

### Step 4: Frontend Display
- Shows cards with symbol, reason, risk, and allocation
- Color-coded by risk level: 🟢 LOW, 🟡 MEDIUM, 🔴 HIGH
- Portfolio summary with diversification score
- Animated entry for visual appeal

---

## Visual Design

### Recommendation Card
```
┌─────────────────────────────────┐
│ BTC                  🟡 MEDIUM   │
│                                  │
│ UPTREND - Price change: +15.42% │
│ Current Price: $73,720.50       │
│ Trend: 📈 UPTREND              │
│                                  │
│ Allocation: [████░░░░░░] 20.0%  │
│ [Invest in BTC]                 │
└─────────────────────────────────┘
```

### Portfolio Summary
```
💼 Recommended Portfolio
├─ Total Assets: 5
├─ Portfolio Risk: MEDIUM
└─ Diversification: 100%
  [📊 Use This Allocation]
```

---

## Risk Level Indicators

| Risk | Color | Volatility | Suitable For |
|------|-------|-----------|--------------|
| 🟢 LOW | Green | < 5% | Conservative investors |
| 🟡 MEDIUM | Orange | 5-15% | Balanced portfolio |
| 🔴 HIGH | Red | > 15% | Risk-tolerant traders |

---

## Configuration

### Backend Settings

```python
# In main.py:
@app.get("/api/recommendations")
async def get_ai_recommendations(count: int = 5):
    # Customize:
    count = min(count, 10)  # Max 10 recommendations
    # SMA window for trend analysis: 5 days
    # Risk calculation based on price volatility
```

### Frontend Settings

```jsx
// In RecommendationsPanel.jsx:
const fetchRecommendations = async () => {
  // Refresh interval: 300000ms = 5 minutes
  // Max recommendations shown: 5
  const response = await cryptoAPI.getRecommendations(5)
}
```

---

## API Integration

### Add to Your API Client

```javascript
// In frontend/src/utils/api.js
export const cryptoAPI = {
  // ... other methods ...
  
  // Recommendations endpoint
  getRecommendations: (count = 5) => 
    api.get('/api/recommendations', { params: { count } }),
}
```

### Call It

```javascript
import { cryptoAPI } from './utils/api'

// Get 5 recommendations
const response = await cryptoAPI.getRecommendations(5)
console.log(response.data.recommendations)
```

---

## Files Created/Modified

| File | Status | Changes |
|------|--------|---------|
| `backend/main.py` | ✅ Updated | Added `/api/recommendations` endpoint |
| `frontend/src/components/RecommendationsPanel.jsx` | ✅ New | Main recommendation component |
| `frontend/src/components/RecommendationsPanel.css` | ✅ New | Styling with animations |
| `frontend/src/utils/api.js` | ✅ Updated | Added `getRecommendations()` method |
| `frontend/src/App.jsx` | ✅ Updated | Imported & added RecommendationsPanel |

---

## Example Workflow

### 1. User Opens Dashboard
```
✅ Backend loads crypto price data
✅ Analyzes trends using SMA
✅ Generates AI recommendations
✅ Frontend fetches and displays
```

### 2. User Sees Recommendations
```
🤖 5 AI-recommended cryptocurrencies
🎯 Each with risk level and allocation
📊 Total portfolio risk displayed
💡 Reasoning shown for transparency
```

### 3. User Takes Action
```
💾 Can save allocation preferences (future)
💳 Can place orders directly (future)
⏰ Recommendations auto-refresh every 5 min
🔄 Manual refresh available
```

---

## Disclaimer

⚠️ **Important**: These AI recommendations are for **educational purposes only**.

- Always conduct your own research
- Consult with financial advisors before investing
- Past performance ≠ future results
- Start with small amounts for testing
- Never invest money you can't afford to lose

---

## Testing

### Verify Backend Endpoint

```bash
# Get 5 recommendations
curl "http://localhost:8000/api/recommendations?count=5"

# Expected response:
# {
#   "status": "success",
#   "recommendations": [...],
#   "reasoning": "...",
#   "risk_level": "MEDIUM"
# }
```

### Verify Frontend Component

```javascript
// In browser console:
const { data } = await fetch('http://localhost:8000/api/recommendations').then(r => r.json())
console.log(data)
```

---

## Next Features (Future)

✨ Possible enhancements:

1. **Save Allocations** - Store recommended allocations in MongoDB
2. **One-Click Invest** - Place orders directly from recommendations
3. **Backtesting** - Test recommendations against historical data
4. **Custom Preferences** - "I like more risk" / "I want stable"
5. **Notifications** - Alert when recommendation changes
6. **Comparison** - See how past recommendations performed
7. **Sector Allocation** - Balance across crypto types
8. **Dollar Cost Averaging** - Suggested buy schedule

---

## Troubleshooting

### No Recommendations Showing?
```
✅ Check: Price data refreshed?
✅ Check: Backend endpoint /api/recommendations?count=5
✅ Check: Frontend API method getRecommendations() exists
```

### AI Recommendations Not Working?
```
✅ Ollama might be offline → Falls back to pattern matching
✅ Check Ollama status: GET /api/ollama/status
✅ Ensure model available: mistral, neural-chat, llama2
```

### Wrong Risk Levels?
```
✅ Risk calculated from price volatility
✅ Adjust risk thresholds in alpaca_api.py if needed
✅ LOW < 5%, MEDIUM 5-15%, HIGH > 15%
```

---

**Ready to invest smarter with AI!** 🚀

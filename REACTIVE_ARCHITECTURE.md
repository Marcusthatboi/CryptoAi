# MongoDB + WebSocket Real-Time Architecture

## Overview
Your system now has three layers for better reactivity:

```
┌─────────────────┐
│  React Frontend │ ← Real-time updates via WebSocket
├─────────────────┤
│  FastAPI Server │ ← Caching + Broadcasting
├─────────────────┤
│    MongoDB      │ ← Persistent storage
│   + Alpaca API  │
└─────────────────┘
```

## What MongoDB Stores

| Collection | Purpose | Retention |
|-----------|---------|-----------|
| `prices` | Cached price history | 30 days |
| `orders` | Executed orders | Lifetime |
| `trades` | Trade logs | Lifetime |
| `portfolio` | Account snapshots | 90 days |
| `alerts` | Price alerts | Lifetime |
| `settings` | User preferences | Lifetime |

## Real-Time Features

### 1. Price Updates
```javascript
// Frontend subscribes to symbol updates
subscribe('BTC')

// Backend broadcasts price changes every 5 seconds
broadcast_price_update('BTC', {bid: 73720, ask: 73774})
```

### 2. Account Updates
```javascript
// Auto-refresh every 30 seconds
// Or push when orders fill

broadcast_account_update({
  equity: 100000,
  buying_power: 200000,
  cash: 50000
})
```

### 3. Order Notifications
```javascript
// Instant notification when order status changes
broadcast_order_update({
  id: 'order-123',
  status: 'filled',
  symbol: 'AAPL'
})
```

## Setup Instructions

### Step 1: Install MongoDB
```bash
# Windows: Download from https://www.mongodb.com/try/download/community
# Or install via chocolatey:
choco install mongodb-community

# Start MongoDB service
mongod
```

### Step 2: Dependencies Already Installed
```bash
# Already added to requirements.txt:
# - pymongo: MongoDB driver
# - motor: Async MongoDB for FastAPI
# - websockets: WebSocket support
```

### Step 3: Environment Configuration
```bash
# Already in .env:
MONGODB_URL=mongodb://localhost:27017
DB_NAME=cryptoai
```

### Step 4: Update Backend (In Progress)
You need to:
1. Import db.py and data_service.py in main.py
2. Add WebSocket endpoint: `/ws`
3. Add startup/shutdown events for MongoDB
4. Update endpoints to use data_service for caching

### Step 5: Update Frontend
```bash
# Install WebSocket hook (already created)
import { useWebSocket } from './hooks/useWebSocket'

# Use in components:
const { isConnected, message, subscribe } = useWebSocket()
```

## Example Usage

### Frontend Component
```jsx
import { useWebSocket } from '../hooks/useWebSocket'

export function PriceUpdater() {
  const { isConnected, message } = useWebSocket()

  useEffect(() => {
    if (isConnected) {
      console.log('✅ Connected to real-time updates')
    }
  }, [isConnected])

  useEffect(() => {
    if (message?.type === 'price_update') {
      console.log(`${message.symbol}: $${message.data.last_price}`)
    }
  }, [message])

  return <div>{isConnected ? '🟢 Live' : '🔴 Offline'}</div>
}
```

### Backend Integration
```python
# In main.py:
from backend.websocket_manager import manager
from backend.data_service import data_service

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.handle_client(websocket)

# Broadcast updates:
await manager.broadcast_account_update(account_data)
await manager.broadcast_price_update('BTC', price_data)
```

## Next Steps

1. **Install MongoDB**: Download and run locally
2. **Integrate WebSocket in Backend**: Add `/ws` endpoint to main.py
3. **Update Components**: Add real-time listeners to React components
4. **Add Caching**: Update endpoints to use data_service
5. **Auto-Refresh**: Set intervals for account/price updates

## Benefits

✅ **Faster UI Updates**: WebSocket instead of polling
✅ **Historical Data**: MongoDB caches all prices/orders
✅ **Better Performance**: Don't re-fetch from Alpaca every time
✅ **Notifications**: Real-time order fills and price alerts
✅ **Scalable**: Database-backed instead of in-memory

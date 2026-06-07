# Portfolio Persistence Debug Guide

## Problem Statement
Investment shows success message on frontend ("✅ Fake money investment recorded!") but portfolio balance doesn't decrease and investment doesn't appear after page refresh.

---

## Quick Diagnostic Checklist

### Step 1: Verify Backend Logs (FIRST)
```bash
# Check terminal where backend is running
# Look for these log messages:

# Expected on investment:
"✅ Fake money investment recorded for user admin: BITCOIN - $100.00"

# Or error:
"Error recording fake investment: ..."
```

**If no log appears**: API endpoint not being called or token not working

---

### Step 2: Direct API Test

**Get Auth Token**:
```bash
curl -X POST http://localhost:8002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin1"}'

# Copy the "access_token" value
```

**Test Investment Endpoint**:
```bash
curl -X POST http://localhost:8002/api/user/portfolio/invest/fake \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol":"BITCOIN",
    "quantity":0.00220291,
    "price":45394.46,
    "total_value":100.00
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "message": "Fake money investment recorded: BITCOIN",
  "holding": {
    "symbol": "BITCOIN",
    "quantity": 0.00220291,
    "price": 45394.46,
    "total_value": 100.00,
    "timestamp": "2026-06-01T20:30:00Z"
  },
  "portfolio": {
    "cash": 99900.00,
    "investments": [...]
  }
}
```

**If response is error**: Check the `detail` field for specific error

---

### Step 3: Check MongoDB Directly

**Connect to MongoDB**:
```bash
# In terminal
mongosh

# In mongosh shell
use crypto_ai
db.users.findOne({ username: "admin" })
```

**Look for**:
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "portfolio": {
    "cash": 99900.00,  // Should be 99900, not 100000
    "investments": [
      {
        "symbol": "BITCOIN",
        "quantity": 0.00220291,
        "price": 45394.46,
        "total_value": 100.00,
        "investment_type": "fake_money",
        "timestamp": "2026-06-01T20:30:00Z"
      }
    ]
  }
}
```

**If cash is still 100000**:
- MongoDB update is not happening
- Check `add_user_holding()` function in backend

**If investments array doesn't exist**:
- User document schema needs initialization
- Check user creation in `/auth/register`

---

### Step 4: Trace Backend Code

**Location**: `backend/main.py` lines 1958-2010

**Check These Functions**:

1. **`user_invest_fake_money()` (line 1958)**
   ```python
   @app.post("/api/user/portfolio/invest/fake")
   async def user_invest_fake_money(...)
   ```
   - Is it receiving the correct data?
   - Is `current_user` populated correctly?
   - Is error handling catching something?

2. **`get_user_portfolio()` (helper function)**
   - Is it returning current cash balance?
   - Does it include investments array?
   - **Common issue**: Returns default structure instead of actual DB data

3. **`add_user_holding()` (helper function)**
   - Is MongoDB update actually executing?
   - **Add logging**:
     ```python
     logger.info(f"Adding holding for {current_user}: {holding}")
     result = await add_user_holding(db, current_user, holding)
     logger.info(f"MongoDB update result: {result}")
     ```

---

## Common Root Causes

### Cause 1: Token Authentication Failing
**Symptom**: Backend gets 401 error
**Fix**: 
- Verify token being sent in Authorization header
- Check JWT secret key matches
- Ensure token hasn't expired

### Cause 2: User Document Missing
**Symptom**: `current_user` is None or empty
**Fix**:
- Verify user created successfully in `/auth/register`
- Check username matches (case-sensitive)
- Verify MongoDB user has portfolio field

### Cause 3: MongoDB Schema Mismatch
**Symptom**: Update succeeds but data not in expected format
**Fix**:
- Verify portfolio structure in user creation:
  ```python
  "portfolio": {
    "cash": 100000.0,
    "investments": []
  }
  ```
- Check if using wrong field names (e.g., "balance" vs "cash")

### Cause 4: Get Portfolio Returns Cached Data
**Symptom**: Update happens but old data returned
**Fix**:
- Ensure `get_user_portfolio()` queries DB after update
- Check for caching that's not being invalidated
- Add `_fresh=True` flag or similar

### Cause 5: Frontend Sending Wrong Field Names
**Symptom**: Backend rejects or ignores data
**Fix**:
- Verify frontend sends: `symbol`, `quantity`, `price`, `total_value`
- NOT: `amount`, `crypto_id`, `totalValue` (wrong case)
- Backend expects exact field names

---

## Debug Logging to Add

**Add to `backend/main.py` investment endpoint**:

```python
@app.post("/api/user/portfolio/invest/fake")
async def user_invest_fake_money(
    invest_data: Dict,
    current_user: str = Depends(get_current_user)
):
    logger.info(f"🔍 Investment Request - User: {current_user}, Data: {invest_data}")
    
    db = await get_db()
    logger.info(f"🔍 Got DB connection")
    
    portfolio = await get_user_portfolio(db, current_user)
    logger.info(f"🔍 Current portfolio: {portfolio}")
    
    total_value = invest_data.get("total_value", 0)
    current_cash = portfolio.get("cash", 100000.0)
    logger.info(f"🔍 Cash check: {current_cash} >= {total_value}?")
    
    # ... rest of function ...
    
    portfolio["cash"] = current_cash - total_value
    logger.info(f"🔍 New cash balance: {portfolio['cash']}")
    
    result = await add_user_holding(db, current_user, holding)
    logger.info(f"🔍 MongoDB update result: {result}")
    
    updated_portfolio = await get_user_portfolio(db, current_user)
    logger.info(f"🔍 Verified portfolio after update: {updated_portfolio}")
```

**Run Test Again**:
- Backend terminal will show each step
- Identify where process stops/fails

---

## Verification Steps (After Fix)

1. **Fresh test after fix**:
   - Create new user
   - Login
   - Invest $100
   - Check backend logs
   - Check MongoDB document
   - Refresh page
   - Verify portfolio shows new balance

2. **Verify data consistency**:
   - Frontend shows $99,900 cash remaining
   - Database shows cash = 99900
   - Portfolio shows 1 holding: 0.00220291 BTC
   - Total value matches: 100

3. **Test edge cases**:
   - Invest beyond available cash (should fail)
   - Invest multiple times (cash should decrease each time)
   - Multiple users (should isolate portfolios)

---

## Quick Test Commands

**Reset database for clean test**:
```bash
mongosh

use crypto_ai
db.users.deleteOne({ username: "admin" })

# Or reset specific user:
db.users.updateOne(
  { username: "admin" },
  { 
    $set: { 
      "portfolio.cash": 100000.0,
      "portfolio.investments": []
    }
  }
)
```

**View all users**:
```bash
db.users.find().pretty()
```

**View specific user portfolio**:
```bash
db.users.findOne({ username: "admin" }).portfolio
```

---

## Expected Timeline

| Task | Time | Difficulty |
|------|------|-----------|
| Add debug logging | 5 min | Very Easy |
| Run test with logs | 10 min | Easy |
| Identify root cause | 20-30 min | Medium |
| Implement fix | 15-30 min | Varies |
| Verify fix works | 10 min | Easy |

**Total**: ~1-2 hours to resolve

---

## Questions to Ask Yourself

1. ✓ Does the endpoint receive the request?
   - Check: Backend logs show request received
   
2. ✓ Does the endpoint process the data correctly?
   - Check: Logs show calculations correct
   
3. ✓ Does MongoDB update execute?
   - Check: Logs show MongoDB update called
   
4. ✓ Does MongoDB update succeed?
   - Check: MongoDB update result shows success
   
5. ✓ Does the next profile fetch get updated data?
   - Check: Fresh query shows new cash balance

If any answer is "no", that's where the bug is!

---

## Contact Info for Help

If still stuck after this debugging:
1. Copy all backend console logs for error context
2. Export MongoDB user document (anonymized)
3. Compare `user_invest_fake_money()` with working endpoints
4. Check if other DB updates work (e.g., `/auth/register`)
5. Verify dependencies installed correctly (`pip list | grep mongo`)

---

**Last Updated**: June 1, 2026  
**Status**: Debug-ready with comprehensive troubleshooting guide  
**Next Step**: Add logging, run test, check logs

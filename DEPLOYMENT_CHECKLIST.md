# CryptoAI Auto Trading - Production Deployment Checklist

## Pre-Deployment Tasks

### 1. Configuration ✓
- [ ] `.env` file created with production values
- [ ] `BINANCE_API_KEY` and `BINANCE_API_SECRET` configured
- [ ] `BINANCE_TESTNET=false` for real trading (or `true` to test first)
- [ ] `BINANCE_TLD=us` for Binance.US (or `com` for global)
- [ ] `FRONTEND_ALLOWED_ORIGINS` updated for production domain
- [ ] Database URL configured (MongoDB connection)
- [ ] `SECRET_KEY` set to strong random value
- [ ] HTTPS certificates configured (via Cloudflare tunnel)

### 2. Backend Setup ✓
- [ ] Python virtual environment created
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Backend tests pass: `python test_auto_trading_e2e.py`
- [ ] Binance connection verified
- [ ] MongoDB auto_trades collection indexed
- [ ] API documentation reviewed: `http://localhost:8002/docs`

### 3. Frontend Setup ✓
- [ ] Node.js dependencies installed: `npm install`
- [ ] Frontend builds without errors: `npm run build`
- [ ] Auto Trading page component displays correctly
- [ ] API_BASE points to correct backend
- [ ] Authentication flow works (login → dashboard → auto-trading)
- [ ] All three tabs render (Warnings, Execute, Active Trades)

### 4. Testing ✓
- [ ] End-to-end test passed: `python test_auto_trading_e2e.py`
- [ ] Sample trade executed (on testnet first)
- [ ] Trade appears in Active Trades tab
- [ ] MongoDB shows trade record
- [ ] Portfolio P&L calculated correctly
- [ ] Risk warnings display on UI
- [ ] Stop-loss and take-profit prices are correct

### 5. Windows Service Setup ✓
- [ ] Run as Administrator: `SETUP_WINDOWS_SERVICE.bat`
- [ ] Both services installed successfully
- [ ] Services set to auto-start
- [ ] Backend service running: `sc query CryptoAI-Backend`
- [ ] Frontend service running: `sc query CryptoAI-Frontend`
- [ ] Services survive reboot test

### 6. Monitoring & Logging ✓
- [ ] Backend logs checked for errors
- [ ] MongoDB logs reviewed
- [ ] Windows Event Viewer configured for service logs
- [ ] Health check endpoint working: `GET /health`
- [ ] Error handling tested (invalid trades, connection failures)
- [ ] Rate limiting configured

### 7. Security Review ✓
- [ ] API keys never committed to git
- [ ] `.env` file added to `.gitignore`
- [ ] JWT tokens configured with expiration
- [ ] CORS properly restricted to known origins
- [ ] Database connection uses authentication
- [ ] SSL/TLS enabled for production
- [ ] CSRF protection enabled on POST endpoints

### 8. User Documentation ✓
- [ ] Premium tier users informed about auto-trading feature
- [ ] User guide created with screenshots
- [ ] Risk disclaimers displayed prominently
- [ ] Support contact info accessible
- [ ] FAQ created for common issues

### 9. Backup & Recovery ✓
- [ ] MongoDB backup strategy defined
- [ ] Trade data exported regularly
- [ ] Disaster recovery plan documented
- [ ] Database rollback procedure tested

---

## Deployment Steps

### Step 1: Prepare Environment
```bash
# Copy .env template to .env
copy .env.example .env

# Edit .env with production values
notepad .env

# Verify configuration
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('BINANCE_API_KEY:', bool(os.getenv('BINANCE_API_KEY')))"
```

### Step 2: Stop Current Services (if any)
```bash
sc stop CryptoAI-Backend
sc stop CryptoAI-Frontend
timeout /t 5
```

### Step 3: Deploy Code
```bash
# Pull latest code
git pull origin main

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Build frontend
cd frontend && npm run build && cd ..
```

### Step 4: Update Services
```bash
# Run as Administrator
SETUP_WINDOWS_SERVICE.bat
```

### Step 5: Verify Deployment
```bash
# Test backend health
powershell -Command "Invoke-WebRequest -Uri 'http://localhost:8002/health' -UseBasicParsing"

# Run end-to-end tests
python test_auto_trading_e2e.py
```

### Step 6: Post-Deployment Checks
```bash
# Check service status
sc query CryptoAI-Backend
sc query CryptoAI-Frontend

# Monitor logs
eventvwr.msc
```

---

## Rollback Procedure

If deployment fails:

```bash
# Stop services
sc stop CryptoAI-Backend
sc stop CryptoAI-Frontend

# Restore previous code
git revert HEAD

# Reinstall dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Restart services
sc start CryptoAI-Backend
sc start CryptoAI-Frontend

# Verify
python test_auto_trading_e2e.py
```

---

## Monitoring Checklist (Post-Deployment)

### Daily Tasks
- [ ] Check `/health` endpoint for backend availability
- [ ] Verify recent trades in MongoDB
- [ ] Review error logs for issues
- [ ] Monitor Binance API rate limits
- [ ] Check system resource usage (CPU, memory, disk)

### Weekly Tasks
- [ ] Backup MongoDB database
- [ ] Review user trading activity
- [ ] Check for failed trades
- [ ] Verify P&L calculations
- [ ] Review support tickets

### Monthly Tasks
- [ ] Full system health audit
- [ ] Update dependencies (`pip list --outdated`)
- [ ] Review and update risk parameters
- [ ] Binance account security audit
- [ ] Performance optimization review

---

## Critical Contacts

- **Binance Support**: https://www.binance.com/en/support
- **Binance API Docs**: https://binance-docs.github.io/apidocs/
- **MongoDB Support**: https://www.mongodb.com/support
- **CryptoAI Issues**: GitHub Issues (if applicable)

---

## Known Issues & Workarounds

### Issue: "Binance credentials not configured"
**Solution**: 
- Verify `.env` file exists in project root
- Check `BINANCE_API_KEY` and `BINANCE_API_SECRET` are set
- Restart services: `net stop CryptoAI-Backend && net start CryptoAI-Backend`

### Issue: "401 Unauthorized" on protected endpoints
**Solution**:
- Clear browser cache and localStorage
- Re-login with valid credentials
- Check JWT token expiration in logs

### Issue: Service won't start
**Solution**:
- Check Windows Event Viewer for errors
- Verify .bat files are executable
- Try manual startup: `cmd /c start_backend.bat`
- Check port 8002 is not in use: `netstat -ano | findstr :8002`

### Issue: Trades not persisting to MongoDB
**Solution**:
- Verify MongoDB is running: `mongo --version`
- Check connection string in backend logs
- Verify `auto_trades` collection exists
- Restart backend service

---

## Performance Optimization Tips

1. **Database Indexing**: Ensure MongoDB indexes are created on frequently queried fields
2. **Connection Pooling**: Configure connection pools for high-traffic scenarios
3. **Caching**: Consider caching Binance account info (5-10 minute TTL)
4. **Rate Limiting**: Implement rate limiting to prevent API abuse
5. **Load Balancing**: For scaling, consider load balancing across multiple backend instances

---

## Contact & Support

- **Issues**: Report via GitHub Issues
- **Security**: email: [security contact]
- **General**: email: cryptosupport74@gmail.com

---

**Last Updated**: 2026-06-06  
**Version**: 1.0  
**Status**: Ready for Production

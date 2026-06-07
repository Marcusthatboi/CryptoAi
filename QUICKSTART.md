# Quick Start Guide - CryptoAI

## ⚡ Get Started in 2 Minutes

### 1. Setup (One-time)

```powershell
# Navigate to project
cd c:\Users\marcu\CryproAI

# Create virtual environment (if not done)
uv venv

# Activate it
.\.venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Run Basic Tracking

```powershell
python src/crypto_tracker.py
```

This will:
- ✅ Fetch live Bitcoin & Ethereum prices
- ✅ Save to `data/crypto_prices.csv`
- ✅ Analyze trends
- ✅ Generate plots in `plots/`
- ✅ Prepare ML-ready data

### 3. View Results

- **Data**: `data/crypto_prices.csv`
- **Plots**: `plots/*.png`
- **Logs**: Console output with full details

---

## 🎯 Common Tasks

### Track Different Cryptocurrencies

Edit `src/crypto_tracker.py` line ~755 or run from Python:

```python
from src.crypto_tracker import main

main(
    crypto_ids=["bitcoin", "ethereum", "cardano", "solana", "ripple"],
    csv_filename="crypto_prices.csv",
    sma_window=5
)
```

### Run Examples

```powershell
# Show all available examples
python examples.py all

# Or run specific examples
python examples.py 1  # Simple fetch
python examples.py 2  # Multi-crypto
python examples.py 3  # Historical analysis
python examples.py 8  # Full automation
```

### Fetch Single Cryptocurrency Price

```python
from src.crypto_tracker import fetch_crypto_price

price = fetch_crypto_price("bitcoin")
print(f"Bitcoin: ${price['price']:.2f}")
```

### Analyze Historical Data

```python
from src.crypto_tracker import load_price_data, analyze_multiple_trends

df = load_price_data("crypto_prices.csv")
trends = analyze_multiple_trends(df)

for trend in trends:
    print(f"{trend['crypto_id']}: {trend['trend']}")
```

### Generate Plots

```python
from src.crypto_tracker import load_price_data, plot_price_trend, plot_multiple_prices

df = load_price_data("crypto_prices.csv")

# Individual plots
plot_price_trend(df, "bitcoin")
plot_price_trend(df, "ethereum")

# Combined comparison
plot_multiple_prices(df)
```

---

## 📊 Data Files

### CSV Structure (`data/crypto_prices.csv`)
```
timestamp,id,price,market_cap,volume_24h,price_change_24h
2026-04-10T16:33:27.610462,bitcoin,73284,1.467e+12,3.96e+10,1.22
2026-04-10T16:33:27.611318,ethereum,2253.87,2.72e+11,1.82e+10,1.56
```

### Available Cryptocurrencies
Popular IDs for CoinGecko API:
- `bitcoin`
- `ethereum`
- `cardano`
- `solana`
- `ripple`
- `polkadot`
- `dogecoin`
- `litecoin`
- `chainlink`
- `uniswap`

[View all](https://api.coingecko.com/api/v3/coins/list)

---

## 🚀 Next Steps After Initial Setup

### 1. **Schedule Regular Updates** (every hour)

Using `schedule` library:
```python
import schedule
import time
from src.crypto_tracker import main

def job():
    main(crypto_ids=["bitcoin", "ethereum"])

schedule.every(1).hours.do(job)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. **Build ML Model**

```python
from src.crypto_tracker import load_price_data, prepare_ml_data
from sklearn.ensemble import RandomForestRegressor

# Prepare data
df = load_price_data("crypto_prices.csv")
X_train, X_test, y_train, y_test = prepare_ml_data(df, "bitcoin")

# Train model
model = RandomForestRegressor(n_estimators=50)
model.fit(X_train, y_train)

# Evaluate
score = model.score(X_test, y_test)
print(f"R² Score: {score:.4f}")
```

### 3. **Add Alerts to Discord/Slack**

```python
from src.crypto_tracker import generate_alerts, load_price_data
import requests

df = load_price_data("crypto_prices.csv")
alerts = generate_alerts(df, threshold=3.0)

for alert in alerts:
    msg = f"{alert['crypto_id']}: {alert['price_change_percent']:+.2f}%"
    # Send to Slack/Discord webhook
    requests.post(WEBHOOK_URL, json={"text": msg})
```

### 4. **Database Integration** (MongoDB/PostgreSQL)

Replace CSV storage with database queries instead of CSV files.

---

## 🆘 Troubleshooting

### "ModuleNotFoundError"
```powershell
# Reactivate environment
.\.venv\Scripts\Activate.ps1

# Reinstall
uv pip install -r requirements.txt
```

### "Connection error to API"
- Check internet connection
- CoinGecko API rate limit: ~10-50 req/min
- Try again in a few seconds

### "No data points for ML"
- Need at least 20 data points for ML preparation
- Run the script multiple times to accumulate history
- Or fetch historical data from another source

### "Plots not showing"
- Plots are saved automatically to `plots/`
- They don't display inline in console
- Open PNG files directly in image viewer

---

## 💡 Pro Tips

1. **Safe to run repeatedly** - Uses append mode for CSV
2. **Check logs** - Timestamp and error info in console
3. **Customize alert threshold** - Edit `PRICE_CHANGE_THRESHOLD`
4. **Add more cryptos** - Just pass more IDs to function
5. **ML ready** - Features and splits already prepared

---

## 📚 Documentation

- See [README.md](README.md) for full features
- See [crypto_tracker.py](src/crypto_tracker.py) for function docstrings
- See [examples.py](examples.py) for code examples

---

## 🎓 Learning Path

1. **Start**: `python src/crypto_tracker.py` → See it work
2. **Explore**: Run `examples.py` → Understand features
3. **Customize**: Edit crypto IDs and thresholds
4. **Extend**: Add scheduling or database
5. **ML**: Train predictive models with prepared data
6. **Deploy**: Build web API or Discord bot

---

## ✅ Project Checklist

- [x] Real-time price fetching
- [x] CSV data storage
- [x] SMA trend analysis
- [x] Price alerts
- [x] Data visualization
- [x] Multi-crypto support
- [x] Error handling
- [x] ML data prep
- [x] Clean, modular code
- [x] Type hints & docstrings

---

**Ready to track crypto? Start with:** `python src/crypto_tracker.py`

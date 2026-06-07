# CryptoAI - Cryptocurrency Price Tracker

A modular, production-ready Python project for tracking cryptocurrency prices with AI/ML foundations. Built with real-time data fetching, trend analysis, alerts, and machine learning data preparation.

## Documentation

Primary maintained documentation is now in `docs/`:

- `docs/README.md` - documentation index
- `docs/API_DOCUMENTATION.md` - backend API and WebSocket reference
- `docs/DEPLOYMENT_GUIDE.md` - container and production deployment instructions
- `docs/ADMIN_GUIDE.md` - admin dashboard and customer operations
- `docs/USER_GUIDE.md` - end-user onboarding and feature usage
- `docs/DEVELOPER_GUIDE.md` - architecture, local development, and test workflows

## 🎯 Features

✅ **Real-time Data Fetching**: Integrates with CoinGecko API for live cryptocurrency prices  
✅ **Historical Data Storage**: Automatic CSV-based data persistence with timestamps  
✅ **Technical Analysis**: Simple Moving Average (SMA) calculations for trend detection  
✅ **Price Alerts**: Automatic alerts when price changes exceed 5% threshold  
✅ **Data Visualization**: Matplotlib plots for single and multiple cryptocurrencies  
✅ **ML Foundation**: Prepared feature engineering for time-series ML models  
✅ **Error Handling**: Comprehensive error handling for API failures and edge cases  
✅ **Modular Design**: Clean, well-documented functions for easy extension  
✅ **Multi-Crypto Support**: Track multiple cryptocurrencies simultaneously  
✅ **Production Ready**: Logging, type hints, and best practices throughout  

## 📋 Requirements

- Python 3.8+
- Dependencies: requests, pandas, numpy, matplotlib

## 🚀 Installation

### 1. Clone or navigate to the project

```bash
cd c:\Users\marcu\CryproAI
```

### 2. Create a virtual environment (recommended)

```bash
# Using uv (fast)
uv venv

# Or using Python venv
python -m venv venv
```

### 3. Activate the virtual environment

**On Windows (PowerShell):**
```bash
.\.venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```bash
.\.venv\Scripts\activate.bat
```

**On macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install dependencies

```bash
# Using uv
uv pip install -r requirements.txt

# Or using pip
pip install -r requirements.txt
```

## 📖 Usage

### Basic Usage

```bash
# Run the main tracker
python src/crypto_tracker.py
```

### As a Python Module

```python
from src.crypto_tracker import main, fetch_crypto_price, analyze_crypto_trend

# Run the full workflow
main(crypto_ids=["bitcoin", "ethereum", "cardano"])

# Or use individual functions
price_data = fetch_crypto_price("bitcoin")
print(f"Bitcoin price: ${price_data['price']:.2f}")
```

### Advanced Usage Examples

```python
from src.crypto_tracker import (
    fetch_crypto_price,
    analyze_crypto_trend,
    load_price_data,
    prepare_ml_data
)
import pandas as pd

# Fetch a single cryptocurrency
btc = fetch_crypto_price("bitcoin")
print(btc)

# Load historical data
df = load_price_data("crypto_prices.csv")

# Analyze trends
analysis = analyze_crypto_trend(df, "bitcoin", sma_window=10)
print(f"Trend: {analysis['trend']}")
print(f"Current Price: ${analysis['current_price']:.2f}")

# Prepare ML data
X_train, X_test, y_train, y_test = prepare_ml_data(df, "bitcoin")
print(f"Training samples: {len(X_train)}")
```

## 📁 Project Structure

```
CryproAI/
├── src/
│   └── crypto_tracker.py      # Main application
├── data/
│   └── crypto_prices.csv      # Historical price data (auto-generated)
├── plots/
│   └── *.png                  # Generated trend plots
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🔌 API Information

### CoinGecko API

**Endpoint:** https://api.coingecko.com/api/v3

**Features:**
- Free tier: No authentication required
- Rate limit: ~10-50 calls/minute
- Data: Real-time prices, market caps, volume, 24h change

**Supported Cryptocurrencies:**
- bitcoin
- ethereum
- cardano
- solana
- ripple
- polkadot
- dogecoin
- And many more...

[Full list of crypto IDs](https://api.coingecko.com/api/v3/coins/list)

## 📊 Output Files

### CSV Data (`data/crypto_prices.csv`)
Columns: timestamp, id, price, market_cap, volume_24h, price_change_24h

Example:
```
timestamp,id,price,market_cap,volume_24h,price_change_24h
2026-04-10T14:30:45.123456,bitcoin,67500.50,1.32e+12,31000000000.0,2.45
2026-04-10T14:30:45.654321,ethereum,3800.25,456000000000.0,15000000000.0,-1.23
```

### Plots (`plots/`)
- `bitcoin_trend_*.png` - Single cryptocurrency trends
- `ethereum_trend_*.png` - Single cryptocurrency trends
- `multi_trend_*.png` - All cryptocurrencies comparison

## 🤖 ML Extension Guide

The project is designed to be extended with machine learning models:

```python
from src.crypto_tracker import prepare_ml_data, load_price_data
from sklearn.ensemble import RandomForestRegressor
import pickle

# Load data
df = load_price_data("crypto_prices.csv")

# Prepare features
X_train, X_test, y_train, y_test = prepare_ml_data(df, "bitcoin")

# Train model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
accuracy = model.score(X_test, y_test)
print(f"Model R² Score: {accuracy:.4f}")

# Save model
with open("btc_model.pkl", "wb") as f:
    pickle.dump(model, f)
```

## 🔧 Configuration

Edit the following constants in `src/crypto_tracker.py` to customize:

```python
PRICE_CHANGE_THRESHOLD = 5.0              # Alert threshold percentage
DEFAULT_CRYPTOCURRENCIES = ["bitcoin", "ethereum"]  # Default cryptos
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"  # API endpoint
```

## ⚠️ Error Handling

The project includes comprehensive error handling for:

- ✅ Network timeouts
- ✅ Connection errors
- ✅ Invalid API responses
- ✅ File I/O errors
- ✅ Data parsing errors
- ✅ Missing data files

All errors are logged with detailed messages for debugging.

## 📝 Function Reference

### Data Fetching
- `fetch_crypto_price()` - Fetch single cryptocurrency price
- `fetch_multiple_cryptocurrencies()` - Batch fetch multiple cryptos

### Data Storage
- `save_price_data()` - Save to CSV
- `save_multiple_prices()` - Batch save
- `load_price_data()` - Load from CSV

### Analysis
- `calculate_sma()` - Simple Moving Average
- `analyze_crypto_trend()` - Trend analysis for one crypto
- `analyze_multiple_trends()` - Batch analysis

### Alerts
- `check_price_alert()` - Check if alert threshold triggered
- `generate_alerts()` - Generate all alerts
- `print_alerts()` - Format and print alerts

### Visualization
- `plot_price_trend()` - Plot single crypto
- `plot_multiple_prices()` - Plot all cryptos

### ML
- `prepare_ml_data()` - Feature engineering for ML models

## 🚀 Next Steps

1. **Real-time Updates**: Extend with scheduled jobs using `schedule` or `APScheduler`
2. **Database Integration**: Replace CSV with MongoDB or PostgreSQL
3. **ML Models**: Add LSTM, Random Forest, or other predictive models
4. **Web Dashboard**: Build with FastAPI + React/Vue.js
5. **Trading Bot**: Add buy/sell signals based on analysis
6. **Alerts System**: Integrate with email, Slack, or Discord
7. **API Wrapper**: Expose as REST API
8. **Docker**: Containerize for deployment

## 📚 Learning Resources

- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Guide](https://matplotlib.org/stable/users/index.html)
- [Time Series Forecasting](https://www.statsmodels.org/stable/tsa.html)

## 📄 License

Open source - Use freely for educational and commercial purposes.

## 🤝 Contributing

Feel free to extend this project with:
- Additional technical indicators (RSI, MACD, Bollinger Bands)
- More cryptocurrencies
- Advanced ML models
- Web interface
- Database backend

## ❓ Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install -r requirements.txt
```

### "Connection error fetching data"
- Check internet connection
- Verify CoinGecko API is accessible
- Check firewall/proxy settings

### "No data found for cryptocurrency"
- Verify crypto ID is correct (e.g., "bitcoin" not "Bitcoin")
- Check [CoinGecko crypto list](https://api.coingecko.com/api/v3/coins/list)

### "CSV file not found for analysis"
- Run the script to generate initial data
- Ensure `data/` directory exists

## 📞 Support

For issues or questions, check the inline code documentation and docstrings.

---

**Happy Tracking! 🚀💰**

"""
Configuration Reference
=======================

This file shows all configurable parameters in the cryptocurrency tracker.
You can modify these in src/crypto_tracker.py or pass them to functions directly.
"""

# ============================================================================
# API CONFIGURATION
# ============================================================================

# CoinGecko API endpoint (free tier, no key required)
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"

# Request timeout in seconds
API_TIMEOUT = 10

# ============================================================================
# ALERT CONFIGURATION
# ============================================================================

# Price change threshold that triggers alerts (in percentage)
PRICE_CHANGE_THRESHOLD = 5.0

# Examples:
# - 5.0 = Alert if price changes by ±5%
# - 3.0 = Alert if price changes by ±3% (more sensitive)
# - 10.0 = Alert if price changes by ±10% (less sensitive)

# ============================================================================
# MOVING AVERAGE CONFIGURATION
# ============================================================================

# Simple Moving Average window size (in data points)
SMA_WINDOW = 5

# Examples:
# - 5 = SMA of last 5 prices (short-term trend, 5 minutes if fetching every minute)
# - 10 = SMA of last 10 prices (medium-term trend)
# - 20 = SMA of last 20 prices (longer-term trend)
# - 50 = SMA of last 50 prices (long-term trend)

# ============================================================================
# DATA STORAGE CONFIGURATION
# ============================================================================

# CSV filename for storing price data
CSV_FILENAME = "crypto_prices.csv"

# Directory paths (relative to project root)
DATA_DIRECTORY = "data"
PLOTS_DIRECTORY = "plots"

# ============================================================================
# CRYPTOCURRENCY SELECTION
# ============================================================================

# Default cryptocurrencies to track
DEFAULT_CRYPTOCURRENCIES = ["bitcoin", "ethereum"]

# Common cryptocurrency IDs (use these for reference):
AVAILABLE_CRYPTOS = {
    "Major Coins": [
        "bitcoin",           # BTC
        "ethereum",          # ETH
        "binancecoin",       # BNB
        "solana",            # SOL
        "cardano",           # ADA
    ],
    "Alternative Coins": [
        "ripple",            # XRP
        "polkadot",          # DOT
        "dogecoin",          # DOGE
        "litecoin",          # LTC
        "chainlink",         # LINK
        "uniswap",           # UNI
        "avalanche-2",       # AVAX
        "polygon",           # MATIC
    ],
    "Emerging Coins": [
        "thepixelv",         # PXLV
        "tao",               # TAO
        "internet-computer", # ICP
        "near",              # NEAR
        "algorand",          # ALGO
    ]
}

# ============================================================================
# VISUALIZATION CONFIGURATION
# ============================================================================

# Plot figure size (width, height in inches)
PLOT_FIGURE_SIZE = (12, 6)

# Plot resolution (dots per inch)
PLOT_DPI = 100

# Plot grid transparency (0.0 = invisible, 1.0 = opaque)
PLOT_GRID_ALPHA = 0.3

# ============================================================================
# MACHINE LEARNING CONFIGURATION
# ============================================================================

# Train/test split ratio
ML_TEST_SPLIT = 0.2  # 20% test, 80% train

# Minimum data points required for ML preparation
ML_MIN_DATA_POINTS = 20

# Features used in ML preparation
ML_FEATURES = [
    "price",          # Current price
    "sma_5",          # 5-period SMA
    "sma_10",         # 10-period SMA
    "price_lag_1",    # Previous price
    "price_lag_2",    # Price from 2 periods ago
    "price_change",   # Percentage change
]

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Log format
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

# Example 1: Track only Bitcoin
# main(crypto_ids=["bitcoin"])

# Example 2: Track top 5 altcoins
# main(crypto_ids=["ethereum", "cardano", "solana", "ripple", "polkadot"])

# Example 3: More sensitive alerts (3% threshold)
# alerts = generate_alerts(df, threshold=3.0)

# Example 4: Shorter term SMA (window of 3)
# analysis = analyze_crypto_trend(df, "bitcoin", sma_window=3)

# Example 5: Longer term SMA (window of 20)
# analysis = analyze_crypto_trend(df, "bitcoin", sma_window=20)

# Example 6: Custom CSV filename for different strategies
# main(csv_filename="bitcoin_short_term.csv", sma_window=5)
# main(csv_filename="bitcoin_long_term.csv", sma_window=20)

# ============================================================================
# PERFORMANCE TIPS
# ============================================================================

"""
1. API RATE LIMITING
   - CoinGecko free tier: ~10-50 requests per minute
   - Use longer intervals between fetches for multiple runs
   - Cache responses if running frequently

2. STORAGE
   - CSV files are small but slow for large datasets
   - Consider MongoDB for production use
   - Archive old data periodically

3. PLOTTING
   - Visual updates slow down script significantly
   - Disable plotting for frequent runs: comment out plot functions
   - Save plots on-demand for slower CI/CD environments

4. ML DATA PREPARATION
   - Requires minimum 20 data points
   - Normalize features before using with ML models
   - More data = better model accuracy

5. MEMORY
   - Large DataFrames consume memory
   - Use chunks or filtering for large historical datasets
   - Monitor memory usage if tracking 100+ cryptocurrencies
"""

# ============================================================================
# ADVANCED: CUSTOM SCHEDULING (requires 'schedule' library)
# ============================================================================

"""
# Install: pip install schedule

import schedule
import time
from src.crypto_tracker import main

# Fetch every hour
schedule.every(1).hours.do(main)

# Fetch every 30 minutes
schedule.every(30).minutes.do(main)

# Fetch at specific time
schedule.every().day.at("10:30").do(main)

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(60)
"""

# ============================================================================
# ADVANCED: DATABASE INTEGRATION (requires MongoDB driver)
# ============================================================================

"""
# Install: pip install pymongo

from pymongo import MongoClient

# Store in MongoDB instead of CSV
client = MongoClient("mongodb://localhost:27017/")
db = client["crypto_tracker"]
prices_collection = db["prices"]

# Insert price data
def save_to_mongodb(crypto_prices):
    for crypto_id, data in crypto_prices.items():
        data['timestamp'] = datetime.now()
        prices_collection.insert_one(data)

# Query data
def load_from_mongodb(crypto_id, hours=24):
    query = {
        "id": crypto_id,
        "timestamp": {"$gte": datetime.now() - timedelta(hours=hours)}
    }
    return list(prices_collection.find(query))
"""

# ============================================================================
# ADVANCED: DISCORD ALERTS (requires 'discord.py' library)
# ============================================================================

"""
# Install: pip install discord.py

import discord
from discord.ext import commands

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

async def send_price_alert(alert):
    embed = discord.Embed(
        title=f"🚨 {alert['crypto_id'].upper()} Alert",
        description=f"Price changed by {alert['price_change_percent']:+.2f}%",
        color=discord.Color.red() if alert['direction'] == 'DOWN' else discord.Color.green()
    )
    embed.add_field(name="Previous Price", value=f"${alert['previous_price']:.2f}")
    embed.add_field(name="Current Price", value=f"${alert['current_price']:.2f}")
    
    channel = bot.get_channel(CHANNEL_ID)
    await channel.send(embed=embed)
"""

# ============================================================================
# ADVANCED: SLACK INTEGRATION
# ============================================================================

"""
# Install: pip install slack-sdk

from slack_sdk import WebClient

slack_client = WebClient(token="your-bot-token")

def send_slack_alert(alert):
    message = f":warning: {alert['crypto_id'].upper()} price changed by {alert['price_change_percent']:+.2f}%\n"
    message += f"${alert['previous_price']:.2f} → ${alert['current_price']:.2f}"
    
    slack_client.chat_postMessage(
        channel="crypto-alerts",
        text=message
    )
"""

print("✅ Configuration reference loaded")
print("Edit these values in: src/crypto_tracker.py (lines near top)")

"""
Multi-Source Data Collection Module
===================================

Integrates data from multiple sources:
- CoinGecko API (Real-time crypto)
- Binance API (Trading data)
- Yahoo Finance (Stocks & crypto)
- Alpha Vantage (Stocks & forex)
- CoinMarketCap (Alternative crypto data)

Provides unified data collection, caching, and export functionality.
"""

import os
import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

import requests
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
COINMARKETCAP_API_URL = "https://pro-api.coinmarketcap.com/v2"
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  # Get from env or use demo

# Cache settings
CACHE_DURATION = 300  # 5 minutes
REQUEST_TIMEOUT = 10


class DataSourceManager:
    """Unified data collection from multiple sources"""

    def __init__(self):
        self.coingecko_cache = {}
        self.cache_time = {}
        self.alpha_vantage = TimeSeries(key=ALPHA_VANTAGE_API_KEY, output_format='pandas')
        
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cached data is still valid"""
        if key not in self.cache_time:
            return False
        age = (datetime.now() - self.cache_time[key]).total_seconds()
        return age < CACHE_DURATION

    # ========================================================================
    # COINGECKO DATA (Crypto - Free, Expanded)
    # ========================================================================

    def get_coingecko_crypto(self, crypto_ids: List[str], vs_currency: str = "usd") -> Dict:
        """
        Fetch comprehensive crypto data from CoinGecko (free, no key needed)
        
        Args:
            crypto_ids: List of crypto IDs (e.g., ['bitcoin', 'ethereum'])
            vs_currency: Currency to compare against (default: 'usd')
            
        Returns:
            Dictionary with price, market cap, volume, 24h/7d/30d changes, ATH, etc.
        """
        cache_key = f"coingecko_{','.join(crypto_ids)}"
        
        if self._is_cache_valid(cache_key):
            logger.info(f"Using cached CoinGecko data for {crypto_ids}")
            return self.coingecko_cache.get(cache_key, {})
        
        try:
            endpoint = f"{COINGECKO_API_URL}/simple/price"
            params = {
                "ids": ",".join(crypto_ids),
                "vs_currencies": vs_currency,
                "include_market_cap": "true",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
                "include_7d_change": "true",
                "include_30d_change": "true",
                "include_market_cap_change_24h": "true",
                "include_ath": "true",
                "include_atl": "true"
            }
            
            response = requests.get(endpoint, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            self.coingecko_cache[cache_key] = data
            self.cache_time[cache_key] = datetime.now()
            
            logger.info(f"✅ Fetched CoinGecko data for {len(crypto_ids)} coins")
            return data
            
        except Exception as e:
            logger.error(f"❌ CoinGecko fetch failed: {e}")
            return {}

    # ========================================================================
    # YAHOO FINANCE DATA (Stocks & Crypto)
    # ========================================================================

    def get_yahoo_finance(self, symbol: str, period: str = "1y", interval: str = "1d") -> Optional[pd.DataFrame]:
        """
        Fetch historical price data from Yahoo Finance (free)
        
        Args:
            symbol: Stock ticker or crypto ticker (e.g., 'AAPL', 'BTC-USD')
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max')
            interval: Data interval ('1m', '5m', '15m', '30m', '60m', '1d', '1wk', '1mo')
            
        Returns:
            pandas DataFrame with historical OHLCV data
        """
        try:
            logger.info(f"Fetching Yahoo Finance data for {symbol}...")
            data = yf.download(symbol, period=period, interval=interval, progress=False)
            
            if data.empty:
                logger.warning(f"No data available for {symbol}")
                return None
                
            logger.info(f"✅ Fetched {len(data)} records for {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Yahoo Finance fetch failed for {symbol}: {e}")
            return None

    # ========================================================================
    # ALPHA VANTAGE DATA (Stocks & Forex - Limited Free Tier)
    # ========================================================================

    def get_alpha_vantage_stock(self, symbol: str, outputsize: str = "full") -> Optional[Dict]:
        """
        Fetch stock data from Alpha Vantage (limited free tier: 5 requests/min, 500/day)
        
        Args:
            symbol: Stock ticker (e.g., 'AAPL', 'MSFT')
            outputsize: 'compact' (100 data points) or 'full' (20+ years)
            
        Returns:
            Dictionary with time series data and metadata
        """
        try:
            if ALPHA_VANTAGE_API_KEY == "demo":
                logger.warning("⚠️ Using demo Alpha Vantage key - limited to demo data")
            
            logger.info(f"Fetching Alpha Vantage data for {symbol}...")
            data, metadata = self.alpha_vantage.get_daily(symbol=symbol, outputsize=outputsize)
            
            logger.info(f"✅ Fetched Alpha Vantage data for {symbol}")
            return {
                "data": data.to_dict(),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Alpha Vantage fetch failed for {symbol}: {e}")
            return None

    def get_alpha_vantage_forex(self, from_symbol: str, to_symbol: str) -> Optional[Dict]:
        """Fetch forex data from Alpha Vantage"""
        try:
            logger.info(f"Fetching forex {from_symbol}/{to_symbol} from Alpha Vantage...")
            data, metadata = self.alpha_vantage.get_currency_exchange_rate(from_symbol, to_symbol)
            
            logger.info(f"✅ Fetched forex data for {from_symbol}/{to_symbol}")
            return {
                "data": data.to_dict() if hasattr(data, 'to_dict') else data,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Alpha Vantage forex fetch failed: {e}")
            return None

    # ========================================================================
    # COINMARKETCAP DATA (Alternative Crypto - Requires API Key)
    # ========================================================================

    def get_coinmarketcap_crypto(self, symbols: List[str], limit: int = 100) -> Optional[Dict]:
        """
        Fetch crypto data from CoinMarketCap (requires API key)
        
        Free tier: 333 calls/day, 10 calls/min
        Get key: https://pro.coinmarketcap.com/
        
        Args:
            symbols: List of crypto symbols (e.g., ['BTC', 'ETH', 'ADA'])
            limit: Max results to return (default 100)
            
        Returns:
            Dictionary with crypto data
        """
        api_key = os.getenv("COINMARKETCAP_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ CoinMarketCap API key not set - set COINMARKETCAP_API_KEY environment variable")
            return None
        
        try:
            logger.info(f"Fetching CoinMarketCap data for {symbols}...")
            
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': api_key,
            }
            
            params = {
                'symbol': ','.join(symbols),
                'convert': 'USD',
                'limit': limit
            }
            
            response = requests.get(
                f"{COINMARKETCAP_API_URL}/cryptocurrency/quotes/latest",
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Fetched CoinMarketCap data for {len(symbols)} coins")
            return data
            
        except Exception as e:
            logger.error(f"❌ CoinMarketCap fetch failed: {e}")
            return None

    # ========================================================================
    # DATA EXPORT & STORAGE
    # ========================================================================

    def export_to_csv(self, crypto_id: str, data: List[Dict], filename: Optional[str] = None) -> str:
        """
        Export crypto data to CSV file
        
        Args:
            crypto_id: Cryptocurrency ID
            data: List of dictionaries with price data
            filename: Optional custom filename
            
        Returns:
            Path to exported CSV file
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{crypto_id}_{timestamp}.csv"
        
        filepath = DATA_DIR / filename
        
        try:
            if data:
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False)
                logger.info(f"✅ Exported {len(data)} records to {filepath}")
            else:
                logger.warning("No data to export")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Export failed: {e}")
            return ""

    def export_dataframe_to_csv(self, df: pd.DataFrame, label: str) -> str:
        """Export pandas DataFrame to CSV"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{label}_{timestamp}.csv"
            filepath = DATA_DIR / filename
            
            df.to_csv(filepath)
            logger.info(f"✅ Exported DataFrame to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ DataFrame export failed: {e}")
            return ""

    # ========================================================================
    # BULK DATA COLLECTION
    # ========================================================================

    def collect_all_sources(self, crypto_symbols: List[str], stock_symbols: List[str]) -> Dict:
        """
        Collect data from all available sources
        
        Args:
            crypto_symbols: List of crypto IDs for CoinGecko
            stock_symbols: List of stock tickers for Yahoo Finance
            
        Returns:
            Dictionary with data from all sources
        """
        logger.info("=" * 60)
        logger.info("🔄 Starting multi-source data collection...")
        logger.info("=" * 60)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "coingecko": {},
            "yahoo_crypto": {},
            "yahoo_stocks": {},
            "alpha_vantage": {},
            "coinmarketcap": {},
            "status": "completed"
        }
        
        # CoinGecko
        logger.info("\n📊 Collecting CoinGecko data...")
        coingecko_data = self.get_coingecko_crypto(crypto_symbols)
        results["coingecko"] = coingecko_data
        
        # Yahoo Finance - Crypto
        logger.info("\n📈 Collecting Yahoo Finance crypto data...")
        for symbol in [f"{s.upper()}-USD" for s in crypto_symbols[:3]]:  # Sample 3
            df = self.get_yahoo_finance(symbol, period="1y")
            if df is not None:
                results["yahoo_crypto"][symbol] = {
                    "records": len(df),
                    "start_date": str(df.index[0]),
                    "end_date": str(df.index[-1])
                }
        
        # Yahoo Finance - Stocks
        logger.info("\n📊 Collecting Yahoo Finance stock data...")
        for symbol in stock_symbols[:5]:  # Sample 5 stocks
            df = self.get_yahoo_finance(symbol, period="1y")
            if df is not None:
                results["yahoo_stocks"][symbol] = {
                    "records": len(df),
                    "start_date": str(df.index[0]),
                    "end_date": str(df.index[-1])
                }
        
        # Alpha Vantage (if key available)
        logger.info("\n🔄 Collecting Alpha Vantage data...")
        alpha_data = self.get_alpha_vantage_stock("AAPL", outputsize="compact")
        results["alpha_vantage"] = {"AAPL": alpha_data is not None}
        
        # CoinMarketCap (if key available)
        logger.info("\n💎 Collecting CoinMarketCap data...")
        cmc_data = self.get_coinmarketcap_crypto(["BTC", "ETH", "ADA"], limit=3)
        results["coinmarketcap"] = {"status": "success" if cmc_data else "no_api_key"}
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Multi-source data collection completed!")
        logger.info("=" * 60)
        
        return results

    def get_data_source_status(self) -> Dict:
        """Get status of all available data sources"""
        return {
            "coingecko": {
                "available": True,
                "requires_api_key": False,
                "description": "Free crypto data, 50 calls/min"
            },
            "yahoo_finance": {
                "available": True,
                "requires_api_key": False,
                "description": "Free stocks & crypto historical data, unlimited"
            },
            "alpha_vantage": {
                "available": ALPHA_VANTAGE_API_KEY != "demo",
                "requires_api_key": True,
                "description": "Stocks & forex, 5 calls/min free tier",
                "api_key_status": "demo" if ALPHA_VANTAGE_API_KEY == "demo" else "configured"
            },
            "coinmarketcap": {
                "available": bool(os.getenv("COINMARKETCAP_API_KEY")),
                "requires_api_key": True,
                "description": "Alternative crypto data, 333 calls/day free tier",
                "api_key_status": "configured" if os.getenv("COINMARKETCAP_API_KEY") else "not_configured"
            },
            "binance": {
                "available": True,
                "requires_api_key": False,
                "description": "Trading data & klines (already integrated)"
            }
        }


# Singleton instance
data_manager = DataSourceManager()

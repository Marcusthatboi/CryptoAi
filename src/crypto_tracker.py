"""
Cryptocurrency Price Tracker with AI Foundation
================================================

This module provides a foundation for tracking cryptocurrency prices and building
AI-based analysis models. It fetches real-time data, stores historical information,
analyzes trends, and generates alerts.

Features:
- Real-time price fetching from CoinGecko API
- Historical data storage in CSV format
- Moving average calculations for trend detection
- Price change alerts
- Data visualization with matplotlib
- Support for multiple cryptocurrencies
- ML-ready data preparation
"""

import os
import sys
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# ============================================================================
# CONFIGURATION AND SETUP
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project directories
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PLOTS_DIR = PROJECT_ROOT / "plots"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
PLOTS_DIR.mkdir(exist_ok=True)

# API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
PRICE_CHANGE_THRESHOLD = 5.0  # Alert threshold in percentage
DEFAULT_CRYPTOCURRENCIES = ["bitcoin", "ethereum"]

# ============================================================================
# DATA FETCHING FUNCTIONS
# ============================================================================

def fetch_crypto_price(
    crypto_id: str,
    vs_currency: str = "usd"
) -> Optional[Dict[str, float]]:
    """
    Fetch current price for a cryptocurrency from CoinGecko API.

    Args:
        crypto_id: Cryptocurrency ID (e.g., 'bitcoin', 'ethereum')
        vs_currency: Currency to compare against (default: 'usd')

    Returns:
        Dictionary with price data or None if request fails
        Format: {
            'id': str,
            'price': float,
            'market_cap': float,
            'volume_24h': float,
            'price_change_24h': float
        }

    Raises:
        Handles requests.RequestException internally with logging
    """
    try:
        endpoint = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": crypto_id,
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }

        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if crypto_id not in data:
            logger.warning(f"Cryptocurrency '{crypto_id}' not found in API response")
            return None

        crypto_data = data[crypto_id]

        return {
            'id': crypto_id,
            'price': crypto_data.get(vs_currency),
            'market_cap': crypto_data.get(f"{vs_currency}_market_cap"),
            'volume_24h': crypto_data.get(f"{vs_currency}_24h_vol"),
            'price_change_24h': crypto_data.get(f"{vs_currency}_24h_change")
        }

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {crypto_id}")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching data for {crypto_id}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching data for {crypto_id}: {e}")
        return None
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing response for {crypto_id}: {e}")
        return None


def fetch_multiple_cryptocurrencies(
    crypto_ids: Optional[List[str]] = None,
    vs_currency: str = "usd"
) -> Dict[str, Dict]:
    """
    Fetch prices for multiple cryptocurrencies.

    Args:
        crypto_ids: List of cryptocurrency IDs. Uses DEFAULT_CRYPTOCURRENCIES if None
        vs_currency: Currency to compare against (default: 'usd')

    Returns:
        Dictionary mapping crypto_id to price data
    """
    if crypto_ids is None:
        crypto_ids = DEFAULT_CRYPTOCURRENCIES

    try:
        endpoint = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true"
        }

        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = {}
        for crypto_id in crypto_ids:
            crypto_data = data.get(crypto_id)
            if not crypto_data:
                logger.warning(f"Failed to fetch {crypto_id}")
                continue

            price_data = {
                'id': crypto_id,
                'price': crypto_data.get(vs_currency),
                'market_cap': crypto_data.get(f"{vs_currency}_market_cap"),
                'volume_24h': crypto_data.get(f"{vs_currency}_24h_vol"),
                'price_change_24h': crypto_data.get(f"{vs_currency}_24h_change")
            }
            results[crypto_id] = price_data
            logger.info(f"Fetched {crypto_id}: ${price_data['price']:.2f}")

        return results

    except requests.exceptions.Timeout:
        logger.error(f"Timeout fetching data for {crypto_ids}")
        return {}
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error fetching data for {crypto_ids}")
        return {}
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error fetching data for {crypto_ids}: {e}")
        return {}
    except (ValueError, KeyError) as e:
        logger.error(f"Error parsing response for {crypto_ids}: {e}")
        return {}


def fetch_available_cryptocurrencies(limit: int = 250, vs_currency: str = "usd") -> List[Dict[str, str]]:
    """Fetch a broad catalog of available cryptocurrencies from CoinGecko.

    Args:
        limit: Maximum number of assets to fetch (CoinGecko max per page is 250)
        vs_currency: Reference currency for market-cap ranking

    Returns:
        List of assets with id/symbol/name
    """
    capped_limit = max(1, min(int(limit), 250))

    try:
        endpoint = f"{COINGECKO_API_URL}/coins/markets"
        params = {
            "vs_currency": vs_currency,
            "order": "market_cap_desc",
            "per_page": capped_limit,
            "page": 1,
            "sparkline": "false",
        }

        response = requests.get(endpoint, params=params, timeout=12)
        response.raise_for_status()
        data = response.json()

        assets = []
        for item in data:
            asset_id = str(item.get("id", "")).strip().lower()
            if not asset_id:
                continue

            assets.append(
                {
                    "id": asset_id,
                    "symbol": str(item.get("symbol", "")).strip().upper(),
                    "name": str(item.get("name", "")).strip(),
                }
            )

        return assets

    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching asset catalog: {e}")
        return []


# ============================================================================
# DATA STORAGE FUNCTIONS
# ============================================================================

def save_price_data(
    filename: str,
    crypto_id: str,
    price_data: Dict[str, float]
) -> bool:
    """
    Save cryptocurrency price data to a CSV file.

    File structure:
        timestamp,id,price,market_cap,volume_24h,price_change_24h

    Args:
        filename: CSV filename (without path)
        crypto_id: Cryptocurrency ID
        price_data: Dictionary containing price information

    Returns:
        True if successful, False otherwise
    """
    try:
        filepath = DATA_DIR / filename
        timestamp = datetime.now().isoformat()

        file_exists = filepath.exists()

        with open(filepath, 'a', newline='') as csvfile:
            fieldnames = ['timestamp', 'id', 'price', 'market_cap', 'volume_24h', 'price_change_24h']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header if file is new
            if not file_exists:
                writer.writeheader()

            writer.writerow({
                'timestamp': timestamp,
                'id': crypto_id,
                'price': price_data.get('price'),
                'market_cap': price_data.get('market_cap'),
                'volume_24h': price_data.get('volume_24h'),
                'price_change_24h': price_data.get('price_change_24h')
            })

        logger.info(f"Saved data for {crypto_id} to {filepath}")
        return True

    except IOError as e:
        logger.error(f"Error writing to CSV file: {e}")
        return False


def save_multiple_prices(
    filename: str,
    crypto_prices: Dict[str, Dict]
) -> bool:
    """
    Save multiple cryptocurrency prices to CSV.

    Args:
        filename: CSV filename (without path)
        crypto_prices: Dictionary mapping crypto_id to price data

    Returns:
        True if all saves successful
    """
    all_saved = True
    for crypto_id, price_data in crypto_prices.items():
        if not save_price_data(filename, crypto_id, price_data):
            all_saved = False

    return all_saved


# ============================================================================
# DATA ANALYSIS FUNCTIONS
# ============================================================================

def load_price_data(filename: str) -> Optional[pd.DataFrame]:
    """
    Load historical price data from CSV file.

    Args:
        filename: CSV filename (without path)

    Returns:
        Pandas DataFrame or None if file doesn't exist
    """
    try:
        filepath = DATA_DIR / filename

        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None

        df = pd.read_csv(filepath)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    except pd.errors.ParserError as e:
        logger.error(f"Error parsing CSV file: {e}")
        return None
    except Exception as e:
        logger.error(f"Error loading price data: {e}")
        return None


def calculate_sma(
    prices: pd.Series,
    window: int = 5
) -> pd.Series:
    """
    Calculate Simple Moving Average (SMA).

    Args:
        prices: Pandas Series of prices
        window: Number of periods for the moving average (default: 5)

    Returns:
        Pandas Series with SMA values
    """
    return prices.rolling(window=window).mean()


def analyze_crypto_trend(
    df: pd.DataFrame,
    crypto_id: str,
    sma_window: int = 5
) -> Dict:
    """
    Analyze cryptocurrency trend using SMA and price statistics.

    Args:
        df: DataFrame with price data
        crypto_id: Cryptocurrency ID to filter
        sma_window: Window size for SMA calculation

    Returns:
        Dictionary with trend analysis results
    """
    # Filter data for specific cryptocurrency
    crypto_df = df[df['id'] == crypto_id].copy()

    if len(crypto_df) == 0:
        logger.warning(f"No data found for {crypto_id}")
        return {}

    # Calculate SMA
    crypto_df['sma'] = calculate_sma(crypto_df['price'], window=sma_window)

    # Calculate statistics
    current_price = crypto_df['price'].iloc[-1]
    latest_sma = crypto_df['sma'].iloc[-1]
    price_change_pct = ((current_price - crypto_df['price'].iloc[0]) / crypto_df['price'].iloc[0]) * 100

    analysis = {
        'crypto_id': crypto_id,
        'current_price': current_price,
        'sma': latest_sma,
        'price_change_percent': price_change_pct,
        'min_price': crypto_df['price'].min(),
        'max_price': crypto_df['price'].max(),
        'avg_price': crypto_df['price'].mean(),
        'data_points': len(crypto_df),
        'trend': 'UPTREND' if current_price > latest_sma else 'DOWNTREND',
        'price_above_sma': current_price > latest_sma
    }

    return analysis


def analyze_multiple_trends(
    df: pd.DataFrame,
    sma_window: int = 5
) -> List[Dict]:
    """
    Analyze trends for all cryptocurrencies in the dataset.

    Args:
        df: DataFrame with price data
        sma_window: Window size for SMA calculation

    Returns:
        List of analysis results for each cryptocurrency
    """
    results = []
    for crypto_id in df['id'].unique():
        analysis = analyze_crypto_trend(df, crypto_id, sma_window)
        if analysis:
            results.append(analysis)

    return results


# ============================================================================
# ALERT SYSTEM
# ============================================================================

def check_price_alert(
    current_price: float,
    previous_price: float,
    threshold: float = PRICE_CHANGE_THRESHOLD
) -> Tuple[bool, float]:
    """
    Check if price change exceeds the threshold.

    Args:
        current_price: Current cryptocurrency price
        previous_price: Previous price to compare against
        threshold: Percentage threshold for alert (default: 5%)

    Returns:
        Tuple of (alert_triggered: bool, price_change_percent: float)
    """
    if previous_price == 0:
        return False, 0.0

    price_change = ((current_price - previous_price) / previous_price) * 100

    if abs(price_change) >= threshold:
        return True, price_change

    return False, price_change


def generate_alerts(
    df: pd.DataFrame,
    threshold: float = PRICE_CHANGE_THRESHOLD
) -> List[Dict]:
    """
    Generate alerts for significant price changes.

    Args:
        df: DataFrame with price data
        threshold: Percentage threshold for alerts

    Returns:
        List of alert dictionaries
    """
    alerts = []

    for crypto_id in df['id'].unique():
        crypto_df = df[df['id'] == crypto_id].sort_values('timestamp')

        if len(crypto_df) < 2:
            continue

        current_price = crypto_df['price'].iloc[-1]
        previous_price = crypto_df['price'].iloc[-2]

        alert_triggered, price_change = check_price_alert(
            current_price,
            previous_price,
            threshold
        )

        if alert_triggered:
            alert = {
                'crypto_id': crypto_id,
                'timestamp': crypto_df['timestamp'].iloc[-1],
                'price_change_percent': price_change,
                'previous_price': previous_price,
                'current_price': current_price,
                'direction': 'UP' if price_change > 0 else 'DOWN'
            }
            alerts.append(alert)
            logger.warning(
                f"⚠️  ALERT: {crypto_id.upper()} price changed by {price_change:.2f}% "
                f"(${previous_price:.2f} → ${current_price:.2f})"
            )

    return alerts


def print_alerts(alerts: List[Dict]) -> None:
    """Print formatted alert messages."""
    if not alerts:
        print("✓ No price alerts triggered")
        return

    print("\n" + "="*70)
    print("🚨 PRICE ALERTS")
    print("="*70)
    for alert in alerts:
        symbol = "📈" if alert['direction'] == 'UP' else "📉"
        print(f"\n{symbol} {alert['crypto_id'].upper()}")
        print(f"   Change: {alert['price_change_percent']:+.2f}%")
        print(f"   Price:  ${alert['previous_price']:.2f} → ${alert['current_price']:.2f}")
        print(f"   Time:   {alert['timestamp']}")


# ============================================================================
# VISUALIZATION FUNCTIONS
# ============================================================================

def plot_price_trend(
    df: pd.DataFrame,
    crypto_id: str,
    sma_window: int = 5
) -> Optional[str]:
    """
    Generate a price trend plot with SMA overlay.

    Args:
        df: DataFrame with price data
        crypto_id: Cryptocurrency ID to plot
        sma_window: Window size for SMA

    Returns:
        Path to saved plot file or None if failed
    """
    try:
        crypto_df = df[df['id'] == crypto_id].copy().sort_values('timestamp')

        if len(crypto_df) == 0:
            logger.warning(f"No data to plot for {crypto_id}")
            return None

        # Calculate SMA
        crypto_df['sma'] = calculate_sma(crypto_df['price'], window=sma_window)

        # Create figure
        plt.figure(figsize=(12, 6))
        plt.plot(crypto_df['timestamp'], crypto_df['price'], label='Price', linewidth=2, marker='o')
        plt.plot(crypto_df['timestamp'], crypto_df['sma'], label=f'SMA({sma_window})', 
                linestyle='--', linewidth=2, color='orange')

        plt.title(f'{crypto_id.upper()} Price Trend', fontsize=16, fontweight='bold')
        plt.xlabel('Date/Time', fontsize=12)
        plt.ylabel('Price (USD)', fontsize=12)
        plt.legend(fontsize=10)
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        filename = f"{crypto_id}_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100)
        logger.info(f"Saved plot to {filepath}")

        plt.close()
        return str(filepath)

    except Exception as e:
        logger.error(f"Error creating plot: {e}")
        return None


def plot_multiple_prices(
    df: pd.DataFrame,
    sma_window: int = 5
) -> Optional[str]:
    """
    Generate a multi-panel plot for all cryptocurrencies.

    Args:
        df: DataFrame with price data
        sma_window: Window size for SMA

    Returns:
        Path to saved plot file or None if failed
    """
    try:
        crypto_ids = df['id'].unique()
        num_cryptos = len(crypto_ids)

        fig, axes = plt.subplots(num_cryptos, 1, figsize=(12, 5*num_cryptos))

        # Handle single vs multiple subplots
        if num_cryptos == 1:
            axes = [axes]

        for idx, crypto_id in enumerate(crypto_ids):
            crypto_df = df[df['id'] == crypto_id].copy().sort_values('timestamp')
            crypto_df['sma'] = calculate_sma(crypto_df['price'], window=sma_window)

            ax = axes[idx]
            ax.plot(crypto_df['timestamp'], crypto_df['price'], label='Price', linewidth=2, marker='o')
            ax.plot(crypto_df['timestamp'], crypto_df['sma'], label=f'SMA({sma_window})', 
                   linestyle='--', linewidth=2, color='orange')

            ax.set_title(f'{crypto_id.upper()} Price Trend', fontsize=14, fontweight='bold')
            ax.set_ylabel('Price (USD)', fontsize=10)
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3)

        axes[-1].set_xlabel('Date/Time', fontsize=10)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        filename = f"multi_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = PLOTS_DIR / filename
        plt.savefig(filepath, dpi=100)
        logger.info(f"Saved multi-panel plot to {filepath}")

        plt.close()
        return str(filepath)

    except Exception as e:
        logger.error(f"Error creating multi-panel plot: {e}")
        return None


# ============================================================================
# ML PREPARATION FUNCTIONS
# ============================================================================

def prepare_ml_data(
    df: pd.DataFrame,
    crypto_id: str,
    test_split: float = 0.2
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for machine learning models.

    Creates feature engineering with lagged prices and technical indicators
    suitable for training time-series ML models.

    Args:
        df: DataFrame with price data
        crypto_id: Cryptocurrency ID to prepare
        test_split: Fraction of data to use for testing

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
        Where features include: price, SMA(5), SMA(10), lagged prices
    """
    crypto_df = df[df['id'] == crypto_id].copy().sort_values('timestamp')

    if len(crypto_df) < 20:
        logger.warning(f"Not enough data for ML preparation ({len(crypto_df)} rows)")
        return np.array([]), np.array([]), np.array([]), np.array([])

    # Feature engineering
    crypto_df['sma_5'] = calculate_sma(crypto_df['price'], window=5)
    crypto_df['sma_10'] = calculate_sma(crypto_df['price'], window=10)
    crypto_df['price_lag_1'] = crypto_df['price'].shift(1)
    crypto_df['price_lag_2'] = crypto_df['price'].shift(2)
    crypto_df['price_change'] = crypto_df['price'].pct_change()

    # Remove rows with NaN values
    crypto_df = crypto_df.dropna()

    # Prepare features and target
    feature_cols = ['price', 'sma_5', 'sma_10', 'price_lag_1', 'price_lag_2', 'price_change']
    X = crypto_df[feature_cols].values
    y = crypto_df['price'].values

    # Split data
    split_idx = int(len(X) * (1 - test_split))
    X_train, X_test = X[:split_idx], X[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]

    logger.info(
        f"ML data prepared for {crypto_id}: "
        f"Training={len(X_train)}, Testing={len(X_test)}"
    )

    return X_train, X_test, y_train, y_test


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

def main(
    crypto_ids: Optional[List[str]] = None,
    csv_filename: str = "crypto_prices.csv",
    sma_window: int = 5
) -> bool:
    """
    Main workflow for cryptocurrency tracking and analysis.

    This function orchestrates:
    1. Fetching latest cryptocurrency prices
    2. Storing data in CSV
    3. Analyzing trends
    4. Generating alerts
    5. Creating visualizations
    6. Preparing ML-ready data

    Args:
        crypto_ids: List of cryptocurrency IDs (uses defaults if None)
        csv_filename: CSV file to store data
        sma_window: Window size for moving average calculations

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info("="*70)
        logger.info("CRYPTOCURRENCY TRACKER - STARTING")
        logger.info("="*70)

        # Step 1: Fetch current prices
        logger.info("\n📡 STEP 1: Fetching cryptocurrency prices...")
        crypto_prices = fetch_multiple_cryptocurrencies(crypto_ids)

        if not crypto_prices:
            logger.error("Failed to fetch any cryptocurrency data")
            return False

        # Step 2: Save data
        logger.info("\n💾 STEP 2: Saving price data...")
        save_multiple_prices(csv_filename, crypto_prices)

        # Step 3: Load historical data
        logger.info("\n📊 STEP 3: Loading historical data...")
        df = load_price_data(csv_filename)

        if df is None:
            logger.warning("No historical data available for analysis")
            return False

        # Step 4: Analyze trends
        logger.info("\n📈 STEP 4: Analyzing trends...")
        trends = analyze_multiple_trends(df, sma_window)

        print("\n" + "="*70)
        print("📊 TREND ANALYSIS")
        print("="*70)
        for trend in trends:
            print(f"\n{trend['crypto_id'].upper()}")
            print(f"  Current Price:    ${trend['current_price']:.2f}")
            print(f"  SMA({sma_window}):           ${trend['sma']:.2f}")
            print(f"  Trend:            {trend['trend']}")
            print(f"  Price vs SMA:     {'Above' if trend['price_above_sma'] else 'Below'}")
            print(f"  Min/Max:          ${trend['min_price']:.2f} / ${trend['max_price']:.2f}")
            print(f"  Data Points:      {trend['data_points']}")

        # Step 5: Check alerts
        logger.info("\n⚠️  STEP 5: Checking price alerts...")
        alerts = generate_alerts(df)
        print_alerts(alerts)

        # Step 6: Generate visualizations
        logger.info("\n📉 STEP 6: Generating visualizations...")
        for crypto_id in df['id'].unique():
            plot_price_trend(df, crypto_id, sma_window)

        if len(df['id'].unique()) > 1:
            plot_multiple_prices(df, sma_window)

        # Step 7: Prepare ML data
        logger.info("\n🤖 STEP 7: Preparing ML data...")
        for crypto_id in df['id'].unique():
            X_train, X_test, y_train, y_test = prepare_ml_data(df, crypto_id)
            if len(X_train) > 0:
                print(f"\n✓ ML data ready for {crypto_id}")
                print(f"  Training samples: {len(X_train)}")
                print(f"  Testing samples:  {len(X_test)}")

        logger.info("\n" + "="*70)
        logger.info("✅ CRYPTOCURRENCY TRACKER - COMPLETED SUCCESSFULLY")
        logger.info("="*70)

        return True

    except Exception as e:
        logger.error(f"Unexpected error in main workflow: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Run the main workflow
    # Customize with different cryptocurrencies as needed
    main(
        crypto_ids=["bitcoin", "ethereum"],  # Add more as needed
        csv_filename="crypto_prices.csv",
        sma_window=5
    )

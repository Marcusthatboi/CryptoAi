"""
Example Usage Scenarios
=======================

This file demonstrates various ways to use the cryptocurrency tracker.
Copy and modify these examples for your specific needs.
"""

from src.crypto_tracker import (
    fetch_crypto_price,
    fetch_multiple_cryptocurrencies,
    save_price_data,
    load_price_data,
    analyze_crypto_trend,
    analyze_multiple_trends,
    calculate_sma,
    generate_alerts,
    plot_price_trend,
    plot_multiple_prices,
    prepare_ml_data,
    main,
)


# ============================================================================
# EXAMPLE 1: Simple Price Fetch
# ============================================================================

def example_simple_fetch():
    """Fetch and print current Bitcoin price."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Simple Price Fetch")
    print("="*70)

    price_data = fetch_crypto_price("bitcoin")
    if price_data:
        print(f"Bitcoin Price: ${price_data['price']:.2f}")
        print(f"24h Change: {price_data['price_change_24h']:.2f}%")
        print(f"Market Cap: ${price_data['market_cap']:,.0f}")


# ============================================================================
# EXAMPLE 2: Multi-Cryptocurrency Tracking
# ============================================================================

def example_multi_crypto():
    """Track multiple cryptocurrencies simultaneously."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Multi-Cryptocurrency Tracking")
    print("="*70)

    cryptos = ["bitcoin", "ethereum", "cardano", "solana"]
    prices = fetch_multiple_cryptocurrencies(cryptos)

    print("\nCurrent Prices:")
    print("-" * 50)
    for crypto_id, data in prices.items():
        print(f"{crypto_id:12} | ${data['price']:>10.2f} | "
              f"24h Change: {data['price_change_24h']:>7.2f}%")


# ============================================================================
# EXAMPLE 3: Historical Data Analysis
# ============================================================================

def example_historical_analysis():
    """Analyze historical trends from saved data."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Historical Data Analysis")
    print("="*70)

    df = load_price_data("crypto_prices.csv")

    if df is not None and len(df) > 0:
        print(f"Total records: {len(df)}")
        print(f"Cryptocurrencies tracked: {df['id'].unique().tolist()}")

        # Analyze each cryptocurrency
        for crypto_id in df['id'].unique():
            analysis = analyze_crypto_trend(df, crypto_id, sma_window=5)

            if analysis:
                print(f"\n{crypto_id.upper()}:")
                print(f"  Current Price: ${analysis['current_price']:.2f}")
                print(f"  SMA(5):        ${analysis['sma']:.2f}")
                print(f"  Trend:         {analysis['trend']}")
                print(f"  Min/Max:       ${analysis['min_price']:.2f} / "
                      f"${analysis['max_price']:.2f}")


# ============================================================================
# EXAMPLE 4: Alert System
# ============================================================================

def example_alerts():
    """Generate and display price alerts."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Price Alert System")
    print("="*70)

    df = load_price_data("crypto_prices.csv")

    if df is not None:
        alerts = generate_alerts(df, threshold=3.0)  # 3% threshold

        if alerts:
            print(f"\nFound {len(alerts)} alerts:")
            for alert in alerts:
                print(f"\n  {alert['crypto_id'].upper()}: "
                      f"{alert['price_change_percent']:+.2f}%")
                print(f"    Direction: {alert['direction']}")
                print(f"    Price: ${alert['previous_price']:.2f} → "
                      f"${alert['current_price']:.2f}")
        else:
            print("\nNo alerts triggered at 3% threshold")


# ============================================================================
# EXAMPLE 5: Visualization
# ============================================================================

def example_visualization():
    """Generate price trend plots."""
    print("\n" + "="*70)
    print("EXAMPLE 5: Data Visualization")
    print("="*70)

    df = load_price_data("crypto_prices.csv")

    if df is not None and len(df) > 0:
        # Plot individual cryptocurrencies
        print("\nGenerating individual plots...")
        for crypto_id in df['id'].unique():
            plot_path = plot_price_trend(df, crypto_id, sma_window=5)
            if plot_path:
                print(f"  ✓ Saved: {plot_path}")

        # Plot all together if multiple cryptos
        if len(df['id'].unique()) > 1:
            print("\nGenerating comparison plot...")
            plot_path = plot_multiple_prices(df, sma_window=5)
            if plot_path:
                print(f"  ✓ Saved: {plot_path}")


# ============================================================================
# EXAMPLE 6: ML Data Preparation
# ============================================================================

def example_ml_preparation():
    """Prepare data for machine learning models."""
    print("\n" + "="*70)
    print("EXAMPLE 6: ML Data Preparation")
    print("="*70)

    df = load_price_data("crypto_prices.csv")

    if df is not None:
        for crypto_id in df['id'].unique():
            X_train, X_test, y_train, y_test = prepare_ml_data(df, crypto_id)

            if len(X_train) > 0:
                print(f"\n{crypto_id.upper()}:")
                print(f"  Training samples: {len(X_train)}")
                print(f"  Testing samples:  {len(X_test)}")
                print(f"  Features per sample: {X_train.shape[1]}")
                print(f"  Train features shape: {X_train.shape}")
                print(f"  Test features shape:  {X_test.shape}")


# ============================================================================
# EXAMPLE 7: Custom Save and Load Workflow
# ============================================================================

def example_custom_workflow():
    """Custom workflow: fetch, save, and analyze data."""
    print("\n" + "="*70)
    print("EXAMPLE 7: Custom Workflow")
    print("="*70)

    # Step 1: Fetch latest data
    print("\n[1] Fetching data...")
    cryptos = ["bitcoin", "ethereum"]
    prices = fetch_multiple_cryptocurrencies(cryptos)

    # Step 2: Save to custom file
    print("[2] Saving data to 'custom_prices.csv'...")
    for crypto_id, data in prices.items():
        save_price_data("custom_prices.csv", crypto_id, data)

    # Step 3: Load and analyze
    print("[3] Loading and analyzing...")
    df = load_price_data("custom_prices.csv")

    if df is not None:
        trends = analyze_multiple_trends(df)
        for trend in trends:
            direction = "📈" if trend['price_above_sma'] else "📉"
            print(f"\n  {direction} {trend['crypto_id'].upper()}")
            print(f"     Price: ${trend['current_price']:.2f}")
            print(f"     Trend: {trend['trend']}")


# ============================================================================
# EXAMPLE 8: Full Automated Run
# ============================================================================

def example_automated_run():
    """Run the complete automated workflow."""
    print("\n" + "="*70)
    print("EXAMPLE 8: Full Automated Workflow")
    print("="*70)

    # Run main with custom cryptocurrencies
    main(
        crypto_ids=["bitcoin", "ethereum", "cardano"],
        csv_filename="crypto_prices.csv",
        sma_window=5
    )


# ============================================================================
# MAIN: Run All Examples
# ============================================================================

if __name__ == "__main__":
    import sys

    print("\n" + "="*70)
    print("CRYPTOCURRENCY TRACKER - EXAMPLES")
    print("="*70)

    examples = {
        "1": ("Simple Price Fetch", example_simple_fetch),
        "2": ("Multi-Cryptocurrency Tracking", example_multi_crypto),
        "3": ("Historical Analysis", example_historical_analysis),
        "4": ("Alert System", example_alerts),
        "5": ("Visualization", example_visualization),
        "6": ("ML Data Preparation", example_ml_preparation),
        "7": ("Custom Workflow", example_custom_workflow),
        "8": ("Full Automated Run", example_automated_run),
        "all": ("Run All Examples", None),
    }

    print("\nAvailable Examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")

    # Run all examples by default or specific example if argument provided
    if len(sys.argv) > 1 and sys.argv[1] in examples:
        choice = sys.argv[1]
    else:
        choice = "all"

    print(f"\nRunning: {examples[choice][0]}")

    if choice == "all":
        # Run all examples
        example_simple_fetch()
        example_multi_crypto()
        example_historical_analysis()
        example_alerts()
        example_visualization()
        example_ml_preparation()
        example_custom_workflow()
        # Uncomment to run full automated:
        # example_automated_run()
    else:
        # Run specific example
        examples[choice][1]()

    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)

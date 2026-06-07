import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.multi_source_data import data_manager
import pandas as pd

# Test Yahoo Finance data fetch
print("Testing Yahoo Finance data fetch...")
df = data_manager.get_yahoo_finance("AAPL", period="1y", interval="1d")

if df is not None:
    print(f"✅ Got {len(df)} records")
    print(f"Columns: {df.columns.tolist()}")
    print(f"\nFirst row:")
    print(df.iloc[0])
    print(f"\nData types:")
    print(df.dtypes)
else:
    print("❌ No data returned from get_yahoo_finance")

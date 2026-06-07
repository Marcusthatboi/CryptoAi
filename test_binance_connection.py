#!/usr/bin/env python
"""Test Binance.US API connection"""
import os
import sys

# Set Binance credentials
os.environ['BINANCE_API_KEY'] = 'J7cgYe3cocdIxD3eLmQzpUgAOUPe1r82dRwTr1LfJBRz5k8FKsEsIo3rqzoxIuya'
os.environ['BINANCE_API_SECRET'] = 'j23poQMorMTY3PGCWv3xtOPUGVVrFimtK8QttC37mAUwbXMGf9uvRxAaOvh3KZhP'
os.environ['BINANCE_TLD'] = 'us'
os.environ['BINANCE_TESTNET'] = 'false'

from backend.binance_api import get_client

try:
    print("🔄 Connecting to Binance.US...")
    client = get_client()
    
    print("✅ Connected! Fetching account info...")
    status = client.get_account()
    
    print("\n" + "="*50)
    print("✅ BINANCE.US CONNECTION SUCCESS")
    print("="*50)
    print(f"Account Balance: {len(status['balances'])} assets")
    print(f"Maker Commission: {status['makerCommission']}%")
    print(f"Taker Commission: {status['takerCommission']}%")
    print(f"Account Status: {status['accountType']}")
    
    # Show top 5 balances
    print("\n📊 Top Balances:")
    balances = [b for b in status['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
    for b in balances[:5]:
        free = float(b['free'])
        locked = float(b['locked'])
        if free > 0 or locked > 0:
            print(f"  {b['asset']}: {free} (free), {locked} (locked)")
    
    print("\n✨ Your Binance.US account is ready for auto trading!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
    sys.exit(1)

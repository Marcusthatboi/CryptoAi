"""Test script to verify auto trading indexes"""
import asyncio
from backend.db import get_db

async def check_indexes():
    db = await get_db()
    col = db['auto_trading_settings']
    indexes = await col.list_indexes().to_list(None)
    print('\n✅ Auto Trading Indexes:')
    for idx in indexes:
        print(f"  - {idx['name']}: {idx['key']}")

asyncio.run(check_indexes())

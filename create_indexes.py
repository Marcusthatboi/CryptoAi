"""Create auto trading indexes directly"""
import asyncio
from backend.db import get_db

async def create_indexes():
    print("Creating auto trading indexes...")
    db = await get_db()
    col = db['auto_trading_settings']
    
    try:
        # Create indexes
        idx1 = await col.create_index([("user_id", 1), ("enabled", 1)])
        print(f"✅ Created index: {idx1}")
        
        idx2 = await col.create_index([("user_id", 1), ("symbol", 1)])
        print(f"✅ Created index: {idx2}")
        
        idx3 = await col.create_index([("user_id", 1), ("enabled", 1), ("symbol", 1)])
        print(f"✅ Created index: {idx3}")
        
        # List all indexes
        indexes = await col.list_indexes().to_list(None)
        print("\n📊 All indexes on auto_trading_settings:")
        for idx in indexes:
            print(f"  - {idx['name']}: {dict(idx['key'])}")
            
        print("\n✅ Index creation complete!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_indexes())

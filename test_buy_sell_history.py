"""
Test script to add sample buy/sell transactions to portfolio holdings
This demonstrates the real vs fake investment type feature
"""
import asyncio
from datetime import datetime, timedelta
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

# MongoDB connection
MONGO_URI = "mongodb://localhost:27017"
DB_NAME = "cryptoai"

async def add_sample_transactions():
    """Add sample transactions to user portfolio"""
    
    # Connect to MongoDB
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    users_col = db["users"]
    
    # Check if database has any users
    all_users = await users_col.find({}).to_list(None)
    print(f"📊 Total users in database: {len(all_users)}")
    
    if all_users:
        for user in all_users[:3]:
            print(f"  - {user.get('username')}")
    
    # Find the admin user (case-insensitive)
    admin_user = await users_col.find_one({"username": {"$regex": "^admin$", "$options": "i"}})
    
    if not admin_user:
        print("❌ Admin user not found, trying to find any user...")
        admin_user = await users_col.find_one({})
        if not admin_user:
            print("❌ No users found in database")
            client.close()
            return
        print(f"✅ Using user: {admin_user.get('username')}")
    else:
        print(f"✅ Found admin user: {admin_user.get('username')}")
    
    # Get portfolio
    portfolio = admin_user.get("portfolio", {})
    holdings = portfolio.get("holdings", [])
    
    if not holdings:
        print("❌ No holdings found in portfolio")
        return
    
    print(f"\n📋 Found {len(holdings)} holdings:")
    for h in holdings:
        print(f"  - Symbol: {h.get('symbol')}, Name: {h.get('name')}")
    
    # Add transactions to each holding
    now = datetime.utcnow()
    
    for holding in holdings:
        symbol = holding.get("symbol", "").upper()
        
        # Initialize transactions list if not present
        if "transactions" not in holding:
            holding["transactions"] = []
        
        # Check for Bitcoin
        if symbol == "BITCOIN":
            # Bitcoin: Add fake money transactions (simulated/paper trading)
            holding["transactions"] = [
                {
                    "type": "BUY",
                    "date": (now - timedelta(days=30)).isoformat(),
                    "quantity": 0.1,
                    "price": 45000,
                    "fee": 10,
                },
                {
                    "type": "BUY",
                    "date": (now - timedelta(days=15)).isoformat(),
                    "quantity": 0.15,
                    "price": 50000,
                    "fee": 15,
                },
                {
                    "type": "SELL",
                    "date": (now - timedelta(days=5)).isoformat(),
                    "quantity": 0.05,
                    "price": 62000,
                    "fee": 10,
                    "profit": (62000 - 47500) * 0.05,  # avg cost: (0.1*45000 + 0.15*50000)/(0.1+0.15) = 47500
                },
            ]
            holding["investment_type"] = "fake_money"
            print(f"  ✅ Added {symbol} transactions (fake_money)")
            
        # Check for Ripple
        elif symbol == "RIPPLE":
            # Ripple: Fake transactions
            holding["transactions"] = [
                {
                    "type": "BUY",
                    "date": (now - timedelta(days=25)).isoformat(),
                    "quantity": 1000,
                    "price": 0.5,
                    "fee": 2,
                },
                {
                    "type": "BUY",
                    "date": (now - timedelta(days=10)).isoformat(),
                    "quantity": 500,
                    "price": 0.6,
                    "fee": 1,
                },
                {
                    "type": "SELL",
                    "date": (now - timedelta(days=3)).isoformat(),
                    "quantity": 300,
                    "price": 0.7,
                    "fee": 1,
                    "profit": (0.7 - 0.533333) * 300,  # avg cost: (1000*0.5 + 500*0.6)/(1000+500) = 0.533333
                },
            ]
            holding["investment_type"] = "fake_money"
            print(f"  ✅ Added {symbol} transactions (fake_money)")
        
        else:
            # Default to real_money for other holdings
            holding["investment_type"] = "real_money"
            print(f"  ℹ️  {symbol}: Set to real_money (no transactions added)")
    
    # Update user portfolio
    result = await users_col.update_one(
        {"_id": admin_user["_id"]},
        {"$set": {"portfolio": portfolio}}
    )
    
    if result.modified_count > 0:
        print("✅ Portfolio updated successfully with sample transactions")
        print("\nSample Transactions Added:")
        print("- BTC (REAL): 2 buys + 1 sell")
        print("- ETH (FAKE): 2 buys")
        print("- XRP (FAKE): 1 buy")
    else:
        print("❌ Failed to update portfolio")
    
    # Verify by fetching updated user
    updated_user = await users_col.find_one({"_id": admin_user["_id"]})
    holdings = updated_user.get("portfolio", {}).get("holdings", [])
    
    print("\n📊 Updated Holdings:")
    for holding in holdings:
        symbol = holding.get("symbol", "").upper()
        investment_type = holding.get("investment_type", "unknown")
        transactions = holding.get("transactions", [])
        print(f"  {symbol}: {investment_type} ({len(transactions)} transactions)")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_sample_transactions())

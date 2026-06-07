#!/usr/bin/env python3
"""
Complete Profit Verification & Audit Script
Verifies profit calculation accuracy against database records
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient
from backend.auth import get_user_by_id

async def verify_all_profits():
    """Complete audit of profit calculations"""
    
    # Connect to MongoDB
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client["cryptoai"]
    
    print("=" * 80)
    print("CRYPTOAI PROFIT VERIFICATION AUDIT")
    print("=" * 80)
    
    # Get all users with investments
    users_col = db["users"]
    users = await users_col.find({}).to_list(None)
    
    for user in users:
        username = user.get("username", "unknown")
        portfolio = user.get("portfolio", {})
        holdings = portfolio.get("holdings", [])
        realized_pnl = portfolio.get("realized_pnl", {})
        activity_log = portfolio.get("activity_log", [])
        
        if not holdings:
            continue
        
        print(f"\n{'='*80}")
        print(f"USER: {username}")
        print(f"{'='*80}")
        
        # Group by investment type
        for inv_type in ["fake_money", "real_money"]:
            type_holdings = [h for h in holdings if h.get("investment_type") == inv_type]
            if not type_holdings:
                continue
                
            print(f"\n[{inv_type.upper().replace('_', ' ')}]")
            print(f"{'-'*80}")
            
            total_cost_basis = 0
            total_market_value = 0
            
            print(f"\n{'Symbol':<10} {'Quantity':<15} {'Avg Price':<15} {'Cost Basis':<15} {'Market Price':<15} {'Market Value':<15} {'Unrealized P&L':<15}")
            print(f"{'-'*110}")
            
            for holding in type_holdings:
                symbol = holding.get("symbol", "?")
                quantity = float(holding.get("quantity", 0) or 0)
                avg_price = float(holding.get("average_price", holding.get("price", 0)) or 0)
                current_price = float(holding.get("price", 0) or 0)
                market_value = float(holding.get("total_value", 0) or 0)
                
                cost_basis = quantity * avg_price
                unrealized_pnl = market_value - cost_basis
                
                total_cost_basis += cost_basis
                total_market_value += market_value
                
                print(f"{symbol:<10} {quantity:<15.8f} ${avg_price:<14.2f} ${cost_basis:<14.2f} ${current_price:<14.2f} ${market_value:<14.2f} ${unrealized_pnl:<14.2f}")
            
            print(f"{'-'*110}")
            total_unrealized = total_market_value - total_cost_basis
            total_return_pct = (total_unrealized / total_cost_basis * 100) if total_cost_basis > 0 else 0
            
            print(f"{'TOTAL':<10} {'':<15} {'':<15} ${total_cost_basis:<14.2f} {'':<15} ${total_market_value:<14.2f} ${total_unrealized:<14.2f}")
            print(f"Return: {total_return_pct:.2f}%")
            
            # Compare with stored realized_pnl
            stored_pnl = realized_pnl.get(inv_type, 0)
            print(f"\nStored in DB: ${stored_pnl:.2f}")
            print(f"Calculated:  ${total_unrealized:.2f}")
            
            if abs(stored_pnl - total_unrealized) > 0.01:
                print(f"⚠️  MISMATCH: Difference of ${abs(stored_pnl - total_unrealized):.2f}")
            else:
                print(f"✅ MATCH: Profit calculation is accurate")
        
        # Show activity log
        print(f"\n{'='*80}")
        print("ACTIVITY LOG (Recent 10):")
        print(f"{'-'*80}")
        for activity in activity_log[-10:]:
            event = activity.get("event", "?")
            symbol = activity.get("symbol", "?")
            qty = activity.get("quantity", 0)
            price = activity.get("price", 0)
            inv_type = activity.get("investment_type", "?")
            timestamp = activity.get("timestamp", "?")
            print(f"{event:<8} {symbol:<10} {qty:<12.8f} @ ${price:<12.2f} ({inv_type}) - {timestamp}")
    
    print(f"\n{'='*80}")
    print("AUDIT COMPLETE")
    print(f"{'='*80}\n")
    
    client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(verify_all_profits())

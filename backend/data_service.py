"""
Data service for caching and storing trading data
"""
from datetime import datetime, timedelta
from backend.db import get_db, COLLECTIONS
import logging

logger = logging.getLogger(__name__)

class DataService:
    """Service for managing cached data in MongoDB"""
    
    @staticmethod
    async def cache_price(symbol: str, price: float, bid: float = None, ask: float = None, timestamp: str = None):
        """Cache price data"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["prices"]]
            
            doc = {
                "symbol": symbol.upper(),
                "price": price,
                "bid": bid,
                "ask": ask,
                "timestamp": timestamp or datetime.utcnow().isoformat(),
                "cached_at": datetime.utcnow().isoformat()
            }
            
            await col.insert_one(doc)
            logger.debug(f"✅ Cached price for {symbol}: ${price}")
        except Exception as e:
            logger.error(f"❌ Error caching price: {e}")
    
    @staticmethod
    async def get_price_history(symbol: str, days: int = 1) -> list:
        """Get cached price history"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["prices"]]
            
            since = datetime.utcnow() - timedelta(days=days)
            cursor = col.find({
                "symbol": symbol.upper(),
                "cached_at": {"$gte": since.isoformat()}
            }).sort("cached_at", 1)
            
            history = await cursor.to_list(length=None)
            return history
        except Exception as e:
            logger.error(f"❌ Error fetching price history: {e}")
            return []
    
    @staticmethod
    async def save_order(account_id: str, order_data: dict):
        """Save order to database"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["orders"]]
            
            doc = {
                "account_id": account_id,
                **order_data,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = await col.insert_one(doc)
            logger.info(f"✅ Saved order: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"❌ Error saving order: {e}")
            return None
    
    @staticmethod
    async def get_orders(account_id: str, limit: int = 50) -> list:
        """Get orders for account"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["orders"]]
            
            cursor = col.find({"account_id": account_id}).sort("created_at", -1).limit(limit)
            orders = await cursor.to_list(length=None)
            return orders
        except Exception as e:
            logger.error(f"❌ Error fetching orders: {e}")
            return []
    
    @staticmethod
    async def save_portfolio_snapshot(account_id: str, account_info: dict, holdings: list):
        """Save portfolio snapshot"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["portfolio"]]
            
            doc = {
                "account_id": account_id,
                "account_info": account_info,
                "holdings": holdings,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await col.insert_one(doc)
            logger.info(f"✅ Saved portfolio snapshot: {result.inserted_id}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"❌ Error saving portfolio: {e}")
            return None
    
    @staticmethod
    async def get_portfolio_history(account_id: str, limit: int = 100) -> list:
        """Get portfolio history"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["portfolio"]]
            
            cursor = col.find({"account_id": account_id}).sort("timestamp", -1).limit(limit)
            history = await cursor.to_list(length=None)
            return history
        except Exception as e:
            logger.error(f"❌ Error fetching portfolio history: {e}")
            return []
    
    @staticmethod
    async def save_alert(account_id: str, symbol: str, threshold: float, alert_type: str = "price"):
        """Save price alert"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["alerts"]]
            
            doc = {
                "account_id": account_id,
                "symbol": symbol.upper(),
                "threshold": threshold,
                "type": alert_type,
                "created_at": datetime.utcnow().isoformat(),
                "active": True
            }
            
            result = await col.insert_one(doc)
            logger.info(f"✅ Created alert for {symbol}")
            return result.inserted_id
        except Exception as e:
            logger.error(f"❌ Error saving alert: {e}")
            return None
    
    @staticmethod
    async def get_alerts(account_id: str) -> list:
        """Get active alerts"""
        try:
            db = await get_db()
            col = db[COLLECTIONS["alerts"]]
            
            cursor = col.find({"account_id": account_id, "active": True})
            alerts = await cursor.to_list(length=None)
            return alerts
        except Exception as e:
            logger.error(f"❌ Error fetching alerts: {e}")
            return []

# Global data service instance
data_service = DataService()

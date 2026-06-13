"""
MongoDB database configuration and utilities
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# MongoDB connection
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "cryptoai")
MONGO_MAX_POOL_SIZE = int(os.getenv("MONGO_MAX_POOL_SIZE", "100"))
MONGO_MIN_POOL_SIZE = int(os.getenv("MONGO_MIN_POOL_SIZE", "10"))
MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "5000"))
MONGO_CONNECT_TIMEOUT_MS = int(os.getenv("MONGO_CONNECT_TIMEOUT_MS", "5000"))

client = None
db = None

async def connect_db():
    """Connect to MongoDB"""
    global client, db
    try:
        client = AsyncIOMotorClient(
            MONGO_URL,
            maxPoolSize=MONGO_MAX_POOL_SIZE,
            minPoolSize=MONGO_MIN_POOL_SIZE,
            serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT_MS,
            connectTimeoutMS=MONGO_CONNECT_TIMEOUT_MS,
            retryWrites=True,
        )
        db = client[DB_NAME]
        # Verify connection
        await client.admin.command('ping')
        logger.info(f"✅ Connected to MongoDB: {DB_NAME}")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

async def close_db():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

async def get_db() -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if db is None:
        await connect_db()
    return db

# Collection names
COLLECTIONS = {
    "prices": "prices",           # Historical price data
    "orders": "orders",           # Trade orders
    "portfolio": "portfolio",     # Portfolio snapshots
    "alerts": "alerts",           # Price alerts
    "ad_campaigns": "ad_campaigns", # Sponsored ad campaigns
    "ad_events": "ad_events",     # Ad impressions and clicks
    "trades": "trades",           # Executed trades
    "settings": "settings",       # User settings
    "users": "users",             # User accounts with authentication
}

async def init_collections():
    """Initialize MongoDB collections with indexes"""
    database = await get_db()
    
    try:
        # Create collections and indexes
        prices_col = database[COLLECTIONS["prices"]]
        await prices_col.create_index([("symbol", 1), ("timestamp", 1)])
        logger.info("✅ Created prices collection with indexes")
        
        orders_col = database[COLLECTIONS["orders"]]
        await orders_col.create_index([("account_id", 1), ("created_at", -1)])
        logger.info("✅ Created orders collection with indexes")
        
        portfolio_col = database[COLLECTIONS["portfolio"]]
        await portfolio_col.create_index([("account_id", 1), ("timestamp", -1)])
        logger.info("✅ Created portfolio collection with indexes")
        
        trades_col = database[COLLECTIONS["trades"]]
        await trades_col.create_index([("account_id", 1), ("executed_at", -1)])
        logger.info("✅ Created trades collection with indexes")
        
        alerts_col = database[COLLECTIONS["alerts"]]
        await alerts_col.create_index([("account_id", 1), ("symbol", 1)])
        logger.info("✅ Created alerts collection with indexes")

        ad_campaigns_col = database[COLLECTIONS["ad_campaigns"]]
        await ad_campaigns_col.create_index([("placement", 1), ("status", 1), ("remaining_budget_cents", -1)])
        await ad_campaigns_col.create_index([("created_at", -1)])
        logger.info("✅ Created ad_campaigns collection with indexes")

        ad_events_col = database[COLLECTIONS["ad_events"]]
        await ad_events_col.create_index([("campaign_id", 1), ("event_type", 1), ("created_at", -1)])
        await ad_events_col.create_index([("campaign_id", 1), ("created_at", -1)])
        logger.info("✅ Created ad_events collection with indexes")
        
        # Users collection with unique username index
        users_col = database[COLLECTIONS["users"]]
        await users_col.create_index([("username", 1)], unique=True)
        await users_col.create_index([("email", 1)], unique=False)
        logger.info("✅ Created users collection with indexes")
        
        # Auto Trading Settings collection indexes (CRITICAL for performance)
        auto_trading_col = database["auto_trading_settings"]
        await auto_trading_col.create_index([("user_id", 1), ("enabled", 1)])
        await auto_trading_col.create_index([("user_id", 1), ("symbol", 1)])
        await auto_trading_col.create_index([("user_id", 1), ("enabled", 1), ("symbol", 1)])
        logger.info("✅ Created auto_trading_settings collection with indexes")
        
    except Exception as e:
        logger.error(f"⚠️ Error initializing collections: {e}")

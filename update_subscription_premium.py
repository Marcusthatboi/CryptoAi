#!/usr/bin/env python
"""Update subscription to premium in the subscriptions collection"""
from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['cryptoai']

# Get user
user = db['users'].find_one({'username': 'testuser_autotrading'})
user_id = str(user.get('_id'))

# Update subscription record
result = db['subscriptions'].update_one(
    {'user_id': user_id},
    {'$set': {
        'tier': 'premium',
        'status': 'active',
        'updated_at': datetime.utcnow()
    }}
)

if result.matched_count > 0:
    print('✅ Subscription updated to PREMIUM!')
    print(f'Matched: {result.matched_count}, Modified: {result.modified_count}')
    
    # Verify
    sub = db['subscriptions'].find_one({'user_id': user_id})
    print(f'Current tier: {sub.get("tier")}')
    print(f'Status: {sub.get("status")}')
else:
    print('❌ Subscription not found')

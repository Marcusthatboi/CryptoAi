#!/usr/bin/env python
"""Upgrade test user to Premium tier"""
from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['cryptoai']

# Update the test user to Premium tier
result = db['users'].update_one(
    {'username': 'testuser_autotrading'},
    {'$set': {
        'subscription_tier': 'premium',
        'subscription_status': 'active',
        'subscription_start_date': datetime.utcnow(),
        'subscription_end_date': datetime.utcnow() + timedelta(days=365),
        'subscription_plan': 'premium'
    }}
)

if result.matched_count > 0:
    print('✅ User upgraded to PREMIUM successfully!')
    print(f'Matched: {result.matched_count}, Modified: {result.modified_count}')
    
    # Verify the upgrade
    user = db['users'].find_one({'username': 'testuser_autotrading'})
    print(f'Current tier: {user.get("subscription_tier")}')
else:
    print('❌ User not found in database')
    print('Available users:')
    for user in db['users'].find({}, {'username': 1}).limit(5):
        print(f"  - {user.get('username')}")

#!/usr/bin/env python
"""Test the subscription API to see what it returns"""
import requests
import json
from pymongo import MongoClient

# Get the user's info from DB
client = MongoClient('mongodb://localhost:27017')
db = client['cryptoai']
user = db['users'].find_one({'username': 'testuser_autotrading'})

if user:
    print(f"✅ User found in database: {user.get('username')}")
    print(f"   Tier in DB: {user.get('subscription_tier')}")
    print(f"   ID in DB: {user.get('_id')}")
    print()
    
    # Now test if we can call the subscription API
    # We need the user ID - it should be the MongoDB _id
    user_id = str(user.get('_id'))
    
    print(f"Testing subscription endpoint...")
    print(f"User ID: {user_id}")
    
    # The subscription API should accept the user ID
    # Let's check the database directly instead
    sub = db['subscriptions'].find_one({'user_id': user_id})
    if sub:
        print(f"\n✅ Subscription found:")
        print(json.dumps(sub, default=str, indent=2))
    else:
        print(f"\n❌ No subscription record found in 'subscriptions' collection")
        print("   (It might be stored in 'users' collection instead)")
        print(f"   Subscription info in users collection:")
        for key in ['subscription_tier', 'subscription_status', 'subscription_plan', 'subscription_start_date', 'subscription_end_date']:
            print(f"      {key}: {user.get(key)}")
else:
    print("❌ User not found")

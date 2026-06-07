#!/usr/bin/env python
"""Test the preview endpoint directly"""
import asyncio
import httpx
from pymongo import MongoClient
from bson import ObjectId

async def test_preview():
    # Get user from DB
    client = MongoClient('mongodb://localhost:27017')
    db = client['cryptoai']
    user = db['users'].find_one({'username': 'testuser_autotrading'})
    user_id = str(user['_id'])
    
    # Get the token first (need to login)
    print(f"User ID: {user_id}")
    print(f"User: {user}")
    
    # Check subscription
    sub = db['subscriptions'].find_one({'user_id': user_id})
    print(f"Subscription: {sub}")
    
    # Make request to preview endpoint
    async with httpx.AsyncClient() as client:
        # First login to get token
        login_response = await client.post(
            'http://127.0.0.1:8002/api/auth/login',
            json={
                'username': 'testuser_autotrading',
                'password': 'TestPassword123!'
            }
        )
        print(f"Login response: {login_response.status_code}")
        login_data = login_response.json()
        token = login_data.get('access_token')
        print(f"Token: {token[:20]}..." if token else "No token")
        
        if token:
            # Now try preview endpoint
            preview_response = await client.post(
                'http://127.0.0.1:8002/api/auto-trading/preview',
                json={
                    'symbol': 'BTCUSDT',
                    'action': 'BUY',
                    'quantity': 0.001,
                    'stop_loss': 59000,
                    'take_profit': 65000,
                    'acknowledge_risks': True,
                    'acknowledge_losses': True,
                    'acknowledge_ai_failures': True
                },
                headers={
                    'Authorization': f'Bearer {token}'
                }
            )
            print(f"Preview response status: {preview_response.status_code}")
            print(f"Preview response: {preview_response.json()}")

# Run the test
asyncio.run(test_preview())

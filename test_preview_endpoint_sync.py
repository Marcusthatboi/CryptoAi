#!/usr/bin/env python
"""Test the preview endpoint directly"""
import httpx
import json

def test_preview_sync():
    # Make request to preview endpoint using sync httpx
    client = httpx.Client()
    
    try:
        # First login to get token
        print("Attempting login...")
        login_response = client.post(
            'http://127.0.0.1:8002/auth/login',
            json={
                'username': 'testuser_autotrading',
                'password': 'TestPassword123!'
            }
        )
        print(f"Login response status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
        
        login_data = login_response.json()
        print(f"Login data: {login_data}")
        token = login_data.get('access_token')
        print(f"Token obtained: {token[:30]}..." if token else "No token")
        
        if token:
            # Now try preview endpoint
            print("\nAttempting preview trade...")
            preview_response = client.post(
                'http://127.0.0.1:8002/api/auto-trading/preview',
                json={
                    'symbol': 'BTCUSDT',
                    'action': 'BUY',
                    'quantity': 0.001,
                    'stop_loss': 59000,
                    'take_profit': 65000,
                    'acknowledgement_risks_understood': True,
                    'acknowledgement_terms_accepted': True
                },
                headers={
                    'Authorization': f'Bearer {token}'
                }
            )
            print(f"Preview response status: {preview_response.status_code}")
            print(f"Preview response: {preview_response.json()}")
    finally:
        client.close()

test_preview_sync()

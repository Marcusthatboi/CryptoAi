import os
from dotenv import load_dotenv

# This is what the backend does
load_dotenv()

print('Environment variables after load_dotenv:')
alpaca_key = os.getenv("ALPACA_API_KEY")
alpaca_secret = os.getenv("ALPACA_SECRET_KEY")
alpaca_url = os.getenv("ALPACA_API_BASE_URL")

print(f'ALPACA_API_KEY present: {bool(alpaca_key)}')
if alpaca_key:
    print(f'  Value: {alpaca_key[:20]}...')
print(f'ALPACA_SECRET_KEY present: {bool(alpaca_secret)}')
if alpaca_secret:
    print(f'  Value: {alpaca_secret[:20]}...')
print(f'ALPACA_API_BASE_URL: {alpaca_url}')

# Now test the alpaca_api module
print('\n--- Testing alpaca_api module ---')
from backend.alpaca_api import is_authenticated, get_alpaca_client, AlpacaAuthError

try:
    print('Calling is_authenticated()...')
    result = is_authenticated()
    print(f'is_authenticated() returned: {result}')
except AlpacaAuthError as e:
    print(f'AlpacaAuthError: {e}')
except Exception as e:
    import traceback
    print(f'Exception: {e}')
    traceback.print_exc()

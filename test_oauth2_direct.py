import requests

url = "https://authx.alpaca.markets/v1/oauth2/token"

payload = {
    "grant_type": "client_credentials",
    "client_id": "AKSF5FVOKXYKG4ATGCJQBA",
    "client_secret": "MFRGGZDFMZTWQYLCMNSGKZTHNBQWEY3EMVTGO2DBMJRWIZLGM5UGCYTDMRSWMZ3I"
}
headers = {
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded"
}

print("Testing OAuth2 token endpoint...")
print(f"URL: {url}")
print(f"Client ID: {payload['client_id']}")

response = requests.post(url, data=payload, headers=headers)

print(f"\nStatus Code: {response.status_code}")
print(f"Response:\n{response.text}")

if response.status_code == 200:
    token_data = response.json()
    print(f"\n✅ SUCCESS!")
    print(f"Access Token: {token_data.get('access_token', 'N/A')[:30]}...")
    print(f"Expires In: {token_data.get('expires_in')} seconds")
    print(f"Token Type: {token_data.get('token_type')}")
else:
    print(f"\n❌ FAILED")
    try:
        error_data = response.json()
        print(f"Error: {error_data}")
    except:
        print(f"Error: {response.text}")

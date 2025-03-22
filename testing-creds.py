import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Load credentials
client_id = os.getenv("ZOOM_CLIENT_ID")
client_secret = os.getenv("ZOOM_CLIENT_SECRET")
account_id = os.getenv("ZOOM_ACCOUNT_ID")

# Get token
url = "https://zoom.us/oauth/token"
data = {
    "grant_type": "account_credentials",
    "account_id": account_id,
    "client_id": client_id,
    "client_secret": client_secret
}
response = requests.post(url, data=data)
print(f"Response status: {response.status_code}")
print(f"Response body: {response.text}")

if response.status_code == 200:
    token = response.json()["access_token"]
    print(f"Token: {token[:10]}...")  # Print just the beginning for security
    
    # Test the token with a simple API call
    headers = {"Authorization": f"Bearer {token}"}
    test_url = "https://api.zoom.us/v2/users/me"
    test_response = requests.get(test_url, headers=headers)
    print(f"Test API call status: {test_response.status_code}")
    print(f"Test API call response: {test_response.text}")
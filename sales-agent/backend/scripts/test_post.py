import requests
import json

url = "http://localhost:8000/api/campaigns/"
data = {
    "name": "Test Campaign",
    "product_description": "Test Product",
    "target_industry": "Tech",
    "company_size": "All",
    "target_regions": ["US"]
}

try:
    print(f"Sending POST to {url}...")
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

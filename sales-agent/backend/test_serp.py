"""Test SerpAPI Status"""
import os
import requests

# Get API key from env file
api_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if 'SERP' in line and '=' in line:
                key, val = line.strip().split('=', 1)
                if 'KEY' in key:
                    api_key = val.strip()
                    break
except:
    pass

if not api_key:
    print('No SerpAPI key found')
else:
    print(f'Testing SerpAPI...')
    print(f'Key: {api_key[:15]}...')
    
    url = 'https://serpapi.com/search'
    params = {
        'engine': 'google',
        'q': 'test search',
        'api_key': api_key
    }
    
    try:
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            print('\n✅ SerpAPI is WORKING!')
            data = resp.json()
            results = data.get('organic_results', [])
            print(f'Results found: {len(results)}')
        elif resp.status_code == 429:
            print('\n❌ SerpAPI QUOTA EXHAUSTED!')
            print('You have used all your free searches for the month.')
            print('\nOptions:')
            print('1. Wait until next month for quota reset')
            print('2. Upgrade to paid SerpAPI plan')
            print('3. Use a different SerpAPI key')
        else:
            print(f'\n❌ SerpAPI Error: {resp.status_code}')
            print(resp.text[:300])
    except Exception as e:
        print(f'Error: {e}')

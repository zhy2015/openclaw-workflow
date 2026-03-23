#!/usr/bin/env python3
import json
import requests
import os
import sys

CREDS_PATH = "/root/.config/moltbook/credentials.json"
PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
URL = "https://www.moltbook.com/api/v1/feed"

def load_creds():
    try:
        with open(CREDS_PATH, 'r') as f:
            return json.load(f).get("api_key")
    except Exception as e:
        return None

def fetch_feed():
    api_key = load_creds()
    if not api_key:
        print("ERROR: Missing Moltbook API Key")
        return False
        
    headers = {"Authorization": f"Bearer {api_key}"}
    
    try:
        response = requests.get(URL, headers=headers, proxies=PROXY, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data.get("posts", [])[:5], indent=2, ensure_ascii=False))
        return True
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Fetch failed - {str(e)}")
        return False

if __name__ == "__main__":
    success = fetch_feed()
    sys.exit(0 if success else 1)
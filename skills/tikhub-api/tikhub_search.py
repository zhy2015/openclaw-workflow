#!/usr/bin/env python3
import requests
import json
import argparse
import sys
import os

def search_notes(api_key, keyword, page=1):
    url = "https://api.tikhub.io/api/v1/xiaohongshu/app_v2/search_notes"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "keyword": keyword,
        "page": page,
        "sort_type": "general",
        "note_type": "不限",
        "time_filter": "不限"
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Request Error: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="TikHub Xiaohongshu Search API Client")
    parser.add_argument("--keyword", required=True, help="Search keyword")
    parser.add_argument("--page", type=int, default=1, help="Page number (starts from 1)")
    parser.add_argument("--api-key", help="TikHub API Key (or set TIKHUB_API_KEY env var)")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("TIKHUB_API_KEY")
    if not api_key:
        print("Error: API Key is required. Pass via --api-key or TIKHUB_API_KEY env var.", file=sys.stderr)
        sys.exit(1)
        
    result = search_notes(api_key, args.keyword, args.page)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

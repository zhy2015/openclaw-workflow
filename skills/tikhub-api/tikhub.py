#!/usr/bin/env python3
import requests
import json
import argparse
import sys
import os

def get_note_info(api_key, note_id=None, share_text=None):
    url = "https://api.tikhub.io/api/v1/xiaohongshu/app/get_note_info"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    params = {}
    if note_id:
        params["note_id"] = note_id
    elif share_text:
        params["share_text"] = share_text
    else:
        print("Error: Must provide either note_id or share_text", file=sys.stderr)
        sys.exit(1)
        
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
    parser = argparse.ArgumentParser(description="TikHub Xiaohongshu API Client")
    parser.add_argument("--note-id", help="The note ID to fetch")
    parser.add_argument("--share-text", help="The share text/link to fetch")
    parser.add_argument("--api-key", help="TikHub API Key (or set TIKHUB_API_KEY env var)")
    
    args = parser.parse_args()
    
    api_key = args.api_key or os.environ.get("TIKHUB_API_KEY")
    if not api_key:
        print("Error: API Key is required. Pass via --api-key or TIKHUB_API_KEY env var.", file=sys.stderr)
        sys.exit(1)
        
    if not args.note_id and not args.share_text:
        print("Error: Must provide either --note-id or --share-text", file=sys.stderr)
        sys.exit(1)
        
    result = get_note_info(api_key, args.note_id, args.share_text)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()

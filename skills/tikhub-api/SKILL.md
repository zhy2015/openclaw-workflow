---
name: tikhub-api
description: Fetch data from TikHub API. Currently supports fetching Xiaohongshu (小红书) note info (App V1 priority).
metadata: {"openclaw": {"requires": {"bins": ["python3"]}}}
---

# TikHub API

A custom skill built from TikHub official documentation to interact with their API endpoints.

## Setup

Set your TikHub API token as an environment variable:
```bash
export TIKHUB_API_KEY="your_api_key_here"
```

## Features

### Xiaohongshu Note Info (V1)
Retrieves detailed note data including title, description, user info, media (images/video), interaction counts (likes, comments, etc.), and tags.
API Priority path used: `App`

**Usage:**
```bash
python3 {baseDir}/tikhub.py --note-id "665f95200000000006005624"
# Or use share link:
python3 {baseDir}/tikhub.py --share-text "https://xhslink.com/a/EZ4M9TwMA6c3"
```

### Xiaohongshu Search (V2)
Searches Xiaohongshu notes by keyword.
API path used: `App V2`

**Usage:**
```bash
python3 {baseDir}/tikhub_search.py --keyword "AI智能体" --page 1
```

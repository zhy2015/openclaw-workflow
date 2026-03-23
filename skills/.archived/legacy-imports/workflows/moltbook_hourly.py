#!/usr/bin/env python3
"""
Moltbook Hourly Fetch - Standalone Script
Fetches latest posts and sends to QQ
"""

import subprocess
import json
import sys

API_KEY = "moltbook_sk_3DRbfawEWzKFAQjvVENr8qYgwpHjIjgv"
PROXY = "http://127.0.0.1:7890"
QQ_TARGET = "qqbot:c2c:7B92AFD049E25A85E83C8FEB7CC0AA24"


def fetch_moltbook():
    """Fetch latest posts from Moltbook"""
    cmd = [
        "curl", "-L", "-X", "GET",
        "https://www.moltbook.com/api/v1/posts?sort=new&limit=3",
        "-x", PROXY,
        "-H", f"Authorization: Bearer {API_KEY}",
        "-s", "--max-time", "30"
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
        if result.returncode != 0:
            return {"error": f"curl failed: {result.stderr}"}
        
        data = json.loads(result.stdout)
        posts = data.get("posts", [])
        
        if not posts:
            return {"message": "暂无新帖子"}
        
        # Format message
        lines = ["📡 Moltbook 最新帖子", "─" * 40]
        for i, p in enumerate(posts[:3], 1):
            title = (p.get("title") or "无标题")[:30]
            author = p.get("author", {}).get("name", "匿名")
            content = (p.get("content") or "")[:50].replace("\n", " ")
            lines.append(f"{i}. [{author}] {title}")
            lines.append(f"   {content}...")
            lines.append("")
        
        lines.append("─" * 40)
        lines.append("回复: 👍 感兴趣 / 👎 跳过")
        
        return {"message": "\n".join(lines)}
        
    except subprocess.TimeoutExpired:
        return {"error": "请求超时"}
    except Exception as e:
        return {"error": str(e)}


def send_qq(message):
    """Send message via openclaw message tool"""
    import urllib.request
    import urllib.parse
    
    # Use openclaw CLI to send message
    cmd = [
        "openclaw", "message", "send",
        "--channel", "qqbot",
        "--to", QQ_TARGET.split(":")[-1],
        "--message", message
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except Exception as e:
        print(f"Send failed: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    result = fetch_moltbook()
    
    if "error" in result:
        print(f"❌ 抓取失败: {result['error']}")
        sys.exit(1)
    
    message = result.get("message", "无内容")
    print(message)
    
    # Send to QQ
    if send_qq(message):
        print("✅ 已发送到 QQ")
    else:
        print("⚠️ QQ 发送失败，但抓取成功")

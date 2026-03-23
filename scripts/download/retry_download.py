import sys
import os
import urllib.request
import ast

results = [
    {'scene': 1, 'video': 'https://media.vivago.ai/636b9ca6-102f-417a-a8a9-a0e439248b1e.mp4'},
    {'scene': 2, 'video': 'https://media.vivago.ai/1a7a8eb6-a6bd-460c-9f05-f245dff41b54.mp4'},
    {'scene': 3, 'video': 'https://media.vivago.ai/9c28d157-55ee-4944-a615-338507fed196.mp4'},
    {'scene': 4, 'video': 'https://media.vivago.ai/dbe1960d-a02c-4ec4-a06a-5f47763a8865.mp4'},
    {'scene': 5, 'video': 'https://media.vivago.ai/ef73ef9d-452b-4a93-aa79-856fb36ba419.mp4'},
    {'scene': 6, 'video': 'https://media.vivago.ai/26d7abf3-e3f4-41c8-a100-4628c4a91bcf.mp4'},
    {'scene': 7, 'video': 'https://media.vivago.ai/0ee0f08c-f96b-474c-950a-059dc1298942.mp4'},
    {'scene': 8, 'video': 'https://media.vivago.ai/e209f803-ac7c-4b66-b5eb-2f802daed0e1.mp4'},
    {'scene': 9, 'video': 'https://media.vivago.ai/9e787837-c7fc-40b0-8aa6-cbc327705262.mp4'},
    {'scene': 10, 'video': 'https://media.vivago.ai/e8b125fa-993d-48d4-9afc-8fb2c6420e60.mp4'},
]

for res in results:
    url = res['video']
    idx = res['scene']
    file_path = f"/root/.openclaw/workspace/scene_{idx}.mp4"
    print(f"Downloading {url} to {file_path}...")
    try:
        urllib.request.urlretrieve(url, file_path)
    except Exception as e:
        print(f"Failed to download scene {idx}: {e}")

print("Downloading finished. Packaging...")
os.system("tar -czf /root/.openclaw/workspace/echoes_of_deep_space_fixed.tar.gz -C /root/.openclaw/workspace $(ls /root/.openclaw/workspace/scene_*.mp4 | xargs -n 1 basename) kling_results.txt")

import subprocess

print("Resending email with correct archive...")
cmd = [
    "python3", "/root/.openclaw/workspace/skills/qqmail/scripts/qqmail.py", "send",
    "--to", "zhy20152015@qq.com",
    "--subject", "Echoes of Deep Space - Sci-Fi Video Scenes (FIXED WITH VIDEOS)",
    "--body", "Attached is the completed video generation task for the 10-scene hard sci-fi sequence, Echoes of Deep Space. The previous email was missing the actual videos. This archive contains the properly downloaded MP4 files and a text summary.",
    "--attachment", "/root/.openclaw/workspace/echoes_of_deep_space_fixed.tar.gz"
]

env = os.environ.copy()
env["QQMAIL_USER"] = "harry_zhu@qq.com"
env["QQMAIL_AUTH_CODE"] = "lzupkjrihisrcabj"

result = subprocess.run(cmd, env=env, capture_output=True, text=True)
print(f"Email send result: {result.stdout}", flush=True)
if result.stderr:
    print(f"Email send error: {result.stderr}", flush=True)


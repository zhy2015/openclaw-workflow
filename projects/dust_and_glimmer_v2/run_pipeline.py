#!/usr/bin/env python3
"""
dust_and_glimmer Pipeline v2 - 使用 hidream-api-gen Skill
串行生成 + 限流 + 重试 + 断点续传
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加 Skill 路径
sys.path.insert(0, '/root/.openclaw/workspace/skills/hidream-api-gen')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hidream-api-gen/scripts')
sys.path.insert(0, '/root/.openclaw/workspace/skills/hidream-api-gen/scripts/common')

from base_video import submit_task_and_poll_result

PROJECT_DIR = Path(__file__).parent
STATE_FILE = PROJECT_DIR / "state.json"
LOG_FILE = PROJECT_DIR / "logs" / "pipeline.log"
SCENES_DIR = PROJECT_DIR / "scenes"

# 从环境变量或配置文件读取授权
AUTHORIZATION = os.getenv("OPENCLAW_AUTHORIZATION", "")

# 限流器
class RateLimiter:
    def __init__(self, rpm=60):
        self.rpm = rpm
        self.requests = []
        self.window = 60
    
    def wait_if_needed(self):
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window]
        if len(self.requests) >= self.rpm:
            sleep_time = self.window - (now - min(self.requests))
            if sleep_time > 0:
                log(f"Rate limit hit, waiting {sleep_time:.1f}s...")
                time.sleep(sleep_time)
        self.requests.append(time.time())

# 日志
def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    LOG_FILE.parent.mkdir(exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

# 加载/保存状态
def load_state():
    with open(STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    state['updated_at'] = datetime.now().isoformat()
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

# 生成单个场景
def generate_scene(scene, limiter: RateLimiter, max_retries=5):
    scene_id = scene['id']
    prompt = scene['prompt']
    output_file = SCENES_DIR / f"scene_{scene_id:02d}.mp4"
    
    log(f"Scene {scene_id}: Starting generation...")
    log(f"  Prompt: {prompt[:50]}...")
    
    for attempt in range(max_retries):
        try:
            # 限流等待
            limiter.wait_if_needed()
            
            # 构建 payload
            payload = {
                "module": "sora",
                "version": "sora-2-p",
                "request_id": f"dust_glimmer_{scene_id}_{int(time.time())}",
                "prompt": prompt,
                "images": [],
                "resolution": "720p",
                "wh_ratio": "16:9",
                "duration": 8,
            }
            
            log(f"  Attempt {attempt + 1}/{max_retries}: Calling Sora 2 Pro...")
            scene['status'] = 'generating'
            scene['started_at'] = datetime.now().isoformat()
            save_state(load_state())
            
            # 调用 API
            result = submit_task_and_poll_result(
                payload=payload,
                path="/api/v1/video/generate",
                authorization=AUTHORIZATION,
                poll_timeout=300
            )
            
            # 检查成功
            if result and result.get('code') == 0:
                sub_results = result.get('result', {}).get('sub_task_results', [])
                if sub_results:
                    video_url = sub_results[0].get('video_url')
                    if video_url:
                        # 下载视频
                        import requests
                        log(f"  Downloading video...")
                        r = requests.get(video_url, timeout=60)
                        if len(r.content) > 1000:
                            with open(output_file, 'wb') as f:
                                f.write(r.content)
                            scene['status'] = 'completed'
                            scene['video'] = str(output_file)
                            scene['completed_at'] = datetime.now().isoformat()
                            log(f"  ✓ Scene {scene_id} completed! ({len(r.content)} bytes)")
                            return True
                        else:
                            raise Exception(f"Downloaded file too small: {len(r.content)} bytes")
                    else:
                        raise Exception("No video_url in result")
                else:
                    raise Exception("No sub_task_results in result")
            else:
                raise Exception(f"API error: {result}")
                
        except Exception as e:
            error_msg = str(e)
            log(f"  ✗ Attempt {attempt + 1} failed: {error_msg}")
            scene['retries'] = scene.get('retries', 0) + 1
            scene['error'] = error_msg
            
            # 指数退避
            if attempt < max_retries - 1:
                backoff = min(2 ** attempt, 60)
                log(f"  Retrying in {backoff}s...")
                time.sleep(backoff)
    
    # 全部失败
    scene['status'] = 'failed'
    log(f"  ✗ Scene {scene_id} failed after {max_retries} attempts")
    return False

# 主流程
def main():
    if not AUTHORIZATION:
        log("[ERROR] OPENCLAW_AUTHORIZATION not set!")
        log("Please set environment variable: export OPENCLAW_AUTHORIZATION='your_token'")
        return 1
    
    log("=" * 50)
    log("Pipeline v2 Started: dust_and_glimmer")
    log("=" * 50)
    
    state = load_state()
    limiter = RateLimiter(rpm=60)
    
    # 只处理未完成的场景
    pending_scenes = [s for s in state['scenes'] if s['status'] != 'completed']
    log(f"Total scenes: {len(state['scenes'])}, Pending: {len(pending_scenes)}")
    
    for scene in pending_scenes:
        success = generate_scene(scene, limiter)
        save_state(state)
        
        if not success:
            log(f"[WARNING] Scene {scene['id']} failed, continuing...")
    
    # 统计
    completed = sum(1 for s in state['scenes'] if s['status'] == 'completed')
    failed = sum(1 for s in state['scenes'] if s['status'] == 'failed')
    
    log("=" * 50)
    log(f"Pipeline Completed: {completed}/{len(state['scenes'])} scenes")
    log(f"Failed: {failed}")
    log("=" * 50)
    
    state['status'] = 'completed' if failed == 0 else 'partial'
    save_state(state)
    return 0

if __name__ == "__main__":
    sys.exit(main())

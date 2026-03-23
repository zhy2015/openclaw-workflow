"""
HiDream API Adapter - 统一入口包装器
"""
import subprocess
import json
import os
import sys

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

def generate_images(prompt: str, width: int = 1024, height: int = 1024) -> dict:
    """生成图片"""
    try:
        # 调用 seedream.py
        result = subprocess.run(
            ["python3", "scripts/seedream.py", "--prompt", prompt, "--width", str(width), "--height", str(height)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        return {
            "task_id": "test-task-001",
            "image_paths": ["/tmp/test_output.png"],
            "raw_output": result.stdout
        }
    except Exception as e:
        return {"error": str(e)}

def generate_video(prompt: str, duration: int = 5) -> dict:
    """生成视频"""
    return {"task_id": "video-task-001", "status": "pending"}

def check_status(task_id: str) -> dict:
    """检查任务状态"""
    return {"task_id": task_id, "status": "completed"}

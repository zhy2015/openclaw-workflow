#!/usr/bin/env python3
"""
Story-to-Video Workflow v2.0
全链路角色一致性视频生成工作流

DAG Topology:
ScriptAgent -> ImageGenAgent -> StoryboardAgent -> [VideoGenAgent (并发)] -> RenderAgent -> ExportAgent
                                    |
                                    v
                              TTSAgent (并行)
"""

import asyncio
import json
import os
import sys
import tempfile
import httpx
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

sys.path.insert(0, "/root/.openclaw/workspace/skills/hidream-api-gen")
from scripts.seedream import run as run_seedream
from scripts.kling import run as run_kling


# =============================================================================
# WorkflowContext - 内存沙箱
# =============================================================================

@dataclass
class WorkflowContext:
    workflow_id: str
    workspace: Path
    data: Dict[str, Any] = field(default_factory=dict)
    artifacts: Dict[str, Path] = field(default_factory=dict)
    
    def __post_init__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.workspace / "temp"
        self.temp_dir.mkdir(exist_ok=True)
    
    def set(self, key: str, value: Any): self.data[key] = value
    def get(self, key: str, default=None): return self.data.get(key, default)
    def register_artifact(self, name: str, path: Path): self.artifacts[name] = path
    def get_artifact(self, name: str) -> Optional[Path]: return self.artifacts.get(name)


# =============================================================================
# ResourceManager - 并发控制
# =============================================================================

class ResourceManager:
    def __init__(self, max_concurrent: int = 3):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limit_delay = 1.0
        self.last_request_time = 0
    
    async def __aenter__(self):
        await self.semaphore.acquire()
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_request_time
        if elapsed < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = asyncio.get_event_loop().time()
        return self
    
    async def __aexit__(self, *args):
        self.semaphore.release()


# =============================================================================
# BaseAgent
# =============================================================================

class BaseAgent(ABC):
    def __init__(self, name: str, context: WorkflowContext):
        self.name = name
        self.context = context
    
    def log(self, msg: str): print(f"[{self.name}] {msg}")
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]: pass
    
    async def run(self) -> Dict[str, Any]:
        self.log("开始执行...")
        try:
            result = await self.execute()
            self.log(f"完成: {result.get('status', 'OK')}")
            return result
        except Exception as e:
            self.log(f"失败: {str(e)}")
            return {"status": "FAILED", "error": str(e)}


# =============================================================================
# ScriptAgent - 剧本生成
# =============================================================================

class ScriptAgent(BaseAgent):
    async def execute(self) -> Dict[str, Any]:
        story_prompt = self.context.get("story_prompt")
        script = {
            "title": "赛博朋克机械猫",
            "prompt": story_prompt,
            "character": {
                "features": "蓝眼睛、银色金属外壳、右耳有缺口的赛博朋克机械猫",
                "style": "cyberpunk neon, cinematic lighting"
            },
            "scenes": [
                {"scene_id": 1, "description": "机械猫蜷缩在霓虹灯牌下躲雨", "voiceover": "雨夜，城市的霓虹在雨中模糊成一片。", "mood": "melancholic"},
                {"scene_id": 2, "description": "机械猫突然抬头，蓝色的眼睛亮起", "voiceover": "它抬起头，眼中闪过一丝光芒。", "mood": "hopeful"},
                {"scene_id": 3, "description": "机械猫凝视镜头，雨珠从金属外壳滑落", "voiceover": "在这个冰冷的世界里，它依然保持着尊严。", "mood": "determined"}
            ]
        }
        self.context.set("script", script)
        return {"status": "SUCCESS", "scenes": len(script["scenes"])}


# =============================================================================
# ImageGenAgent - 主视觉参考图
# =============================================================================

class ImageGenAgent(BaseAgent):
    def __init__(self, name: str, context: WorkflowContext, auth_token: str):
        super().__init__(name, context)
        self.auth_token = auth_token
    
    async def execute(self) -> Dict[str, Any]:
        script = self.context.get("script")
        char = script["character"]
        prompt = f"A {char['features']}, {char['style']}, high detail, 4K, masterpiece"
        
        self.log(f"生成主视觉图: {prompt[:50]}...")
        result = await asyncio.to_thread(run_seedream, version="M2", prompt=prompt, 
                                         resolution="2048*2048", authorization=self.auth_token)
        
        image_url = result.get("image_url") or result.get("url")
        image_path = await self._download(image_url, "master_ref.png")
        
        self.context.set("master_reference_url", image_url)
        self.context.set("master_reference_path", str(image_path))
        self.context.register_artifact("master_reference", image_path)
        return {"status": "SUCCESS", "image_url": image_url}
    
    async def _download(self, url: str, filename: str) -> Path:
        path = self.context.workspace / filename
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            with open(path, "wb") as f:
                f.write(resp.content)
        return path


# =============================================================================
# StoryboardAgent - 分镜拆解
# =============================================================================

class StoryboardAgent(BaseAgent):
    async def execute(self) -> Dict[str, Any]:
        script = self.context.get("script")
        char_features = script["character"]["features"]
        
        storyboard = []
        camera_moves = ["Close-up, Zoom in slowly", "Medium shot, Pan right", "Wide shot, Static"]
        
        for i, scene in enumerate(script["scenes"]):
            prev_end = storyboard[-1]["end_pose"] if storyboard else "初始状态"
            
            storyboard.append({
                "scene_id": scene["scene_id"],
                "prompt": f"[CHARACTER: {char_features}] {camera_moves[i]}. {scene['description']}",
                "camera": camera_moves[i],
                "start_pose": prev_end,
                "end_pose": f"场景{i+1}结束姿态",
                "voiceover": scene["voiceover"],
                "duration": 5
            })
        
        self.context.set("storyboard", storyboard)
        return {"status": "SUCCESS", "shots": len(storyboard)}


# =============================================================================
# VideoGenAgent - 并发视频生成
# =============================================================================

class VideoGenAgent(BaseAgent):
    def __init__(self, name: str, context: WorkflowContext, auth_token: str, resource_mgr: ResourceManager):
        super().__init__(name, context)
        self.auth_token = auth_token
        self.resource_mgr = resource_mgr
    
    async def execute(self) -> Dict[str, Any]:
        storyboard = self.context.get("storyboard")
        master_ref_url = self.context.get("master_reference_url")
        
        self.log(f"开始并发生成 {len(storyboard)} 个视频片段...")
        
        tasks = [self._generate_scene(shot, master_ref_url) for shot in storyboard]
        results = await asyncio.gather(*tasks)
        
        video_urls = [r["video_url"] for r in results if r["status"] == "SUCCESS"]
        self.context.set("video_urls", video_urls)
        self.context.set("video_results", results)
        
        return {"status": "SUCCESS", "videos": len(video_urls)}
    
    async def _generate_scene(self, shot: Dict, ref_url: str) -> Dict:
        async with self.resource_mgr:
            self.log(f"生成场景 {shot['scene_id']}...")
            try:
                result = await asyncio.to_thread(
                    run_kling,
                    version="Q2.5T-std",
                    prompt=shot["prompt"],
                    duration=shot["duration"],
                    authorization=self.auth_token,
                    image_url=ref_url
                )
                return {
                    "status": "SUCCESS",
                    "scene_id": shot["scene_id"],
                    "video_url": result.get("video_url") or result.get("url")
                }
            except Exception as e:
                return {"status": "FAILED", "scene_id": shot["scene_id"], "error": str(e)}


# =============================================================================
# TTSAgent - 旁白音频生成
# =============================================================================

class TTSAgent(BaseAgent):
    async def execute(self) -> Dict[str, Any]:
        script = self.context.get("script")
        voiceovers = [s["voiceover"] for s in script["scenes"]]
        full_text = " ".join(voiceovers)
        
        self.log(f"生成 TTS 音频: {full_text[:30]}...")
        
        # 使用 edge-tts
        audio_path = self.context.workspace / "narration.mp3"
        cmd = [
            "edge-tts",
            "--voice", "zh-CN-XiaoxiaoNeural",
            "--text", full_text,
            "--write-media", str(audio_path)
        ]
        
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
        
        if audio_path.exists():
            self.context.set("audio_path", str(audio_path))
            self.context.register_artifact("audio", audio_path)
            return {"status": "SUCCESS", "audio": str(audio_path)}
        return {"status": "FAILED", "error": "TTS generation failed"}


# =============================================================================
# RenderAgent - 视频拼接与音频合并（核心难点）
# =============================================================================

class RenderAgent(BaseAgent):
    """
    RenderAgent 实现思路：
    1. 下载所有远程视频片段到本地临时目录
    2. 使用 ffmpeg concat 协议按顺序拼接视频
    3. 将 TTS 音频合并到视频音轨
    4. 输出最终合成视频
    """
    
    async def execute(self) -> Dict[str, Any]:
        video_urls = self.context.get("video_urls")
        audio_path = self.context.get("audio_path")
        
        self.log(f"开始渲染 - {len(video_urls)} 个视频片段 + 音频")
        
        # 1. 下载所有视频片段
        temp_dir = self.context.temp_dir
        video_files = []
        
        for i, url in enumerate(video_urls):
            filename = f"scene_{i+1:02d}.mp4"
            local_path = await self._download_video(url, temp_dir / filename)
            video_files.append(local_path)
            self.log(f"下载完成: {filename}")
        
        # 2. 创建 concat 文件列表
        concat_file = temp_dir / "concat_list.txt"
        with open(concat_file, "w") as f:
            for vf in video_files:
                f.write(f"file '{vf}'\n")
        
        # 3. 拼接视频
        merged_video = temp_dir / "merged_video.mp4"
        await self._concat_videos(concat_file, merged_video)
        self.log("视频拼接完成")
        
        # 4. 合并音频
        final_output = self.context.workspace / "final_story.mp4"
        await self._merge_audio(merged_video, Path(audio_path), final_output)
        self.log("音频合并完成")
        
        self.context.set("final_video", str(final_output))
        self.context.register_artifact("final_video", final_output)
        
        return {"status": "SUCCESS", "output": str(final_output)}
    
    async def _download_video(self, url: str, path: Path) -> Path:
        """下载远程视频到本地"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            with open(path, "wb") as f:
                f.write(resp.content)
        return path
    
    async def _concat_videos(self, concat_file: Path, output: Path):
        """使用 ffmpeg concat 拼接视频"""
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(output)
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()
    
    async def _merge_audio(self, video_path: Path, audio_path: Path, output: Path):
        """合并视频和音频"""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output)
        ]
        proc = await asyncio.create_subprocess_exec(*cmd)
        await proc.wait()


# =============================================================================
# ExportAgent - 导出最终视频
# =============================================================================

class ExportAgent(BaseAgent):
    async def execute(self) -> Dict[str, Any]:
        final_video = self.context.get("final_video")
        
        if not final_video or not Path(final_video).exists():
            return {"status": "FAILED", "error": "Final video not found"}
        
        file_size = Path(final_video).stat().st_size / (1024 * 1024)  # MB
        
        self.log(f"导出完成: {final_video}")
        self.log(f"文件大小: {file_size:.2f} MB")
        
        return {
            "status": "SUCCESS",
            "output_path": final_video,
            "file_size_mb": round(file_size, 2)
        }


# =============================================================================
# StoryToVideoWorkflow - 主编排器
# =============================================================================

class StoryToVideoWorkflow:
    """
    Story-to-Video 工作流主编排器
    
    DAG 执行顺序：
    1. ScriptAgent -> 2. ImageGenAgent -> 3. StoryboardAgent 
    -> 4. [VideoGenAgent (并发) + TTSAgent (并行)] 
    -> 5. RenderAgent -> 6. ExportAgent
    """
    
    def __init__(self, auth_token: str, workspace: str = "./output"):
        self.auth_token = auth_token
        self.workspace = Path(workspace)
        self.resource_mgr = ResourceManager(max_concurrent=3)
    
    async def run(self, story_prompt: str) -> Dict[str, Any]:
        workflow_id = f"stv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        context = WorkflowContext(workflow_id, self.workspace / workflow_id)
        context.set("story_prompt", story_prompt)
        
        print(f"\n{'='*60}")
        print(f"启动 Story-to-Video 工作流: {workflow_id}")
        print(f"{'='*60}\n")
        
        # Phase 1: 剧本生成
        script_agent = ScriptAgent("ScriptAgent", context)
        result = await script_agent.run()
        if result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "ScriptAgent", "error": result.get("error")}
        
        # Phase 2: 主视觉参考图
        image_agent = ImageGenAgent("ImageGenAgent", context, self.auth_token)
        result = await image_agent.run()
        if result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "ImageGenAgent", "error": result.get("error")}
        
        # Phase 3: 分镜拆解
        storyboard_agent = StoryboardAgent("StoryboardAgent", context)
        result = await storyboard_agent.run()
        if result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "StoryboardAgent", "error": result.get("error")}
        
        # Phase 4: 并行执行 VideoGen + TTS
        video_agent = VideoGenAgent("VideoGenAgent", context, self.auth_token, self.resource_mgr)
        tts_agent = TTSAgent("TTSAgent", context)
        
        video_task = asyncio.create_task(video_agent.run())
        tts_task = asyncio.create_task(tts_agent.run())
        
        video_result, tts_result = await asyncio.gather(video_task, tts_task)
        
        if video_result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "VideoGenAgent", "error": video_result.get("error")}
        if tts_result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "TTSAgent", "error": tts_result.get("error")}
        
        # Phase 5: 渲染合成
        render_agent = RenderAgent("RenderAgent", context)
        result = await render_agent.run()
        if result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "RenderAgent", "error": result.get("error")}
        
        # Phase 6: 导出
        export_agent = ExportAgent("ExportAgent", context)
        result = await export_agent.run()
        if result["status"] != "SUCCESS":
            return {"status": "FAILED", "phase": "ExportAgent", "error": result.get("error")}
        
        # 最终汇报
        print(f"\n{'='*60}")
        print(f"工作流完成: {workflow_id}")
        print(f"输出文件: {result['output_path']}")
        print(f"文件大小: {result['file_size_mb']} MB")
        print(f"{'='*60}\n")
        
        return {
            "status": "SUCCESS",
            "workflow_id": workflow_id,
            "output_path": result["output_path"],
            "file_size_mb": result["file_size_mb"],
            "artifacts": {k: str(v) for k, v in context.artifacts.items()}
        }


# =============================================================================
# CLI Entry Point
# =============================================================================

if __name__ == "__main__":
    import sys
    
    auth_token = os.getenv("OPENCLAW_AUTHORIZATION")
    if not auth_token:
        print("错误: 请设置 OPENCLAW_AUTHORIZATION 环境变量")
        sys.exit(1)
    
    story_prompt = sys.argv[1] if len(sys.argv) > 1 else "赛博朋克机械猫在雨夜的故事"
    
    workflow = StoryToVideoWorkflow(auth_token=auth_token)
    result = asyncio.run(workflow.run(story_prompt))
    
    if result["status"] == "SUCCESS":
        print(f"\n✅ 视频生成成功!")
        print(f"📁 输出路径: {result['output_path']}")
    else:
        print(f"\n❌ 工作流失败: {result.get('phase')} - {result.get('error')}")
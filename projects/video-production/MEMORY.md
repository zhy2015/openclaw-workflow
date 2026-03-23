# Video Production Skill - 记忆区

## 项目信息
- **名称**: one-story-video (One Story Video)
- **路径**: `/root/.openclaw/workspace/skills/video-production/`
- **功能**: 故事到视频的端到端生成流水线

## 架构组件

### 01-Generation (视觉生成)
- **hidream-api-gen**: Kling I2V, Seedream T2I 等模型调用
- **配置**: `~/.config/openclaw/hidream_config.json` (Token 已保存)

### 02-Audio (音频生成)
- **edge-tts**: Microsoft Edge TTS 配音

### 03-Compositing (后期合成)
- **ffmpeg-master**: FFmpeg 视频拼接、音画同步

### 04-Orchestration (编排层)
- **DirectorAgent**: 总导演，场景分解与调度
- **ArtDirectorAgent**: 生成锚点图
- **NarratorAgent**: 生成配音
- **AnimatorAgent**: 生成视频片段 (含尾帧接力)
- **ComposerAgent**: 最终合成

## 关键修复记录

### 2026-03-16: Tail-to-Head 尾帧接力实现
**问题**: 场景切换时出现闪现，视频不连贯

**解决方案**:
1. AnimatorAgent 生成视频后立即下载到本地
2. 使用 FFmpeg 提取最后一帧
3. 将尾帧传递给下一幕作为 reference_image

**代码位置**:
- `04-orchestration/story-to-video-director/agents/animator.py`
- 关键函数: `extract_last_frame()`, 下载逻辑在 `_execute()` 中

**代理配置**:
```python
env["http_proxy"] = "http://127.0.0.1:7890"
env["https_proxy"] = "http://127.0.0.1:7890"
```

### 2026-03-16: FFmpeg 截断修复
**问题**: 视频被 `-shortest` 参数截断，丢失内容

**解决方案**:
- 移除 `-shortest`
- 视频比音频长时，循环音频匹配视频时长

**代码位置**:
- `03-compositing/ffmpeg-master/scripts/ffmpeg_wrapper.py`

### 2026-03-16: Mock 数据替换
**问题**: DirectorAgent 使用 Mock 数据，不解析真实剧本

**解决方案**:
- 实现 `_decompose_story()` 硬编码场景分解
- 支持三幕剧本解析 (第X幕 标记)

**代码位置**:
- `04-orchestration/story-to-video-director/agents/director.py`

## 使用方式

### 启动命令
```bash
cd /root/.openclaw/workspace/skills/video-production/04-orchestration/story-to-video-director
PYTHONPATH=/root/.openclaw/workspace/skills/video-production/04-orchestration/story-to-video-director:$PYTHONPATH \
python3 scripts/workflow_v2.py "你的三幕剧本"
```

### 剧本格式
```
第一幕：...
第二幕：...
第三幕：...
```

## 依赖检查清单

- [ ] `hidream-api-gen` 已安装 (ClawHub)
- [ ] `~/.config/openclaw/hidream_config.json` 存在
- [ ] Clash VPN 运行中 (127.0.0.1:7890)
- [ ] FFmpeg 已安装
- [ ] Edge TTS 依赖已安装

## 常见错误

### 1. API 限流
```
Code: 3022, Message: "Exceeded Maximum Parallel Number Limit"
```
**解决**: 等待几分钟后重试

### 2. 视频下载超时
```
curl exit code 18 (partial download)
```
**解决**: 检查 Clash VPN 是否运行

### 3. ModuleNotFoundError
```
No module named 'agents'
```
**解决**: 设置 PYTHONPATH

## 文件位置

- 最终视频: `/tmp/tmpXXXXXX/final_movie.mp4`
- 音频文件: `04-orchestration/story-to-video-director/audio_*.mp3`
- 日志文件: `04-orchestration/story-to-video-director/director_v2.log`

---
*最后更新: 2026-03-16*

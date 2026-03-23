# Audio Mixer Skill

音频混音技能 - 多轨音频合成与视频混音

## 功能
- 多轨音频按时间轴混音
- 支持延迟、淡入淡出、音量调节
- 音视频合并输出

## 使用

```python
from audio_mixer import AudioMixer

mixer = AudioMixer()

# 添加音轨
mixer.add_track("ambient.mp3", start=0, volume=0.3)
mixer.add_track("music.mp3", start=5, volume=0.7, fade_in=1.0)

# 混音
mixed = mixer.mix("/tmp/mixed.mp3", duration=30)

# 合并到视频
final = mixer.merge_with_video("video.mp4", mixed, "output.mp4")
```

## 依赖
- FFmpeg

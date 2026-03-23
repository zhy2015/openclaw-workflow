#!/usr/bin/env python3
"""
Audio Mixer - 音频混音器
多轨音频合成与视频混音
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class AudioTrack:
    """音频轨道"""
    path: Path
    start: float = 0.0
    volume: float = 1.0
    fade_in: float = 0.5
    fade_out: float = 0.5
    duration: Optional[float] = None


class AudioMixer:
    """音频混音器"""

    def __init__(self):
        self.tracks: List[AudioTrack] = []

    def add_track(self, path: str, start: float = 0, volume: float = 1.0,
                  fade_in: float = 0.5, fade_out: float = 0.5):
        """添加音轨"""
        self.tracks.append(AudioTrack(
            path=Path(path),
            start=start,
            volume=volume,
            fade_in=fade_in,
            fade_out=fade_out
        ))

    def mix(self, output_path: str, duration: float = 30.0) -> Path:
        """
        混音合成

        Args:
            output_path: 输出文件路径
            duration: 总时长(秒)

        Returns:
            输出文件路径
        """
        if not self.tracks:
            raise ValueError("No tracks added")

        output = Path(output_path)

        # 构建 FFmpeg 命令
        inputs = []
        filters = []

        for i, track in enumerate(self.tracks):
            inputs.extend(["-i", str(track.path)])

            # 计算淡出时间
            track_duration = track.duration or (duration - track.start)
            fade_out_start = track.start + track_duration - track.fade_out

            # 构建滤镜链
            filter_parts = [
                f"[{i}:a]",
                f"adelay={int(track.start*1000)}|{int(track.start*1000)}",
                f"volume={track.volume}",
                f"afade=t=in:st={track.start}:d={track.fade_in}",
                f"afade=t=out:st={fade_out_start}:d={track.fade_out}",
                f"[a{i}]"
            ]
            filters.append("".join(filter_parts))

        # 合并所有音轨
        mix_inputs = "".join([f"[a{i}]" for i in range(len(self.tracks))])
        filters.append(f"{mix_inputs}amix=inputs={len(self.tracks)}:duration=longest[aout]")

        # 构建完整命令
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filters),
            "-map", "[aout]",
            "-t", str(duration),
            "-ar", "44100",
            "-ac", "2",
            str(output)
        ]

        subprocess.run(cmd, capture_output=True)
        return output

    def merge_with_video(self, video_path: str, audio_path: str, output_path: str) -> Path:
        """
        音视频合并

        Args:
            video_path: 视频文件路径
            audio_path: 音频文件路径
            output_path: 输出文件路径

        Returns:
            输出文件路径
        """
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", audio_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            output_path
        ]

        subprocess.run(cmd, capture_output=True)
        return Path(output_path)


# 快捷函数
def quick_mix(tracks: List[Dict], output: str, duration: float = 30.0) -> Path:
    """
    快速混音

    Args:
        tracks: 音轨列表 [{"path": "x.mp3", "start": 0, "volume": 0.5}, ...]
        output: 输出路径
        duration: 总时长
    """
    mixer = AudioMixer()
    for track in tracks:
        mixer.add_track(
            path=track["path"],
            start=track.get("start", 0),
            volume=track.get("volume", 1.0),
            fade_in=track.get("fade_in", 0.5),
            fade_out=track.get("fade_out", 0.5)
        )
    return mixer.mix(output, duration)


if __name__ == "__main__":
    # 测试
    mixer = AudioMixer()
    mixer.add_track("/tmp/test1.mp3", start=0, volume=0.5)
    mixer.add_track("/tmp/test2.mp3", start=5, volume=0.7)
    print("AudioMixer ready")

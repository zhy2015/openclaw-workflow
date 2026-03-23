#!/usr/bin/env python3
"""
Procedural SFX Generator
使用 FFmpeg 生成程序化音效 - 无需外部下载
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


def resolve_ffmpeg() -> str:
    from_path = shutil.which("ffmpeg")
    if from_path:
        return from_path
    workspace_bin = Path(__file__).resolve().parents[2] / "bin" / "ffmpeg"
    if workspace_bin.exists() and os.access(workspace_bin, os.X_OK):
        return str(workspace_bin)
    raise FileNotFoundError(f"ffmpeg not found in PATH or {workspace_bin}")


class SFXGenerator:
    """程序化音效生成器"""

    def __init__(self, output_dir: str = "./sfx"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_bin = resolve_ffmpeg()

    def _run(self, cmd: list, output: Path) -> Path:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not output.exists() or output.stat().st_size <= 0:
            raise RuntimeError(result.stderr.strip() or f"ffmpeg failed for {output}")
        return output

    def generate_ambient_hum(self, duration: float = 8.0, output: str = None) -> Path:
        """生成机房/环境底噪"""
        output = Path(output or self.output_dir / "ambient_hum.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=50:duration={duration}",
            "-f", "lavfi", "-i", f"anoisesrc=a=0.3:c=brown:duration={duration}",
            "-filter_complex", "[0:a][1:a]amix=inputs=2:weights='0.7 0.3'[mix];[mix]lowpass=f=200,volume=0.5",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)

    def generate_electric_sparks(self, duration: float = 9.0, output: str = None) -> Path:
        """生成电流/电火花声"""
        output = Path(output or self.output_dir / "electric_sparks.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=1200:duration={duration}",
            "-f", "lavfi", "-i", f"anoisesrc=a=0.25:c=white:duration={duration}",
            "-filter_complex", f"[0:a][1:a]amix=inputs=2:weights='0.65 0.35'[mix];[mix]highpass=f=700,treble=g=8,volume=0.35,afade=t=in:st=0:d=0.05,afade=t=out:st={max(0, duration-0.12)}:d=0.12",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)

    def generate_digital_data(self, duration: float = 9.0, output: str = None) -> Path:
        """生成数字数据流声"""
        output = Path(output or self.output_dir / "digital_data.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=800:duration={duration}",
            "-f", "lavfi", "-i", f"sine=frequency=1200:duration={duration}",
            "-f", "lavfi", "-i", f"anoisesrc=a=0.2:c=white:duration={duration}",
            "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3:weights='0.4 0.3 0.3'[mix];[mix]vibrato=f=15:d=0.3,highpass=f=500,volume=0.4",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)

    def generate_heartbeat(self, duration: float = 9.0, output: str = None) -> Path:
        """生成心跳声"""
        output = Path(output or self.output_dir / "heartbeat.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=30:duration={duration}",
            "-filter_complex", f"volume=0.8,apulsator=hz=1.2,lowpass=f=100,afade=t=in:st=0:d=1,afade=t=out:st={max(0, duration-2)}:d=2",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)

    def generate_bass_drop(self, duration: float = 9.0, output: str = None) -> Path:
        """生成低频重音坠落"""
        output = Path(output or self.output_dir / "bass_drop.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=200:duration={duration}",
            "-filter_complex", f"volume=0.9,lowpass=f=150,afade=t=in:st=0:d=0.05,afade=t=out:st={max(0, duration-0.2)}:d=0.2",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)

    def generate_energy_surge(self, duration: float = 9.0, output: str = None) -> Path:
        """生成能量涌动声"""
        output = Path(output or self.output_dir / "energy_surge.mp3")
        cmd = [
            self.ffmpeg_bin, "-y",
            "-f", "lavfi", "-i", f"sine=frequency=100:duration={duration}",
            "-f", "lavfi", "-i", f"anoisesrc=a=0.5:c=pink:duration={duration}",
            "-filter_complex", f"[0:a]afade=t=in:st=0:d=1,afade=t=out:st={max(0, duration-1)}:d=1[sine];[1:a]afade=t=in:st=0:d=2,afade=t=out:st={max(0, duration-2)}:d=2[noise];[sine][noise]amix=inputs=2:weights='0.6 0.4'[mix];[mix]highpass=f=80,lowpass=f=3000,volume=0.7",
            "-t", str(duration), "-ar", "44100", "-ac", "2", str(output)
        ]
        return self._run(cmd, output)


# 快捷函数
def generate_sfx_pack(output_dir: str = "./sfx") -> dict:
    """生成完整音效包"""
    gen = SFXGenerator(output_dir)

    sfx = {
        "ambient_hum": gen.generate_ambient_hum(8.0),
        "electric_sparks": gen.generate_electric_sparks(9.0),
        "digital_data": gen.generate_digital_data(9.0),
        "heartbeat": gen.generate_heartbeat(9.0),
        "bass_drop": gen.generate_bass_drop(9.0),
        "energy_surge": gen.generate_energy_surge(9.0),
    }

    return sfx


if __name__ == "__main__":
    print("Generating SFX pack...")
    sfx = generate_sfx_pack("/tmp/procedural_sfx")
    for name, path in sfx.items():
        size = path.stat().st_size if path.exists() else 0
        print(f"  {name}: {path} ({size} bytes)")

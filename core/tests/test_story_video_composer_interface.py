from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from composer import VideoComposer  # noqa: E402
from media_runtime import resolve_binary  # noqa: E402


def test_composer_accepts_audio_edit_plan(tmp_path):
    ffmpeg = resolve_binary("ffmpeg")
    video = tmp_path / "video.mp4"
    audio = tmp_path / "audio.mp3"
    out = tmp_path / "out.mp4"

    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=1.0",
            "-c:v", "libx264",
            str(video),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=1.0",
            "-c:a", "libmp3lame",
            str(audio),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    composer = VideoComposer(str(tmp_path))
    ok = composer.compose_scene(
        str(video),
        str(audio),
        str(out),
        subtitle_path=None,
        audio_edit_plan={"subtitle_policy": "none"},
    )
    assert ok is True
    assert out.exists()

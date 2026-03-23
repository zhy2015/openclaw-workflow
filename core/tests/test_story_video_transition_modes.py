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


def _make_scene(ffmpeg: str, path: Path, color: str, freq: int):
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x240:d=1.0",
            "-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=44100:duration=1.0",
            "-shortest",
            "-c:v", "libx264",
            "-c:a", "aac",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_composer_concat_scenes_respects_explicit_hard_cut(tmp_path):
    ffmpeg = resolve_binary("ffmpeg")
    s1 = tmp_path / "scene1.mp4"
    s2 = tmp_path / "scene2.mp4"
    out = tmp_path / "final.mp4"
    _make_scene(ffmpeg, s1, "black", 440)
    _make_scene(ffmpeg, s2, "blue", 660)

    edit_plan = {
        "transitions": [{"type": "hard_cut", "from_scene": 0, "to_scene": 1}],
        "audio_rules": {"crossfade_ms": 250},
        "execution": {"transition_mode": None, "crossfade_applied": False},
    }
    composer = VideoComposer(str(tmp_path))
    ok = composer.concat_scenes([str(s1), str(s2)], str(out), edit_plan=edit_plan)
    assert ok is True
    assert out.exists()
    assert edit_plan["execution"]["transition_mode"] == "hard_cut"
    assert edit_plan["execution"]["crossfade_applied"] is False

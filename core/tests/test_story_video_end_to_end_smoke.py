from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from composer import VideoComposer  # noqa: E402
from edit_planner import EditPlanner  # noqa: E402
from media_runtime import json_word_timing_to_srt, resolve_binary  # noqa: E402
from schema import Project, Scene  # noqa: E402


def _make_video(ffmpeg: str, path: Path, color: str, duration: float = 1.2):
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"color=c={color}:s=320x240:d={duration}",
            "-c:v", "libx264",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _make_audio(ffmpeg: str, path: Path, freq: int, duration: float = 1.2):
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", f"sine=frequency={freq}:sample_rate=44100:duration={duration}",
            "-c:a", "libmp3lame",
            str(path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_story_video_end_to_end_edit_smoke(tmp_path):
    ffmpeg = resolve_binary("ffmpeg")
    planner = EditPlanner()
    composer = VideoComposer(str(tmp_path))

    scene1 = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="hello there",
        visual_prompt="quiet dawn",
        story_beat="gentle opening",
        emotion="calm",
        audio_path=str(tmp_path / "audio1.mp3"),
        video_path=str(tmp_path / "video1.mp4"),
    )
    scene2 = Scene(
        index=1,
        scene_id="scene_01",
        narration_text="then the reveal",
        visual_prompt="memory glow",
        story_beat="dream reveal",
        emotion="gentle",
        audio_path=str(tmp_path / "audio2.mp3"),
        video_path=str(tmp_path / "video2.mp4"),
    )

    _make_video(ffmpeg, Path(scene1.video_path), "black")
    _make_video(ffmpeg, Path(scene2.video_path), "blue")
    _make_audio(ffmpeg, Path(scene1.audio_path), 440)
    _make_audio(ffmpeg, Path(scene2.audio_path), 660)

    subtitle_json = tmp_path / "audio1.mp3.json"
    subtitle_json.write_text(json.dumps([
        {"part": "hello", "start": 0, "end": 400},
        {"part": "there", "start": 450, "end": 900},
    ]), encoding="utf-8")
    scene1.subtitle_path = json_word_timing_to_srt(str(subtitle_json))

    audio_plan1 = planner.build_audio_edit_plan(scene1, {"bgm": {"style": "ambient soft"}, "sfx": []})
    audio_plan2 = planner.build_audio_edit_plan(scene2, {"bgm": {"style": "memory glow"}, "sfx": []})
    project = Project(id="proj_smoke", story_prompt="smoke", scenes=[scene1, scene2])
    edit_plan = planner.build_project_edit_plan(project)

    scene1_out = tmp_path / "scene1_final.mp4"
    scene2_out = tmp_path / "scene2_final.mp4"
    final_out = tmp_path / "final.mp4"

    assert composer.compose_scene(scene1.video_path, scene1.audio_path, str(scene1_out), scene1.subtitle_path, audio_plan1) is True
    assert composer.compose_scene(scene2.video_path, scene2.audio_path, str(scene2_out), scene2.subtitle_path, audio_plan2) is True
    assert composer.concat_scenes([str(scene1_out), str(scene2_out)], str(final_out), edit_plan=edit_plan) is True

    assert scene1_out.exists()
    assert scene2_out.exists()
    assert final_out.exists()
    assert edit_plan["execution"]["transition_mode"] in {"crossfade", "fade_black", "mixed_soft"}

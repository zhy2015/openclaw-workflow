from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from schema import Project, Scene  # noqa: E402
from workflow import Director  # noqa: E402


def test_build_manifest_includes_audio_edit_and_execution_trace(tmp_path):
    director = Director(str(tmp_path))
    project = Project(
        id="proj_test",
        story_prompt="story",
        scenes=[
            Scene(
                index=0,
                scene_id="scene_00",
                narration_text="hello",
                visual_prompt="prompt",
                audio_path=str(tmp_path / "audio.mp3"),
                video_path=str(tmp_path / "video.mp4"),
                status="done",
            )
        ],
    )
    project.sound_plan = {"scenes": [{"scene_id": "scene_00", "bgm": {"style": "ambient hopeful"}, "sfx": []}]}
    project.audio_edit_plan = {
        "scenes": [
            {
                "scene_id": "scene_00",
                "normalize_dialog": True,
                "subtitle_policy": "burn_if_present",
                "execution": {
                    "normalized_dialog": True,
                    "subtitle_policy_applied": "burn_if_present",
                },
            }
        ],
        "execution_summary": {
            "normalized_dialog_scenes": 1,
            "subtitle_policy_values": ["burn_if_present"],
        },
    }
    project.edit_plan = {
        "execution": {
            "transition_mode": "crossfade",
            "crossfade_applied": True,
        }
    }

    director.build_manifest(project)
    manifest = json.loads(Path(director.manifest_file).read_text(encoding="utf-8"))
    assert "audio_edit_plan" in manifest
    assert "edit_plan" in manifest
    assert "capability_report" in manifest
    assert "downstream_outputs" in manifest
    assert manifest["audio_edit_plan"]["execution_summary"]["normalized_dialog_scenes"] == 1
    assert manifest["edit_plan"]["execution"]["crossfade_applied"] is True
    assert manifest["scenes"][0]["audio_edit_plan"]["execution"]["normalized_dialog"] is True
    assert manifest["capability_report"]["coverage_ratio"] > 0

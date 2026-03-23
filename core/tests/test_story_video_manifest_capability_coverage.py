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


def test_manifest_includes_capability_coverage_summary(tmp_path):
    director = Director(str(tmp_path))
    scene = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="hello",
        visual_prompt="prompt",
        audio_path=str(tmp_path / "audio.mp3"),
        video_path=str(tmp_path / "video.mp4"),
        mix_notes=["bgm_synthesized:ambient hopeful", "sfx_resolved:1"],
        status="done",
    )
    project = Project(id="proj_test", story_prompt="story", scenes=[scene])
    project.sound_plan = {"scenes": [{"scene_id": "scene_00"}]}
    project.audio_edit_plan = {
        "scenes": [
            {
                "scene_id": "scene_00",
                "execution": {
                    "normalized_dialog": True,
                    "subtitle_policy_applied": "burn_if_present",
                },
            }
        ]
    }
    project.edit_plan = {"execution": {"crossfade_applied": True}}

    director.build_manifest(project)
    manifest = json.loads(Path(director.manifest_file).read_text(encoding="utf-8"))
    coverage = manifest["capability_coverage"]
    assert coverage["sound_plan"] is True
    assert coverage["audio_edit_plan"] is True
    assert coverage["edit_plan"] is True
    assert coverage["bgm_mix"] is True
    assert coverage["sfx_mix"] is True
    assert coverage["dialog_normalize"] is True
    assert coverage["subtitle_policy"] is True
    assert coverage["transition_crossfade"] is True

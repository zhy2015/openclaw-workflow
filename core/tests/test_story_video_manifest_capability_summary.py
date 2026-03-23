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


def test_manifest_includes_human_readable_capability_summary(tmp_path):
    director = Director(str(tmp_path))
    scene = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="hello",
        visual_prompt="prompt",
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
    assert "active_capability_tags" in manifest
    assert "capability_summary" in manifest
    assert "capability_report" in manifest
    assert "downstream_outputs" in manifest
    assert "rendered_summary" in manifest
    assert "bgm_mix" in manifest["active_capability_tags"]
    assert "sfx_mix" in manifest["active_capability_tags"]
    assert "transition_crossfade" in manifest["active_capability_tags"]
    assert "dialog_normalize" in manifest["capability_summary"]
    assert "audio" in manifest["capability_report"]["grouped"]
    assert manifest["downstream_outputs"]["dashboard_stats"]["enabled_count"] >= 1

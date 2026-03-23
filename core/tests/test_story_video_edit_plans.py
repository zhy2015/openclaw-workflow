from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from edit_planner import EditPlanner  # noqa: E402
from schema import Project, Scene  # noqa: E402


def test_edit_planner_builds_audio_and_project_edit_plans():
    planner = EditPlanner()
    scene = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="hello",
        visual_prompt="prompt",
        audio_path="/tmp/audio.mp3",
        video_path="/tmp/video.mp4",
    )
    audio_plan = planner.build_audio_edit_plan(
        scene,
        {
            "bgm": {"style": "ambient hopeful", "duck_under_voice": True, "target_level_db": -22},
            "sfx": [{"type": "wind", "timing": 0.2}],
        },
    )
    assert audio_plan["scene_id"] == "scene_00"
    assert audio_plan["bgm"]["style"] == "ambient hopeful"
    assert audio_plan["mix_strategy"] == "voice_priority_ducking"

    project = Project(id="proj_test", story_prompt="story", scenes=[scene])
    edit_plan = planner.build_project_edit_plan(project)
    assert edit_plan["project_id"] == "proj_test"
    assert edit_plan["scene_count"] == 1
    assert edit_plan["audio_rules"]["subtitle_policy"] == "burn_if_present"
    assert "timing_rules" in audio_plan
    assert "loudness_rules" in audio_plan
    assert audio_plan["scene_profile"]["pacing"] in {"slow", "medium", "fast"}
    assert "rule_summary" in edit_plan
    assert "scene_rule_language" in edit_plan["rule_summary"]

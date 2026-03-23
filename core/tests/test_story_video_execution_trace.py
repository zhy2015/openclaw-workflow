from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from edit_planner import EditPlanner  # noqa: E402
from schema import Project, Scene  # noqa: E402


def test_edit_plans_include_execution_trace_fields():
    planner = EditPlanner()
    scene = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="hello",
        visual_prompt="prompt",
        audio_path="/tmp/audio.mp3",
        video_path="/tmp/video.mp4",
    )
    audio_plan = planner.build_audio_edit_plan(scene, None)
    assert "execution" in audio_plan
    assert audio_plan["execution"]["normalized_dialog"] is False
    assert audio_plan["execution"]["subtitle_policy_applied"] is None

    project = Project(id="proj_test", story_prompt="story", scenes=[scene, scene])
    edit_plan = planner.build_project_edit_plan(project)
    assert "execution" in edit_plan
    assert edit_plan["execution"]["transition_mode"] is None
    assert edit_plan["execution"]["crossfade_applied"] is False

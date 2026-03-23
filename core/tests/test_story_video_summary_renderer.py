from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from summary_renderer import StoryVideoSummaryRenderer  # noqa: E402


def test_story_video_summary_renderer_builds_downstream_payloads():
    renderer = StoryVideoSummaryRenderer()
    manifest = {
        "project_id": "proj_test",
        "scene_count": 2,
        "final_movie": "/tmp/final.mp4",
        "scenes": [
            {"scene_id": "scene_00", "status": "done"},
            {"scene_id": "scene_01", "status": "done"},
        ],
        "capability_report": {
            "enabled": ["sound_plan", "audio_edit_plan", "bgm_mix", "transition_crossfade"],
            "missing": ["sfx_mix"],
            "grouped": {
                "planning": ["sound_plan", "audio_edit_plan"],
                "audio": ["bgm_mix"],
                "transitions": ["transition_crossfade"],
            },
            "coverage_ratio": 0.75,
        },
        "downstream_outputs": {
            "dashboard_stats": {
                "enabled_count": 4,
                "missing_count": 1,
                "coverage_ratio": 0.75,
            }
        },
    }

    result = renderer.render(manifest)
    assert result["headline"]["project_id"] == "proj_test"
    assert result["headline"]["done_scenes"] == 2
    assert result["headline"]["coverage_ratio"] == 0.75
    assert "enabled=sound_plan, audio_edit_plan, bgm_mix, transition_crossfade" in result["chat_text"]
    assert result["card_payload"]["stats"]["enabled_count"] == 4
    assert any(section["title"] == "Missing" for section in result["sections"])

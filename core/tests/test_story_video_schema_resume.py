from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from schema import Project  # noqa: E402


def test_story_video_project_roundtrip_preserves_sound_plan_and_mix_notes():
    fixture = {
        "id": "proj_test",
        "story_prompt": "test prompt",
        "workspace_dir": "/tmp/story-video-test",
        "output_video_path": "/tmp/story-video-test/final_movie.mp4",
        "story_plan": {"plan_id": "storyplan_test"},
        "visual_plan": {"plan_id": "visualplan_test"},
        "sound_plan": {
            "plan_id": "soundplan_test",
            "schema_version": "v0proto",
            "source_story_plan_id": "storyplan_test",
            "scenes": [
                {
                    "scene_id": "scene_00",
                    "bgm": {"style": "ambient hopeful", "duck_under_voice": True, "target_level_db": -22},
                    "sfx": [],
                }
            ],
        },
        "scenes": [
            {
                "index": 0,
                "narration_text": "hello",
                "visual_prompt": "prompt",
                "duration_seconds": 5.0,
                "scene_id": "scene_00",
                "audio_path": "/tmp/story-video-test/audio.mp3",
                "video_path": "/tmp/story-video-test/video.mp4",
                "mix_notes": ["voice_only_passthrough", "bgm_planned:ambient hopeful"],
                "status": "done",
                "error": None,
            }
        ],
    }

    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "project.json"
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2), encoding="utf-8")

        project = Project.load(str(path))
        assert project.sound_plan is not None
        assert project.sound_plan["plan_id"] == "soundplan_test"
        assert project.scenes[0].mix_notes == ["voice_only_passthrough", "bgm_planned:ambient hopeful"]

        project.save(str(path))
        roundtrip = json.loads(path.read_text(encoding="utf-8"))
        assert "sound_plan" in roundtrip
        assert roundtrip["sound_plan"]["plan_id"] == "soundplan_test"
        assert roundtrip["scenes"][0]["mix_notes"] == ["voice_only_passthrough", "bgm_planned:ambient hopeful"]

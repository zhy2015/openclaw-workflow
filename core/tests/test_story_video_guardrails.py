from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from story_planner import StoryPlanner  # noqa: E402
from workflow import Director  # noqa: E402


def test_story_planner_normalizes_meta_constraints_out_of_story():
    planner = StoryPlanner(api_key=None)
    normalized = planner.normalize_prompt("小城停电，维修员护送小灯穿城而行。要求：生成一个约1分钟、电影感、连贯转场的短片。")
    assert normalized["story_content"] == "小城停电，维修员护送小灯穿城而行"
    assert "1分钟" in normalized["production_constraints"]
    assert normalized["requested_duration_sec"] == 60.0
    assert normalized["target_scene_count"] == 12


def test_story_planner_dummy_plan_expands_for_one_minute_request():
    planner = StoryPlanner(api_key=None)
    plan = planner.plan_story("小城停电，维修员护送小灯穿城而行。要求：生成一个约1分钟、电影感、连贯转场的短片。")
    assert plan.target_duration_sec == 60.0
    assert len(plan.scenes) >= 8
    assert all("要求：" not in scene.narration for scene in plan.scenes)


def test_director_story_plan_validation_rejects_leaked_meta_instruction(tmp_path):
    director = Director(str(tmp_path))
    project = director.create_project("测试")
    project.story_plan = {
        "target_duration_sec": 20,
        "scenes": [
            {"narration": "要求：生成一个约1分钟短片。"}
        ],
    }
    try:
        director.validate_story_plan(project)
        assert False, "expected validate_story_plan to fail"
    except ValueError as e:
        assert "leaked production constraints" in str(e)


def test_director_writes_progress_file(tmp_path):
    director = Director(str(tmp_path))
    project = director.create_project("测试故事")
    director.update_progress(project, "story_plan_ready", "running", 0.1, "ok")
    progress_file = Path(tmp_path) / "progress" / f"{project.id}.json"
    assert progress_file.exists()
    data = json.loads(progress_file.read_text(encoding="utf-8"))
    assert data["stage"] == "story_plan_ready"
    assert data["status"] == "running"

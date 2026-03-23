from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from workflow import Director  # noqa: E402
from core.runtime.long_task_registry import LongTaskRegistry  # noqa: E402


def test_story_video_updates_active_long_task_registry(tmp_path):
    active = tmp_path / "active_long_tasks.json"
    archive = tmp_path / "archive"
    director = Director(str(tmp_path))
    director.long_task_registry = LongTaskRegistry(active_path=active, archive_root=archive)
    project = director.create_project("测试长任务")
    director.update_progress(project, "story_plan_ready", "running", 0.1, "ok")

    data = json.loads(active.read_text(encoding="utf-8"))
    assert len(data["tasks"]) == 1
    task = data["tasks"][0]
    assert task["task_id"] == project.id
    assert task["status"] == "running"
    assert task["source"] == "story-to-video-director"

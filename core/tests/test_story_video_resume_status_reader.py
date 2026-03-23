from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from resume_status_reader import ResumeStatusReader  # noqa: E402


def test_resume_status_reader_reads_progress_project_and_manifest(tmp_path):
    progress_dir = tmp_path / "progress"
    progress_dir.mkdir(parents=True, exist_ok=True)
    (progress_dir / "proj_test.json").write_text(json.dumps({
        "task_id": "proj_test",
        "request_id": "proj_test",
        "intent": "demo",
        "stage": "scene_compose_running",
        "status": "running",
        "progress_hint": 0.5,
        "message": "scene=scene_03",
        "meta": {"resume_from": str(tmp_path / 'project.json')},
    }), encoding="utf-8")
    (tmp_path / "project.json").write_text(json.dumps({"id": "proj_test", "output_video_path": None}), encoding="utf-8")
    (tmp_path / "manifest.json").write_text(json.dumps({
        "scenes": [
            {"scene_id": "scene_00", "status": "done", "error": None},
            {"scene_id": "scene_03", "status": "running", "error": None},
        ]
    }), encoding="utf-8")

    reader = ResumeStatusReader(str(tmp_path))
    data = reader.read()
    assert data["project_id"] == "proj_test"
    assert data["can_resume"] is True
    assert data["latest_progress"]["stage"] == "scene_compose_running"
    assert len(data["scene_status"]) == 2

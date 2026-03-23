from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.infra.real_comic_workflow_skill import RealComicWorkflowSkill
from core.infra.skill_contracts import GlobalContext


def make_skill():
    skill = RealComicWorkflowSkill()
    skill.init(GlobalContext(config={
        "workspace_root": str(REPO_ROOT),
        "skills_root": "/Users/hidream/.openclaw/workspace/skills",
    }))
    return skill


def test_adapt_hidream_requests_tool():
    skill = make_skill()
    compiled = skill.execute("compile_storyboard", {"topic": "倒悬的钟楼"}).data
    payloads = skill.execute("build_hidream_payloads", {"compiled_storyboard": compiled}).data
    result = skill.execute("adapt_hidream_requests", {"hidream_payloads": payloads})
    assert result.ok is True
    assert result.data["character_sheet_request"]["model"] == "seedream"
    assert len(result.data["panel_requests"]) == 6

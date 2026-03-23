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


def test_compile_storyboard_tool():
    skill = make_skill()
    result = skill.execute("compile_storyboard", {"topic": "赛博朋克算命局"})
    assert result.ok is True
    assert "global_settings" in result.data
    assert len(result.data["panel_array"]) == 6


def test_build_hidream_payloads_tool():
    skill = make_skill()
    compiled = skill.execute("compile_storyboard", {"topic": "赛博朋克算命局"}).data
    result = skill.execute("build_hidream_payloads", {"compiled_storyboard": compiled})
    assert result.ok is True
    assert "character_sheet_payload" in result.data
    assert len(result.data["panel_payloads"]) == 6

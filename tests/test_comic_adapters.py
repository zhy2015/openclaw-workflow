from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_SKILLS = Path('/Users/hidream/.openclaw/workspace/skills')
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.infra.comic_adapters import (
    AdapterValidationError,
    AnimeAvatarAdapter,
    BaoyuComicAdapter,
    ComicScriptAdapter,
    ComiCogAdapter,
    ScriptGenerateInput,
)


def test_script_generate_input_rejects_invalid_panels():
    try:
        ScriptGenerateInput.from_params({"topic": "x", "panels": 0})
    except AdapterValidationError as e:
        assert "positive integer" in str(e)
    else:
        raise AssertionError("expected AdapterValidationError")


def test_baoyu_plan_returns_expected_contract():
    adapter = BaoyuComicAdapter(workspace_root=REPO_ROOT, skills_root=WORKSPACE_SKILLS)
    result = adapter.plan_knowledge_comic(
        {
            "topic": "Recursion Explained",
            "source_text": "Recursion is when a function calls itself.",
            "art": "manga",
            "tone": "neutral",
            "layout": "standard",
            "aspect": "3:4",
            "lang": "en",
        }
    )
    assert result["source_skill"] == "baoyu-comic"
    assert result["output_dir"].startswith("comic/")
    assert "--art manga" in result["command_preview"]


def test_comic_script_adapter_runs_storyboard_contract():
    adapter = ComicScriptAdapter(workspace_root=REPO_ROOT, skills_root=WORKSPACE_SKILLS)
    result = adapter.generate_script_scaffold({"topic": "Hero Journey", "panels": 3})
    assert result["source_skill"] == "comic-script"
    assert result["panels"] == 3
    assert "Storyboard" in result["script_outline"]


def test_anime_avatar_adapter_returns_prompt_contract():
    adapter = AnimeAvatarAdapter(workspace_root=REPO_ROOT, skills_root=WORKSPACE_SKILLS)
    result = adapter.build_avatar_prompt({
        "character_prompt": "young hero with silver hair",
        "style": "manga",
        "mode": "max",
    })
    assert result["source_skill"] == "anime-avatar-generation"
    assert "young hero with silver hair" in result["avatar_prompt"]


def test_comi_cog_adapter_returns_render_contract():
    adapter = ComiCogAdapter(workspace_root=REPO_ROOT, skills_root=WORKSPACE_SKILLS)
    result = adapter.build_render_prompt({
        "story_prompt": "panel 1 hero enters the room",
        "format": "page",
        "chat_mode": "agent",
    })
    assert result["source_skill"] == "comi-cog"
    assert "panel 1 hero enters the room" in result["render_prompt"]

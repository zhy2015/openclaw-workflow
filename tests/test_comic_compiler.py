from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.infra.comic_compiler import ComicScriptCompiler, build_hidream_payloads


def test_compiler_returns_strong_json_shape():
    compiled = ComicScriptCompiler().compile("赛博朋克算命局")
    assert "global_settings" in compiled
    assert "panel_array" in compiled
    assert len(compiled["panel_array"]) == 6
    assert compiled["panel_array"][0]["shot_type"]
    assert compiled["panel_array"][0]["visual_prompt"]


def test_hidream_payload_builder_returns_character_and_panels():
    compiled = ComicScriptCompiler().compile("赛博朋克算命局")
    payloads = build_hidream_payloads(compiled)
    assert "character_sheet_payload" in payloads
    assert "panel_payloads" in payloads
    assert len(payloads["panel_payloads"]) == 6
    assert payloads["panel_payloads"][0]["model_hint"] == "hidream-api-gen"

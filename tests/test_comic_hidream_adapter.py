from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.infra.comic_compiler import ComicScriptCompiler, build_hidream_payloads
from core.infra.comic_hidream_adapter import ComicHiDreamAdapter


SKILLS_ROOT = "/Users/hidream/.openclaw/workspace/skills"


def test_comic_hidream_adapter_adapts_requests():
    compiled = ComicScriptCompiler().compile("倒悬的钟楼")
    payloads = build_hidream_payloads(compiled)
    bundle = ComicHiDreamAdapter(SKILLS_ROOT).adapt_payloads(payloads)
    assert bundle["character_sheet_request"]["model"] == "seedream"
    assert len(bundle["panel_requests"]) == 6
    assert bundle["panel_requests"][0]["panel_number"] == 1

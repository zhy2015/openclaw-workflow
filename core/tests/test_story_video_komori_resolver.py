from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from komori_resolver import KomoriResolver  # noqa: E402


def test_komori_resolver_finds_local_asset_without_download(tmp_path):
    resolver = KomoriResolver(str(tmp_path))
    path = resolver.resolve(["knocking", "iron", "door"])
    assert path is not None
    assert Path(path).exists()
    assert path.endswith('.mp3')

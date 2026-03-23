from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audio_mixer as audio_mixer_module  # noqa: E402
from audio_mixer import AudioMixer  # noqa: E402


def test_audio_mixer_sfx_fallback_generates_local_asset(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_mixer_module, 'KomoriResolver', None)
    monkeypatch.setattr(audio_mixer_module, 'search_sfx', None)
    monkeypatch.setattr(audio_mixer_module, 'match_sfx_for_scene', None)
    mixer = AudioMixer(str(tmp_path))
    path = mixer._resolve_sfx_asset('light_switch', 0.18)
    assert path is not None
    assert Path(path).exists()
    assert path.endswith('.mp3')

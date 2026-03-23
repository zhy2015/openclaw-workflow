from __future__ import annotations

import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import audio_mixer as audio_mixer_module  # noqa: E402
from audio_mixer import AudioMixer  # noqa: E402
from media_runtime import resolve_binary  # noqa: E402


def test_audio_mixer_generates_bgm_mix(tmp_path, monkeypatch):
    ffmpeg_bin = resolve_binary("ffmpeg")
    voice_path = tmp_path / "voice.mp3"

    subprocess.run(
        [
            ffmpeg_bin,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:sample_rate=44100:duration=1.2",
            "-c:a",
            "libmp3lame",
            str(voice_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    monkeypatch.setattr(audio_mixer_module, "KomoriResolver", None)
    monkeypatch.setattr(audio_mixer_module, "search_sfx", None)
    monkeypatch.setattr(audio_mixer_module, "match_sfx_for_scene", None)
    mixer = AudioMixer(str(tmp_path))
    result = mixer.mix_scene_audio(
        str(voice_path),
        {
            "bgm": {"style": "ambient hopeful", "duck_under_voice": True, "target_level_db": -22},
            "sfx": [
                {"type": "wind", "timing": 0.2},
                {"type": "train_rumble", "timing": 0.8},
            ],
        },
    )

    assert result["audio"] is not None
    assert Path(result["audio"]).exists()
    assert any(note.startswith("bgm_synthesized:") for note in result["mix_notes"])
    assert "ducking_applied" in result["mix_notes"]
    assert "sfx_resolved:2" in result["mix_notes"]
    assert "resolver_chain:komori_local>sfx_generator>procedural_fallback" in result["mix_notes"]

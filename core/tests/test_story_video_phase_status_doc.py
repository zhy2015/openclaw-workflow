from pathlib import Path


def test_story_video_phase_status_doc_exists_and_mentions_current_layers():
    path = Path('/root/.openclaw/workspace/skills/one-story-video/04-orchestration/story-to-video-director/PHASE_STATUS.md')
    assert path.exists()
    text = path.read_text(encoding='utf-8')
    assert 'Phase A' in text
    assert 'Phase B' in text
    assert 'Phase C' in text
    assert 'audio_edit_plan.json' in text
    assert 'crossfade_ms' in text
    assert 'run_story_video_regression.sh' in text

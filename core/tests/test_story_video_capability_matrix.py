from pathlib import Path


def test_story_video_phase_status_contains_capability_matrix():
    path = Path('/root/.openclaw/workspace/skills/one-story-video/04-orchestration/story-to-video-director/PHASE_STATUS.md')
    text = path.read_text(encoding='utf-8')
    assert 'Capability Matrix' in text
    assert '| Capability | Plan | Execute | Trace |' in text
    assert 'BGM resolve/mix' in text
    assert 'SFX resolve/mix' in text
    assert 'Dialog normalize' in text
    assert 'Transition crossfade' in text

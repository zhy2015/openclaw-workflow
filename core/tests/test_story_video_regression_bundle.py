from pathlib import Path


def test_story_video_regression_bundle_inventory():
    root = Path('/root/.openclaw/workspace/core/tests')
    expected = [
        'test_story_video_schema_resume.py',
        'test_story_video_audio_mixer.py',
        'test_story_video_komori_resolver.py',
        'test_story_video_sfx_fallback.py',
        'test_story_video_edit_plans.py',
        'test_story_video_composer_interface.py',
        'test_story_video_crossfade.py',
        'test_story_video_dialog_normalize.py',
        'test_story_video_execution_trace.py',
        'test_story_video_manifest_trace.py',
        'test_story_video_phase_status_doc.py',
        'test_story_video_capability_matrix.py',
        'test_story_video_manifest_capability_coverage.py',
        'test_story_video_manifest_capability_summary.py',
        'test_story_video_capability_consistency.py',
        'test_story_video_visual_qa.py',
        'test_story_video_transition_mixed_fallback.py',
        'test_story_video_transition_modes.py',
        'test_story_video_quasi_e2e_workflow.py',
        'test_story_video_summary_renderer.py',
    ]
    missing = [name for name in expected if not (root / name).exists()]
    assert missing == []

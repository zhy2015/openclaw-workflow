#!/usr/bin/env bash
set -euo pipefail
cd /root/.openclaw/workspace
pytest -q \
  core/tests/test_story_video_schema_resume.py \
  core/tests/test_story_video_audio_mixer.py \
  core/tests/test_story_video_komori_resolver.py \
  core/tests/test_story_video_sfx_fallback.py \
  core/tests/test_story_video_edit_plans.py \
  core/tests/test_story_video_composer_interface.py \
  core/tests/test_story_video_crossfade.py \
  core/tests/test_story_video_dialog_normalize.py \
  core/tests/test_story_video_execution_trace.py \
  core/tests/test_story_video_manifest_trace.py \
  core/tests/test_story_video_phase_status_doc.py \
  core/tests/test_story_video_capability_matrix.py \
  core/tests/test_story_video_manifest_capability_coverage.py \
  core/tests/test_story_video_manifest_capability_summary.py \
  core/tests/test_story_video_capability_consistency.py \
  core/tests/test_story_video_transition_mixed_fallback.py \
  core/tests/test_story_video_transition_modes.py \
  core/tests/test_story_video_end_to_end_smoke.py \
  core/tests/test_story_video_quasi_e2e_workflow.py \
  core/tests/test_story_video_summary_renderer.py \
  core/tests/test_story_video_regression_bundle.py

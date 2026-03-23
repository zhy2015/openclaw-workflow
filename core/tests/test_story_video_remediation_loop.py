from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from remediation import SceneRemediator  # noqa: E402
from schema import Project, Scene  # noqa: E402
from summary_renderer import StoryVideoSummaryRenderer  # noqa: E402
from workflow import Director  # noqa: E402


def _scene(scene_id: str, index: int, flags: list[str], qa_status: str = "review") -> Scene:
    qa_report = {
        "scene_id": scene_id,
        "status": qa_status,
        "flags": flags,
        "continuity_strength": 0.5,
        "prompt_text_risk": {
            "risk_score": 0.7 if "text_gibberish_risk" in flags else 0.0,
            "reasons": ["text_artifact_terms=text"] if "text_gibberish_risk" in flags else [],
            "artifact_hits": ["text"] if "rendered_text_artifact" in flags or "text_gibberish_risk" in flags else [],
        },
        "repetition": {"duplicate": "repeat_segment_risk" in flags, "reasons": ["same_shot_and_motion"]},
        "direction": {"conflict": "reverse_motion_risk" in flags, "reasons": ["direction_reversal=left->right"], "current_directions": ["right"]},
        "visual_video_report": {
            "text_artifact": {"risk_score": 0.8 if "rendered_text_artifact" in flags else 0.0},
            "repetition": {"risk_score": 0.9 if "rendered_repeated_shot" in flags else 0.0},
            "motion": {"conflict": "rendered_motion_conflict" in flags},
        },
        "cross_scene_video_reuse": {"reuse_detected": "cross_scene_video_reuse" in flags},
    }
    return Scene(
        index=index,
        scene_id=scene_id,
        narration_text=f"narration {scene_id}",
        visual_prompt="hero runs through the city with cinematic style",
        shot_type="wide shot",
        movement="forward tracking",
        motion_direction="left",
        subject_anchor="hero",
        environment_anchor="city",
        prop_anchor="core",
        continuity_anchor="hero|city|core",
        entry_state="arrive at gate",
        exit_state="leave the gate",
        forbidden_elements=["watermark"],
        quality_notes=["base"],
        qa_report=qa_report,
    )


def test_scene_remediator_classifies_and_rewrites_multiple_failure_modes():
    remediator = SceneRemediator(max_attempts=2)
    scene = _scene(
        "scene_01",
        1,
        ["rendered_text_artifact", "rendered_repeated_shot", "rendered_motion_conflict", "weak_continuity_anchor", "text_gibberish_risk"],
        qa_status="fail",
    )
    project = Project(
        id="proj_remediate",
        story_prompt="x",
        scenes=[scene],
        qa_report={"overall_status": "fail", "summary": {"flagged_scene_ids": ["scene_01"]}},
    )

    plan = remediator.plan_project_remediation(project)
    assert plan.summary["planned_retry_count"] == 1
    scene_plan = plan.scene_plans[0]
    assert scene_plan.should_retry is True
    assert scene_plan.failure_modes[:3] == ["text_artifact", "repeated_shot", "motion_conflict"]

    record = remediator.rewrite_scene_in_place(scene, scene_plan)
    assert "zero readable text" in scene.visual_prompt
    assert "distinctly new composition" in scene.visual_prompt
    assert "continue left movement only" in scene.visual_prompt
    assert "ui overlay" in scene.forbidden_elements
    assert "remediation:text_artifact_hardening" in scene.quality_notes
    assert record["attempt"] == 1


def test_scene_remediator_honors_retry_budget():
    remediator = SceneRemediator(max_attempts=1)
    scene = _scene("scene_02", 2, ["rendered_text_artifact"], qa_status="review")
    scene.remediation_history = [{"attempt": 1, "status_after": "review"}]
    project = Project(
        id="proj_budget",
        story_prompt="x",
        scenes=[scene],
        qa_report={"overall_status": "review", "summary": {"flagged_scene_ids": ["scene_02"]}},
    )

    plan = remediator.plan_project_remediation(project)
    assert plan.scene_plans[0].should_retry is False
    assert plan.scene_plans[0].blocked_reason == "retry_budget_exhausted"
    assert plan.summary["exhausted_scene_ids"] == ["scene_02"]


def test_scene_remediator_escalates_persistent_repeated_shot_on_second_attempt():
    remediator = SceneRemediator(max_attempts=3)
    scene = _scene("scene_03", 3, ["rendered_repeated_shot"], qa_status="review")
    scene.remediation_history = [
        {
            "attempt": 1,
            "failure_modes": ["repeated_shot"],
            "status_after": "review",
            "plan": {"failure_modes": ["repeated_shot"]},
        }
    ]
    project = Project(
        id="proj_repeat_escalate",
        story_prompt="x",
        scenes=[scene],
        qa_report={"overall_status": "review", "summary": {"flagged_scene_ids": ["scene_03"]}},
    )

    plan = remediator.plan_project_remediation(project)
    scene_plan = plan.scene_plans[0]
    assert scene_plan.should_retry is True
    assert scene_plan.escalation_level == 2
    assert "persistent_repeated_shot_promoted" in scene_plan.policy_flags
    assert plan.summary["repeated_shot_escalated_scene_ids"] == ["scene_03"]
    assert plan.summary["persistent_repeated_shot_promoted_count"] == 1


def test_director_manifest_includes_remediation_fields(tmp_path):
    director = Director(str(tmp_path))
    scene = _scene("scene_00", 0, ["rendered_text_artifact"], qa_status="review")
    scene.remediation_history = [{"attempt": 1, "failure_modes": ["text_artifact"], "result": {"status": "pass"}}]
    scene.remediation_summary = {"attempts": 1, "failure_modes": ["text_artifact"], "last_status": "pass"}
    project = Project(
        id="proj_manifest",
        story_prompt="prompt",
        workspace_dir=str(tmp_path),
        scenes=[scene],
        qa_report={"overall_status": "review", "summary": {"flagged_scene_ids": ["scene_00"]}},
        remediation_plan={"summary": {"planned_retry_count": 1}},
        remediation_history=[{"scene_id": "scene_00", "attempt": 1}],
        remediation_summary={"planned_retry_count": 1, "history_count": 1, "retried_scene_ids": ["scene_00"], "remaining_flagged_scene_ids": []},
    )

    director.build_manifest(project)
    manifest = json.loads(Path(director.manifest_file).read_text(encoding="utf-8"))
    assert manifest["remediation_summary"]["history_count"] == 1
    assert manifest["scenes"][0]["remediation_summary"]["last_status"] == "pass"
    assert manifest["rendered_summary"]["chat_text"].find("retry_planned=1") >= 0


def test_summary_renderer_surfaces_remediation_section():
    renderer = StoryVideoSummaryRenderer()
    result = renderer.render({
        "project_id": "proj_sum",
        "scene_count": 1,
        "scenes": [{"scene_id": "scene_00", "status": "done"}],
        "capability_report": {"enabled": [], "missing": [], "grouped": {}, "coverage_ratio": 0.1},
        "downstream_outputs": {"dashboard_stats": {"enabled_count": 0, "missing_count": 0, "coverage_ratio": 0.1}},
        "qa_report": {"overall_status": "review", "review_count": 1, "fail_count": 0, "summary": {"flagged_scene_ids": ["scene_00"]}},
        "remediation_summary": {"planned_retry_count": 1, "history_count": 1, "retried_scene_ids": ["scene_00"], "remaining_flagged_scene_ids": []},
    })
    titles = [section["title"] for section in result["sections"]]
    assert "Remediation" in titles
    assert "retried=scene_00" in result["chat_text"]

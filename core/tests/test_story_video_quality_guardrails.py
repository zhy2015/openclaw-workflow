from __future__ import annotations

import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from schema import Scene, Project
from story_video_quality import build_scene_qc, aggregate_project_qc, infer_text_risk
from story_planner import StoryPlanner
from visual_director import VisualDirector
from summary_renderer import StoryVideoSummaryRenderer


def test_story_planner_emits_continuity_and_motion_metadata():
    planner = StoryPlanner(api_key="")
    plan = planner.plan_story("一个人穿过沙漠废墟找到能量核心，最终点亮希望。要求：做成1分钟电影感短片")
    assert plan.schema_version == "v1alpha3"
    assert plan.scenes
    first = plan.scenes[0]
    assert first.continuity_anchor
    assert first.motion_direction
    assert isinstance(first.forbidden_elements, list) and first.forbidden_elements


def test_scene_qc_detects_duplicate_and_reverse_motion():
    prev = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="K runs left through the tunnel holding the green core.",
        visual_prompt="same masked hero, no text, running left through tunnel",
        action_anchor="run left through tunnel holding core",
        movement="leftward tracking",
        motion_direction="left",
        subject_anchor="same masked hero",
        environment_anchor="same tunnel",
        prop_anchor="green core",
        continuity_anchor="hero|tunnel|core",
    )
    curr = Scene(
        index=1,
        scene_id="scene_01",
        narration_text="K runs right through the tunnel holding the green core.",
        visual_prompt="same masked hero, no text, running right through tunnel",
        action_anchor="run right through tunnel holding core",
        movement="rightward tracking",
        motion_direction="right",
        subject_anchor="same masked hero",
        environment_anchor="same tunnel",
        prop_anchor="green core",
        continuity_anchor="hero|tunnel|core",
    )
    qc = build_scene_qc(curr, prev)
    assert "reverse_motion_risk" in qc["flags"]

    dup = Scene(
        index=2,
        scene_id="scene_02",
        narration_text=curr.narration_text,
        visual_prompt=curr.visual_prompt,
        action_anchor=curr.action_anchor,
        movement=curr.movement,
        motion_direction=curr.motion_direction,
        subject_anchor=curr.subject_anchor,
        environment_anchor=curr.environment_anchor,
        prop_anchor=curr.prop_anchor,
        continuity_anchor=curr.continuity_anchor,
        shot_type="medium shot",
    )
    curr.shot_type = "medium shot"
    qc_dup = build_scene_qc(dup, curr)
    assert "repeat_segment_risk" in qc_dup["flags"]


def test_prompt_quality_flags_text_artifacts():
    report = infer_text_risk("cinematic hero shot with giant neon TEXT LOGO banner watermark watermark watermark")
    assert report["risk_score"] >= 0.45
    assert report["artifact_hits"]


def test_project_qc_and_summary_include_qa_section():
    planner = StoryPlanner(api_key="")
    director = VisualDirector()
    plan = planner.plan_story("主角进入地铁，拿到核心，冲出地面，最终看到新生")
    visuals = director.create_visual_plan(plan)
    scenes = director.to_scenes(plan, visuals)
    project = Project(id="proj_qc", story_prompt="x", scenes=scenes)
    qa_report = aggregate_project_qc(project)
    assert qa_report["scene_count"] == len(scenes)

    manifest = {
        "project_id": project.id,
        "scene_count": len(scenes),
        "scenes": [{"status": "done"} for _ in scenes],
        "capability_report": {"enabled": ["qa_report"], "missing": [], "grouped": {}, "coverage_ratio": 1.0},
        "qa_report": qa_report,
    }
    rendered = StoryVideoSummaryRenderer().render(manifest)
    qa_titles = [section["title"] for section in rendered["sections"]]
    assert "QA" in qa_titles

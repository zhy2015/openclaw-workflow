from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = WORKSPACE_ROOT / "skills" / "one-story-video" / "04-orchestration" / "story-to-video-director" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from schema import Project, Scene  # noqa: E402
from story_video_quality import (  # noqa: E402
    aggregate_project_qc,
    analyze_motion_direction,
    build_scene_qc,
    build_visual_qa_report,
    compare_video_segments_for_reuse,
    heuristic_text_artifact_scan,
    sample_video_frames,
)


def _ffmpeg_bin() -> str:
    return str(WORKSPACE_ROOT / "bin" / "ffmpeg")


def _png_frame(path: Path, color: str, draw_text: str | None = None, x: int = 30, y: int = 90):
    image = Image.new("RGB", (320, 240), color=color)
    if draw_text:
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 176, 320, 239), fill="black")
        draw.rectangle((x, 184, min(310, x + 120), 226), fill="white")
        draw.text((x + 8, 192), draw_text, fill="black")
    image.save(path)


def _render_video_from_frames(ffmpeg: str, frames_dir: Path, out_path: Path, fps: int = 4):
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%03d.png"),
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            str(out_path),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def test_visual_qa_detects_overlay_text_and_motion_conflict(tmp_path):
    ffmpeg = _ffmpeg_bin()
    frames = tmp_path / "frames"
    frames.mkdir()
    positions = [40, 90, 140, 190]
    for idx, x in enumerate(positions, start=1):
        _png_frame(frames / f"frame_{idx:03d}.png", color="#334455", draw_text="SALE", x=x)

    video_path = tmp_path / "overlay_motion.mp4"
    _render_video_from_frames(ffmpeg, frames, video_path)

    report = build_visual_qa_report(str(video_path), expected_direction="left", ffmpeg_bin=ffmpeg)
    assert report["status"] in {"review", "fail"}
    assert "detected_text_artifact" in report["flags"]
    assert "detected_motion_direction_conflict" in report["flags"]


def test_visual_qa_detects_repeated_frames_and_cross_scene_reuse(tmp_path):
    ffmpeg = _ffmpeg_bin()
    frames_a = tmp_path / "frames_a"
    frames_b = tmp_path / "frames_b"
    frames_a.mkdir()
    frames_b.mkdir()

    for idx in range(1, 5):
        _png_frame(frames_a / f"frame_{idx:03d}.png", color="#117733")
        _png_frame(frames_b / f"frame_{idx:03d}.png", color="#117733")

    video_a = tmp_path / "static_a.mp4"
    video_b = tmp_path / "static_b.mp4"
    _render_video_from_frames(ffmpeg, frames_a, video_a)
    _render_video_from_frames(ffmpeg, frames_b, video_b)

    report_a = build_visual_qa_report(str(video_a), ffmpeg_bin=ffmpeg)
    report_b = build_visual_qa_report(str(video_b), ffmpeg_bin=ffmpeg)
    assert "detected_repeated_shot" in report_a["flags"]

    reuse = compare_video_segments_for_reuse(report_a, report_b)
    assert reuse["reuse_detected"] is True
    assert reuse["risk_score"] >= 0.7


def test_scene_qc_embeds_visual_report_and_project_summary(tmp_path):
    ffmpeg = _ffmpeg_bin()
    frames = tmp_path / "frames_scene"
    frames.mkdir()
    for idx, x in enumerate([30, 60, 90, 120], start=1):
        _png_frame(frames / f"frame_{idx:03d}.png", color="#222244", draw_text="TXT", x=x)
    video_path = tmp_path / "scene_visual.mp4"
    _render_video_from_frames(ffmpeg, frames, video_path)

    prev = Scene(
        index=0,
        scene_id="scene_00",
        narration_text="Hero runs left.",
        visual_prompt="hero running left with no text",
        action_anchor="run left",
        movement="leftward tracking",
        motion_direction="left",
        subject_anchor="hero",
        environment_anchor="hall",
        prop_anchor="core",
        continuity_anchor="hero|hall|core",
        video_path=str(video_path),
    )
    curr = Scene(
        index=1,
        scene_id="scene_01",
        narration_text="Hero runs right with overlay letters.",
        visual_prompt="hero running right with clean frame",
        action_anchor="run right",
        movement="rightward tracking",
        motion_direction="left",
        subject_anchor="hero",
        environment_anchor="hall",
        prop_anchor="core",
        continuity_anchor="hero|hall|core",
        video_path=str(video_path),
    )
    prev.qa_report = build_scene_qc(prev, None)
    qc = build_scene_qc(curr, prev)
    assert qc["visual_video_report"] is not None
    assert "rendered_text_artifact" in qc["flags"]
    assert "cross_scene_video_reuse" in qc["flags"]

    project = Project(id="proj_visual_qc", story_prompt="x", scenes=[prev, curr])
    report = aggregate_project_qc(project)
    assert report["overall_status"] in {"review", "fail"}
    assert "scene_01" in report["summary"]["flagged_scene_ids"]


def test_frame_sampling_and_text_heuristic_work_without_ocr(tmp_path):
    image = Image.new("RGB", (320, 240), color="#111111")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 176, 320, 239), fill="black")
    draw.rectangle((50, 184, 220, 226), fill="white")
    draw.text((60, 192), "HELLO", fill="black")
    report = heuristic_text_artifact_scan(image)
    assert report["risk_score"] > 0.2

    ffmpeg = _ffmpeg_bin()
    frames = tmp_path / "frames_sample"
    frames.mkdir()
    for idx in range(1, 5):
        _png_frame(frames / f"frame_{idx:03d}.png", color=f"#{idx}{idx}{idx}444")
    video = tmp_path / "sample.mp4"
    _render_video_from_frames(ffmpeg, frames, video)
    sampled = sample_video_frames(str(video), max_samples=3, ffmpeg_bin=ffmpeg)
    assert len(sampled) == 3
    assert all(item.get("average_hash") for item in sampled)

    motion = analyze_motion_direction(sampled, expected_direction="right")
    assert "expected_direction" in motion

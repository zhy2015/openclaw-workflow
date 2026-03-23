#!/usr/bin/env python3
"""Task-node-based skill visibility router (v1 skeleton)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

TASK_KEYWORDS = {
    "memory": ["记忆", "memory", "蒸馏", "归档", "检索", "日志"],
    "media": ["视频", "音频", "图片", "配音", "图像", "render", "ffmpeg"],
    "monitoring": ["抓取", "scrape", "crawl", "监控", "网页", "搜索", "playwright"],
    "automation": ["自动化", "workflow", "批处理", "代理", "脚本", "执行"],
    "governance": ["skill", "治理", "路由", "manifest", "registry", "治理层"],
    "coding": ["代码", "bug", "debug", "修复", "重构", "开发"],
    "social": ["消息", "社交", "发帖", "moltbook", "通知"],
}


def infer_task_nodes(text: str) -> List[str]:
    lowered = text.lower()
    hits = []
    for node, keywords in TASK_KEYWORDS.items():
        if any(k.lower() in lowered for k in keywords):
            hits.append(node)
    return hits or ["automation"]


def load_manifests() -> List[Dict]:
    manifests = []
    for path in sorted(SKILLS_DIR.glob("*/manifest.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            data["_path"] = str(path)
            manifests.append(data)
        except Exception:
            continue
    return manifests


def filter_visible_skills(task_nodes: List[str], startup_mode: bool = False) -> List[Dict]:
    manifests = load_manifests()
    visible = []
    for manifest in manifests:
        status = manifest.get("status", "experimental")
        visibility = manifest.get("visibility", "public")
        manifest_nodes = set(manifest.get("task_nodes", []))
        routing = manifest.get("routing", {}) if isinstance(manifest.get("routing"), dict) else {}
        startup_expose = routing.get("startup_expose", True)

        if status not in {"active", "experimental"}:
            continue
        if visibility not in {"public", "internal"}:
            continue
        if startup_mode and startup_expose is False:
            continue
        if not manifest_nodes:
            if status == "experimental":
                continue
        elif not (manifest_nodes & set(task_nodes)):
            continue

        visible.append({
            "name": manifest.get("name"),
            "task_nodes": manifest.get("task_nodes", []),
            "status": status,
            "visibility": visibility,
            "category": manifest.get("category"),
            "startup_expose": startup_expose,
        })
    return visible


def filter_startup_skills(task_nodes: List[str]) -> List[Dict]:
    return filter_visible_skills(task_nodes, startup_mode=True)


def route(text: str) -> Dict:
    nodes = infer_task_nodes(text)
    return {
        "query": text,
        "task_nodes": nodes,
        "visible_skills": filter_visible_skills(nodes),
    }


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "memory maintenance"
    print(json.dumps(route(query), indent=2, ensure_ascii=False))

#!/usr/bin/env python3
"""Audit local skill manifests against governance rules."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Dict, List, Set

ROOT = Path("/root/.openclaw/workspace")
SKILLS_DIR = ROOT / "skills"
USAGE_CSV = ROOT / "memory/metrics/skill_usage.csv"
REPORT_PATH = ROOT / "skills/skill_audit_report.json"

REQUIRED_FIELDS = ["name", "version", "category", "actions"]
GOVERNANCE_FIELDS = ["task_nodes", "status", "visibility", "owner", "last_verified_at"]
VALID_STATUS = {"active", "archived", "experimental", "deprecated"}
VALID_VISIBILITY = {"public", "internal", "hidden"}


def load_usage_counter() -> Counter:
    counter: Counter = Counter()
    if not USAGE_CSV.exists():
        return counter
    success_aliases = {"success", "completed", "ok"}
    for line in USAGE_CSV.read_text(encoding="utf-8", errors="ignore").splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 4 and parts[3].lower() in success_aliases:
            counter[parts[1]] += 1
    return counter


def load_gitlink_skills() -> Set[str]:
    try:
        out = subprocess.check_output(
            ["git", "ls-files", "-s", "skills"],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        return set()

    gitlinks: Set[str] = set()
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "160000":
            path = parts[3]
            if path.startswith("skills/"):
                gitlinks.add(path.split("/", 1)[1])
    return gitlinks


def classify_skill(path: Path, manifest: Dict, usage_counter: Counter, gitlinks: Set[str]) -> Dict:
    skill_dir = path.parent
    skill_name = manifest.get("name", skill_dir.name)
    issues: List[str] = []
    suggestions: List[str] = []

    for field in REQUIRED_FIELDS:
        if field not in manifest:
            issues.append(f"missing required field: {field}")

    for field in GOVERNANCE_FIELDS:
        if field not in manifest:
            issues.append(f"missing governance field: {field}")

    status = manifest.get("status")
    visibility = manifest.get("visibility")
    is_gitlink = skill_dir.name in gitlinks

    if status and status not in VALID_STATUS:
        issues.append(f"invalid status: {status}")
    if visibility and visibility not in VALID_VISIBILITY:
        issues.append(f"invalid visibility: {visibility}")

    if not (skill_dir / "SKILL.md").exists():
        issues.append("missing SKILL.md trigger contract")

    if is_gitlink:
        issues.append("external gitlink/submodule skill boundary")
        suggestions.append("govern inside the child repo or convert to normal workspace directory before direct edits")

    usage = usage_counter[skill_name]
    if usage == 0:
        suggestions.append("no successful usage found; consider experimental or archived")
    elif usage > 0 and status in {None, "experimental"}:
        suggestions.append("has usage; consider promoting to active if stable")

    if manifest.get("category") and not manifest.get("task_nodes"):
        suggestions.append("add task_nodes for task-first routing")

    if status == "active" and visibility == "public" and usage == 0:
        suggestions.append("active+public but no ROI evidence yet; verify necessity")

    return {
        "skill": skill_name,
        "path": str(skill_dir),
        "usage_count": usage,
        "status": status,
        "visibility": visibility,
        "is_gitlink": is_gitlink,
        "issues": issues,
        "suggestions": suggestions,
    }


def main():
    usage_counter = load_usage_counter()
    gitlinks = load_gitlink_skills()
    reports = []

    for manifest_path in sorted(SKILLS_DIR.glob("*/manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            reports.append({
                "skill": manifest_path.parent.name,
                "path": str(manifest_path.parent),
                "is_gitlink": manifest_path.parent.name in gitlinks,
                "issues": [f"manifest unreadable: {e}"],
                "suggestions": ["fix manifest JSON first"],
            })
            continue
        reports.append(classify_skill(manifest_path, manifest, usage_counter, gitlinks))

    summary = {
        "total_skills": len(reports),
        "missing_governance_fields": sum(1 for r in reports if any("missing governance field" in i for i in r.get("issues", []))),
        "missing_skill_md": sum(1 for r in reports if any("missing SKILL.md" in i for i in r.get("issues", []))),
        "gitlink_skills": sum(1 for r in reports if r.get("is_gitlink")),
        "zero_usage": sum(1 for r in reports if r.get("usage_count", 0) == 0),
        "active_public": sum(1 for r in reports if r.get("status") == "active" and r.get("visibility") == "public"),
    }

    payload = {"summary": summary, "skills": reports}
    REPORT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

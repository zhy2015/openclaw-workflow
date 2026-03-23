#!/usr/bin/env python3
"""Compact governance status summary for heartbeat / ops review."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace')
AUDIT = ROOT / 'skills/skill_audit_report.json'
SNAPSHOT = ROOT / 'skills/skill_visibility_snapshot.json'
OUT = ROOT / 'skills/skill_governance_status.json'
ADVICE = ROOT / 'skills/skill_lifecycle_advice.json'

GOVERNANCE_FIELDS = ['task_nodes', 'status', 'visibility', 'owner', 'last_verified_at']


def has_full_governance(skill: dict) -> bool:
    issues = skill.get('issues', []) or []
    if skill.get('is_gitlink'):
        return False
    return not any(
        any(f'missing governance field: {field}' == issue for issue in issues)
        for field in GOVERNANCE_FIELDS
    )


def main():
    audit = json.loads(AUDIT.read_text(encoding='utf-8')) if AUDIT.exists() else {'summary': {}, 'skills': []}
    snapshot = json.loads(SNAPSHOT.read_text(encoding='utf-8')) if SNAPSHOT.exists() else {'nodes': {}}
    advice = json.loads(ADVICE.read_text(encoding='utf-8')) if ADVICE.exists() else {'summary': {}, 'advice': []}
    node_counts = {k: len(v) for k, v in snapshot.get('nodes', {}).items()}
    payload = {
        'audit_summary': audit.get('summary', {}),
        'visibility_counts': node_counts,
        'advice_summary': advice.get('summary', {}),
        'governed_skills': [
            s['skill'] for s in audit.get('skills', [])
            if has_full_governance(s)
        ],
        'ungoverned_skills': [
            s['skill'] for s in audit.get('skills', [])
            if not has_full_governance(s)
        ],
        'gitlink_skills': [
            s['skill'] for s in audit.get('skills', [])
            if s.get('is_gitlink')
        ],
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

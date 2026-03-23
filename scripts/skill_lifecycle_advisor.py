#!/usr/bin/env python3
"""Generate lifecycle recommendations from audit + ROI + visibility data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path('/root/.openclaw/workspace')
AUDIT = ROOT / 'skills/skill_audit_report.json'
SNAPSHOT = ROOT / 'skills/skill_visibility_snapshot.json'
OUT = ROOT / 'skills/skill_lifecycle_advice.json'


def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return default


def visibility_map(snapshot: Dict) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for _, skills in snapshot.get('nodes', {}).items():
        for s in skills:
            counts[s['name']] = counts.get(s['name'], 0) + 1
    return counts


def advise(skill: Dict, exposure_count: int) -> List[Dict]:
    status = skill.get('status')
    visibility = skill.get('visibility')
    usage = skill.get('usage_count', 0)
    issues = skill.get('issues', [])
    suggestions = []

    missing_governance = any('missing governance field' in i for i in issues)
    missing_skill_md = any('missing SKILL.md' in i for i in issues)
    is_gitlink = skill.get('is_gitlink', False)

    if is_gitlink:
        suggestions.append({
            'type': 'boundary_fix',
            'priority': 'high',
            'reason': '该 skill 是 gitlink/submodule，父仓治理写入不可直接提交，应在子仓治理或解除边界后再治理',
            'suggested_state': status or 'experimental',
        })

    if missing_governance:
        suggestions.append({
            'type': 'govern',
            'priority': 'high',
            'reason': '缺少治理字段，无法稳定进入 task-node routing',
            'suggested_state': 'experimental',
        })

    if missing_skill_md:
        suggestions.append({
            'type': 'fix_contract',
            'priority': 'high',
            'reason': '缺少 SKILL.md 触发契约',
            'suggested_state': status or 'experimental',
        })

    if status == 'experimental' and usage >= 1 and exposure_count >= 1 and not is_gitlink:
        suggestions.append({
            'type': 'promote',
            'priority': 'medium',
            'reason': '已有成功使用记录，且已进入可见面，可考虑晋升 active',
            'suggested_state': 'active',
        })

    if status == 'active' and visibility == 'public' and usage == 0:
        suggestions.append({
            'type': 'downgrade',
            'priority': 'medium',
            'reason': 'active+public 但暂无 ROI 证据，建议降为 experimental 或限制曝光',
            'suggested_state': 'experimental',
        })

    if ((status is None and usage == 0) or (status == 'experimental' and usage == 0 and exposure_count == 0)) and not is_gitlink:
        suggestions.append({
            'type': 'archive_candidate',
            'priority': 'low',
            'reason': '暂无 ROI，且未进入默认可见面，可作为归档候选',
            'suggested_state': 'archived',
        })

    if visibility == 'internal' and usage >= 1 and not is_gitlink:
        suggestions.append({
            'type': 'keep_internal',
            'priority': 'low',
            'reason': '已有使用记录，当前 internal 可见性合理',
            'suggested_state': status or 'active',
        })

    return suggestions


def main():
    audit = load_json(AUDIT, {'skills': [], 'summary': {}})
    snapshot = load_json(SNAPSHOT, {'nodes': {}})
    exposure = visibility_map(snapshot)

    advice = []
    for skill in audit.get('skills', []):
        suggestions = advise(skill, exposure.get(skill['skill'], 0))
        if suggestions:
            advice.append({
                'skill': skill['skill'],
                'current_status': skill.get('status'),
                'current_visibility': skill.get('visibility'),
                'usage_count': skill.get('usage_count', 0),
                'visible_in_nodes': exposure.get(skill['skill'], 0),
                'is_gitlink': skill.get('is_gitlink', False),
                'recommendations': suggestions,
            })

    payload = {
        'summary': {
            'skills_with_advice': len(advice),
            'promote_candidates': sum(1 for a in advice if any(r['type'] == 'promote' for r in a['recommendations'])),
            'downgrade_candidates': sum(1 for a in advice if any(r['type'] == 'downgrade' for r in a['recommendations'])),
            'archive_candidates': sum(1 for a in advice if any(r['type'] == 'archive_candidate' for r in a['recommendations'])),
            'governance_fixes': sum(1 for a in advice if any(r['type'] == 'govern' for r in a['recommendations'])),
            'boundary_fixes': sum(1 for a in advice if any(r['type'] == 'boundary_fix' for r in a['recommendations'])),
        },
        'advice': advice,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

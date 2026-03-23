#!/usr/bin/env python3
"""Build governed skill visibility snapshots for common task nodes."""

from __future__ import annotations

import json
from pathlib import Path

from task_node_router import filter_visible_skills, filter_startup_skills

ROOT = Path('/root/.openclaw/workspace')
OUT = ROOT / 'skills/skill_visibility_snapshot.json'
DEFAULT_NODES = ['memory', 'media', 'monitoring', 'automation', 'governance', 'coding', 'social']


def main():
    payload = {
        'generated_at': __import__('datetime').datetime.utcnow().isoformat() + 'Z',
        'nodes': {},
        'startup_nodes': {}
    }
    for node in DEFAULT_NODES:
        payload['nodes'][node] = filter_visible_skills([node])
        payload['startup_nodes'][node] = filter_startup_skills([node])
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()

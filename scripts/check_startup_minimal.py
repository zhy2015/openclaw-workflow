#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/root/.openclaw/workspace')

required_files = [
    ROOT / 'AGENTS.md',
    ROOT / 'STARTUP_AGENT_CARD.md',
    ROOT / 'STARTUP_USER_CARD.md',
    ROOT / 'STARTUP_MEMORY_CARD.md',
    ROOT / 'STARTUP_SKILLS_CARD.md',
    ROOT / 'memory' / 'STARTUP_MEMORY_ROUTING.md',
    ROOT / 'skills' / 'STARTUP_SKILL_ROUTING.md',
    ROOT / 'memory' / 'todos' / 'active.md',
]

missing = [str(p) for p in required_files if not p.exists()]

print('STARTUP_MINIMAL_AUDIT')
print(f'workspace={ROOT}')
print(f'missing={len(missing)}')
for item in missing:
    print(f'- MISSING: {item}')

agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
checks = {
    'startup_cards_declared': 'STARTUP_AGENT_CARD.md' in agents and 'STARTUP_USER_CARD.md' in agents and 'STARTUP_MEMORY_CARD.md' in agents and 'STARTUP_SKILLS_CARD.md' in agents,
    'todos_declared': 'memory/todos/active.md' in agents,
    'heavy_memory_deferred': 'Do not read heavy memory/docs by default' in agents,
    'skills_deferred': 'Never assume all skills should be loaded or exposed.' in agents,
}
for k, v in checks.items():
    print(f'{k}={"OK" if v else "FAIL"}')

if missing or not all(checks.values()):
    raise SystemExit(1)

print('RESULT=PASS')
